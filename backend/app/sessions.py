"""In-memory session store (dict + TTL). No database; everything is lost on restart."""

import secrets
import time
from dataclasses import dataclass, field

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

    def create(self, session: Session) -> str:
        self._purge()
        sid = secrets.token_urlsafe(16)
        session.last_seen = self.clock()
        self._data[sid] = session
        return sid

    def get(self, sid: str) -> Session | None:
        self._purge()
        s = self._data.get(sid)
        if s:
            s.last_seen = self.clock()
        return s

    def delete(self, sid: str) -> bool:
        return self._data.pop(sid, None) is not None

    def _purge(self) -> None:
        now = self.clock()
        for sid in [k for k, s in self._data.items() if now - s.last_seen > self.ttl]:
            del self._data[sid]
