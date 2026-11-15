
import logging
import os
import threading
import time

from collections import defaultdict
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger("email_management.llm")


class LLMUsageCallback(BaseCallbackHandler):

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.usage_available = False

    def on_llm_end(self, response, **kwargs):

        for generations in response.generations:
            for generation in generations:

                message = getattr(generation, "message", None)

                if not message:
                    continue

                usage = getattr(message, "usage_metadata", None)

                if usage:
                    self.input_tokens += usage.get("input_tokens", 0)
                    self.output_tokens += usage.get("output_tokens", 0)
                    self.total_tokens += usage.get("total_tokens", 0)
                    self.usage_available = True

        llm_output = getattr(response, "llm_output", None) or {}
        usage = llm_output.get("token_usage", {})

        if usage and not self.usage_available:
            self.input_tokens = usage.get("prompt_tokens", 0)
            self.output_tokens = usage.get("completion_tokens", 0)
            self.total_tokens = usage.get("total_tokens", 0)
            self.usage_available = True


class LLMObservability:

    def __init__(self):

        self.lock = threading.Lock()

        self.metrics = defaultdict(lambda: {
            "requests": 0,
            "success": 0,
            "failures": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latencies": [],
            "usage_unavailable": 0,
            "structured_output_failures": 0,
        })

        self.tools = defaultdict(lambda: {
            "calls": 0,
            "success": 0,
            "failures": 0,
            "latencies": [],
        })

        self.input_price = float(
            os.getenv("GROQ_INPUT_PRICE_PER_MILLION", "0")
        )

        self.output_price = float(
            os.getenv("GROQ_OUTPUT_PRICE_PER_MILLION", "0")
        )

    @staticmethod
    def percentile(values, percentile):

        if not values:
            return 0

        ordered = sorted(values)

        index = round((len(ordered) - 1) * percentile / 100)

        return round(ordered[index], 4)

    def record_llm_call(
        self,
        operation,
        duration,
        usage,
        success,
        error=None
    ):

        with self.lock:

            metric = self.metrics[operation]

            metric["requests"] += 1
            metric["latencies"].append(duration)

            if success:
                metric["success"] += 1
            else:
                metric["failures"] += 1

            if usage.usage_available:
                metric["input_tokens"] += usage.input_tokens
                metric["output_tokens"] += usage.output_tokens
                metric["total_tokens"] += usage.total_tokens
            else:
                metric["usage_unavailable"] += 1

        cost = None

        if usage.usage_available and (
            self.input_price or self.output_price
        ):
            cost = (
                usage.input_tokens * self.input_price
                + usage.output_tokens * self.output_price
            ) / 1_000_000

        logger.info(
            "LLM invocation",
            extra={
                "event_data": {
                    "operation": operation,
                    "duration_seconds": round(duration, 4),
                    "success": success,
                    "input_tokens": (
                        usage.input_tokens if usage.usage_available else None
                    ),
                    "output_tokens": (
                        usage.output_tokens if usage.usage_available else None
                    ),
                    "total_tokens": (
                        usage.total_tokens if usage.usage_available else None
                    ),
                    "estimated_cost_usd": (
                        round(cost, 8) if cost is not None else None
                    ),
                    "error_type": type(error).__name__ if error else None,
                }
            }
        )

    def record_tool_call(self, name, duration, success):

        with self.lock:

            metric = self.tools[name]

            metric["calls"] += 1
            metric["latencies"].append(duration)

            if success:
                metric["success"] += 1
            else:
                metric["failures"] += 1

    def record_structured_output_failure(self, operation):

        with self.lock:
            self.metrics[operation]["structured_output_failures"] += 1

    def get_metrics(self):

        with self.lock:

            result = {}

            for operation, metric in self.metrics.items():

                latencies = metric["latencies"]
                requests = metric["requests"]

                cost = None

                if self.input_price or self.output_price:
                    cost = (
                        metric["input_tokens"] * self.input_price
                        + metric["output_tokens"] * self.output_price
                    ) / 1_000_000

                result[operation] = {
                    "requests": requests,
                    "success": metric["success"],
                    "failures": metric["failures"],
                    "success_rate": round(
                        metric["success"] / requests * 100, 2
                    ) if requests else 0,
                    "input_tokens": metric["input_tokens"],
                    "output_tokens": metric["output_tokens"],
                    "total_tokens": metric["total_tokens"],
                    "usage_unavailable": metric["usage_unavailable"],
                    "average_latency_seconds": round(
                        sum(latencies) / len(latencies), 4
                    ) if latencies else 0,
                    "p50_latency_seconds": self.percentile(latencies, 50),
                    "p90_latency_seconds": self.percentile(latencies, 90),
                    "p95_latency_seconds": self.percentile(latencies, 95),
                    "p99_latency_seconds": self.percentile(latencies, 99),
                    "structured_output_failures": metric[
                        "structured_output_failures"
                    ],
                    "estimated_cost_usd": (
                        round(cost, 8) if cost is not None else None
                    ),
                }

            tools = {
                name: {
                    "calls": metric["calls"],
                    "success": metric["success"],
                    "failures": metric["failures"],
                    "average_latency_seconds": round(
                        sum(metric["latencies"]) /
                        len(metric["latencies"]), 4
                    ) if metric["latencies"] else 0,
                }
                for name, metric in self.tools.items()
            }

            return {
                "llm": result,
                "tools": tools,
            }


llm_observability = LLMObservability()


def invoke_observed(
    runnable,
    payload,
    operation,
    structured_output=False
):

    callback = LLMUsageCallback()
    start_time = time.perf_counter()

    try:

        result = runnable.invoke(
            payload,
            config={
                "callbacks": [callback],
                "run_name": operation,
                "tags": ["email-management", operation],
                "metadata": {"operation": operation},
            }
        )

        duration = time.perf_counter() - start_time

        llm_observability.record_llm_call(
            operation=operation,
            duration=duration,
            usage=callback,
            success=True
        )

        return result

    except Exception as error:

        duration = time.perf_counter() - start_time

        llm_observability.record_llm_call(
            operation=operation,
            duration=duration,
            usage=callback,
            success=False,
            error=error
        )

        if structured_output:
            llm_observability.record_structured_output_failure(operation)

        raise


def observe_tool_call(name, callback):

    start_time = time.perf_counter()

    try:

        result = callback()

        llm_observability.record_tool_call(
            name,
            time.perf_counter() - start_time,
            True
        )

        return result

    except Exception:

        llm_observability.record_tool_call(
            name,
            time.perf_counter() - start_time,
            False
        )

        raise