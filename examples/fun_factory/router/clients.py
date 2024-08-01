from ekosis.clients import TransientTCPClient

fortunes_client      = TransientTCPClient("127.0.0.1", 8100)
joker_client         = TransientTCPClient("127.0.0.1", 8200)
lottery_client       = TransientTCPClient("127.0.0.1", 8300)
magic8ball_client    = TransientTCPClient("127.0.0.1", 8400)
time_reporter_client = TransientTCPClient("127.0.0.1", 8500)
tracker_client       = TransientTCPClient("127.0.0.1", 8700)
