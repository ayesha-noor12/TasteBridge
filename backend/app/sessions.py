"""Session stores: in-memory (dict + TTL), or Upstash Redis when it is configured.

Serverless instances (Vercel) do not share memory, so a deployment there needs Redis
for a session created by one request to be found by the next.
"""

import base64
import logging
import pickle
import secrets
import time
from dataclasses import dataclass, field

import httpx

from . import config
from .models import Candidate, Explanation, Plan, Profile, ResolverSummary


@dataclass
class Session:
    profile: Profile
    resolver: ResolverSummary
    candidates: list[Candidate]  # cached Qloo + curated; re-plans never call Qloo again
    qloo_notes: list[str]
    rejected_ids: set[str] = field(default_factory=set)
    social_boost: float = 0.0
    min_social: int = 1
    plan: Plan | None = None
    explanations: dict[str, tuple[Explanation, str]] = field(default_factory=dict)
    last_seen: float = field(default_factory=time.monotonic)


class SessionStore:
    def __init__(self, ttl: float = config.SESSION_TTL_SECONDS, clock=time.monotonic):
        self.ttl = ttl
        self.clock = clock
        self._data: dict[str, Session] = {}

    async def create(self, session: Session) -> str:
        self._purge()
        sid = secrets.token_urlsafe(16)
        session.last_seen = self.clock()
        self._data[sid] = session
        return sid

    async def get(self, sid: str) -> Session | None:
        self._purge()
        s = self._data.get(sid)
        if s:
            s.last_seen = self.clock()
        return s

    async def save(self, sid: str, session: Session) -> None:
        pass  # sessions are mutated in place

    async def delete(self, sid: str) -> bool:
        return self._data.pop(sid, None) is not None

    def _purge(self) -> None:
        now = self.clock()
        for sid in [k for k, s in self._data.items() if now - s.last_seen > self.ttl]:
            del self._data[sid]


log = logging.getLogger("tastebridge.sessions")


class RedisSessionStore:
    """Sessions pickled into Upstash Redis via its REST API; Redis expires them after the TTL.

    Only this server writes these values, so unpickling them is safe as long as the
    Redis credentials stay secret.
    """

    PREFIX = "tastebridge:session:"

    def __init__(self, url: str, token: str, ttl: float = config.SESSION_TTL_SECONDS):
        self.url = url.rstrip("/")
        self.token = token
        self.ttl = int(ttl)

    async def _command(self, *args: str):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(self.url, json=list(args), headers={"Authorization": f"Bearer {self.token}"})
        resp.raise_for_status()
        return resp.json().get("result")

    async def create(self, session: Session) -> str:
        sid = secrets.token_urlsafe(16)
        await self.save(sid, session)
        return sid

    async def get(self, sid: str) -> Session | None:
        value = await self._command("GETEX", self.PREFIX + sid, "EX", str(self.ttl))
        if not value:
            return None
        try:
            return pickle.loads(base64.b64decode(value))
        except Exception:
            log.warning("unreadable session entry; treating it as expired")
            return None

    async def save(self, sid: str, session: Session) -> None:
        value = base64.b64encode(pickle.dumps(session)).decode()
        await self._command("SET", self.PREFIX + sid, value, "EX", str(self.ttl))

    async def delete(self, sid: str) -> bool:
        return bool(await self._command("DEL", self.PREFIX + sid))


def make_store() -> SessionStore | RedisSessionStore:
    creds = config.redis_rest()
    if creds:
        return RedisSessionStore(*creds)
    if config.on_vercel():
        log.warning("no Redis configured: sessions live in one instance's memory and may vanish between requests")
    return SessionStore()
