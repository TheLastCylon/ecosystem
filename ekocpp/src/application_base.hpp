#pragma once

#include <asio.hpp>
#include <chrono>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "clients/multiplexed_tcp_client.hpp"
#include "clients/multiplexed_uds_client.hpp"
#include "configuration/config_models.hpp"
#include "exceptions/exceptions.hpp"
#include "requests/buffered_handler_interface.hpp"
#include "requests/buffered_request_handler.hpp"
#include "requests/request_router.hpp"
#include "sending/buffered_sender.hpp"
#include "servers/tcp_server.hpp"
#include "servers/udp_server.hpp"
#include "servers/uds_server.hpp"
#include "state_keepers/statistics_keeper.hpp"

// --------------------------------------------------------------------------------
class InstanceAlreadyRunningException : public ExceptionBase {
    public:
        InstanceAlreadyRunningException(const std::string& application_name, const std::string& instance_id, int process_id);
};

// --------------------------------------------------------------------------------
// Mirrors ekosis/application_base.py's ApplicationBase, scoped to what
// ekocpp has real consumers for today: routing (standard + buffered
// endpoints), buffered senders, the three transport servers, the lock-file
// singleton check, signal-driven shutdown, statistics keeper tuning.
//
// No metaclass singleton (no C++ equivalent) -- the one instance a user
// constructs in main() IS the application. register_endpoint() is an
// explicit call from the derived class's constructor, not decorator-based
// registration -- same static-init-order reasoning already settled for
// RequestRouter.
//
// Requires AppConfiguration::initialize() to have already been called
// (typically right after parsing argv in main(), before constructing the
// derived application class) -- ApplicationBase reads AppConfiguration::
// instance() in its own constructor to decide which servers to build.

class ApplicationBase {
    public:
        ApplicationBase(int argc, char** argv);
        virtual ~ApplicationBase();

        // Registers signal handlers, starts every configured server, calls the
        // setup_tasks() hook, then runs the io_context -- blocks until stop()
        // (or a termination signal) brings the io_context down.
        void start();

        // Stops every active server and the io_context. Callable externally,
        // or invoked automatically by the SIGTERM/SIGINT/SIGHUP handler.
        void stop();

    protected:
        template <typename Handler>
        void register_endpoint(std::string route_key, Handler handler) {
            router_.register_endpoint(std::move(route_key), std::move(handler));
        }

        template <typename ClassType, typename ReturnType, typename... Args>
        void register_endpoint(std::string route_key, ClassType* instance, ReturnType (ClassType::*method)(Args...)) {
            router_.register_endpoint(std::move(route_key), instance, method);
        }

        // Mirrors ekosis/application_base.py's __setup_buffered_handlers (the
        // queue/directory setup half -- the actual setup() two-phase split
        // Python needs doesn't apply here, since this is called directly from
        // the derived app's constructor with AppConfiguration already known)
        // + buffered_endpoint.py's decorator (the registration half). Requires
        // buffer_directory to be configured (ECOENV_BUFFER_DIR) -- deliberately
        // throws rather than silently defaulting anywhere, same reasoning as
        // Python's "do not default buffer_directory" comment.
        //
        // Handler contract: same SpanKey/RequestDTO& injectable parameters as
        // register_endpoint, but MUST return bool (success/retry) -- see
        // buffered_request_handler.hpp's class comment.
        template <typename ClassType, typename ReturnType, typename... Args>
        void register_buffered_endpoint(const std::string& route_key, ClassType* instance, ReturnType (ClassType::*method)(Args...), int page_size = 100, int max_retries = 0) {
            register_buffered_endpoint(route_key, [instance, method](Args... args) -> ReturnType {
                return (instance->*method)(std::forward<Args>(args)...);
            }, page_size, max_retries);
        }

        template <typename Handler>
        void register_buffered_endpoint(const std::string& route_key, Handler handler, int page_size = 100, int max_retries = 0) {
            if (!configuration_.buffer_directory()) {
                throw ExceptionBase("Cannot register buffered endpoint '" + route_key + "': no buffer_directory configured (set ECOENV_BUFFER_DIR).");
            }

            const std::string file_basename = configuration_.name() + "-" + configuration_.instance_id() + "-" + route_key + "-endpoint";
            auto buffered = std::make_shared<BufferedRequestHandler<Handler>>(
                io_context_.get_executor(), route_key, std::move(handler), *configuration_.buffer_directory(), file_basename, page_size, max_retries
            );
            buffered->unpause_receiving();
            buffered->unpause_processing();

            StatisticsKeeper::instance().add_persisted_queue("buffered_endpoint_sizes." + route_key + ".pending", [buffered]() { return buffered->pending_queue_size(); });
            StatisticsKeeper::instance().add_persisted_queue("buffered_endpoint_sizes." + route_key + ".error", [buffered]() { return buffered->error_queue_size(); });

            router_.register_raw_handler(route_key, [buffered](RequestContext& request_context) -> asio::awaitable<nlohmann::json> { return buffered->push(request_context); });

            buffered_shutdowns_.push_back([buffered]() -> asio::awaitable<void> { co_await buffered->shut_down(); });
            buffered_handler_registry_[route_key] = buffered; // type-erased to BufferedHandlerInterface -- see that header for why
        }

        // Mirrors ekosis/sending/buffered_sender.py's decorator + buffered_sender_base.py's
        // setup() (queue/directory configuration). Unlike register_buffered_endpoint,
        // this returns the constructed sender directly -- a sender has no inbound
        // route to dispatch through; the derived app calls ->enqueue(...) on the
        // returned shared_ptr itself whenever it has something to send.
        //
        // Takes connection parameters, NOT a client -- deliberately. An earlier
        // version of this method accepted a caller-constructed shared_ptr<ClientT>,
        // which is exactly what let observable_fun's router pass the SAME
        // MultiplexedUDSClient to two different senders (app.log_request and
        // app.log_response), silently colliding in that client's demux map (see
        // multiplexed_stream_client.md's "Two BufferedSenders must never share
        // one MultiplexedClient" section for the full incident). Removing the
        // client parameter removes the shape that made the mistake possible --
        // each call here always builds its own fresh client internally, so
        // sharing one across two senders is no longer something a caller can
        // even express. Direct construction of BufferedSender with an explicit
        // client is still possible (and still MultiplexedClient-constrained) for
        // unit tests that need to inject controlled failure behaviour without a
        // real socket -- see buffered_sender_smoke_test.cpp's FakeClient -- but
        // that path is not, and was never meant to be, something application
        // code reaches for.
        std::shared_ptr<BufferedSender> register_buffered_sender(
            const std::string&        route_key,
            std::string               socket_path,
            std::chrono::milliseconds wait_period = std::chrono::milliseconds{0},
            int                       page_size   = 100,
            int                       max_retries = 0
        ) {
            auto client = std::make_shared<MultiplexedUDSClient>(io_context_.get_executor(), std::move(socket_path));
            client->start();
            return register_buffered_sender_with_client(route_key, std::move(client), wait_period, page_size, max_retries);
        }

        std::shared_ptr<BufferedSender> register_buffered_sender(
            const std::string&        route_key,
            std::string               host,
            uint16_t                  port,
            std::chrono::milliseconds wait_period = std::chrono::milliseconds{0},
            int                       page_size   = 100,
            int                       max_retries = 0
        ) {
            auto client = std::make_shared<MultiplexedTCPClient>(io_context_.get_executor(), std::move(host), port);
            client->start();
            return register_buffered_sender_with_client(route_key, std::move(client), wait_period, page_size, max_retries);
        }

    protected:
        // Shared tail of both register_buffered_sender overloads above -- queue
        // setup, statistics registration, shutdown wiring. Templated (rather than
        // taking shared_ptr<ClientBase>) so BufferedSender's own MultiplexedClient
        // constraint applies here too, not just at its constructor. protected,
        // not private -- an ApplicationBase subclass (a test app that needs to
        // inject a deliberately-failing client, e.g. standard_endpoints_buffered_
        // management_live_test.cpp's TestApp/AlwaysFailClient) can still reach it
        // directly. That's a different thing from the public register_buffered_
        // sender overloads accepting an arbitrary caller-supplied client -- this
        // is a deliberate, subclass-authored escape hatch, not something any
        // external caller holding an ApplicationBase can trigger.
        template <MultiplexedClient ClientT>
        std::shared_ptr<BufferedSender> register_buffered_sender_with_client(
            const std::string&        route_key,
            std::shared_ptr<ClientT>  client,
            std::chrono::milliseconds wait_period,
            int                       page_size,
            int                       max_retries
        ) {
            if (!configuration_.buffer_directory()) {
                throw ExceptionBase("Cannot register buffered sender '" + route_key + "': no buffer_directory configured (set ECOENV_BUFFER_DIR).");
            }

            const std::string file_basename = configuration_.name() + "-" + configuration_.instance_id() + "-" + route_key + "-sender";
            auto sender = std::make_shared<BufferedSender>(
                io_context_.get_executor(), std::move(client), route_key, *configuration_.buffer_directory(), file_basename, wait_period, page_size, max_retries
            );
            sender->unpause_send_process();

            StatisticsKeeper::instance().add_persisted_queue("buffered_sender_sizes." + route_key + ".pending", [sender]() { return sender->pending_queue_size(); });
            StatisticsKeeper::instance().add_persisted_queue("buffered_sender_sizes." + route_key + ".error", [sender]() { return sender->error_queue_size(); });

            buffered_shutdowns_.push_back([sender]() -> asio::awaitable<void> { co_await sender->shut_down(); });
            buffered_sender_registry_[route_key] = sender; // no interface needed -- BufferedSender is already concrete, non-template

            return sender;
        }

    public:
        // Hook for a derived application to co_spawn extra background
        // coroutines onto the same io_context, called from start() just before
        // io_context.run(). Mirrors Python's setup_tasks(tasks: list), shaped
        // differently -- C++ coroutines are spawned directly onto the executor
        // rather than collected into a list and gathered afterward.
        virtual void setup_tasks();

        asio::io_context& io_context();

    private:
        void lock_file_check();
        void setup_signal_handlers();

        // Mirrors Python's __start_stats_keeper / StatisticsKeeper.gather_statistics():
        // calls start() once, then loops: wait gather_period, call gather_now(), repeat.
        // Spawned as detached coroutine in start() alongside the transport servers.
        asio::awaitable<void> run_statistics_gather();

        // Drains every registered buffered handler's AND sender's queue
        // (co_await'd one at a time -- shutdown is a one-time event, not a hot
        // path, so sequencing for simplicity over throughput is the right call)
        // before finally stopping io_context_ -- mirrors Python's
        // asyncio.gather(*tasks) not letting __start() return until every
        // buffered handler's/sender's wait_for_shutdown() has resolved.
        asio::awaitable<void> shut_down_buffered_subsystems();

        AppConfiguration&        configuration_;
        asio::io_context         io_context_;
        RequestRouter            router_;
        asio::signal_set         signals_;

        std::string              lock_file_path_;
        int                      lock_fd_ = -1;

        std::optional<TCPServer> server_tcp_;
        std::optional<UDPServer> server_udp_;
        std::optional<UDSServer> server_uds_;

        std::vector<std::function<asio::awaitable<void>()>> buffered_shutdowns_;

        // Route-key-keyed registries, populated by register_buffered_endpoint/
        // register_buffered_sender -- the actual C++ equivalent of Python's
        // BufferedHandlerKeeper/BufferedSenderKeeper singletons. Owned directly
        // by ApplicationBase rather than a separate global keeper class, same
        // simplification already applied throughout (no decorator-based global
        // registration exists here, so there's no orphaned registration step
        // that needs its own singleton to land in).
        std::unordered_map<std::string, std::shared_ptr<BufferedHandlerInterface>> buffered_handler_registry_;
        std::unordered_map<std::string, std::shared_ptr<BufferedSender>>           buffered_sender_registry_;
};
