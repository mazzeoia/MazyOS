from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStatus(Enum):
    OK = "ok"
    THROTTLE = "throttle"
    BLOCKED = "blocked"


@dataclass
class _AccountUsage:
    call_count: int = 0
    total_cputime: int = 0
    total_time: int = 0
    estimated_time_to_regain_access: int = 0


class RateLimiter:
    """Per-account rate limiter using Meta's X-Business-Use-Case-Usage header.

    Thresholds:
      < 75%  -> OK
      75-95% -> THROTTLE (wait before calling)
      > 95%  -> BLOCKED (do not call)
    """

    THROTTLE_THRESHOLD = 75
    BLOCK_THRESHOLD = 95

    def __init__(self, default_throttle_seconds: int = 60):
        self._usage: dict[str, _AccountUsage] = {}
        self._default_throttle = default_throttle_seconds

    def update_from_header(self, act_id: str, header_value: str) -> None:
        """Parse X-Business-Use-Case-Usage JSON and update state for act_id."""
        try:
            data = json.loads(header_value)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Malformed rate limit header for %s, ignoring", act_id)
            return

        entries = data.get(act_id, [])
        if not entries:
            for _key, value in data.items():
                if isinstance(value, list) and value:
                    entries = value
                    break

        if not entries:
            return

        entry = entries[0] if isinstance(entries, list) else entries
        self._usage[act_id] = _AccountUsage(
            call_count=int(entry.get("call_count", 0)),
            total_cputime=int(entry.get("total_cputime", 0)),
            total_time=int(entry.get("total_time", 0)),
            estimated_time_to_regain_access=int(entry.get("estimated_time_to_regain_access", 0)),
        )

    def check(self, act_id: str) -> RateLimitStatus:
        """Check current usage level for the account."""
        usage = self._usage.get(act_id)
        if usage is None:
            return RateLimitStatus.OK

        max_pct = max(usage.call_count, usage.total_cputime, usage.total_time)

        if max_pct > self.BLOCK_THRESHOLD:
            return RateLimitStatus.BLOCKED
        if max_pct >= self.THROTTLE_THRESHOLD:
            return RateLimitStatus.THROTTLE
        return RateLimitStatus.OK

    @property
    def throttle_seconds(self) -> int:
        return self._default_throttle
