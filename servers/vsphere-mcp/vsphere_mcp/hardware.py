"""Fleet hardware queries: which VMs have, or lack, a given virtual device.

For a production issue traced to a device — a missing sound card a product
expects, a NIC type that misbehaves, a leftover USB controller — this answers
"which VMs across these vCenters have it, and which do not", by reading each
VM's device list (the one heavy property) and matching a category or a kind.
"""

from __future__ import annotations

import asyncio
from collections import Counter
from typing import TYPE_CHECKING, Any

from vsphere_mcp.ages import under_any
from vsphere_mcp.inventory import read_folders, read_vm_devices

if TYPE_CHECKING:
    from collections.abc import Sequence

    from vsphere_mcp.config import Settings
    from vsphere_mcp.vcenter import VCenterPool, VCenterSession

CATEGORIES = ("ethernet", "disk", "cdrom", "serial", "sound", "usb", "controller", "video", "input")


def _has_device(row: dict[str, Any], device: str) -> bool:
    """Whether a VM row has the device, matched as a category or a kind substring."""
    wanted = device.strip().lower()
    if wanted in row["categories"]:
        return True
    return any(wanted in kind.lower() for kind in row["kinds"])


def _scan_devices(session: VCenterSession, under: Sequence[str]) -> list[dict[str, Any]]:
    folders = read_folders(session)
    rows = read_vm_devices(session, folders)
    if under:
        rows = [row for row in rows if under_any(row["folder"], under)]
    return rows


async def find_vms_by_device(
    pool: VCenterPool,
    settings: Settings,  # noqa: ARG001 - kept for symmetry with the other fleet calls
    names: Sequence[str],
    *,
    device: str,
    present: bool,
    include_templates: bool,
    under: Sequence[str],
    limit: int,
) -> dict[str, Any]:
    """VMs across the named vCenters that have (present) or lack (not present) a device."""
    results = await asyncio.gather(
        *(pool.run(name, lambda session: _scan_devices(session, under)) for name in names),
        return_exceptions=True,
    )
    rows: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    read: dict[str, int] = {}
    for name, result in zip(names, results, strict=True):
        if isinstance(result, BaseException):
            errors[name] = str(result)
            continue
        read[name] = len(result)
        rows.extend(result)

    considered = [row for row in rows if include_templates or not row["template"]]
    matched = [row for row in considered if _has_device(row, device) == present]
    verb = "with" if present else "without"
    by_vcenter = Counter(row["vcenter"] for row in matched)
    findings = [
        f"{len(matched)} of {len(considered)} VMs are {verb} a {device} device across {len(read)} vCenter(s)"
    ]
    findings.extend(f"{vcenter}: {count}" for vcenter, count in by_vcenter.most_common())
    # When looking for VMs lacking a device, the template lacking it is the usual root.
    if not present and include_templates:
        bare_templates = [row for row in matched if row["template"]]
        if bare_templates:
            findings.append(
                f"{len(bare_templates)} of these are templates — a clone lacks the device "
                "because its base does"
            )
    for name, error in errors.items():
        findings.append(f"vCenter {name} not read: {error}")
    return {
        "device": device,
        "present": present,
        "findings": findings,
        "matched_total": len(matched),
        "matched": [
            {
                "vcenter": row["vcenter"],
                "moref": row["moref"],
                "name": row["name"],
                "folder": row["folder"],
                "template": row["template"],
                "kinds": row["kinds"],
            }
            for row in matched[:limit]
        ],
        "vcenters_read": read,
        "errors": errors,
        "note": (
            "matched by device category (sound, ethernet, cdrom, usb, ...) or a kind substring "
            "(e.g. Vmxnet3, HdAudioCard); this is the virtual hardware, read without Tools"
        ),
    }
