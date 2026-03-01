"""Tests for rate limiter and cost tracker."""

from airlock.rate_limiter import CostTracker, TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    def test_allows_under_limit(self) -> None:
        limiter = TokenBucketRateLimiter(requests_per_minute=10, tokens_per_minute=1000)
        result = limiter.check_request("test-key")
        assert result.allowed is True
        assert result.remaining >= 0

    def test_rejects_over_limit(self) -> None:
        limiter = TokenBucketRateLimiter(requests_per_minute=2, tokens_per_minute=1000)
        limiter.check_request("test-key")
        limiter.check_request("test-key")
        result = limiter.check_request("test-key")
        assert result.allowed is False
        assert result.retry_after is not None
        assert result.retry_after > 0

    def test_different_keys_independent(self) -> None:
        limiter = TokenBucketRateLimiter(requests_per_minute=1, tokens_per_minute=1000)
        result_a = limiter.check_request("key-a")
        result_b = limiter.check_request("key-b")
        assert result_a.allowed is True
        assert result_b.allowed is True

    def test_token_usage_tracking(self) -> None:
        limiter = TokenBucketRateLimiter(requests_per_minute=100, tokens_per_minute=100)
        result = limiter.record_token_usage("test-key", 50)
        assert result.allowed is True
        result = limiter.record_token_usage("test-key", 60)
        assert result.allowed is False

    def test_stats(self) -> None:
        limiter = TokenBucketRateLimiter(requests_per_minute=100, tokens_per_minute=100000)
        limiter.check_request("key-1")
        limiter.check_request("key-1")
        stats = limiter.get_stats("key-1")
        assert stats["total_requests"] == 2


class TestCostTracker:
    def test_records_cost(self) -> None:
        tracker = CostTracker()
        record = tracker.record("key-1", "gpt-4", input_tokens=100, output_tokens=50)
        assert record.estimated_cost_usd > 0
        assert record.model == "gpt-4"

    def test_cumulative_tracking(self) -> None:
        tracker = CostTracker()
        tracker.record("key-1", "gpt-4", input_tokens=1000, output_tokens=1000)
        record = tracker.record("key-1", "gpt-4", input_tokens=1000, output_tokens=1000)
        assert record.cumulative_cost_usd > record.estimated_cost_usd

    def test_budget_exceeded(self) -> None:
        tracker = CostTracker(budget_limit_usd=0.001)
        record = tracker.record("key-1", "gpt-4", input_tokens=10000, output_tokens=10000)
        assert record.budget_exceeded is True

    def test_unknown_model_fallback(self) -> None:
        tracker = CostTracker()
        record = tracker.record("key-1", "custom-model", input_tokens=100, output_tokens=100)
        assert record.estimated_cost_usd > 0

    def test_get_usage(self) -> None:
        tracker = CostTracker()
        tracker.record("key-1", "gpt-4o-mini", input_tokens=500, output_tokens=200)
        usage = tracker.get_usage("key-1")
        assert usage["total_cost"] > 0
        assert usage["total_tokens"] == 700
