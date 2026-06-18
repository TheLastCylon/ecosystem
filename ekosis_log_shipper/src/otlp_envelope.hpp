#pragma once

#include <string>
#include <vector>

// service_name/service_instance_id are OTel Resource attributes -- one per
// file, not repeated per log line (see the Alloy config's reasoning for
// the same distinction on the Loki side).
struct ResourceInfo {
    std::string service_name;
    std::string service_instance_id;
};

// application_name/application_instance already ride in every ekosis log
// line's attributes (OtlpFormatter put them there for the no-observability
// -stack human reading the raw file). Pull the Resource identity from there
// rather than parsing it out of the filename.
ResourceInfo extract_resource_info(const std::string& json_line);

// Wraps raw OtlpLogRecord JSON lines (one per ekosis log line) into one
// OTLP/HTTP+JSON logs export payload: resourceLogs -> scopeLogs ->
// logRecords. Mechanical, fixed shape -- no branching on log content.
std::string build_otlp_logs_payload(const std::vector<std::string>& json_lines, const ResourceInfo& resource);
