from __future__ import annotations

import json

import pytest

from app.meta.rate_limiter import RateLimiter, RateLimitStatus


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


def test_unknown_account_returns_ok(limiter):
    assert limiter.check("act_unknown") == RateLimitStatus.OK


def test_low_usage_returns_ok(limiter):
    header = json.dumps(
        {
            "act_123": [
                {
                    "call_count": 10,
                    "total_cputime": 5,
                    "total_time": 5,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 0,
                }
            ]
        }
    )
    limiter.update_from_header("act_123", header)
    assert limiter.check("act_123") == RateLimitStatus.OK


def test_high_usage_returns_throttle(limiter):
    header = json.dumps(
        {
            "act_123": [
                {
                    "call_count": 80,
                    "total_cputime": 80,
                    "total_time": 80,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 0,
                }
            ]
        }
    )
    limiter.update_from_header("act_123", header)
    assert limiter.check("act_123") == RateLimitStatus.THROTTLE


def test_critical_usage_returns_blocked(limiter):
    header = json.dumps(
        {
            "act_123": [
                {
                    "call_count": 96,
                    "total_cputime": 96,
                    "total_time": 96,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 300,
                }
            ]
        }
    )
    limiter.update_from_header("act_123", header)
    assert limiter.check("act_123") == RateLimitStatus.BLOCKED


def test_throttle_seconds_default(limiter):
    assert limiter.throttle_seconds >= 30


def test_update_replaces_previous(limiter):
    low = json.dumps(
        {
            "act_1": [
                {
                    "call_count": 10,
                    "total_cputime": 10,
                    "total_time": 10,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 0,
                }
            ],
        }
    )
    high = json.dumps(
        {
            "act_1": [
                {
                    "call_count": 96,
                    "total_cputime": 96,
                    "total_time": 96,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 120,
                }
            ],
        }
    )
    limiter.update_from_header("act_1", low)
    assert limiter.check("act_1") == RateLimitStatus.OK
    limiter.update_from_header("act_1", high)
    assert limiter.check("act_1") == RateLimitStatus.BLOCKED


def test_malformed_header_is_ignored(limiter):
    limiter.update_from_header("act_x", "not-json")
    assert limiter.check("act_x") == RateLimitStatus.OK
