#include "tracked_file.hpp"
#include "state_store.hpp"
#include "otlp_envelope.hpp"
#include "http_sender.hpp"

#include <dirent.h>
#include <sys/inotify.h>
#include <sys/select.h>
#include <unistd.h>

#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace {

bool has_log_suffix(const std::string& name) {
    static const std::string suffix = ".log";
    return name.size() >= suffix.size()
        && name.compare(name.size() - suffix.size(), suffix.size(), suffix) == 0;
}

std::vector<std::string> list_log_files(const std::string& directory) {
    std::vector<std::string> result;
    DIR* dir = ::opendir(directory.c_str());
    if (!dir) {
        return result;
    }
    struct dirent* entry;
    while ((entry = ::readdir(dir)) != nullptr) {
        std::string name = entry->d_name;
        if (has_log_suffix(name)) {
            result.push_back(directory + "/" + name);
        }
    }
    ::closedir(dir);
    return result;
}

struct WatchedFile {
    std::unique_ptr<TrackedFile> tracked;
    std::vector<std::string>     undelivered; // polled but not yet successfully shipped
};

} // namespace

int main(int argc, char** argv) {
    std::cout << std::unitbuf; // a shipper killed by systemd/SIGTERM shouldn't lose its last buffered line

    if (argc < 4) {
        std::cerr << "usage: ekosis_log_shipper <watch_directory> <otlp_logs_endpoint> <state_db_path>\n";
        return 1;
    }

    const std::string watch_directory = argv[1];
    const std::string otlp_endpoint   = argv[2];
    const std::string state_db_path   = argv[3];

    StateStore state_store(state_db_path);
    HttpSender http_sender(otlp_endpoint);

    std::map<std::string, WatchedFile> watched;

    auto attach = [&](const std::string& path) {
        if (watched.count(path)) {
            return;
        }
        auto         resume = state_store.load(path);
        WatchedFile  wf;
        wf.tracked = resume
            ? std::make_unique<TrackedFile>(path, resume->inode, resume->offset)
            : std::make_unique<TrackedFile>(path);
        watched.emplace(path, std::move(wf));
        std::cout << "ekosis_log_shipper: watching " << path << "\n";
    };

    for (const auto& path : list_log_files(watch_directory)) {
        attach(path);
    }

    int inotify_fd = ::inotify_init1(IN_NONBLOCK);
    if (inotify_fd == -1) {
        std::cerr << "ekosis_log_shipper: inotify_init1 failed\n";
        return 1;
    }
    ::inotify_add_watch(inotify_fd, watch_directory.c_str(),
                         IN_MODIFY | IN_CREATE | IN_MOVED_TO | IN_MOVED_FROM);

    std::cout << "ekosis_log_shipper: " << watch_directory << " -> " << otlp_endpoint << "\n";

    char inotify_event_buf[4096];

    while (true) {
        // Defensive: pick up newly-created files even if an inotify event
        // is somehow missed. Cheap relative to the network round trip below.
        for (const auto& path : list_log_files(watch_directory)) {
            attach(path);
        }

        for (auto& [path, wf] : watched) {
            if (wf.undelivered.empty()) {
                wf.undelivered = wf.tracked->poll();
            }
            if (wf.undelivered.empty()) {
                continue;
            }

            ResourceInfo resource = extract_resource_info(wf.undelivered.front());
            std::string  payload  = build_otlp_logs_payload(wf.undelivered, resource);

            PostResult result = http_sender.post_json(payload);
            if (result.success) {
                state_store.save(path, wf.tracked->inode(), wf.tracked->offset());
                wf.undelivered.clear();
            } else {
                std::cerr << "ekosis_log_shipper: POST failed for " << path
                           << " [" << result.http_status << "] " << result.response_body
                           << ", will retry\n";
            }
        }

        // Wake on inotify activity, or every 2s regardless -- that's what
        // drives retries of a previously-failed POST even with no new
        // file activity.
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(inotify_fd, &read_fds);
        struct timeval timeout{2, 0};
        ::select(inotify_fd + 1, &read_fds, nullptr, nullptr, &timeout);
        if (FD_ISSET(inotify_fd, &read_fds)) {
            ::read(inotify_fd, inotify_event_buf, sizeof(inotify_event_buf)); // drain, contents unused
        }
    }
}
