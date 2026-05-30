from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Iterable


LabelItems = tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class MetricSample:
    name: str
    labels: LabelItems
    value: float


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, LabelItems], float] = {}
        self._gauges: dict[tuple[str, LabelItems], float] = {}

    def increment_counter(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        amount: float = 1.0,
    ) -> None:
        key = (name, _normalize_labels(labels))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + amount

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = (name, _normalize_labels(labels))
        with self._lock:
            self._gauges[key] = value

    def record_tool_call(self, tool_name: str, result_code: str, duration_ms: float) -> None:
        labels = {"tool_name": tool_name, "result_code": result_code}
        self.increment_counter("mcp_gateway_tool_calls_total", labels)
        self.increment_counter("mcp_gateway_tool_call_duration_ms_count", labels)
        self.increment_counter("mcp_gateway_tool_call_duration_ms_sum", labels, duration_ms)

    def record_catalog_refresh(self, result) -> None:
        refresh_result = "success" if result.success else "failure"
        if result.used_snapshot:
            refresh_result = "snapshot"
        self.increment_counter(
            "mcp_gateway_catalog_refresh_total",
            {"result": refresh_result},
        )
        self.set_gauge("mcp_gateway_catalog_tools", result.tool_count)
        self.set_gauge("mcp_gateway_catalog_instances", result.instance_count)
        self.set_gauge(
            "mcp_gateway_catalog_healthy_instances",
            result.healthy_instance_count,
        )
        self.set_gauge(
            "mcp_gateway_catalog_unavailable_instances",
            result.unavailable_instance_count,
        )

    def render_prometheus(self) -> str:
        with self._lock:
            counters = [
                MetricSample(name, labels, value)
                for (name, labels), value in self._counters.items()
            ]
            gauges = [
                MetricSample(name, labels, value)
                for (name, labels), value in self._gauges.items()
            ]

        lines: list[str] = []
        _append_metric_family(lines, counters, "counter")
        _append_metric_family(lines, gauges, "gauge")
        return "\n".join(lines) + "\n"


def _normalize_labels(labels: dict[str, str] | None) -> LabelItems:
    if not labels:
        return ()
    return tuple(sorted((key, str(value)) for key, value in labels.items()))


def _append_metric_family(lines: list[str], samples: Iterable[MetricSample], metric_type: str) -> None:
    emitted_names: set[str] = set()
    for sample in sorted(samples, key=lambda item: (item.name, item.labels)):
        if sample.name not in emitted_names:
            lines.append(f"# TYPE {sample.name} {metric_type}")
            emitted_names.add(sample.name)
        lines.append(f"{sample.name}{_format_labels(sample.labels)} {_format_value(sample.value)}")


def _format_labels(labels: LabelItems) -> str:
    if not labels:
        return ""
    label_text = ",".join(f'{key}="{_escape_label_value(value)}"' for key, value in labels)
    return "{" + label_text + "}"


def _escape_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _format_value(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
