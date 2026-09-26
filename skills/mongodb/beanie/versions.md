# Beanie 1.x and 2.x

Read first on any Beanie task: the version decides the client, the
startup code and some method names.

```
uv pip show beanie pymongo motor
```

## What each version depends on (read from the wheels' METADATA)

| | Beanie 2.2.0 | Beanie 1.30.0 |
| --- | --- | --- |
| driver | `pymongo>=4.11.0,!=4.15.0,<5.0.0` | `motor>=2.5.0,<4.0.0` |
| pydantic | `>=2.4,<3.0` | `>=1.10.18,<3.0` |
| Python | `>=3.10,<3.14` | `>=3.9,<4.0` |
| `init_beanie(database=...)` | `AsyncDatabase` (PyMongo) | `AsyncIOMotorDatabase` |
| `init_beanie` other arguments | `connection_string`, `document_models`, `allow_index_dropping`, `recreate_views`, `skip_indexes` | the same, plus `multiprocessing_mode` |
| the collection behind a model | `Model.get_pymongo_collection()` | `Model.get_motor_collection()` |
| sessions | `AsyncClientSession` (PyMongo) | `AsyncIOMotorClientSession` |

Beanie 2 does not install Motor. Motor 3.7.1 says it is deprecated from
May 14th, 2026, with critical fixes until May 14th, 2027
(`pymongo/clients.md`).

## Recognise the version in code

| You see | It is |
| --- | --- |
| `from motor.motor_asyncio import AsyncIOMotorClient` next to `init_beanie` | Beanie 1.x style |
| `get_motor_collection()` | Beanie 1.x |
| `from pymongo import AsyncMongoClient` | Beanie 2.x style |
| `get_pymongo_collection()` | Beanie 2.x |

## Mixing them (*lab*)

- **Motor client, Beanie 2.2.0** (Motor 3.7.1 installed by hand):
  `init_beanie` failed: `TypeError: MotorDatabase object is not
  callable. If you meant to call the 'append_metadata' method on a
  AsyncIOMotorClient object it is failing because no such method
  exists.` Without Motor installed, the import itself fails.
- **PyMongo `AsyncMongoClient`, Beanie 1.30.0**: `init_beanie`, an
  insert and a find worked, although the signature names Motor's type.
  Do not rely on it; upgrade Beanie instead.

## Upgrading 1.x to 2.x

1. Replace Motor's client with `AsyncMongoClient` at startup
   (`beanie/documents.md`), and remove `motor` from the dependencies.
2. Rename `get_motor_collection()` to `get_pymongo_collection()`; remove
   `multiprocessing_mode=`.
3. Code that used the Motor collection directly now awaits PyMongo's
   async API (`pymongo/clients.md`): `to_list()` and cursors are awaited
   the same way.
4. Run the tests against a development server, not mongomock.

Anything else that changed between the two: read the installed source
of both (offline-docs skill) rather than recall it.
