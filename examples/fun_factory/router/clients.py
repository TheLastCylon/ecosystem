from ecosystem.clients import TCPClient

fortunes_client      = TCPClient("127.0.0.1", 1111)
joker_client         = TCPClient("127.0.0.1", 2222)
lottery_client       = TCPClient("127.0.0.1", 3333)
magic8ball_client    = TCPClient("127.0.0.1", 4444)
time_reporter_client = TCPClient("127.0.0.1", 5555)
tracker_client       = TCPClient("127.0.0.1", 7777)
