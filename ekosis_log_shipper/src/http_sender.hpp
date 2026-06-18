#pragma once

#include <string>

struct PostResult {
    bool        success;
    long        http_status;
    std::string response_body; // the endpoint's own error detail, on failure
};

// One per process. POSTs an OTLP/HTTP+JSON payload to a logs endpoint.
class HttpSender {
public:
    explicit HttpSender(std::string endpoint_url);
    ~HttpSender();

    HttpSender(const HttpSender&)            = delete;
    HttpSender& operator=(const HttpSender&) = delete;

    // success is true on a 2xx response. On failure, the caller should NOT
    // advance any persisted offset -- nothing was consumed, safe to retry
    // the same payload. response_body carries the endpoint's own error
    // detail so failures are diagnosable instead of just "POST failed".
    PostResult post_json(const std::string& json_body);

private:
    std::string _endpoint_url;
};
