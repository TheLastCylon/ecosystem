import argparse

argument_parser: argparse.ArgumentParser = argparse.ArgumentParser()

# --------------------------------------------------------------------------------
argument_parser.add_argument(
    "-st", "--server_type",
    required = True,
    choices  = ["tcp", "udp", "uds"],
    type     = str,
    default  = None,
    help     = "The type of server you want to interact with."
)

argument_parser.add_argument(
    "-sd", "--server_details",
    metavar  = "<server details>",
    required = True,
    default  = None,
    help     = "Connection details for the server. If TCP or UDP, format should be HOST:PORT. If UDS, the path to the socket file."
)

argument_parser.add_argument(
    "-ac", "--action",
    required = False,
    choices  = ["stat", "qem"],
    type     = str,
    default  = "stat",
    help     = "The action you want to perform. 'stat' = get statistics or 'qem' = queued endpoint management. Default is 'stat'."
)

# Stats or queue group
# --------------------------------------------------------------------------------
stat_or_queue_group = argument_parser.add_mutually_exclusive_group()

stat_or_queue_group.add_argument(
    "-stat", "--statistics_type",
    required = False,
    choices  = ["current", "gathered", "full"],
    type     = str,
    default  = "current",
    help     = "The statistics type you want to retrieve. Default is 'current'."
)

stat_or_queue_group.add_argument(
    "-rk" , "--route_key",
    metavar = "<route_key>",
    default = None,
    type    = str,
    help    = "The route key of the queue you wish to interact with."
)

# QUEUED ENDPOINT COMMANDS
# --------------------------------------------------------------------------------
queue_one_action_group = argument_parser.add_mutually_exclusive_group()

queue_one_action_group.add_argument("-dt" , "--data"              , required=False, action="store_true", help="Get data about a queue.")
queue_one_action_group.add_argument("-pr" , "--pause_receiving"   , required=False, action="store_true", help="Pause receiving on a queue.")
queue_one_action_group.add_argument("-pp" , "--pause_processing"  , required=False, action="store_true", help="Pause processing on a queue.")
queue_one_action_group.add_argument("-pa" , "--pause_all"         , required=False, action="store_true", help="Pause both receiving and processing on a queue.")
queue_one_action_group.add_argument("-ur" , "--unpause_receiving" , required=False, action="store_true", help="UN-Pause receiving on a queue.")
queue_one_action_group.add_argument("-up" , "--unpause_processing", required=False, action="store_true", help="UN-Pause processing on a queue.")
queue_one_action_group.add_argument("-ua" , "--unpause_all"       , required=False, action="store_true", help="UN-Pause both receiving and processing on a queue.")
queue_one_action_group.add_argument("-e10", "--error_10"          , required=False, action="store_true", help="Get the first 10 uuids in an error queue.")
queue_one_action_group.add_argument("-rp1", "--reprocess_one"     , required=False, action="store_true", help="Reprocess a specified entry in an error queue. [Requires -rid].")
queue_one_action_group.add_argument("-rpa", "--reprocess_all"     , required=False, action="store_true", help="Reprocess all entries in an error queue.")

# The danger zone
# --------------------------------------------------------------------------------
queue_one_action_group.add_argument("-ins", "--inspect_request"   , required=False, action="store_true", help="View a request on an error queue. [Requires -rid].")
queue_one_action_group.add_argument("-pop", "--pop_request"       , required=False, action="store_true", help="Pop a request from an error queue. [Requires -rid].")
queue_one_action_group.add_argument("-clr", "--clear"             , required=False, action="store_true", help="Clear an error queue completely. WARNING: All requests in the error queue are deleted!")

# Request id
# --------------------------------------------------------------------------------
argument_parser.add_argument(
    "-rid", "--request_uid",
    metavar = "<request uuid>",
    default = None,
    type    = str,
    help    = "The UUID for an item in a queue."
)

command_line_args: argparse.Namespace = argument_parser.parse_args()
