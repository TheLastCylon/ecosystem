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
    help     = "The type of server you want to get telemetry from."
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
    "-ifu", "--influx_url",
    metavar  = "<server details>",
    required = True,
    default  = None,
    help     = "A URL in the form http://HOST:PORT for the InfluxDb instance you want to use."
)

argument_parser.add_argument(
    "-ifo", "--influx_org",
    metavar  = "<influx organization>",
    required = True,
    default  = None,
    help     = "The organization you created on InfluxDb."
)

argument_parser.add_argument(
    "-ifb", "--influx_bucket",
    metavar  = "<influx bucket>",
    required = True,
    default  = None,
    help     = "The InfluxDb bucket you wish to use."
)

argument_parser.add_argument(
    "-ift", "--influx_token",
    metavar  = "<influx token>",
    required = True,
    default  = None,
    help     = "The InfluxDb client token, for interacting with its API."
)

command_line_args: argparse.Namespace = argument_parser.parse_args()
