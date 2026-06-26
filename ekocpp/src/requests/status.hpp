#pragma once

// Mirrors ekosis/requests/status.py exactly -- same numeric values, both
// sides of the wire agree on what a status code means.
enum class Status : int {
    SUCCESS                   = 0,   // The request was successfully processed.
    PROTOCOL_PARSING_ERROR    = 100, // A message received was so broken we could not do basic msgpack parsing on it.
    CLIENT_DENIED             = 200, // The Client is not in the white list and may not communicate to this process.
    PYDANTIC_VALIDATION_ERROR = 300, // DTO validation failed for the data we received.
    ROUTE_KEY_UNKNOWN         = 400, // No matching identifier for the supplied value of "route_key" was found.
    APPLICATION_BUSY          = 500, // Server applications use this to report overload.
    PROCESSING_FAILURE        = 600, // For use by apps that need to report on an internal processing failure.
    UNHANDLED                 = 999, // An unhandled exception occurred.
};
