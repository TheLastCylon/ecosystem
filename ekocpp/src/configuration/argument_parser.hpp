#pragma once

#include <optional>
#include <string>

// Mirrors ekosis/configuration/argument_parser.py -- minimal CLI surface,
// hand-rolled over POSIX getopt_long rather than a third-party CLI library
// (cxxopts/CLI11) or Boost.Program_options. A handful of real flags don't
// justify a new dependency, and getopt_long is already linked via glibc on
// every target this project runs on (Linux-only, same call already made for
// UDSServer/UDSClient).
struct CommandLineArgs {
    std::string                instance;          // -i / --instance, required
    std::optional<std::string> config_file;       // -c / --config_file, optional

    // -lco/-lfo on the Python side -- genuinely mutually exclusive (Python's
    // argparse.add_mutually_exclusive_group()), enforced below the same way:
    // both false by default (console AND file logging), passing both is a
    // parse error, not silently resolved one way or the other.
    bool log_console_only = false; // -lco / --log_console_only
    bool log_file_only    = false; // -lfo / --log_file_only
};

// Exits the process with a usage message on missing/invalid required
// arguments -- same failure mode as Python's argparse (which calls
// sys.exit(2) on a parse error), not an exception.
CommandLineArgs parse_command_line_args(int argc, char** argv);
