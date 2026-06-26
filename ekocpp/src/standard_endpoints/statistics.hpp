#pragma once

#include "../requests/request_router.hpp"

// Mirrors ekosis/standard_endpoints/statistics.py.
void register_statistics_endpoints(RequestRouter& router);
