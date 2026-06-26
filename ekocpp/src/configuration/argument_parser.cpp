#include "argument_parser.hpp"

#include <cstdlib>
#include <getopt.h>
#include <iostream>

namespace {

constexpr const char* USAGE =
    " -i/--instance <id> [-c/--config_file <path>] [-lco/--log_console_only | -lfo/--log_file_only]";

} // namespace

CommandLineArgs parse_command_line_args(int argc, char** argv) {
    // "lco"/"lfo" are listed as their own long-option names (not single
    // chars) so getopt_long_only below matches Python's actual `-lco`/`-lfo`
    // spelling on a single dash -- getopt_long's short-option mechanism
    // can't parse a multi-character short flag like "-lco" at all.
    static const option long_options[] = {
        {"instance",         required_argument, nullptr, 'i'},
        {"config_file",      required_argument, nullptr, 'c'},
        {"lco",              no_argument,       nullptr, 'o'},
        {"log_console_only", no_argument,       nullptr, 'o'},
        {"lfo",              no_argument,       nullptr, 'f'},
        {"log_file_only",    no_argument,       nullptr, 'f'},
        {nullptr,            0,                 nullptr, 0},
    };

    CommandLineArgs args;
    bool            instance_set = false;

    int option_char;
    while ((option_char = getopt_long_only(argc, argv, "i:c:", long_options, nullptr)) != -1) {
        switch (option_char) {
            case 'i':
                args.instance = optarg;
                instance_set  = true;
                break;
            case 'c':
                args.config_file = optarg;
                break;
            case 'o':
                args.log_console_only = true;
                break;
            case 'f':
                args.log_file_only = true;
                break;
            default:
                std::cerr << "Usage: " << argv[0] << USAGE << std::endl;
                std::exit(2); // mirrors Python argparse's exit code on a parse error
        }
    }

    if (!instance_set) {
        std::cerr << "Usage: " << argv[0] << USAGE << std::endl;
        std::cerr << "Error: -i/--instance is required." << std::endl;
        std::exit(2);
    }

    if (args.log_console_only && args.log_file_only) {
        std::cerr << "Usage: " << argv[0] << USAGE << std::endl;
        std::cerr << "Error: -lco/--log_console_only and -lfo/--log_file_only are mutually exclusive." << std::endl;
        std::exit(2); // mirrors argparse.add_mutually_exclusive_group()'s parse error
    }

    return args;
}
