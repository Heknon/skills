# room-bookings

A new service. Nothing is written yet.

- `POST /bookings` with `room`, `starts_at`, `ends_at`, `booked_by`.
  A booking that overlaps another booking of the same room is refused
  with 409. `ends_at` must be after `starts_at` (422).
- `GET /rooms/{room}/bookings?day=2026-10-01` lists that room's
  bookings on that day, earliest first.

Storage is PostgreSQL through SQLAlchemy 2 (asyncpg), like our other
services; tests may use SQLite (aiosqlite). A reporting job will read
the same bookings next quarter.
