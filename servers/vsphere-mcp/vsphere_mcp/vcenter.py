"""One session per vCenter, and the handful of reads everything else is built from.

pyVmomi blocks, so each read runs in a worker thread, at most
`VSPHERE_MAX_CONCURRENT_PER_VCENTER` at a time per vCenter, under the server's
own deadline. Every call goes through `ReadOnlyStub`; every HTTP request (a
datastore file, the console screen) through `ensure_read_request`.

Properties are always read through the property collector, naming the paths
wanted, so a scan of a vCenter is one round trip per few hundred objects and
not one per property. A property the server did not return is simply absent
from the result: vCenter omits unset properties, and a simulator omits more.
"""

from __future__ import annotations

import asyncio
import collections
import contextlib
import logging
import ssl
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, TypeVar
from urllib.parse import quote

import httpx
from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim, vmodl

from vsphere_mcp.readonly import ReadOnlyStub, ensure_read_request

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from vsphere_mcp.config import Settings, VCenter

logger = logging.getLogger(__name__)

T = TypeVar("T")

PAGE_SIZE = 500
# QueryEvents answers with at most this many events, the newest; a busier
# window is cut, and results that use it say so.
QUERY_EVENTS_CAP = 1000
TASK_POLL_SECONDS = 0.1
REALTIME_INTERVAL_SECONDS = 20
HISTORICAL_INTERVAL_SECONDS = 300
# vCenter keeps 20-second samples for about an hour; older windows come from
# the first historical rollup, if the statistics level kept the counter at all.
REALTIME_SPAN = timedelta(minutes=60)
# vCenter refuses a historical query naming more entity-counter pairs than
# `config.vpxd.stats.maxQueryMetrics` (64 by default); realtime comes from the
# hosts and has no such limit, but is still sent in batches to bound each reply.
HISTORICAL_METRICS_PER_QUERY = 64
REALTIME_ENTITIES_PER_QUERY = 50


class VSphereError(RuntimeError):
    """A vSphere read failed in a way the caller should see, worded for a reader."""


@dataclass
class DatastoreFile:
    """A file read from a datastore: possibly only its end, and said so."""

    path: str
    text: str
    size: int | None
    truncated: bool
    status: int


@dataclass
class PerfSeries:
    """One counter on one entity: samples per instance, oldest first."""

    counter: str
    unit: str
    interval_seconds: int
    samples: dict[str, list[tuple[datetime, float]]] = field(default_factory=dict)


def ssl_context(settings: Settings) -> ssl.SSLContext:
    """The TLS context for vCenter: verified, unless explicitly turned off."""
    if not settings.tls_verify:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    return ssl.create_default_context(cafile=settings.ca_bundle)


def session_cookie(raw: str) -> str:
    """The `name=value` pair of the SOAP session cookie, for HTTP endpoints."""
    return raw.split(";", 1)[0].strip()


def parse_datastore_path(path: str) -> tuple[str, str]:
    """Split `[datastore] folder/file` into the datastore and the path inside it."""
    text = path.strip()
    if not text.startswith("[") or "]" not in text:
        msg = f"Not a datastore path: {path!r}"
        raise ValueError(msg)
    name, rest = text[1:].split("]", 1)
    return name.strip(), rest.strip()


class VCenterSession:
    """A logged-in, read-only session on one vCenter. Not thread-safe to create."""

    def __init__(self, vcenter: VCenter, settings: Settings) -> None:
        """Connect lazily: nothing is sent until the first read."""
        self.vcenter = vcenter
        self.settings = settings
        self._service: Any = None
        self._content: Any = None
        self._stub: ReadOnlyStub | None = None
        self._http: httpx.Client | None = None
        self._counters: dict[str, Any] | None = None

    # -- the session ---------------------------------------------------------

    def connect(self) -> None:
        """Log in and put the read-only stub between this session and vCenter."""
        username, password = self.settings.credentials_for(self.vcenter)
        try:
            raw = SmartConnect(
                host=self.vcenter.host,
                port=self.vcenter.port,
                user=username,
                pwd=password,
                sslContext=ssl_context(self.settings),
                connectionPoolTimeout=int(self.settings.timeout_seconds),
            )
        except vim.fault.InvalidLogin as error:
            msg = f"vCenter {self.vcenter.name}: login refused for {username!r}"
            raise VSphereError(msg) from error
        except (OSError, ssl.SSLError) as error:
            msg = f"vCenter {self.vcenter.name} ({self.vcenter.host}) unreachable: {error}"
            raise VSphereError(msg) from error
        self._stub = ReadOnlyStub(raw._stub)  # noqa: SLF001 - wrapping is the point
        self._service = vim.ServiceInstance("ServiceInstance", self._stub)
        self._content = self._service.RetrieveContent()
        self._raw = raw
        self._http = httpx.Client(
            verify=ssl_context(self.settings),
            timeout=self.settings.timeout_seconds,
            follow_redirects=False,
        )

    def close(self) -> None:
        """Log out and drop the HTTP client; safe to call twice."""
        if self._http is not None:
            self._http.close()
            self._http = None
        if self._service is not None:
            with contextlib.suppress(Exception):
                Disconnect(self._raw)
        self._service = None
        self._content = None
        self._counters = None

    @property
    def content(self) -> Any:
        """The service content, connecting first if needed."""
        if self._content is None:
            self.connect()
        return self._content

    @property
    def methods_seen(self) -> set[str]:
        """Every vSphere method this session has sent, for the read-only test."""
        return set(self._stub.seen) if self._stub else set()

    def about(self) -> dict[str, Any]:
        """Which vCenter this is: product, version, build, and its clock."""
        about = self.content.about
        return {
            "name": self.vcenter.name,
            "host": self.vcenter.host,
            "product": about.fullName,
            "version": about.version,
            "build": about.build,
            "api_version": about.apiVersion,
            "instance_uuid": getattr(about, "instanceUuid", None),
            "clock": as_utc(self._service.CurrentTime()),
        }

    def now(self) -> datetime:
        """VCenter's own clock, which every window on this vCenter is measured by."""
        _ = self.content
        return as_utc(self._service.CurrentTime())

    # -- properties ----------------------------------------------------------

    def retrieve(
        self,
        kind: type,
        paths: Sequence[str],
        *,
        root: Any = None,
        objects: Iterable[Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Read `paths` from every `kind` under `root`, or from the given objects.

        Each row carries `_ref` (the object), `moref` and whichever paths came
        back. `_missing` names paths the server refused, usually permission.
        """
        content = self.content
        view = None
        if objects is not None:
            object_set = [vmodl.query.PropertyCollector.ObjectSpec(obj=item, skip=False) for item in objects]
            if not object_set:
                return []
        else:
            view = content.viewManager.CreateContainerView(root or content.rootFolder, [kind], recursive=True)
            traversal = vmodl.query.PropertyCollector.TraversalSpec(
                name="view", path="view", skip=False, type=vim.view.ContainerView
            )
            object_set = [
                vmodl.query.PropertyCollector.ObjectSpec(obj=view, skip=True, selectSet=[traversal])
            ]
        spec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=object_set,
            propSet=[vmodl.query.PropertyCollector.PropertySpec(type=kind, pathSet=list(paths), all=False)],
        )
        collector = content.propertyCollector
        rows: list[dict[str, Any]] = []
        try:
            result = collector.RetrievePropertiesEx(
                [spec], vmodl.query.PropertyCollector.RetrieveOptions(maxObjects=PAGE_SIZE)
            )
            while result is not None:
                rows.extend(_rows(result.objects))
                token = result.token
                if not token:
                    break
                result = collector.ContinueRetrievePropertiesEx(token)
        except vmodl.fault.ManagedObjectNotFound:
            # An object listed by hand is gone: a short-lived VM was destroyed.
            if objects is None:
                raise
        finally:
            if view is not None:
                with contextlib.suppress(Exception):
                    view.DestroyView()
        return rows

    def reference(self, kind: str, moref: str) -> Any:
        """A managed object by type and id, bound to this session's read-only stub."""
        _ = self.content
        return getattr(vim, kind)(moref, self._stub)

    # -- events --------------------------------------------------------------

    def events(
        self,
        *,
        entity: Any = None,
        begin: datetime | None = None,
        end: datetime | None = None,
        types: Sequence[str] = (),
    ) -> list[Any]:
        """The events on an entity (or everywhere), in a window, oldest first."""
        criteria = vim.event.EventFilterSpec()
        if entity is not None:
            criteria.entity = vim.event.EventFilterSpec.ByEntity(entity=entity, recursion="self")
        if begin or end:
            criteria.time = vim.event.EventFilterSpec.ByTime(beginTime=begin, endTime=end)
        if types:
            criteria.eventTypeId = list(types)
        found = self.content.eventManager.QueryEvents(criteria) or []
        return sorted(found, key=lambda event: event.createdTime)

    # -- performance ---------------------------------------------------------

    def counters(self) -> dict[str, Any]:
        """Every performance counter by `group.name.rollup`, read once per session."""
        if self._counters is None:
            self._counters = {
                f"{counter.groupInfo.key}.{counter.nameInfo.key}.{counter.rollupType}": counter
                for counter in self.content.perfManager.perfCounter
            }
        return self._counters

    def perf(
        self,
        entities: Sequence[Any],
        counter_names: Sequence[str],
        *,
        begin: datetime,
        end: datetime,
        instance: str = "*",
    ) -> tuple[dict[str, dict[str, PerfSeries]], list[str]]:
        """Samples for counters on entities, keyed by moref then counter name.

        Realtime (20 s) samples when the window is inside the last hour, the
        first historical rollup otherwise. Counter names this vCenter does not
        have come back in the second element instead of failing the read.
        """
        known = self.counters()
        wanted = [name for name in counter_names if name in known]
        unknown = [name for name in counter_names if name not in known]
        if not wanted or not entities:
            return {}, unknown
        now = self.now()
        interval = REALTIME_INTERVAL_SECONDS if now - begin <= REALTIME_SPAN else HISTORICAL_INTERVAL_SECONDS
        by_key = {known[name].key: name for name in wanted}
        specs = [
            vim.PerformanceManager.QuerySpec(
                entity=entity,
                metricId=[
                    vim.PerformanceManager.MetricId(counterId=known[name].key, instance=instance)
                    for name in wanted
                ],
                intervalId=interval,
                startTime=begin,
                endTime=end,
                format="normal",
            )
            for entity in entities
        ]
        batch = (
            REALTIME_ENTITIES_PER_QUERY
            if interval == REALTIME_INTERVAL_SECONDS
            else max(1, HISTORICAL_METRICS_PER_QUERY // len(wanted))
        )
        metrics = []
        for start in range(0, len(specs), batch):
            metrics.extend(self.content.perfManager.QueryPerf(specs[start : start + batch]) or [])
        results: dict[str, dict[str, PerfSeries]] = {}
        for metric in metrics:
            stamps = [as_utc(sample.timestamp) for sample in metric.sampleInfo or []]
            per_counter = results.setdefault(metric.entity._moId, {})  # noqa: SLF001
            for value in metric.value or []:
                name = by_key.get(value.id.counterId)
                if name is None:
                    continue
                series = per_counter.setdefault(
                    name,
                    PerfSeries(
                        counter=name,
                        unit=known[name].unitInfo.key,
                        interval_seconds=interval,
                    ),
                )
                series.samples[value.id.instance or ""] = [
                    (stamp, float(sample))
                    for stamp, sample in zip(stamps, value.value or [], strict=False)
                    if sample is not None and sample >= 0
                ]
        return results, unknown

    # -- host logs -----------------------------------------------------------

    def host_log(self, host: Any, key: str, lines: int) -> dict[str, Any]:
        """The last `lines` of a host log (`vmkernel`, `hostd`, `vpxa`, ...)."""
        manager = self.content.diagnosticManager
        try:
            # Without a start line, the answer is just the log's length in lineEnd.
            header = manager.BrowseDiagnosticLog(host=host, key=key)
            last = header.lineEnd
            start = max(1, last - lines + 1)
            body = manager.BrowseDiagnosticLog(host=host, key=key, start=start, lines=lines)
        except (vmodl.fault.NotSupported, vmodl.MethodFault, vmodl.RuntimeFault) as fault:
            descriptions = []
            with contextlib.suppress(Exception):
                descriptions = [item.key for item in manager.QueryDescriptions(host=host)]
            return {
                "available": False,
                "reason": f"{type(fault).__name__}: {getattr(fault, 'msg', '') or fault}",
                "keys_offered": descriptions,
            }
        return {
            "available": True,
            "line_start": body.lineStart,
            "line_end": body.lineEnd,
            "lines": list(body.lineText or []),
        }

    # -- datastore files and the console --------------------------------------

    def list_folder(self, datastore: Any, folder: str, patterns: Sequence[str]) -> list[dict[str, Any]]:
        """The files in a datastore folder matching `patterns`, with sizes and times."""
        details = vim.host.DatastoreBrowser.FileInfo.Details(fileSize=True, modification=True, fileType=True)
        spec = vim.host.DatastoreBrowser.SearchSpec(matchPattern=list(patterns), details=details)
        task = datastore.browser.SearchDatastore_Task(folder, spec)
        deadline = time.monotonic() + self.settings.timeout_seconds
        while task.info.state in ("queued", "running"):
            if time.monotonic() > deadline:
                msg = f"Listing {folder} did not finish in time"
                raise VSphereError(msg)
            time.sleep(TASK_POLL_SECONDS)
        info = task.info
        if info.state != "success":
            fault = info.error
            if isinstance(fault, vim.fault.FileNotFound):
                return []
            msg = f"Listing {folder} failed: {getattr(fault, 'msg', fault)}"
            raise VSphereError(msg)
        return [
            {
                "name": item.path,
                "size": getattr(item, "fileSize", None),
                "modified": as_utc(item.modification) if getattr(item, "modification", None) else None,
            }
            for item in (info.result.file or [])
        ]

    def _get_request(self, path: str, params: dict[str, str]) -> httpx.Request:
        """A GET on this vCenter's HTTPS endpoints, carrying the SOAP session."""
        ensure_read_request("GET")
        _ = self.content
        if self._http is None or self._stub is None:
            msg = "Session is not connected"
            raise VSphereError(msg)
        url = f"https://{self.vcenter.host}:{self.vcenter.port}{path}"
        return self._http.build_request(
            "GET", url, params=params, headers={"Cookie": session_cookie(self._stub.cookie)}
        )

    def read_datastore_file(self, datacenter: str, path: str, max_bytes: int) -> DatastoreFile:
        """The end of a datastore file, at most `max_bytes` of it, over HTTPS GET."""
        datastore, inside = parse_datastore_path(path)
        request = self._get_request(
            "/folder/" + quote(inside),
            {"dcPath": datacenter, "dsName": datastore},
        )
        assert self._http is not None  # noqa: S101 - set by _get_request
        tail: collections.deque[bytes] = collections.deque()
        kept = 0
        total = 0
        response = self._http.send(request, stream=True)
        try:
            if response.status_code != 200:  # noqa: PLR2004
                return DatastoreFile(path, "", None, truncated=False, status=response.status_code)
            declared = response.headers.get("content-length")
            for chunk in response.iter_bytes():
                total += len(chunk)
                tail.append(chunk)
                kept += len(chunk)
                while kept - len(tail[0]) >= max_bytes:
                    kept -= len(tail.popleft())
        finally:
            response.close()
        data = b"".join(tail)
        truncated = len(data) > max_bytes or total > len(data)
        if len(data) > max_bytes:
            data = data[-max_bytes:]
        if truncated:
            # Start on a whole line rather than mid-line.
            newline = data.find(b"\n")
            if newline >= 0:
                data = data[newline + 1 :]
        size = int(declared) if declared and declared.isdigit() else total
        return DatastoreFile(path, data.decode("utf-8", errors="replace"), size, truncated, 200)

    def screenshot(self, moref: str) -> tuple[int, bytes, str | None]:
        """The console as vCenter renders it, over the read-only `/screen` endpoint.

        Never `CreateScreenshot_Task`: that writes a PNG into the VM's folder.
        """
        request = self._get_request("/screen", {"id": moref})
        assert self._http is not None  # noqa: S101 - set by _get_request
        response = self._http.send(request, stream=True)
        try:
            if response.status_code != 200:  # noqa: PLR2004
                return response.status_code, b"", response.headers.get("content-type")
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > self.settings.max_screenshot_bytes:
                    msg = "Screenshot larger than VSPHERE_MAX_SCREENSHOT_BYTES"
                    raise VSphereError(msg)
            return 200, bytes(body), response.headers.get("content-type")
        finally:
            response.close()


def _rows(objects: Iterable[Any]) -> list[dict[str, Any]]:
    rows = []
    for item in objects or []:
        row: dict[str, Any] = {"_ref": item.obj, "moref": item.obj._moId}  # noqa: SLF001
        for prop in item.propSet or []:
            row[prop.name] = prop.val
        missing = [missing.path for missing in (item.missingSet or [])]
        if missing:
            row["_missing"] = missing
        rows.append(row)
    return rows


def as_utc(value: datetime) -> datetime:
    """A vSphere timestamp as an aware UTC datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class VCenterPool:
    """The configured vCenters, each with a lazy session, a limit and a deadline."""

    def __init__(self, settings: Settings) -> None:
        """Create no session until a vCenter is first read."""
        self.settings = settings
        self._sessions: dict[str, VCenterSession] = {}
        self._limits: dict[str, asyncio.Semaphore] = {}
        self._connect_locks: dict[str, asyncio.Lock] = {}

    def names(self) -> list[str]:
        """The configured vCenters, by the name tools use."""
        return [vcenter.name for vcenter in self.settings.vcenters]

    def resolve(self, spelling: str) -> str:
        """The configured name for any spelling an upstream system used."""
        return self.settings.vcenter(spelling).name

    def session(self, name: str) -> VCenterSession:
        """The session object for a vCenter (not necessarily connected yet)."""
        if name not in self._sessions:
            self._sessions[name] = VCenterSession(self.settings.vcenter(name), self.settings)
            self._limits[name] = asyncio.Semaphore(self.settings.max_concurrent_per_vcenter)
            self._connect_locks[name] = asyncio.Lock()
        return self._sessions[name]

    async def run(self, name: str, work: Callable[[VCenterSession], T]) -> T:
        """Run one blocking read against a vCenter, bounded and with one re-login."""
        session = self.session(name)
        async with self._limits[name]:
            if session._content is None:  # noqa: SLF001 - connect once, not per call
                async with self._connect_locks[name]:
                    if session._content is None:  # noqa: SLF001
                        await self._bounded(session.connect)
            try:
                return await self._bounded(lambda: work(session))
            except vim.fault.NotAuthenticated:
                session.close()
                await self._bounded(session.connect)
                return await self._bounded(lambda: work(session))

    async def _bounded(self, work: Callable[[], T]) -> T:
        try:
            return await asyncio.wait_for(asyncio.to_thread(work), timeout=self.settings.timeout_seconds)
        except TimeoutError as error:
            msg = f"vCenter read exceeded VSPHERE_TIMEOUT_SECONDS ({self.settings.timeout_seconds:g}s)"
            raise VSphereError(msg) from error

    def methods_seen(self) -> set[str]:
        """Every vSphere method any session has sent."""
        seen: set[str] = set()
        for session in self._sessions.values():
            seen |= session.methods_seen
        return seen

    def close(self) -> None:
        """Log every session out."""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
