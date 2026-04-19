from __future__ import annotations

import pytest

from ash_cli.error import (
    APIConnectionError,
    ASHError,
    ConnectionError,
    FallbackMode,
    RateLimitError,
    RetryConfig,
    TimeoutError,
    ValidationError,
    _calculate_delay,
    should_fallback,
    validate_arg_range,
    validate_non_empty,
    validate_positive,
    validate_url,
    with_retry,
)


class TestRetryConfig:
    def test_default_values(self) -> None:
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0


class TestCalculateDelay:
    def test_exponential_backoff(self) -> None:
        config = RetryConfig()
        delay = _calculate_delay(0, config)
        assert delay == 1.0

    def test_doubles_each_attempt(self) -> None:
        config = RetryConfig()
        delay = _calculate_delay(1, config)
        assert delay == 2.0

    def test_caps_at_max_delay(self) -> None:
        config = RetryConfig(base_delay=5.0, max_delay=10.0)
        delay = _calculate_delay(2, config)
        assert delay == 10.0


class TestWithRetry:
    def test_success_on_first_try(self) -> None:
        result = with_retry(lambda: "success")
        assert result == "success"

    def test_retries_on_connection_error(self, mocker: pytest.MockerFixture) -> None:
        call_count = 0

        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("failed")
            return "success"

        result = with_retry(failing_func, RetryConfig(max_retries=3))
        assert result == "success"
        assert call_count == 3

    def test_exhausts_retries(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch("ash_cli.error.time.sleep")

        def always_fail() -> str:
            raise ConnectionError("failed")

        with pytest.raises(ConnectionError):
            with_retry(always_fail, RetryConfig(max_retries=3))

    def test_retries_on_rate_limit(self, mocker: pytest.MockerFixture) -> None:
        call_count = 0

        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("rate limited")
            return "success"

        result = with_retry(failing_func, RetryConfig(max_retries=3))
        assert result == "success"

    def test_retries_on_timeout(self, mocker: pytest.MockerFixture) -> None:
        call_count = 0

        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("timeout")
            return "success"

        result = with_retry(failing_func, RetryConfig(max_retries=3))
        assert result == "success"

    def test_calls_on_retry_callback(self, mocker: pytest.MockerFixture) -> None:
        call_count = 0

        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("failed")
            return "success"

        callback_calls: list[tuple[float, Exception]] = []

        def on_retry(delay: float, exc: Exception) -> None:
            callback_calls.append((delay, exc))

        with_retry(failing_func, RetryConfig(max_retries=3), on_retry=on_retry)
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == 1.0


class TestValidateArgRange:
    def test_passes_for_valid_value(self) -> None:
        validate_arg_range(5.0, 0.0, 10.0, "test")
        validate_arg_range(0.0, 0.0, 10.0, "test")
        validate_arg_range(10.0, 0.0, 10.0, "test")

    def test_allows_none(self) -> None:
        validate_arg_range(None, 0.0, 10.0, "test")

    def test_raises_for_below_min(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_arg_range(-1.0, 0.0, 10.0, "test")
        assert "must be between" in str(exc.value)

    def test_raises_for_above_max(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_arg_range(11.0, 0.0, 10.0, "test")
        assert "must be between" in str(exc.value)


class TestValidatePositive:
    def test_passes_for_positive(self) -> None:
        validate_positive(1, "test")
        validate_positive(100, "test")

    def test_allows_none(self) -> None:
        validate_positive(None, "test")

    def test_raises_for_zero(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_positive(0, "test")
        assert "must be positive" in str(exc.value)

    def test_raises_for_negative(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_positive(-1, "test")
        assert "must be positive" in str(exc.value)


class TestValidateNonEmpty:
    def test_passes_for_non_empty(self) -> None:
        validate_non_empty("hello", "test")
        validate_non_empty("  hello  ", "test")

    def test_allows_none(self) -> None:
        validate_non_empty(None, "test")

    def test_raises_for_empty(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_non_empty("", "test")
        assert "cannot be empty" in str(exc.value)

    def test_raises_for_whitespace(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_non_empty("   ", "test")
        assert "cannot be empty" in str(exc.value)


class TestValidateUrl:
    def test_passes_for_http(self) -> None:
        validate_url("http://example.com", "test")

    def test_passes_for_https(self) -> None:
        validate_url("https://example.com", "test")

    def test_allows_none(self) -> None:
        validate_url(None, "test")

    def test_raises_for_invalid(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_url("ftp://example.com", "test")
        assert "must be a valid URL" in str(exc.value)


class TestShouldFallback:
    def test_true_for_connection_error(self) -> None:
        assert should_fallback(ConnectionError("test")) is True

    def test_true_for_timeout_error(self) -> None:
        assert should_fallback(TimeoutError("test")) is True

    def test_true_for_api_connection_error(self) -> None:
        assert should_fallback(APIConnectionError("test", "http://example.com")) is True

    def test_false_for_validation_error(self) -> None:
        assert should_fallback(ValidationError("test")) is False

    def test_false_for_generic_exception(self) -> None:
        assert should_fallback(Exception("test")) is False


class TestErrorClasses:
    def test_ash_error(self) -> None:
        error = ASHError("test message")
        assert str(error) == "test message"

    def test_connection_error(self) -> None:
        error = ConnectionError("connection failed")
        assert isinstance(error, ASHError)
        assert str(error) == "connection failed"

    def test_api_connection_error(self) -> None:
        error = APIConnectionError("api failed", "http://api.example.com")
        assert error.url == "http://api.example.com"
        assert str(error) == "api failed"

    def test_validation_error(self) -> None:
        error = ValidationError("invalid", field_name="field")
        assert error.field_name == "field"
        assert str(error) == "invalid"

    def test_rate_limit_error(self) -> None:
        error = RateLimitError("rate limited")
        assert isinstance(error, ConnectionError)

    def test_timeout_error(self) -> None:
        error = TimeoutError("timed out")
        assert isinstance(error, ConnectionError)


class TestFallbackMode:
    def test_default_values(self) -> None:
        mode = FallbackMode()
        assert mode.enabled is False
        assert mode.reason == ""
        assert mode.use_basic is False
