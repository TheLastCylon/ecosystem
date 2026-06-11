from ekosis.clients import UDPClient

fortunes_client      = UDPClient("127.0.0.1", 8100)
joker_client         = UDPClient("127.0.0.1", 8200)
lottery_client       = UDPClient("127.0.0.1", 8300)
magic8ball_client    = UDPClient("127.0.0.1", 8400)
time_reporter_client = UDPClient("127.0.0.1", 8500)
tracker_client       = UDPClient("127.0.0.1", 8700)
