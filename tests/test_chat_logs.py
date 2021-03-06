import pytest

from chat_thief.chat_logs import ChatLogs


# This need to target other logs
@pytest.mark.skip
class TestChatLogs:
    def test_users(self):
        users = ChatLogs().users()
        assert len(users) > 10

    def test_most_msgs(self):
        msg_counts = ChatLogs().most_msgs()
        assert len(msg_counts) > 10

    def test_recent_stream_peasants(self):
        msg_counts = ChatLogs().recent_stream_peasants()
        assert msg_counts
