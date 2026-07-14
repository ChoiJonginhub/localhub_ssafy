import asyncio
import json
import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from main import ConnectionManager, PostResponse, app


class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent_messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        self.sent_messages.append(payload)
        json.dumps(payload)


class CommunityRealtimeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_websocket_reports_presence_count(self):
        with self.client.websocket_connect('/ws/notifications') as websocket:
            message = websocket.receive_json()
            self.assertEqual(message['type'], 'presence')
            self.assertEqual(message['count'], 1)
            self.assertTrue(message['connected'])

    def test_broadcast_post_serializes_dates_for_websocket(self):
        async def run_test():
            manager = ConnectionManager()
            websocket = DummyWebSocket()
            await manager.connect(websocket, 'client-1')
            post = PostResponse(
                id=1,
                category='seoul',
                title='hello',
                content='world',
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 0, 0),
            )
            await manager.broadcast_post(post)
            self.assertTrue(websocket.sent_messages[-1]['type'], 'new_post')

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
