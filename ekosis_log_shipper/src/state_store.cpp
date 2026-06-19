#include "state_store.hpp"

// --------------------------------------------------------------------------------
StateStore::StateStore(const std::string& db_path)
    : _db(db_path, SQLite::OPEN_READWRITE | SQLite::OPEN_CREATE)
{
    _db.exec(
        "CREATE TABLE IF NOT EXISTS tracked_files ("
        "  path   TEXT PRIMARY KEY,"
        "  inode  INTEGER NOT NULL,"
        "  offset INTEGER NOT NULL"
        ")"
    );
}

// --------------------------------------------------------------------------------
std::optional<StateStore::FileState> StateStore::load(const std::string& path) {
    SQLite::Statement query(_db, "SELECT inode, offset FROM tracked_files WHERE path = ?");
    query.bind(1, path);
    if (query.executeStep()) {
        return FileState{
            static_cast<uint64_t>(query.getColumn(0).getInt64()),
            static_cast<uint64_t>(query.getColumn(1).getInt64())
        };
    }
    return std::nullopt;
}

// --------------------------------------------------------------------------------
void StateStore::save(const std::string& path, uint64_t inode, uint64_t offset) {
    SQLite::Statement stmt(_db,
        "INSERT INTO tracked_files (path, inode, offset) VALUES (?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET inode = excluded.inode, offset = excluded.offset"
    );
    stmt.bind(1, path);
    stmt.bind(2, static_cast<int64_t>(inode));
    stmt.bind(3, static_cast<int64_t>(offset));
    stmt.exec();
}
