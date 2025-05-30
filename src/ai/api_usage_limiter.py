import time

from src.config.config import (
    USE_FREE_TIER, MAX_RPM, MAX_RPD ,MAX_TPM
)

_request_count_minute = 0
_request_count_day = 0
_token_count_minute = 0
_last_minute = time.localtime().tm_min
_last_day = time.localtime().tm_yday

def rate_limit_guard(tokens_used=0):
    global _request_count_minute, _request_count_day, _token_count_minute
    global _last_minute, _last_day

    if not USE_FREE_TIER:
        return

    now = time.localtime()
    minute = now.tm_min
    day = now.tm_yday

    if minute != _last_minute:
        _last_minute = minute
        _request_count_minute = 0
        _token_count_minute = 0
    if day != _last_day:
        _last_day = day
        _request_count_day = 0

    if _request_count_minute >= MAX_RPM:
        raise RuntimeError("❌ 프리티어 RPM(분당 요청) 초과")
    if _request_count_day >= MAX_RPD:
        raise RuntimeError("❌ 프리티어 RPD(일일 요청) 초과")
    if _token_count_minute + tokens_used > MAX_TPM:
        raise RuntimeError("❌ 프리티어 TPM(분당 토큰 수) 초과")

    _request_count_minute += 1
    _request_count_day += 1
    _token_count_minute += tokens_used