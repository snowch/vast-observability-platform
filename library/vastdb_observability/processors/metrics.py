"""
Processes OTLP metrics into the generic Metric model.
This version includes a fix to robustly handle numeric values that may be
represented as strings in the raw JSON data.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from vastdb_observability.models import Metric
from vastdb_observability.processors.base import BaseProcessor


class MetricsProcessor(BaseProcessor[List[Metric]]):
    """Processes OTLP metrics into the generic Metric model."""

    def normalize(self, otlp_data: Dict[str, Any]) -> List[Metric]:
        """Normalizes an OTLP metrics payload into a list of Metric objects."""
        metrics = []
        resource_attrs = self._extract_resource_attributes(otlp_data.get("resource", {}))
        
        entity_id = resource_attrs.get("host.name", "unknown_host")

        for scope_metric in otlp_data.get("scope_metrics", []):
            for metric in scope_metric.get("metrics", []):
                processed = self._process_metric(metric, resource_attrs, entity_id)
                if processed:
                    metrics.extend(processed)
        return metrics

    def _extract_resource_attributes(self, resource: Dict) -> Dict[str, str]:
        """Extracts key-value pairs from OTLP resource attributes."""
        attrs = {}
        for attr in resource.get("attributes", []):
            key = attr.get("key", "")
            value_dict = attr.get("value", {})
            value = value_dict.get("stringValue") or value_dict.get("intValue")
            if key and value:
                attrs[key] = str(value)
        return attrs

    def _process_metric(self, metric: Dict, resource_attrs: Dict[str, str], entity_id: str) -> List[Metric]:
        """Processes a single OTLP metric into one or more Metric objects."""
        metrics = []
        metric_name = metric.get("name", "unknown")
        
        metric_type_map = {"gauge": "gauge", "sum": "counter", "histogram": "histogram"}
        metric_type_key = next((key for key in metric_type_map if key in metric), None)

        if not metric_type_key:
            return []

        for point in metric[metric_type_key].get("data_points", []):
            # *** BUG FIX IS HERE ***
            # Safely get and convert the value, whether it's 'as_int' or 'as_double',
            # and handle if it's a string or number.
            raw_value = point.get("as_int") or point.get("as_double")
            if raw_value is None:
                continue
            
            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                continue # Skip data points with non-numeric values

            metrics.append(Metric(
                timestamp=self._parse_otlp_timestamp(point.get("time_unix_nano", 0)),
                entity_id=entity_id,
                metric_name=metric_name,
                metric_value=value,
                metric_type=metric_type_map[metric_type_key],
                source=resource_attrs.get("db.system", "unknown"),
                environment=resource_attrs.get("deployment.environment", "production"),
                unit=metric.get("unit"),
                tags=self._extract_attributes(point.get("attributes", [])),
                metadata={"description": metric.get("description", "")},
            ))
        return metrics

    def _extract_attributes(self, attributes: List[Dict]) -> Dict[str, str]:
        """Extracts key-value pairs from data point attributes."""
        attrs = {}
        for attr in attributes:
            key = attr.get("key", "")
            value_dict = attr.get("value", {})
            value = value_dict.get("stringValue")
            if key and value:
                attrs[key] = value
        return attrs

    def _parse_otlp_timestamp(self, time_unix_nano: Any) -> datetime:
        """Safely convert OTLP nanosecond timestamp (str or int) to datetime."""
        try:
            return datetime.fromtimestamp(int(time_unix_nano) / 1_000_000_000)
        except (ValueError, TypeError):
            return datetime.utcnow()

    def enrich(self, metrics: List[Metric]) -> List[Metric]:
        """Enriches metrics with computed tags based on their values."""
        for metric in metrics:
            if "error" in metric.metric_name and metric.metric_value > 0:
                metric.tags["severity"] = "warning"
        return metrics
    
    def process(self, otlp_data: Dict[str, Any], **kwargs) -> List[Metric]:
        """Full processing pipeline for OTLP metrics."""
        normalized = self.normalize(otlp_data)
        if self.config.enable_enrichment:
            normalized = self.enrich(normalized)
        return normalized