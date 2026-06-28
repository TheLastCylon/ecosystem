#include "application_base.hpp"

#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <sys/file.h>
#include <unistd.h>

#include "configuration/argument_parser.hpp"
#include "logs/eco_logger.hpp"
#include "standard_endpoints/buffered_handler_manager.hpp"
#include "standard_endpoints/buffered_sender_manager.hpp"
#include "standard_endpoints/errors.hpp"
#include "standard_endpoints/log_manager.hpp"
#include "standard_endpoints/statistics.hpp"

InstanceAlreadyRunningException::InstanceAlreadyRunningException(
    const std::string& application_name, const std::string& instance_id, int process_id
) : ExceptionBase(
        "Instance [" + instance_id + "] of [" + application_name + "] already running with process id ["
        + std::to_string(process_id) + "]!"
    ) {}

namespace {
// Parses argv, initialises AppConfiguration and EcoLogger, then returns the
// config reference that ApplicationBase::configuration_ binds to. Called
// from the initialiser list so everything is ready before the constructor
// body -- and therefore before any derived class constructor body -- runs.
AppConfiguration& initialise(int argc, char** argv) {
    const CommandLineArgs args = parse_command_line_args(argc, argv);
    AppConfiguration::initialize(argv[0], args);
    EcoLogger::instance().setup();
    return AppConfiguration::instance();
}
} // namespace

ApplicationBase::ApplicationBase(int argc, char** argv)
    : configuration_(initialise(argc, argv)),
      io_context_(1),
      signals_(io_context_, SIGTERM, SIGINT, SIGHUP) {
    lock_file_check();

    StatisticsKeeper::instance().set_gather_period(configuration_.stats_keeper().gather_period);
    StatisticsKeeper::instance().set_history_length(configuration_.stats_keeper().history_length);

    register_error_endpoints(router_);
    register_statistics_endpoints(router_);
    register_log_manager_endpoints(router_);
    register_buffered_handler_management_endpoints(router_, buffered_handler_registry_);
    register_buffered_sender_management_endpoints(router_, buffered_sender_registry_);

    if (configuration_.tcp()) {
        spdlog::info("Starting TCP server: host={}, port={}", configuration_.tcp()->host, configuration_.tcp()->port);
        server_tcp_.emplace(io_context_, router_, configuration_.tcp()->host, configuration_.tcp()->port);
    }
    if (configuration_.udp()) {
        spdlog::info("Starting UDP server: host={}, port={}", configuration_.udp()->host, configuration_.udp()->port);
        server_udp_.emplace(io_context_, router_, configuration_.udp()->host, configuration_.udp()->port);
    }
    if (configuration_.uds()) {
        std::string uds_path = configuration_.uds()->directory + "/" + configuration_.uds()->socket_file_name;
        spdlog::info("Starting UDS server: path={}", uds_path);
        server_uds_.emplace(io_context_, router_, uds_path);
    }
}

ApplicationBase::~ApplicationBase() {
    // Idempotent on purpose -- guaranteed to run on every exit path (normal
    // return from start(), or an exception unwinding through main()), even
    // if stop() was never called explicitly. This is the actual RAII
    // translation of Python's __exit__ guarantee -- stop() handles the
    // immediate, deliberate shutdown; this handles the "no matter what" part.
    //
    // Closing the fd releases the flock() automatically, but doing it
    // explicitly here (rather than just letting the destructor's implicit
    // fd-leak-on-process-exit handle it) keeps the unlink ordered after the
    // unlock, and makes both steps visible in one place.
    if (lock_fd_ != -1) {
        flock(lock_fd_, LOCK_UN);
        close(lock_fd_);
        std::remove(lock_file_path_.c_str());
        lock_fd_ = -1;
    }
}

void ApplicationBase::lock_file_check() {
    const std::string lock_file_name = configuration_.name() + "-" + configuration_.instance_id() + ".lock";
    lock_file_path_ = configuration_.lock_directory() + "/" + lock_file_name;

    // O_CREAT here does NOT race with another instance doing the same --
    // flock() below is the actual exclusion mechanism, atomic at the kernel
    // level. Two processes can both open() the same path successfully; only
    // one can hold LOCK_EX at a time.
    const int fd = open(lock_file_path_.c_str(), O_CREAT | O_RDWR, 0644);
    if (fd == -1) {
        throw ExceptionBase("Unable to open lock file [" + lock_file_path_ + "]: " + std::strerror(errno));
    }

    if (flock(fd, LOCK_EX | LOCK_NB) == -1) {
        const int flock_errno = errno;
        close(fd);
        if (flock_errno == EWOULDBLOCK) {
            // Another live process holds the lock. Read whatever PID it
            // last wrote purely for the error message -- the lock itself,
            // not this PID read, is what proved it's alive.
            int process_id = 0;
            std::ifstream existing(lock_file_path_);
            existing >> process_id;
            throw InstanceAlreadyRunningException(configuration_.name(), configuration_.instance_id(), process_id);
        }
        throw ExceptionBase("Unable to lock file [" + lock_file_path_ + "]: " + std::strerror(flock_errno));
    }

    // We hold the lock. A previous run's stale PID (if the file already
    // existed from a crash) is irrelevant -- flock() above already proved
    // no live holder exists. Truncate and overwrite with our own PID.
    if (ftruncate(fd, 0) == -1) {
        const int truncate_errno = errno;
        flock(fd, LOCK_UN);
        close(fd);
        throw ExceptionBase("Unable to truncate lock file [" + lock_file_path_ + "]: " + std::strerror(truncate_errno));
    }
    const std::string pid_line = std::to_string(getpid()) + "\n";
    if (write(fd, pid_line.c_str(), pid_line.size()) == -1) {
        const int write_errno = errno;
        flock(fd, LOCK_UN);
        close(fd);
        throw ExceptionBase("Unable to write lock file [" + lock_file_path_ + "]: " + std::strerror(write_errno));
    }

    lock_fd_ = fd; // kept open for the process lifetime -- closing it is what releases the flock
}

void ApplicationBase::setup_signal_handlers() {
    // Single-shot, deliberately -- the application is shutting down the
    // moment any of these fire, so there's no reason to re-arm async_wait
    // afterward, unlike a long-lived listener.
    signals_.async_wait([this](const std::error_code& ec, int) {
        if (!ec) {
            std::cout << "Shutdown: Termination signal received." << std::endl;
            stop();
        }
    });
}

asio::awaitable<void> ApplicationBase::run_statistics_gather() {
    auto& keeper = StatisticsKeeper::instance();
    keeper.start();
    const std::chrono::seconds period{configuration_.stats_keeper().gather_period};
    for (;;) {
        asio::steady_timer timer(io_context_.get_executor(), period);
        co_await timer.async_wait(asio::use_awaitable);
        keeper.gather_now();
    }
}

void ApplicationBase::start() {
    setup_signal_handlers();

    asio::co_spawn(io_context_, run_statistics_gather(), asio::detached);
    if (server_tcp_) asio::co_spawn(io_context_, server_tcp_->serve(), asio::detached);
    if (server_udp_) asio::co_spawn(io_context_, server_udp_->serve(), asio::detached);
    if (server_uds_) asio::co_spawn(io_context_, server_uds_->serve(), asio::detached);

    setup_tasks();

    io_context_.run();
}

void ApplicationBase::stop() {
    StatisticsKeeper::instance().stop();
    if (server_tcp_) server_tcp_->stop();
    if (server_udp_) server_udp_->stop();
    if (server_uds_) server_uds_->stop();

    // Don't stop io_context_ here directly -- buffered handlers/senders may
    // still be mid-flush. shut_down_buffered_subsystems() stops it itself,
    // only once every registered one's queue has actually finished shutting
    // down (or immediately, if none are registered).
    asio::co_spawn(io_context_, shut_down_buffered_subsystems(), asio::detached);
}

asio::awaitable<void> ApplicationBase::shut_down_buffered_subsystems() {
    for (const auto& shutdown_fn : buffered_shutdowns_) {
        co_await shutdown_fn();
    }
    io_context_.stop();
}

void ApplicationBase::setup_tasks() {}

asio::io_context& ApplicationBase::io_context() { return io_context_; }
