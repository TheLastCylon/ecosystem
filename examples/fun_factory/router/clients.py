from ecosystem.clients import TCPClient

fortunes_client      = TCPClient("127.0.0.1", 8100)
joker_client         = TCPClient("127.0.0.1", 8200)
lottery_client       = TCPClient("127.0.0.1", 8300)
magic8ball_client    = TCPClient("127.0.0.1", 8400)
time_reporter_client = TCPClient("127.0.0.1", 8500)
tracker_client       = TCPClient("127.0.0.1", 8700)
