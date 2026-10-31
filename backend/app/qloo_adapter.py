"""Wrapper around the public `qloo` CLI (@qloo/qloo-harness).

Only the two commands confirmed by discovery (docs/QLOO_NOTES.md) are built:
  qloo api search   --query=<text> [--type=<type>] --take=<n> --json
  qloo api insights --type=<type> --signal-entities=<ids> [--filter-location=<city>] --take=<n> --json

User text is only ever passed as the value half of `--flag=value`, so it can never
be read as a flag. The credential is read by the CLI from QLOO_API_KEY in the
environment; it is never put on the command line.

With QLOO_TRANSPORT=http (the default on Vercel) the same argv is served by
http_runner, which makes the CLI's REST calls directly instead of spawning Node.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx

from . import config
from .models import QlooEntity, QlooFacts, QlooResult

log = logging.getLogger("tastebridge.qloo")

# Aliases accepted by `qloo api search --type` / `insights --type` (from `qloo api search --help`).
ALLOWED_TYPES = {"artist", "place", "tv_show", "movie", "book", "brand", "podcast", "locality"}
ENTITY_ID_RE = re.compile(r"^[A-Za-z0-9:_\-]{1,120}$")

# Exit codes observed in the CLI source (router.js): 3 auth, 4 not found, 5 API error.
EXIT_AUTH = 3
EXIT_NOT_FOUND = 4


class QlooError(Exception):
    code = "qloo_error"
    status = 502
    user_message = "Qloo request failed."

    def __init__(self, detail: str = ""):
        self.detail = config.redact(detail)[:300]
        super().__init__(self.user_message)


class QlooAuthError(QlooError):
    code = "qloo_auth"
    status = 502
    user_message = "Qloo rejected the credential, or no credential is configured on the server."


class QlooRateLimitError(QlooError):
    code = "qloo_rate_limit"
    status = 429
    user_message = "Qloo rate limit reached. Please wait a minute and try again."


class QlooNoResult(QlooError):
    code = "qloo_no_result"
    status = 404
    user_message = "Qloo returned no result for this request."


class QlooUnavailable(QlooError):
    code = "qloo_unavailable"
    status = 503
    user_message = "Qloo is unavailable right now (timeout, network error or unexpected output)."


# A runner executes argv and returns (returncode, stdout, stderr). Injectable for tests.
Runner = Callable[[list[str], float], Awaitable[tuple[int, str, str]]]


async def subprocess_runner(argv: list[str], timeout: float) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


OFFICIAL_BASE_URL = "https://api.qloo.com"
EXIT_API_ERROR = 5


def _cli_error(code: str, message: str) -> str:
    return json.dumps({"error": True, "code": code, "message": message})


async def http_runner(argv: list[str], timeout: float) -> tuple[int, str, str]:
    """Same contract as subprocess_runner, but calls the Qloo REST API directly.

    Used where the Node CLI cannot run (Vercel's Python functions). It sends the same
    requests as `qloo api search|insights` (see docs/QLOO_NOTES.md) and prints what the
    CLI prints for --json, so parsing, caching and error mapping stay shared.
    """
    command = argv[2]
    flags = dict(a[2:].split("=", 1) for a in argv[3:] if a.startswith("--") and "=" in a)
    if command == "search":
        endpoint, params = "/search", {"query": flags["query"], "take": flags["take"]}
        if "type" in flags:
            params["types"] = f"urn:entity:{flags['type']}"
    elif command == "insights":
        endpoint = "/v2/insights"
        params = {
            "filter.type": f"urn:entity:{flags['type']}",
            "signal.interests.entities": flags["signal-entities"],
            "take": flags["take"],
        }
        if "filter-location" in flags:
            params["filter.location.query"] = flags["filter-location"]
    else:
        raise ValueError(f"unsupported qloo command: {command}")

    api_key = os.getenv("QLOO_API_KEY", "").strip()
    if not api_key:
        return EXIT_AUTH, _cli_error("AUTH_FAILED", "No Qloo API key configured"), ""
    # Like the CLI: the key goes only to the official endpoint or one explicitly trusted.
    base_url = (os.getenv("QLOO_BASE_URL", "").strip() or OFFICIAL_BASE_URL).rstrip("/")
    trusted = os.getenv("QLOO_TRUSTED_BASE_URL", "").strip().rstrip("/")
    if not base_url.startswith("https://") or base_url not in (OFFICIAL_BASE_URL, trusted):
        return EXIT_AUTH, _cli_error("AUTH_FAILED", "Qloo base URL is not trusted"), ""

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                base_url + endpoint, params=params, headers={"X-Api-Key": api_key, "Accept": "application/json"}
            )
    except httpx.TimeoutException:
        raise asyncio.TimeoutError()
    except httpx.HTTPError as exc:
        return EXIT_API_ERROR, _cli_error("API_ERROR", f"network error: {type(exc).__name__}"), ""

    if resp.status_code >= 400:
        message = f"API request failed: {resp.status_code} {resp.reason_phrase}"
        return EXIT_API_ERROR, _cli_error("API_ERROR", message), ""
    try:
        body = resp.json()
    except ValueError:
        return EXIT_API_ERROR, resp.text[:300], ""
    results = body.get("results") if isinstance(body, dict) else None
    if command == "insights" and isinstance(results, dict):
        results = results.get("entities")
    return 0, json.dumps(results or []), ""


def build_search_argv(binary: str, query: str, entity_type: str | None, take: int) -> list[str]:
    if entity_type is not None and entity_type not in ALLOWED_TYPES:
        raise ValueError(f"entity type not allowed: {entity_type}")
    argv = [binary, "api", "search", f"--query={query}"]
    if entity_type:
        argv.append(f"--type={entity_type}")
    argv += [f"--take={int(take)}", "--json"]
    return argv


def build_insights_argv(
    binary: str, seed_ids: list[str], target_type: str, city: str | None, take: int
) -> list[str]:
    if target_type not in ALLOWED_TYPES:
        raise ValueError(f"entity type not allowed: {target_type}")
    bad = [s for s in seed_ids if not ENTITY_ID_RE.match(s)]
    if bad or not seed_ids:
        raise ValueError("invalid seed entity ids")
    argv = [binary, "api", "insights", f"--type={target_type}", f"--signal-entities={','.join(seed_ids)}"]
    if city:
        argv.append(f"--filter-location={city}")
    argv += [f"--take={int(take)}", "--json"]
    return argv


def truncate_raw(obj: dict) -> dict:
    text = json.dumps(obj, ensure_ascii=False)
    if len(text) <= config.QLOO_RAW_MAX_CHARS:
        return obj
    return {"truncated": text[: config.QLOO_RAW_MAX_CHARS] + "..."}


def _parse_json(stdout: str):
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        # Tolerate stray text before the JSON payload.
        starts = [i for i in (stdout.find("["), stdout.find("{")) if i >= 0]
        if not starts:
            raise
        return json.loads(stdout[min(starts):])


def _entity_list(payload) -> list[dict]:
    """The CLI prints a bare array for --json; also accept {results: [...]} / {results: {entities: [...]}}."""
    if isinstance(payload, list):
        return [e for e in payload if isinstance(e, dict)]
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return [e for e in results if isinstance(e, dict)]
        if isinstance(results, dict) and isinstance(results.get("entities"), list):
            return [e for e in results["entities"] if isinstance(e, dict)]
    return []


def _str_or_none(value) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _affinity(e: dict) -> float | None:
    value = e.get("affinity")
    if value is None and isinstance(e.get("query"), dict):
        value = e["query"].get("affinity")
    return float(value) if isinstance(value, (int, float)) else None


def _image(e: dict) -> str | None:
    """Qloo's image URL from properties.image.url, accepted only from Qloo's image host."""
    props = e.get("properties") if isinstance(e.get("properties"), dict) else {}
    image = props.get("image") if isinstance(props.get("image"), dict) else {}
    url = _str_or_none(image.get("url"))
    return url if url and url.startswith("https://images.qloo.com/") else None


def _tags(e: dict) -> list[str]:
    tags = e.get("tags")
    if not isinstance(tags, list):
        return []
    return [t["name"] for t in tags if isinstance(t, dict) and isinstance(t.get("name"), str)][:15]


def _hours(props: dict) -> dict[str, str]:
    out = {}
    hours = props.get("hours") if isinstance(props.get("hours"), dict) else {}
    for day, spans in hours.items():
        if not isinstance(spans, list):
            continue
        parts = []
        for s in spans:
            if not isinstance(s, dict):
                continue
            if s.get("closed"):
                parts = ["closed"]
                break
            opens, closes = _str_or_none(s.get("opens")), _str_or_none(s.get("closes"))
            if opens and closes:
                parts.append(f"{opens.lstrip('T')[:5]}-{closes.lstrip('T')[:5]}")
        if parts:
            out[day.lower()] = ", ".join(parts)
    return out


def _facts(props: dict) -> QlooFacts:
    genre = props.get("primary_genre") if isinstance(props.get("primary_genre"), dict) else {}
    rating, level = props.get("business_rating"), props.get("price_level")
    return QlooFacts(
        genre=_str_or_none(genre.get("name")),
        rating=round(float(rating), 1) if isinstance(rating, (int, float)) and 0 < rating <= 5 else None,
        price_level=level if isinstance(level, int) and 1 <= level <= 4 else None,
        neighborhood=_str_or_none(props.get("neighborhood")),
        description=_str_or_none(props.get("short_description") or props.get("description")),
        hours=_hours(props),
        live_music=props.get("live_music") is True,
    )


def parse_entities(payload) -> list[QlooEntity]:
    out = []
    for e in _entity_list(payload):
        entity_id, name = _str_or_none(e.get("entity_id")), _str_or_none(e.get("name"))
        if entity_id and name:
            out.append(QlooEntity(entity_id=entity_id, name=name, type=_str_or_none(e.get("subtype") or e.get("type")), image_url=_image(e), raw=truncate_raw(e)))
    return out


def parse_results(payload) -> list[QlooResult]:
    entities = [e for e in _entity_list(payload) if _str_or_none(e.get("entity_id")) and _str_or_none(e.get("name"))]
    out = []
    for i, e in enumerate(entities, start=1):
        props = e.get("properties") if isinstance(e.get("properties"), dict) else {}
        address = _str_or_none(props.get("address"))
        website = _str_or_none(props.get("website"))
        genre = props.get("primary_genre") if isinstance(props.get("primary_genre"), dict) else {}
        out.append(
            QlooResult(
                entity_id=e["entity_id"],
                name=e["name"],
                type=_str_or_none(e.get("subtype") or e.get("type")),
                affinity=_affinity(e),
                rank=i,
                total=len(entities),
                address=address,
                url=website if website and website.startswith("https://") else None,
                tags=_tags(e),
                image_url=_image(e),
                genre_id=_str_or_none(genre.get("id")),
                is_closed=props.get("is_closed") is True,
                facts=_facts(props),
                raw=truncate_raw(e),
            )
        )
    return out


def classify_error(returncode: int, stdout: str, stderr: str) -> QlooError:
    text = f"{stdout}\n{stderr}"
    lower = text.lower()
    if returncode == EXIT_AUTH or any(s in lower for s in ("401", "403", "unauthorized", "forbidden", "auth_failed", "api key")):
        return QlooAuthError(text)
    if "429" in lower or "rate limit" in lower or "too many requests" in lower:
        return QlooRateLimitError(text)
    if returncode == EXIT_NOT_FOUND or "not_found" in lower:
        return QlooNoResult(text)
    return QlooUnavailable(text)


class QlooAdapter:
    def __init__(
        self,
        mode: str | None = None,
        binary: str | None = None,
        cache_dir: Path | None = None,
        runner: Runner | None = None,
        timeout: float = config.QLOO_TIMEOUT_SECONDS,
        fixtures_dir: Path = config.FIXTURES_DIR,
    ):
        self.mode = mode or config.qloo_mode()
        self.binary = binary or config.qloo_bin()
        self.cache_dir = cache_dir or config.cache_dir()
        self.runner = runner or (http_runner if config.qloo_transport() == "http" else subprocess_runner)
        self.timeout = timeout
        self.fixtures_dir = fixtures_dir
        self.calls_used = 0  # real CLI invocations in this process
        self.cache_hits = 0
        self._semaphore = asyncio.Semaphore(config.QLOO_MAX_CONCURRENCY)
        self._fixtures: dict | None = None

    # ---- public interface ----

    async def search_entities(self, query: str, entity_type: str | None, take: int = 3) -> list[QlooEntity]:
        if self.mode == "mock":
            return parse_entities(self._mock_search(query, entity_type))
        argv = build_search_argv(self.binary, query, entity_type, take)
        return parse_entities(await self._run(argv))

    async def recommend(self, seed_entity_ids: list[str], target_type: str, city: str | None, take: int = 10) -> list[QlooResult]:
        if self.mode == "mock":
            return parse_results(self._mock_insights(target_type))
        argv = build_insights_argv(self.binary, seed_entity_ids, target_type, city, take)
        return parse_results(await self._run(argv))

    # ---- live path ----

    def _cache_path(self, argv: list[str]) -> Path:
        key = hashlib.sha256(json.dumps(argv[1:]).encode()).hexdigest()[:32]
        return self.cache_dir / f"{key}.json"

    async def _run(self, argv: list[str]):
        path = self._cache_path(argv)
        if path.exists():
            try:
                self.cache_hits += 1
                return json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                pass

        async with self._semaphore:
            returncode, stdout, stderr = await self._run_with_retry(argv)

        if returncode != 0:
            raise classify_error(returncode, stdout, stderr)
        try:
            payload = _parse_json(stdout)
        except (json.JSONDecodeError, ValueError):
            raise QlooUnavailable("qloo returned output that is not JSON")
        if isinstance(payload, dict) and payload.get("error"):
            raise classify_error(returncode, stdout, stderr)

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload))
        except OSError:
            log.warning("could not write qloo cache entry")
        return payload

    async def _run_with_retry(self, argv: list[str]) -> tuple[int, str, str]:
        for attempt in (1, 2):  # max one retry, only on timeout
            self.calls_used += 1
            try:
                return await self.runner(argv, self.timeout)
            except asyncio.TimeoutError:
                log.warning("qloo %s timed out (attempt %d)", argv[2], attempt)
            except FileNotFoundError:
                raise QlooUnavailable("qloo CLI is not installed on the server")
        raise QlooUnavailable("qloo timed out twice")

    # ---- mock path (synthetic fixtures, DEMO DATA, not from Qloo) ----

    def _load_fixtures(self) -> dict:
        if self._fixtures is None:
            self._fixtures = json.loads((self.fixtures_dir / "qloo_mock.json").read_text())
        return self._fixtures

    def _mock_search(self, query: str, entity_type: str | None) -> list[dict]:
        hits = self._load_fixtures()["search"].get(query.strip().lower(), [])
        if entity_type:
            hits = [h for h in hits if h.get("type", "").endswith(entity_type)]
        return hits

    def _mock_insights(self, target_type: str) -> list[dict]:
        return self._load_fixtures()["insights"].get(target_type, [])
