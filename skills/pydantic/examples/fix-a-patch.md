# Worked example: a PATCH that rejects a nested change

Kinds: Partial. Outputs from a lab run on pydantic-partial 0.11.1,
pydantic 2.13.5.

## The ask

> PATCH /articles/1 with {"seo": {"description": "New"}} returns 422
> "seo.title Field required", although ArticlePatch is built with
> recursive=True and Seo has the mixin. Fix it.

```python
class Seo(PartialModelMixin, BaseModel):
    title: str
    description: str

class Article(PartialModelMixin, BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=5)
    body: str
    seo: Seo | None = None
    tags: list[str] = []

ArticlePatch = Article.model_as_partial(recursive=True)

def patch_article(stored: Article, body: dict) -> Article:
    patch = ArticlePatch.model_validate(body)
    return stored.model_copy(update=patch.model_dump(exclude_unset=True))
```

## Steps

1. **The installed release** (`partial/check-installed.md`):
   `uv pip show pydantic-partial` gave `Version: 0.11.1`.
2. **Probe** the handler with four bodies (`probe_patch.py`):
   ```
   {'seo': {'description': 'New'}} -> 422 [('missing', ('seo', 'title'))]
   {'title': 'Hi'} -> title='Hi' ...
   {'tags': ['b']} -> ... tags=['b']
   {'title': None} -> title=None ...
   seo field: cms.models.Seo | None
   ```
   Three problems, not one: the nested field is not partial, a title
   shorter than `min_length=5` is stored, and so is `None` for a `str`.
3. **Why `seo` is not partial**: `partial.py` line 113 makes only
   `field_info.is_required()` fields optional, and only those get the
   recursive treatment; `seo` has a default (`None`), so it keeps its
   full type (`partial/build.md`). Naming it with `"seo.*"` takes the
   other branch (line 128), which rebuilds its annotation.
4. **Why `"Hi"` and `None` got in**: the partial copy of `title` has no
   constraints and accepts `None`, and `model_copy(update=...)`
   validates nothing (`partial/validators.md`, `partial/handoff.md`).
5. **Fix**, with the recipe's `patching.py` copied to
   `src/cms/patching.py`:

```python
# recursive=True does not reach seo: it has a default. "seo.*" does.
ArticlePatch = Article.model_as_partial("title", "body", "tags", "seo.*", recursive=True)

def patch_article(stored: Article, body: dict) -> Patched[Article]:
    """PATCH /articles/{id}. A ValidationError is a 422 in the web layer."""
    return apply_patch(stored, ArticlePatch, body)
```

6. **Probe again**:
   ```
   {'seo': {'description': 'New'}} -> ... seo=Seo(title='Hello', description='New') ... | changes: {'seo': {'description': 'New'}}
   {'title': 'Hi'} -> 422 [('string_too_short', ('title',))]
   {'tags': ['b']} -> ... tags=['b'] | changes: {'tags': ['b']}
   {'title': None} -> 422 [('string_type', ('title',))]
   seo field: typing.Optional[pydantic_partial.partial.SeoPartial]
   ```
7. **Tests** for the three cases: `3 passed`. With the old
   `model_as_partial(recursive=True)` put back, `1 failed, 2 passed`:
   the nested test can fail.

## The answer

```
## Result
Three faults in PATCH /articles:
- seo has a default, and pydantic-partial 0.11.1 only makes required
  fields partial, even with recursive=True; listing it as "seo.*"
  fixes it (src/cms/models.py).
- the partial model drops min_length and accepts None for title, and
  model_copy(update=...) validated nothing: "Hi" and null were stored.
  patch_article now uses apply_patch (src/cms/patching.py), which
  validates the merged article with Article; both are 422s now.
- patch_article returns Patched: .model for the response, .changes for
  the store (only the paths the body set). The endpoint must store
  .changes; writing it as a dotted $set is the mongodb skill's part.

## Checked
- probe_patch.py before and after (outputs above).
- uv run pytest -q: 3 passed; with the old partial, 1 failed.
- pydantic 2.13.5, pydantic-partial 0.11.1.

## Not checked
- The endpoint's status codes (api skill) and the store's update
  (mongodb skill): not in this repository's tests.
```
