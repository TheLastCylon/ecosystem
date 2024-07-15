import argparse

from typing import List


# --------------------------------------------------------------------------------
class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text: str, width: int) -> List[str]:
        lines: List[str] = []
        for line_str in text.split('\n'):
            line: List[str] = []
            line_len = 0
            for word in line_str.split():
                word_len = len(word)
                next_len = line_len + word_len
                if line:
                    next_len += 1
                if next_len > width:
                    lines.append(' '.join(line))
                    line.clear()
                    line_len = 0
                elif line:
                    line_len += 1

                line.append(word)
                line_len += word_len

            lines.append(' '.join(line))
        return lines

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        return '\n'.join(indent + line for line in self._split_lines(text, width - len(indent)))


argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(
    formatter_class=SmartFormatter
)


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
    help     = "Connection details for the server.\n"
               "- For TCP or UDP:\n"
               "- : This should be a string in the format [HOST:PORT].\n"
               "- For UDS:\n"
               "- : This should be a path to the socket file."
)

argument_parser.add_argument(
    "-ac", "--action",
    required = False,
    choices  = ["stat", "qem", "qsm"],
    type     = str,
    default  = "stat",
    help     = "The action you want to perform.\n"
               " - 'stat': get statistics\n"
               " - 'qem' : Queued Endpoint Management.\n"
               " - 'qes' : Queued Sender Management.\n"
               "(default = 'stat')"
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
    help     = "The statistics type you want to retrieve.\n"
               "- 'current': The current statistical period.\n"
               "- 'gathered': The last gathered statistical period.\n"
               "- 'full': The full gathered statistics history.\n"
               " (default = 'current')"
)

stat_or_queue_group.add_argument(
    "-rk" , "--route_key",
    metavar = "<route_key>",
    default = None,
    type    = str,
    help    = "The route key of the queue you wish to interact with."
)

# --------------------------------------------------------------------------------
queue_one_action_group = argument_parser.add_mutually_exclusive_group()

queue_one_action_group.add_argument("-dt" , "--data"              , required=False, action="store_true", help="Get data about a queue.")

# Queued Endpoints Only
queue_one_action_group.add_argument("-pr" , "--pause_receiving"   , required=False, action="store_true", help="For Queued Endpoints Only:\n- Pause receiving on a queue.")
queue_one_action_group.add_argument("-pp" , "--pause_processing"  , required=False, action="store_true", help="For Queued Endpoints Only:\n- Pause processing on a queue.")
queue_one_action_group.add_argument("-ur" , "--unpause_receiving" , required=False, action="store_true", help="For Queued Endpoints Only:\n- UN-Pause receiving on a queue.")
queue_one_action_group.add_argument("-up" , "--unpause_processing", required=False, action="store_true", help="For Queued Endpoints Only:\n- UN-Pause processing on a queue.")

queue_one_action_group.add_argument("-pa" , "--pause_all"         , required=False, action="store_true", help="For Queued Endpoints:\n- Pause both receiving and processing.\nFor Queued Senders:\n- Pause sending.")
queue_one_action_group.add_argument("-ua" , "--unpause_all"       , required=False, action="store_true", help="For Queued Endpoints:\n- UN-Pause both receiving and processing.\nFor Queued Senders:\n- UN-Pause sending.")
queue_one_action_group.add_argument("-e10", "--error_10"          , required=False, action="store_true", help="Get the first 10 uuids in an error database of a queue.")
queue_one_action_group.add_argument("-rp1", "--reprocess_one"     , required=False, action="store_true", help="Reprocess a specified entry in an error database of a queue.\n- [Requires -rid].")
queue_one_action_group.add_argument("-rpa", "--reprocess_all"     , required=False, action="store_true", help="Reprocess all entries in an error queue.")

# The danger zone
# --------------------------------------------------------------------------------
queue_one_action_group.add_argument("-ins", "--inspect_request"   , required=False, action="store_true", help="View a request on an error database of a queue.\n- [Requires -rid].")
queue_one_action_group.add_argument("-pop", "--pop_request"       , required=False, action="store_true", help="Pop a request from an error database of a queue.\n- [Requires -rid].")
queue_one_action_group.add_argument("-clr", "--clear"             , required=False, action="store_true", help="Clear the error database of a queue completely.\n- WARNING: All requests in the error queue are deleted!")

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
