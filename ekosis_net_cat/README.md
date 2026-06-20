# esnc -- EcoSystem NetCat

A small C++ debug client for EcoSystem's binary wire protocol -- connects, sends one
request, reads the response, prints it, exits. `nc`-shaped, not `tcpdump`-shaped: it's
for manually testing a route, not for sniffing traffic.

It exists because the move to a binary header + MessagePack body (replacing
line-delimited JSON) meant `echo '{"route_key": ...}' | nc localhost 8888` -- the
previous way of manually poking an EcoSystem server -- stopped being possible. You can't
hand-type MessagePack.

`esnc` is also the first piece of **EcoSystem's C++ protocol layer**
(`ekosis_net_cat_lib`): a `SpanKey` struct and `pack_frame`/`parse_header` implementation
that mirrors `ekosis/data_transfer_objects/binary_frame.py` field-for-field, verified
byte-for-byte identical against the real Python implementation during development. A
future C++ server can link against the same library rather than reimplementing the
protocol -- this is deliberately a reusable static library, not logic baked into one
binary.

---

## What it does

1. Builds a `SpanKey` (fresh, randomly generated trace_id/span_id) and a request frame:
   `[24B SpanKey][4B total_len][1B route_key_len][1B flags][2B reserved][route_key][body]`,
   body being the given JSON payload encoded as MessagePack.
2. Sends it over TCP, UDP, or UDS (your choice), using a one-shot connection -- no
   retries, no persisted/heartbeat machinery, matching `ekosis/clients/transient_*.py`'s
   simplicity rather than the persisted clients'.
3. Reads the response frame back, decodes the MessagePack body, and prints the
   `span_key`, `status` (numeric + name, e.g. `0 SUCCESS` or `400 ROUTE_KEY_UNKNOWN`),
   and `data`.
4. Exits `0` on `SUCCESS`, `1` otherwise (including on a connection/parse failure).

**Not yet supported (v0.1 simplification):** explicit `--trace_id`/`--span_id` flags for
correlating a manual probe against existing logs/traces -- `esnc` always generates a
fresh `SpanKey`. Easy to add later if needed.

---

## Building

### Dependencies

```bash
sudo apt install libasio-dev nlohmann-json3-dev
```

CMake 3.28+, a C++20 compiler (developed against gcc 13.3).

### Build

```bash
mkdir build && cd build
cmake ..
make
ctest   # runs the frame pack/parse round-trip test (no live server needed)
```

Produces the `esnc` binary, plus `libekosis_net_cat_lib.a` (the protocol layer, linked
into both `esnc` and `tests/manual_frame_roundtrip`).

---

## Running

```bash
esnc <tcp|udp|uds> <target> <route_key> [data_json]
```

- `<target>`: `host:port` for `tcp`/`udp`, a socket path for `uds`.
- `<route_key>`: the route to send the request to.
- `[data_json]`: the request payload, as a JSON string. Defaults to `{}`.

Examples:

```bash
esnc tcp 127.0.0.1:8888 echo '{"message": "hi"}'
esnc udp 127.0.0.1:8889 echo '{"message": "hi"}'
esnc uds /tmp/echo_example_0.uds.sock echo '{"message": "hi"}'
```

Output:

```
Sending : span_key=[4cd1eded-6d6e-17cd-b414-d1aeb6341e2d:127b06ddf74c4f12] route_key=[echo] data={"message":"hi"}
Response: span_key=[4cd1eded-6d6e-17cd-b414-d1aeb6341e2d:127b06ddf74c4f12] status=[0 SUCCESS] data={"message":"hi"}
```

---

## Licence

BSD-3-Clause (same as the rest of EcoSystem).
