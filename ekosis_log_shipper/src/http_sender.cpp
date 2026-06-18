#include "http_sender.hpp"

#include <curl/curl.h>

namespace {

size_t capture_response_body(char* ptr, size_t size, size_t nmemb, void* user_data) {
    auto* out = static_cast<std::string*>(user_data);
    out->append(ptr, size * nmemb);
    return size * nmemb;
}

} // namespace

// --------------------------------------------------------------------------------
HttpSender::HttpSender(std::string endpoint_url)
    : _endpoint_url(std::move(endpoint_url))
{
    curl_global_init(CURL_GLOBAL_DEFAULT);
}

// --------------------------------------------------------------------------------
HttpSender::~HttpSender() {
    curl_global_cleanup();
}

// --------------------------------------------------------------------------------
PostResult HttpSender::post_json(const std::string& json_body) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        return PostResult{false, 0, "curl_easy_init failed"};
    }

    struct curl_slist* headers       = curl_slist_append(nullptr, "Content-Type: application/json");
    std::string         response_body;

    curl_easy_setopt(curl, CURLOPT_URL,            _endpoint_url.c_str());
    curl_easy_setopt(curl, CURLOPT_POST,            1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS,      json_body.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE,   static_cast<long>(json_body.size()));
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER,      headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION,   capture_response_body);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA,       &response_body);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT,         10L);

    CURLcode result    = curl_easy_perform(curl);
    long     http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);

    if (result != CURLE_OK) {
        response_body = curl_easy_strerror(result);
    }
    curl_easy_cleanup(curl);

    bool success = result == CURLE_OK && http_code >= 200 && http_code < 300;
    return PostResult{success, http_code, response_body};
}
