from .shared_argument_parser import argument_parser

argument_parser.add_argument(
    "-rk" , "--route_key",
    metavar = "<route_key>",
    required= True,
    default = None,
    type    = str,
    help    = "The route key of the queue you wish to interact with."
)

queue_one_action_group = argument_parser.add_mutually_exclusive_group()

# --------------------------------------------------------------------------------
def setup_shared_options():
    queue_one_action_group.add_argument("-e10", "--error_10"      , required=False, action="store_true", help="Get the first 10 uuids in an error database of a queue.")
    queue_one_action_group.add_argument("-rp1", "--reprocess_one" , required=False, action="store_true", help="Reprocess a specified entry in an error database of a queue.\n- [Requires -rid].")
    queue_one_action_group.add_argument("-rpa", "--reprocess_all" , required=False, action="store_true", help="Reprocess all entries in an error queue.")

    # The danger zone
    # --------------------------------------------------------------------------------
    queue_one_action_group.add_argument("-ins", "--inspect_request", required=False, action="store_true", help="View a request on an error database of a queue.\n- [Requires -rid].")
    queue_one_action_group.add_argument("-pop", "--pop_request"    , required=False, action="store_true", help="Pop a request from an error database of a queue.\n- [Requires -rid].")
    queue_one_action_group.add_argument("-clr", "--clear"          , required=False, action="store_true", help="Clear the error database of a queue completely.\n- WARNING: All requests in the error queue are deleted!")

    argument_parser.add_argument(
        "-rid", "--request_uid",
        metavar = "<request uuid>",
        default = None,
        type    = str,
        help    = "The UUID for an item in a queue."
    )

# --------------------------------------------------------------------------------
def setup_queued_endpoint_options():
    queue_one_action_group.add_argument("-pr" , "--pause_receiving"   , required=False, action="store_true", help="Pause receiving on a queue.")
    queue_one_action_group.add_argument("-pp" , "--pause_processing"  , required=False, action="store_true", help="Pause processing on a queue.")
    queue_one_action_group.add_argument("-ur" , "--unpause_receiving" , required=False, action="store_true", help="UN-Pause receiving on a queue.")
    queue_one_action_group.add_argument("-up" , "--unpause_processing", required=False, action="store_true", help="UN-Pause processing on a queue.")
    queue_one_action_group.add_argument("-pa" , "--pause_all"         , required=False, action="store_true", help="Pause both receiving and processing.")
    queue_one_action_group.add_argument("-ua" , "--unpause_all"       , required=False, action="store_true", help="UN-Pause both receiving and processing.")
    setup_shared_options()

# --------------------------------------------------------------------------------
def setup_queued_sender_options():
    queue_one_action_group.add_argument("-ps" , "--pause_sending"  , required=False, action="store_true", help="Pause sending.")
    queue_one_action_group.add_argument("-us" , "--unpause_sending", required=False, action="store_true", help="UN-Pause sending.")
    setup_shared_options()
