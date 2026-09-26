# Documents, settings and startup

Beanie 2.2.0 on PyMongo 4.18.2 and MongoDB 8.0.32, *lab*. A Beanie
`Document` is a pydantic model: fields, validators, aliases and
serialisation are the pydantic skill's. This file says what Beanie adds
and what it sends.

## A document

```python
from beanie import Document, Indexed, Link
from pymongo import ASCENDING, IndexModel

class Customer(Document):
    name: str
    email: Indexed(str, unique=True)
    address: Address                  # a pydantic BaseModel: stored embedded
    tags: list[str] = []

    class Settings:
        name = "customers"            # the collection; default is the class name
        use_revision = True           # beanie/writes.md
        indexes = [IndexModel([("name", ASCENDING)], name="name_1")]
```

`id` is the `_id` (a `PydanticObjectId` by default). `revision_id` is a
field of every document, excluded from `model_dump()`, stored only when
`use_revision` is on.

## Settings keys (from `DocumentSettings` and `ItemSettings` in 2.2.0)

| Key | Default | Effect |
| --- | --- | --- |
| `name` | `None` (class name) | collection name |
| `indexes` | `[]` | extra indexes (`beanie/indexes.md`) |
| `use_revision` | `False` | updates filter on `revision_id` and set a new one |
| `use_state_management` | `False` | `save_changes()` sends only changed paths |
| `state_management_replace_objects` | `False` | changed sub-documents are sent whole instead of as dotted paths |
| `validate_on_save` | `False` | validate before writing |
| `keep_nulls` | `True` | `False`: `None` fields are `$unset` on save |
| `projection` | `None` | the projection every find uses |
| `use_cache`, `cache_capacity`, `cache_expiration_time` | `False`, 32, 10 minutes | an in-process query cache |
| `merge_indexes`, `timeseries`, `lazy_parsing`, `bson_encoders`, `is_root`, `class_id` | | read the source before using |

`keep_nulls = False` contradicts decision M5 (`None` is stored as null,
never unset): leave it `True`.

## Startup

```python
from beanie import init_beanie
from pymongo import AsyncMongoClient

client = AsyncMongoClient(os.environ["MONGODB_URI"])
await init_beanie(database=client["shop"], document_models=[Customer, Order], skip_indexes=True)
```

`init_beanie` (2.2.0) takes `database` or `connection_string` (one of
them, else `ValueError: connection_string parameter or database
parameter must be set`), `document_models`, `allow_index_dropping`,
`recreate_views`, `skip_indexes`. *lab*, the commands it sent:

| Call | Commands |
| --- | --- |
| default | `buildInfo`, `listCollections`, then per model `listIndexes` and, when it declares indexes, `createIndexes` |
| `skip_indexes=True` | `buildInfo`, `listCollections` |
| `allow_index_dropping=True` | also `dropIndexes` for every index the model does not declare |

Why startup should skip indexes on large collections: `core/index-live.md`.
The whole startup, with a test that it sends no index commands:
`recipes/beanie_app/app/db.py`.
