from typing import Any, Dict, Generator, Optional, Set, Tuple


# Groups excluded from endpoint_data and queue metrics by default.
# eco.* endpoints are EcoSystem system internals -- near-zero call counts,
# -1 p95/p99 most of the time, and irrelevant to application health monitoring.
_DEFAULT_EXCLUDE_GROUPS: Set[str] = {"eco"}


# --------------------------------------------------------------------------------
def _flatten(obj: Any, prefix: str) -> Generator[Tuple[str, float], None, None]:
    if isinstance(obj, dict):
        for key, val in obj.items():
            safe_key = key.replace(".", "_").replace("-", "_")
            yield from _flatten(val, f"{prefix}_{safe_key}" if prefix else safe_key)
    elif isinstance(obj, (int, float)):
        yield prefix, float(obj)


# --------------------------------------------------------------------------------
def _iter_queue_groups(
    queue_data     : Dict,
    exclude_groups : Set[str],
    metric_prefix  : str,
    labels         : Dict,
) -> Generator[Tuple[str, float, dict], None, None]:
    for group, endpoints in queue_data.items():
        if group in exclude_groups:
            continue
        if not isinstance(endpoints, dict):
            continue
        for endpoint_name, sizes in endpoints.items():
            if not isinstance(sizes, dict):
                continue
            queue_labels = {**labels, "group": group, "endpoint": endpoint_name}
            pending = sizes.get("pending")
            if pending is not None:
                yield f"{metric_prefix}_queue_pending", float(pending), queue_labels
            error = sizes.get("error")
            if error is not None:
                yield f"{metric_prefix}_queue_error", float(error), queue_labels


# --------------------------------------------------------------------------------
def translate_gathered_stats(
    stats          : Dict,
    service_name   : str,
    instance       : str,
    exclude_groups : Optional[Set[str]] = None,
) -> Generator[Tuple[str, float, dict], None, None]:
    """Yield (metric_name, value, labels) tuples from a gathered stats response.

    service_name and instance are used as fallbacks only -- the stats response
    carries application.name and application.instance which are more authoritative
    (the service knows its own identity).

    exclude_groups: set of endpoint group names to skip. Defaults to {"eco"} which
    filters out EcoSystem internal endpoints. Pass set() to include everything.
    """
    if exclude_groups is None:
        exclude_groups = _DEFAULT_EXCLUDE_GROUPS

    # Application identity from the stats response itself
    app          = stats.get("application", {})
    service_name = app.get("name",     service_name)
    instance     = app.get("instance", instance)
    labels       = {"service": service_name, "instance": instance}

    # uptime
    uptime = stats.get("uptime")
    if uptime is not None:
        yield "ekosis_uptime_seconds", float(uptime), labels

    # gather_period -- needed to derive per-second rates from call_count (which resets each period)
    gather_period = stats.get("gather_period")
    if gather_period is not None:
        yield "ekosis_gather_period_seconds", float(gather_period), labels

    # endpoint_data -- call_count, p95, p99 per endpoint (user groups only)
    endpoint_data = stats.get("endpoint_data", {})
    for group, endpoints in endpoint_data.items():
        if group in exclude_groups:
            continue
        if not isinstance(endpoints, dict):
            continue
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

    # buffered endpoint queues
    yield from _iter_queue_groups(
        stats.get("buffered_endpoint_sizes", {}),
        exclude_groups,
        "ekosis_buffered_endpoint",
        labels,
    )

    # buffered sender queues
    yield from _iter_queue_groups(
        stats.get("buffered_sender_sizes", {}),
        exclude_groups,
        "ekosis_buffered_sender",
        labels,
    )

    # custom stats -- top-level keys not in the known set
    known_keys = {
        "application",
        "endpoint_data",
        "buffered_endpoint_sizes",
        "buffered_sender_sizes",
        "timestamp",
        "uptime",
        "gather_period",
    }
    for key, val in stats.items():
        if key in known_keys:
            continue
        for metric_suffix, metric_val in _flatten(val, key):
            yield f"ekosis_custom_{metric_suffix}", metric_val, labels
