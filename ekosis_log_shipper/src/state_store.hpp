#pragma once

#include <cstdint>
#include <optional>
#include <string>

#include <SQLiteCpp/SQLiteCpp.h>

// Survives shipper restarts: remembers, per watched file path, which inode
// it was attached to and how far it had read. On restart, TrackedFile uses
// this to resume exactly where it left off if the file hasn't rotated since,
// or start fresh at offset 0 if it has (small loss window only across a
// restart that spans an entire rotation -- the log file itself is the
// durable buffer otherwise).
class StateStore {
public:
    explicit StateStore(const std::string& db_path);

    struct FileState {
        uint64_t inode;
        uint64_t offset;
    };

    std::optional<FileState> load(const std::string& path);
    void save(const std::string& path, uint64_t inode, uint64_t offset);

private:
    SQLite::Database _db;
};
