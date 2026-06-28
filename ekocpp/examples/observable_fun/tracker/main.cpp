#include <memory>
#include <string>

#include <SQLiteCpp/SQLiteCpp.h>

#include "application_base.hpp"
#include "configuration/config_models.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "data_transfer_objects/request_dto.hpp"
#include "initiate_otlp_tracing.hpp"
#include "tracker_dto.hpp"

class LogDatabase {
public:
    explicit LogDatabase(const std::string& path)
        : db_(path, SQLite::OPEN_READWRITE | SQLite::OPEN_CREATE) {
        db_.exec(R"(
            CREATE TABLE IF NOT EXISTS tracker_logs (
                record_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                span_key           BLOB    NOT NULL UNIQUE,
                request_message    TEXT,
                request_timestamp  REAL,
                response_message   TEXT,
                response_timestamp REAL
            )
        )");
    }

    void log_request(const SpanKey& span_key, const std::string& message, double timestamp) {
        const auto bytes = span_key.to_bytes();
        if (exists(bytes)) {
            SQLite::Statement s(db_, "UPDATE tracker_logs SET request_message=?, request_timestamp=? WHERE span_key=?");
            s.bind(1, message);
            s.bind(2, timestamp);
            s.bind(3, bytes.data(), static_cast<int>(bytes.size()));
            s.exec();
        } else {
            SQLite::Statement s(db_, "INSERT INTO tracker_logs (span_key, request_message, request_timestamp) VALUES (?,?,?)");
            s.bind(1, bytes.data(), static_cast<int>(bytes.size()));
            s.bind(2, message);
            s.bind(3, timestamp);
            s.exec();
        }
    }

    void log_response(const SpanKey& span_key, const std::string& message, double timestamp) {
        const auto bytes = span_key.to_bytes();
        if (exists(bytes)) {
            SQLite::Statement s(db_, "UPDATE tracker_logs SET response_message=?, response_timestamp=? WHERE span_key=?");
            s.bind(1, message);
            s.bind(2, timestamp);
            s.bind(3, bytes.data(), static_cast<int>(bytes.size()));
            s.exec();
        } else {
            SQLite::Statement s(db_, "INSERT INTO tracker_logs (span_key, response_message, response_timestamp) VALUES (?,?,?)");
            s.bind(1, bytes.data(), static_cast<int>(bytes.size()));
            s.bind(2, message);
            s.bind(3, timestamp);
            s.exec();
        }
    }

private:
    bool exists(const std::array<uint8_t, 24>& bytes) {
        SQLite::Statement s(db_, "SELECT 1 FROM tracker_logs WHERE span_key=?");
        s.bind(1, bytes.data(), static_cast<int>(bytes.size()));
        return s.executeStep();
    }

    SQLite::Database db_;
};

class TrackerServer : public ApplicationBase {
public:
    TrackerServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        const std::string db_file = AppConfiguration::instance().extra("DB_FILE");
        db_ = std::make_unique<LogDatabase>(db_file);
        initiate_otlp_tracing();
        register_buffered_endpoint("app.log_request",  this, &TrackerServer::log_request,  1000);
        register_buffered_endpoint("app.log_response", this, &TrackerServer::log_response, 1000);
    }

private:
    bool log_request(SpanKey span_key, TrackerLogRequestDto dto) {
        spdlog::info(
            "REQUEST : span_key[{}], time[{}], data[{}]",
            span_key.to_string(),
            dto.timestamp,
            dto.request
        );
        db_->log_request(span_key, dto.request, dto.timestamp);
        return true;
    }

    bool log_response(SpanKey span_key, TrackerLogRequestDto dto) {
        spdlog::info(
            "RESPONSE : span_key[{}], time[{}], data[{}]",
            span_key.to_string(),
            dto.timestamp,
            dto.request
        );
        db_->log_response(span_key, dto.request, dto.timestamp);
        return true;
    }

    std::unique_ptr<LogDatabase> db_;
};

int main(int argc, char** argv) {
    TrackerServer app(argc, argv);
    app.start();
}
