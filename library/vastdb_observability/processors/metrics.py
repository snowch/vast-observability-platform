from typing import Dict, Any, List
from datetime import datetime
from vastdb_observability.models import ProcessedMetric
from vastdb_observability.processors.base import BaseProcessor


class MetricsProcessor(BaseProcessor[List[ProcessedMetric]]):
    """Process OTLP metrics into normalized format."""

    def normalize(self, otlp_data: Dict[str, Any]) -> List[ProcessedMetric]:
        """Normalize OTLP metrics format to ProcessedMetric model."""
        metrics = []
        resource_attrs = self._extract_resource_attributes(otlp_data.get("resource", {}))

        for scope_metric in otlp_data.get("scopeMetrics", []):
            for metric in scope_metric.get("metrics", []):
                processed = self._process_metric(metric, resource_attrs)
                if processed:
                    metrics.extend(processed)

        return metrics

    def _extract_resource_attributes(self, resource: Dict) -> Dict[str, str]:
        """Extract key-value pairs from OTLP resource attributes."""
        attrs = {}
        for attr in resource.get("attributes", []):
            key = attr.get("key", "")
            value = attr.get("value", {})

            if "stringValue" in value:
                attrs[key] = value["stringValue"]
            elif "intValue" in value:
                attrs[key] = str(value["intValue"])
            elif "doubleValue" in value:
                attrs[key] = str(value["doubleValue"])

        return attrs

    def _process_metric(self, metric: Dict, resource_attrs: Dict[str, str]) -> List[ProcessedMetric]:
        """Process a single OTLP metric into ProcessedMetric objects."""
        metrics = []
        metric_name = metric.get("name", "unknown")
        unit = metric.get("unit", "")

        if "gauge" in metric:
            metric_type = "gauge"
            data_points = metric["gauge"].get("dataPoints", [])
        elif "sum" in metric:
            metric_type = "counter"
            data_points = metric["sum"].get("dataPoints", [])
        elif "histogram" in metric:
            metric_type = "histogram"
            data_points = metric["histogram"].get("dataPoints", [])
        else:
            return metrics

        for point in data_points:
            timestamp = self._parse_otlp_timestamp(point.get("timeUnixNano", 0))

            value = None
            if "asInt" in point:
                value = float(point["asInt"])
            elif "asDouble" in point:
                value = point["asDouble"]

            if value is None:
                continue

            point_attrs = self._extract_attributes(point.get("attributes", []))

            processed = ProcessedMetric(
                timestamp=timestamp,
                source=resource_attrs.get("db.system", "unknown"),
                host=resource_attrs.get("host.name", "unknown"),
                database_name=resource_attrs.get("db.name", "unknown"),
                environment=resource_attrs.get("deployment.environment", "production"),
                metric_name=metric_name,
                metric_value=value,
                metric_type=metric_type,
                unit=unit or None,
                tags=point_attrs,
                metadata={"description": metric.get("description", "")},
            )

            metrics.append(processed)

        return metrics

    def _extract_attributes(self, attributes: List[Dict]) -> Dict[str, str]:
        """Extract attributes from data point."""
        attrs = {}
        for attr in attributes:
            key = attr.get("key", "")
            value = attr.get("value", {})
            if "stringValue" in value:
                attrs[key] = value["stringValue"]
        return attrs

    def _parse_otlp_timestamp(self, time_unix_nano: int) -> datetime:
        """Convert OTLP nanosecond timestamp to datetime."""
        if time_unix_nano == 0:
            return datetime.utcnow()
        return datetime.fromtimestamp(time_unix_nano / 1_000_000_000)

    def enrich(self, metrics: List[ProcessedMetric]) -> List[ProcessedMetric]:
        """Enrich metrics with computed fields."""
        for metric in metrics:
            if "time" in metric.metric_name.lower() or "latency" in metric.metric_name.lower():
                if metric.metric_value < 100:
                    metric.tags["performance"] = "fast"
                elif metric.metric_value < 1000:
                    metric.tags["performance"] = "normal"
                else:
                    metric.tags["performance"] = "slow"

            if "error" in metric.metric_name.lower() or "deadlock" in metric.metric_name.lower():
                if metric.metric_value > 0:
                    metric.tags["severity"] = "warning"

        return metrics

    def process(self, otlp_data: Dict[str, Any], **kwargs) -> List[ProcessedMetric]:
        """Process OTLP metrics through full pipeline."""
        normalized = self.normalize(otlp_data)
        if self.config.enable_enrichment and kwargs.get("enrich", True):
            normalized = self.enrich(normalized)
        return normalized
