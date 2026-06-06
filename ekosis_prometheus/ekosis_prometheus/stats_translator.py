from typing import Any, Dict, Generator, Tuple


# --------------------------------------------------------------------------------
# Yields (metric_name, value, labels) tuples from a gathered stats response.
# metric_name uses underscores; labels are a dict.
# --------------------------------------------------------------------------------
def _flatten(obj: Any, prefix: str) -> Generator[Tuple[str, float], None, None]:
    if isinstance(obj, dict):
        for key, val in obj.items():
            safe_key = key.replace(".", "_").replace("-", "_")
            yield from _flatten(val, f"{prefix}_{safe_key}" if prefix else safe_key)
    elif isinstance(obj, (int, float)):
        yield prefix, float(obj)


# --------------------------------------------------------------------------------
def translate_gathered_stats(stats: Dict, service_name: str, instance: str) -> Generator[Tuple[str, float, dict], None, None]:
    labels = {"service": service_name, "instance": instance}

    # uptime
    uptime = stats.get("uptime")
    if uptime is not None:
        yield "ekosis_uptime_seconds", float(uptime), labels

    # endpoint_data -- call_count, p95, p99 per endpoint
    endpoint_data = stats.get("endpoint_data", {})
    for group, endpoints in endpoint_data.items():
        for endpoint_name, data in endpoints.items():
            if not isinstance(data, dict):
                continue
            endpoint_labels = {**labels, "group": group, "endpoint": endpoint_name}

            call_count = data.get("call_count")
            if call_count is not None:
                yield "ekosis_endpoint_call_count", float(call_count), endpoint_labels

            p95 = data.get("p95")
            if p95 is not None and p95 >= 0:
                yield "ekosis_endpoint_p95_seconds", float(p95), endpoint_labels

            p99 = data.get("p99")
            if p99 is not None and p99 >= 0:
                yield "ekosis_endpoint_p99_seconds", float(p99), endpoint_labels

    # buffered_endpoint_sizes -- pending and error queue depths
    queue_sizes = stats.get("buffered_endpoint_sizes", {})
    for group, endpoints in queue_sizes.items():
        for endpoint_name, sizes in endpoints.items():
            if not isinstance(sizes, dict):
                continue
            queue_labels = {**labels, "group": group, "endpoint": endpoint_name}

            pending = sizes.get("pending")
            if pending is not None:
                yield "ekosis_queue_pending", float(pending), queue_labels

            error = sizes.get("error")
            if error is not None:
                yield "ekosis_queue_error", float(error), queue_labels

    # custom stats -- anything under a top-level key that isn't the known fields
    known_keys = {"application", "endpoint_data", "buffered_endpoint_sizes", "timestamp", "uptime"}
    for key, val in stats.items():
        if key in known_keys:
            continue
        for metric_suffix, metric_val in _flatten(val, key):
            yield f"ekosis_custom_{metric_suffix}", metric_val, labels
