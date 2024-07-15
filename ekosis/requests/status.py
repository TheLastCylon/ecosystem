from enum import Enum


# --------------------------------------------------------------------------------
class Status(Enum):
    # All is good
    SUCCESS                   = 0   # The request was successfully processed.
    # Client is broken
    PROTOCOL_PARSING_ERROR    = 100 # A message received was so broken we could not do basic JSON parsing on it.
    CLIENT_DENIED             = 200 # The Client is not in the white list and my not communicate to this process.
    PYDANTIC_VALIDATION_ERROR = 300 # Pydantic could not validate a DTO, from the JSON we received.
    ROUTE_KEY_UNKNOWN         = 400 # No matching identifier for the supplied value of "route_key" in request, was found
    # Server is broken
    APPLICATION_BUSY          = 500 # used by server applications to inform requesters that a request won't be processed due to server overload.
    PROCESSING_FAILURE        = 600 # For use by apps that need to report on an internal processing failure.
    UNKNOWN                   = 999 # Sorry, I don't know what went wrong.


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
