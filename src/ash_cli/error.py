from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0


class ASHError(Exception):
    pass


class ConnectionError(ASHError):
    pass


class APIConnectionError(ConnectionError):
    def __init__(self, message: str, url: str | None = None) -> None:
        self.url = url
        super().__init__(message)


class ValidationError(ASHError):
    def __init__(self, message: str, field_name: str | None = None) -> None:
        self.field_name = field_name
        super().__init__(message)


class RateLimitError(ConnectionError):
    pass


class TimeoutError(ConnectionError):
    pass


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    delay = config.base_delay * (2**attempt)
    return float(min(delay, config.max_delay))


def with_retry[T](
    func: Callable[[], T],
    config: RetryConfig | None = None,
    on_retry: Callable[[float, Exception], None] | None = None,
) -> T:
    cfg = config or RetryConfig()
    last_exception: BaseException | None = None

    for attempt in range(cfg.max_retries):
        try:
            return func()
        except (ConnectionError, TimeoutError, RateLimitError) as e:
            last_exception = e
            if attempt < cfg.max_retries - 1:
                delay = _calculate_delay(attempt, cfg)
                if on_retry:
                    on_retry(delay, e)
                time.sleep(delay)
            else:
                raise

    raise last_exception if last_exception is not None else ASHError("Max retries reached")


def validate_arg_range(
    value: float | None,
    min_val: float,
    max_val: float,
    name: str,
) -> None:
    if value is not None and (value < min_val or value > max_val):
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got {value}",
            field_name=name,
        )


def validate_positive(value: int | None, name: str) -> None:
    if value is not None and value <= 0:
        raise ValidationError(
            f"{name} must be positive, got {value}",
            field_name=name,
        )


def validate_non_empty(value: str | None, name: str) -> None:
    if value is not None and not value.strip():
        raise ValidationError(
            f"{name} cannot be empty",
            field_name=name,
        )


def validate_url(value: str | None, name: str) -> None:
    if value is not None:
        if not value.startswith(("http://", "https://")):
            raise ValidationError(
                f"{name} must be a valid URL (http:// or https://)",
                field_name=name,
            )


@dataclass
class FallbackMode:
    enabled: bool = False
    reason: str = ""
    use_basic: bool = False


def should_fallback(error: Exception) -> bool:
    return isinstance(error, (ConnectionError, TimeoutError, APIConnectionError))
