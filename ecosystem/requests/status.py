from enum import Enum


# --------------------------------------------------------------------------------
class Status(Enum):
    SUCCESS                   = 0   # The request was successfully processed.
    JSON_PARSING_ERROR        = 100 # Could not parse the provided json.
    COMMAND_NOT_SUPPORTED     = 200 # No matching identifier for the supplied value of "route_key" in request, was found
    INVALID_PARAMETER         = 300 # used to indicate invalid values for supplied parameters
    MISSING_PARAMETER         = 400 # used to indicate the absence of an expected parameter
    APPLICATION_BUSY          = 500 # used by server applications to inform requesters that a request won't be processed due to server overload.
    APPLICATION_SHUTTING_DOWN = 600 # used by server applications to inform requesters that a request won't be processed due to the server shutting down.
    CLIENT_DENIED             = 700 # The Client is not in the white list and my not communicate to this process.
    PROCESSING_FAILURE        = 800 # For use by apps that need to report on an internal processing failure.
    UNKNOWN                   = 900 # Sorry, I don't know what went wrong.


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
