#pragma once

#include <cstdint>
#include <string>
#include <vector>

// Tails one ekosis log file, surviving rotation.
//
// Identity is the inode, not the path. RotatingFileHandler renames the
// active file out from under its path on rollover and opens a fresh, empty
// file at the original path -- a path-based tailer would see the new empty
// file and silently lose whatever was still unread in the renamed one. An
// open file descriptor stays attached to the same underlying file (same
// inode) regardless of what name it currently has on disk, or even if it
// gets unlinked -- so draining the OLD fd to its end before switching to a
// freshly-opened fd at the (now-different) path is rotation-safe with no
// path-guessing involved.
class TrackedFile {
public:
    explicit TrackedFile(std::string path);
    TrackedFile(std::string path, uint64_t resume_inode, uint64_t resume_offset);
    ~TrackedFile();

    TrackedFile(const TrackedFile&)            = delete;
    TrackedFile& operator=(const TrackedFile&) = delete;

    // Returns any new, complete (newline-terminated) lines since the last
    // call. Detects rotation internally -- drains the old file to its end
    // before reading from the new one, so a rotation mid-call never loses
    // a line. A trailing incomplete line is buffered and completed on a
    // later call, never reported early.
    std::vector<std::string> poll();

    const std::string& path()   const { return _path;   }
    uint64_t            inode() const { return _inode;  }
    uint64_t            offset() const { return _offset; }

private:
    void open_at_path(uint64_t start_offset);
    void read_available_lines(std::vector<std::string>& lines);

    std::string _path;
    int         _fd     = -1;
    uint64_t    _inode  = 0;
    uint64_t    _offset = 0;
    std::string _pending; // bytes read but not yet part of a complete line
};
