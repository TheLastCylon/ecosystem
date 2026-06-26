#pragma once

#include <stdexcept>
#include <string>

#include "../requests/status.hpp"

// Mirrors ekosis/exceptions/{exception_base,response,communication}.py.
// Flat hierarchy, message-carrying only -- no behaviour beyond what() --
// exists so callers can catch a specific failure category rather than a
// bare std::exception.

class ExceptionBase : public std::runtime_error {
public:
    explicit ExceptionBase(const std::string& message) : std::runtime_error(message) {}
};

// --------------------------------------------------------------------------------
// Mirrors ekosis/exceptions/application_level.py's ApplicationProcessingException
// -- deliberately a plain ExceptionBase, NOT a ResponseException. A handler
// can already throw a ResponseException subtype (ServerBusyException etc.)
// directly to pick its own exact status -- this is for the OTHER case: a
// handler that wants to signal "processing failed" generically, without
// depending on the wire-protocol Status enum at all. RequestRouter::dispatch
// catches this specifically and decides the PROCESSING_FAILURE mapping
// itself, the same separation of concerns Python's request_router.py draws
// between ApplicationProcessingException (handler-thrown) and
// RouterProcessingException (router-attached status).
class ApplicationProcessingException : public ExceptionBase {
public:
    using ExceptionBase::ExceptionBase;
};

// --------------------------------------------------------------------------------
// Raised when a response's status is anything other than SUCCESS. Carries
// its actual status value now (previously message-only) -- until the
// buffered-handler work, every ResponseException subclass only ever got
// thrown client-side, reconstructed FROM an already-known status code
// received over the wire (see client_base.cpp). A handler signalling
// APPLICATION_BUSY from inside the server itself is the first real
// server-side consumer, and ServerBase::route_request's catch-all needs the
// actual status to map to instead of always falling back to UNHANDLED.
class ResponseException : public ExceptionBase {
public:
    ResponseException(int status, const std::string& message) : ExceptionBase(message), status_(status) {}
    int status() const { return status_; }
private:
    int status_;
};

class ProtocolParsingException : public ResponseException {
public:
    explicit ProtocolParsingException(const std::string& message) : ResponseException(static_cast<int>(Status::PROTOCOL_PARSING_ERROR), message) {}
};
class ClientDeniedException : public ResponseException {
public:
    explicit ClientDeniedException(const std::string& message) : ResponseException(static_cast<int>(Status::CLIENT_DENIED), message) {}
};
class PydanticValidationException : public ResponseException {
public:
    explicit PydanticValidationException(const std::string& message) : ResponseException(static_cast<int>(Status::PYDANTIC_VALIDATION_ERROR), message) {}
};
class RouteKeyUnknownException : public ResponseException {
public:
    explicit RouteKeyUnknownException(const std::string& message) : ResponseException(static_cast<int>(Status::ROUTE_KEY_UNKNOWN), message) {}
};
class ServerBusyException : public ResponseException {
public:
    explicit ServerBusyException(const std::string& message) : ResponseException(static_cast<int>(Status::APPLICATION_BUSY), message) {}
};
class ProcessingException : public ResponseException {
public:
    explicit ProcessingException(const std::string& message) : ResponseException(static_cast<int>(Status::PROCESSING_FAILURE), message) {}
};
class UnhandledException : public ResponseException {
public:
    explicit UnhandledException(const std::string& message) : ResponseException(static_cast<int>(Status::UNHANDLED), message) {}
};
class UnknownStatusCodeException : public ResponseException {
public:
    explicit UnknownStatusCodeException(const std::string& message) : ResponseException(static_cast<int>(Status::UNHANDLED), message) {}
};

// --------------------------------------------------------------------------------
// Raised by the transport layer itself (not a server response at all).
class CommunicationExceptionBase    : public ExceptionBase { using ExceptionBase::ExceptionBase; };
class ClientDisconnectedException   : public CommunicationExceptionBase { using CommunicationExceptionBase::CommunicationExceptionBase; };
class CommunicationsNonRetryable    : public CommunicationExceptionBase { using CommunicationExceptionBase::CommunicationExceptionBase; };
class CommunicationsMaxRetriesReached : public CommunicationExceptionBase { using CommunicationExceptionBase::CommunicationExceptionBase; };
class CommunicationsEmptyResponse   : public CommunicationExceptionBase { using CommunicationExceptionBase::CommunicationExceptionBase; };
