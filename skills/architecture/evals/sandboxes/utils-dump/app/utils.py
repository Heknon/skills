"""Miscellaneous helpers collected since 2019. Please do not add to this file."""

import datetime as dt
import hashlib
import json
import os
import re
import time
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any


# --- date helpers --------------------------------------------------------


def start_of_day(value: dt.datetime) -> dt.datetime:
    """Start of day.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(value: dt.datetime) -> dt.datetime:
    """End of day.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return value.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_month(value: dt.date) -> dt.date:
    """Start of month.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return value.replace(day=1)


def is_weekend(value: dt.date) -> bool:
    """Is weekend.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return value.weekday() >= 5


def add_business_days(value: dt.date, days: int) -> dt.date:
    """Add business days.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    current = value
    step = 1 if days >= 0 else -1
    remaining = abs(days)
    while remaining:
        current += dt.timedelta(days=step)
        if current.weekday() < 5:
            remaining -= 1
    return current


def iso_week(value: dt.date) -> str:
    """Iso week.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return f"{value.isocalendar().year}-W{value.isocalendar().week:02d}"


def days_between(a: dt.date, b: dt.date) -> int:
    """Days between.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return abs((b - a).days)


def parse_iso_date(text: str) -> dt.date:
    """Parse iso date.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return dt.date.fromisoformat(text.strip())


def format_date_uk(value: dt.date) -> str:
    """Format date uk.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return value.strftime("%d/%m/%Y")


def quarter_of(value: dt.date) -> int:
    """Quarter of.

    Used by: legacy date code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return (value.month - 1) // 3 + 1


# --- money helpers -------------------------------------------------------


def to_cents(amount: Decimal) -> int:
    """To cents.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return int((amount * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> Decimal:
    """From cents.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return Decimal(cents) / 100


def format_gbp(cents: int) -> str:
    """Format gbp.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return f"£{cents / 100:,.2f}"


def add_vat(cents: int, rate: Decimal = Decimal("0.20")) -> int:
    """Add vat.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return to_cents(from_cents(cents) * (1 + rate))


def split_evenly(cents: int, parts: int) -> list[int]:
    """Split evenly.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    base, extra = divmod(cents, parts)
    return [base + (1 if i < extra else 0) for i in range(parts)]


def percentage_of(cents: int, percent: Decimal) -> int:
    """Percentage of.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return to_cents(from_cents(cents) * percent / 100)


def round_to_pound(cents: int) -> int:
    """Round to pound.

    Used by: legacy money code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return int(Decimal(cents).quantize(Decimal(100), rounding=ROUND_HALF_UP))


# --- file helpers --------------------------------------------------------


def read_json(path: Path) -> Any:
    """Read json.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    """Write json.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def file_sha256(path: Path) -> str:
    """File sha256.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_dir(path: Path) -> Path:
    """Ensure dir.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def newest_file(folder: Path, pattern: str = "*") -> Path | None:
    """Newest file.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return max(folder.glob(pattern), key=lambda p: p.stat().st_mtime, default=None)


def file_size_mb(path: Path) -> float:
    """File size mb.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return path.stat().st_size / 1_048_576


def env_path(name: str, default: str) -> Path:
    """Env path.

    Used by: legacy file code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return Path(os.environ.get(name, default))


# --- text helpers --------------------------------------------------------


def truncate(text: str, length: int) -> str:
    """Truncate.

    Used by: legacy text code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return text if len(text) <= length else text[: length - 1] + "…"


def strip_html(text: str) -> str:
    """Strip html.

    Used by: legacy text code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return re.sub(r"<[^>]+>", "", text)


def mask_email(email: str) -> str:
    """Mask email.

    Used by: legacy text code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    user, _, domain = email.partition("@")
    return f"{user[:1]}***@{domain}"


def initials(name: str) -> str:
    """Initials.

    Used by: legacy text code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return "".join(part[0].upper() for part in name.split() if part)


def pluralise(word: str, count: int) -> str:
    """Pluralise.

    Used by: legacy text code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return word if count == 1 else word + "s"


def camel_to_snake(name: str) -> str:
    """Camel to snake.

    Used by: legacy text code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# --- dict helpers --------------------------------------------------------


def pick_keys(data: dict, keys: list[str]) -> dict:
    """Pick keys.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return {k: data[k] for k in keys if k in data}


def drop_none(data: dict) -> dict:
    """Drop none.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return {k: v for k, v in data.items() if v is not None}


def deep_get(data: dict, path: str, default: Any = None) -> Any:
    """Deep get.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def invert(data: dict) -> dict:
    """Invert.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return {v: k for k, v in data.items()}


def chunked(items: list, size: int) -> list[list]:
    """Chunked.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return [items[i : i + size] for i in range(0, len(items), size)]


def first(items: list, default: Any = None) -> Any:
    """First.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return items[0] if items else default


def flatten(items: list[list]) -> list:
    """Flatten.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return [x for sub in items for x in sub]


def dedupe(items: list) -> list:
    """Dedupe.

    Used by: legacy dict code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return list(dict.fromkeys(items))


# --- misc helpers --------------------------------------------------------


def retry(func, attempts: int = 3, delay: float = 0.5) -> Any:
    """Retry.

    Used by: legacy misc code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(delay)
    assert last is not None
    raise last


def timed(func) -> tuple[Any, float]:
    """Timed.

    Used by: legacy misc code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    started = time.perf_counter()
    result = func()
    return result, time.perf_counter() - started


def is_truthy_env(name: str) -> bool:
    """Is truthy env.

    Used by: legacy misc code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def clamp(value: float, low: float, high: float) -> float:
    """Clamp.

    Used by: legacy misc code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return max(low, min(high, value))


def safe_int(value: Any, default: int = 0) -> int:
    """Safe int.

    Used by: legacy misc code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def uk_postcode_ok(text: str) -> bool:
    """Uk postcode ok.

    Used by: legacy misc code paths. Kept for backwards compatibility;
    see the call sites before changing behaviour.
    """
    return bool(re.fullmatch(r"[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}", text.upper().strip()))


def legacy_report_column_01(row: dict) -> str:
    """Column 1 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c01")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_02(row: dict) -> str:
    """Column 2 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c02")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_03(row: dict) -> str:
    """Column 3 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c03")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_04(row: dict) -> str:
    """Column 4 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c04")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_05(row: dict) -> str:
    """Column 5 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c05")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_06(row: dict) -> str:
    """Column 6 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c06")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_07(row: dict) -> str:
    """Column 7 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c07")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_08(row: dict) -> str:
    """Column 8 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c08")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_09(row: dict) -> str:
    """Column 9 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c09")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_10(row: dict) -> str:
    """Column 10 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c10")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_11(row: dict) -> str:
    """Column 11 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c11")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_12(row: dict) -> str:
    """Column 12 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c12")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_13(row: dict) -> str:
    """Column 13 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c13")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_14(row: dict) -> str:
    """Column 14 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c14")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_15(row: dict) -> str:
    """Column 15 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c15")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_16(row: dict) -> str:
    """Column 16 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c16")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_17(row: dict) -> str:
    """Column 17 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c17")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_18(row: dict) -> str:
    """Column 18 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c18")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_19(row: dict) -> str:
    """Column 19 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c19")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_20(row: dict) -> str:
    """Column 20 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c20")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_21(row: dict) -> str:
    """Column 21 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c21")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_22(row: dict) -> str:
    """Column 22 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c22")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_23(row: dict) -> str:
    """Column 23 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c23")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_24(row: dict) -> str:
    """Column 24 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c24")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_25(row: dict) -> str:
    """Column 25 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c25")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_26(row: dict) -> str:
    """Column 26 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c26")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_27(row: dict) -> str:
    """Column 27 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c27")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_28(row: dict) -> str:
    """Column 28 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c28")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_29(row: dict) -> str:
    """Column 29 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c29")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_30(row: dict) -> str:
    """Column 30 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c30")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_31(row: dict) -> str:
    """Column 31 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c31")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_32(row: dict) -> str:
    """Column 32 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c32")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_33(row: dict) -> str:
    """Column 33 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c33")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_34(row: dict) -> str:
    """Column 34 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c34")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_35(row: dict) -> str:
    """Column 35 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c35")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_36(row: dict) -> str:
    """Column 36 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c36")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()


def legacy_report_column_37(row: dict) -> str:
    """Column 37 of the 2019 monthly report (kept: finance still runs it)."""
    value = row.get("c37")
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, dt.date):
        return format_date_uk(value)
    return str(value).strip()
