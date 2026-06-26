#pragma once

#include <mutex>
#include <string>

#include <spdlog/common.h>
#include <spdlog/details/file_helper.h>
#include <spdlog/details/null_mutex.h>
#include <spdlog/details/os.h>
#include <spdlog/sinks/base_sink.h>

// Rotating file sink matching ekosis's logging.handlers.RotatingFileHandler
// naming convention exactly. spdlog's own spdlog::sinks::rotating_file_sink
// inserts the backup index BEFORE the extension ("mylog.3.txt"); Python
// appends it AFTER the whole filename ("mylog.log.3"). Nothing else differs
// -- rotate-on-size, rename-then-fresh-file-at-the-unchanged-active-path are
// copied verbatim from spdlog::sinks::rotating_file_sink (MIT licensed).
// This exists only to fix the naming gap, not to reinvent rotation.
//
// rotating_file_sink doesn't expose a FileNameCalc template policy the way
// spdlog's own daily_file_sink/hourly_file_sink do (checked -- it's a real
// inconsistency in spdlog's own sinks, not a deliberate design stance) --
// extending base_sink<Mutex> ourselves is exactly the documented spdlog
// answer to "I need different sink behaviour." A real dependent of spdlog,
// not a fork of it. See documentation/logging.md.
template <typename Mutex>
class EkosisRotatingFileSink final : public spdlog::sinks::base_sink<Mutex> {
public:
    EkosisRotatingFileSink(spdlog::filename_t base_filename, std::size_t max_size, std::size_t max_files,
                            bool rotate_on_open = false, const spdlog::file_event_handlers& event_handlers = {})
        : base_filename_(std::move(base_filename)),
          max_size_(max_size),
          max_files_(max_files),
          file_helper_(event_handlers) {
        if (max_size == 0) {
            spdlog::throw_spdlog_ex("EkosisRotatingFileSink: max_size arg cannot be zero");
        }
        if (max_files > 200000) {
            spdlog::throw_spdlog_ex("EkosisRotatingFileSink: max_files arg cannot exceed 200000");
        }

        file_helper_.open(calc_filename(base_filename_, 0));
        current_size_ = file_helper_.size(); // expensive, called only once

        if (rotate_on_open && current_size_ > 0) {
            rotate_();
            current_size_ = 0;
        }
    }

    // e.g. calc_filename("logs/mylog.log", 3) => "logs/mylog.log.3" -- index
    // appended after the FULL filename, matching Python's
    // `self.baseFilename + "." + str(i)` exactly (unlike spdlog's own
    // rotating_file_sink, which inserts before the extension).
    static spdlog::filename_t calc_filename(const spdlog::filename_t& filename, std::size_t index) {
        if (index == 0u) {
            return filename;
        }
        return spdlog::fmt_lib::format(SPDLOG_FILENAME_T("{}.{}"), filename, index);
    }

    spdlog::filename_t filename() {
        std::lock_guard<Mutex> lock(spdlog::sinks::base_sink<Mutex>::mutex_);
        return file_helper_.filename();
    }

protected:
    void sink_it_(const spdlog::details::log_msg& msg) override {
        spdlog::memory_buf_t formatted;
        spdlog::sinks::base_sink<Mutex>::formatter_->format(msg, formatted);
        auto new_size = current_size_ + formatted.size();

        // rotate if the new estimated file size exceeds max size. Only
        // rotate if the real size > 0, to better deal with a full disk.
        if (new_size > max_size_) {
            file_helper_.flush();
            if (file_helper_.size() > 0) {
                rotate_();
                new_size = formatted.size();
            }
        }

        file_helper_.write(formatted);
        current_size_ = new_size;
    }

    void flush_() override {
        file_helper_.flush();
    }

private:
    // Rotate files (with this sink's naming, not spdlog's):
    // mylog.log -> mylog.log.1 -> mylog.log.2 -> ... -> deleted past max_files_.
    void rotate_() {
        using spdlog::details::os::filename_to_str;
        using spdlog::details::os::path_exists;

        file_helper_.close();
        for (auto i = max_files_; i > 0; --i) {
            spdlog::filename_t src = calc_filename(base_filename_, i - 1);
            if (!path_exists(src)) {
                continue;
            }
            spdlog::filename_t target = calc_filename(base_filename_, i);

            if (!rename_file_(src, target)) {
                // Retry once after a short delay -- mirrors spdlog's own
                // workaround for transient rename failures under load.
                spdlog::details::os::sleep_for_millis(100);
                if (!rename_file_(src, target)) {
                    file_helper_.reopen(true); // truncate anyway, don't grow past the limit
                    current_size_ = 0;
                    spdlog::throw_spdlog_ex(
                        "EkosisRotatingFileSink: failed renaming " + filename_to_str(src) +
                            " to " + filename_to_str(target),
                        errno);
                }
            }
        }
        file_helper_.reopen(true);
    }

    // Deletes the target if it already exists, then renames src to target.
    bool rename_file_(const spdlog::filename_t& src_filename, const spdlog::filename_t& target_filename) {
        (void)spdlog::details::os::remove(target_filename);
        return spdlog::details::os::rename(src_filename, target_filename) == 0;
    }

    spdlog::filename_t          base_filename_;
    std::size_t                 max_size_;
    std::size_t                 max_files_;
    std::size_t                 current_size_;
    spdlog::details::file_helper file_helper_;
};

using EkosisRotatingFileSinkMt = EkosisRotatingFileSink<std::mutex>;
using EkosisRotatingFileSinkSt = EkosisRotatingFileSink<spdlog::details::null_mutex>;
