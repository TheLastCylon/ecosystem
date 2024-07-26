# from ekosis.clients import TCPClient
from ekosis.clients import PersistedTCPClient

fortunes_client      = PersistedTCPClient("127.0.0.1", 8100)
joker_client         = PersistedTCPClient("127.0.0.1", 8200)
lottery_client       = PersistedTCPClient("127.0.0.1", 8300)
magic8ball_client    = PersistedTCPClient("127.0.0.1", 8400)
time_reporter_client = PersistedTCPClient("127.0.0.1", 8500)
tracker_client       = PersistedTCPClient("127.0.0.1", 8700)
