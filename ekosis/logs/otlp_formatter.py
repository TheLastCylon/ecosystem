import datetime
import logging

from ..configuration.config_models import AppConfiguration
from ..data_transfer_objects.otlp_log_record import OtlpLogRecord, severity_for_levelno
from ..requests.request_context import _get_current_span_key

# --------------------------------------------------------------------------------
class OtlpFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        severity_number, severity_text = severity_for_levelno(record.levelno)
        span_key                       = _get_current_span_key()
        app_config                     = AppConfiguration()

        log_record = OtlpLogRecord(
            timestamp       = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc).isoformat(),
            severity_number = severity_number,
            severity_text   = severity_text,
            body            = record.getMessage(),
            attributes      = {
                # application_name/instance properly belong on the OTLP
                # Resource (one per file, set from the shipper's own config
                # at wrap-time) -- not repeated per record. They're included
                # here anyway, on purpose: a user with no observability
                # stack reading the raw file directly (tail -f, cat across
                # several apps' files at once) has no other way to tell
                # which app/instance a line came from once it's out of its
                # original filename's context.
                "application_name"    : app_config.name,
                "application_instance": app_config.instance,
                "filename"            : record.filename,
                "lineno"              : record.lineno,
                "module"              : record.module,
                "funcName"            : record.funcName,
            },
            trace_id = span_key.trace_id.hex if span_key else None,
            span_id  = span_key.span_id.hex  if span_key else None,
        )
        return log_record.model_dump_json()
