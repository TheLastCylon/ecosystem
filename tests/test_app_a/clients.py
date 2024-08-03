from ekosis.clients import TransientTCPClient

transient_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=9998)
no_such_tcp_server   = TransientTCPClient(server_host='127.0.0.1', server_port=1234)
