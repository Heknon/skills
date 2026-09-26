"""Ingest for the cold-room sensors: 500 devices, one reading every 10
seconds each, kept for two years. The dashboard shows one device's
readings for a chosen day."""

import datetime as dt
import os

from pymongo import MongoClient

db = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))["sensors"]


def add_reading(device_id: str, ts: dt.datetime, value: float) -> None:
    db.devices.update_one(
        {"_id": device_id},
        {"$push": {"readings": {"ts": ts, "value": value}}},
        upsert=True,
    )


def readings_for_day(device_id: str, day: dt.date) -> list[dict]:
    raise NotImplementedError  # TODO
