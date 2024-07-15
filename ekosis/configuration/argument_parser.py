import argparse

argument_parser: argparse.ArgumentParser = argparse.ArgumentParser()

argument_parser.add_argument(
    "-i", "--instance",
    type     = str,
    required = True,
    help     = 'The instance id this invocation of the script needs to run as.',
)

argument_parser.add_argument(
    "-c", "--config_file",
    type     = str,
    required = False,
    default  = None,
    help     = "Specify a configuration file to load for this invocation of the application. Default is: None",
)

logging_group = argument_parser.add_mutually_exclusive_group()

logging_group.add_argument(
    "-lco", "--log_console_only",
    required = False,
    action   = "store_true",
    help     = "Set logging too console only. i.e. Don't log to a file.",
)

logging_group.add_argument(
    "-lfo", "--log_file_only",
    required = False,
    action   = "store_true",
    help     = "Set logging too file only. i.e. Don't log to console.",
)

command_line_args = argument_parser.parse_args()
