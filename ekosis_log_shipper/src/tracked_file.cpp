#include "tracked_file.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <stdexcept>

// --------------------------------------------------------------------------------
TrackedFile::TrackedFile(std::string path)
    : _path(std::move(path))
{
    open_at_path(0);
}

// --------------------------------------------------------------------------------
TrackedFile::TrackedFile(std::string path, uint64_t resume_inode, uint64_t resume_offset)
    : _path(std::move(path))
{
    struct stat path_stat{};
    if (::stat(_path.c_str(), &path_stat) == 0 && static_cast<uint64_t>(path_stat.st_ino) == resume_inode) {
        open_at_path(resume_offset); // same file we left off on -- resume exactly where we stopped
    } else {
        open_at_path(0); // rotated while we were away -- start the current file from the top
    }
}

// --------------------------------------------------------------------------------
TrackedFile::~TrackedFile() {
    if (_fd != -1) {
        ::close(_fd);
    }
}

// --------------------------------------------------------------------------------
void TrackedFile::open_at_path(uint64_t start_offset) {
    _fd = ::open(_path.c_str(), O_RDONLY);
    if (_fd == -1) {
        throw std::runtime_error("TrackedFile: unable to open '" + _path + "'");
    }

    struct stat file_stat{};
    if (::fstat(_fd, &file_stat) != 0) {
        ::close(_fd);
        _fd = -1;
        throw std::runtime_error("TrackedFile: unable to fstat '" + _path + "'");
    }

    if (start_offset > 0) {
        ::lseek(_fd, static_cast<off_t>(start_offset), SEEK_SET);
    }

    _inode   = static_cast<uint64_t>(file_stat.st_ino);
    _offset  = start_offset;
    _pending.clear();
}

// --------------------------------------------------------------------------------
void TrackedFile::read_available_lines(std::vector<std::string>& lines) {
    char    buf[8192];
    ssize_t n;
    while ((n = ::read(_fd, buf, sizeof(buf))) > 0) {
        _pending.append(buf, static_cast<size_t>(n));
    }

    size_t start = 0;
    while (true) {
        size_t newline = _pending.find('\n', start);
        if (newline == std::string::npos) {
            break;
        }
        lines.push_back(_pending.substr(start, newline - start));
        start = newline + 1;
    }

    _offset += start;       // only count bytes belonging to complete, shipped lines
    _pending.erase(0, start);
}

// --------------------------------------------------------------------------------
std::vector<std::string> TrackedFile::poll() {
    std::vector<std::string> lines;

    struct stat path_stat{};
    bool        path_exists = ::stat(_path.c_str(), &path_stat) == 0;

    if (path_exists && static_cast<uint64_t>(path_stat.st_ino) != _inode) {
        // Rotation: drain whatever is still unread in the OLD file before
        // switching. The old fd is still attached to the renamed/unlinked
        // file regardless of its current name -- this is what makes the
        // drain safe rather than a race against the rename.
        read_available_lines(lines);
        ::close(_fd);
        _fd = -1;
        open_at_path(0);
    }

    read_available_lines(lines);
    return lines;
}
