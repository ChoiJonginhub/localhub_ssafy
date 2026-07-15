import asyncio
import json
import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from main import ConnectionManager, PostResponse, app


class CommunityPostFeatureTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_post_with_region_and_category_metadata(self):
        response = self.client.post(
            '/api/boards/seoul/posts',
            json={
                'title': '테스트 게시글',
                'content': '테스트 내용',
                'password': '1234',
                'region': '강남구',
                'category': '맛집',
                'visitor_count': 120,
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['region'], '강남구')
        self.assertEqual(payload['category'], '맛집')
        self.assertEqual(payload['like_count'], 0)
        self.assertEqual(payload['view_count'], 0)
        self.assertEqual(payload['visitor_count'], 120)
        self.assertEqual(payload['comments'], [])

    def test_like_view_and_comment_endpoints_update_post(self):
        created = self.client.post(
            '/api/boards/seoul/posts',
            json={
                'title': '상호작용 테스트',
                'content': '좋아요와 조회수 댓글 테스트',
                'password': '5678',
                'region': '마포구',
                'category': '카페',
            },
        )
        post_id = created.json()['id']

        like_response = self.client.post(f'/api/boards/seoul/posts/{post_id}/like')
        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(like_response.json()['like_count'], 1)

        view_response = self.client.post(f'/api/boards/seoul/posts/{post_id}/view')
        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(view_response.json()['view_count'], 1)

        comment_response = self.client.post(
            f'/api/boards/seoul/posts/{post_id}/comments',
            json={'content': '좋아요!'}
        )
        self.assertEqual(comment_response.status_code, 201)
        self.assertEqual(comment_response.json()['comments'][0]['content'], '좋아요!')


class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent_messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        self.sent_messages.append(payload)
        json.dumps(payload)


class CommunityStatisticsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_statistics_endpoint_filters_seoul_from_categories_and_exposes_top_posts(self):
        self.client.post(
            '/api/boards/seoul/posts',
            json={
                'title': '서울 카테고리 게시글',
                'content': '서울 카테고리',
                'password': '1111',
                'region': '강남구',
                'category': 'seoul',
            },
        )
        self.client.post(
            '/api/boards/seoul/posts',
            json={
                'title': '맛집 인기 게시글',
                'content': '맛집 게시글',
                'password': '2222',
                'region': '마포구',
                'category': '맛집',
            },
        )

        response = self.client.get('/api/statistics/regions')

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        category_names = [item['category'] for item in payload['categories']]
        self.assertNotIn('seoul', category_names)
        self.assertFalse(any(item['category'] == 'seoul' for item in payload['category_daily_views']))
        self.assertTrue(payload['top_posts'])
        self.assertEqual(payload['top_posts'][0]['writer'], '익명')
        self.assertTrue(payload['category_daily_views'])
        self.assertTrue(payload['weekly_posts'])
        self.assertTrue(payload['hourly_posts'])


class MeetupFeatureTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_meetup_and_join(self):
        created = self.client.post(
            '/api/meetups',
            json={
                'title': '주말 산책 모임',
                'host_nickname': '모집자',
                'recruitment_count': 5,
                'recruitment_period': '2026-07-20',
                'activity_content': '한강 산책',
                'location': '한강공원',
                'latitude': 37.5271,
                'longitude': 126.9344,
            },
        )
        self.assertEqual(created.status_code, 201)
        payload = created.json()
        self.assertEqual(payload['current_participants'], 1)

        joined = self.client.post(
            f"/api/meetups/{payload['id']}/join",
            json={'participant_nickname': '참가자'}
        )
        self.assertEqual(joined.status_code, 200)
        self.assertEqual(joined.json()['current_participants'], 2)
        self.assertEqual(joined.json()['participants'][1], '참가자')


class MeetupChatTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_and_list_meetup_chat_messages(self):
        created = self.client.post(
            '/api/meetups',
            json={
                'title': '채팅 테스트 모임',
                'host_nickname': '모집자',
                'recruitment_count': 3,
                'recruitment_period': '2026-07-22',
                'activity_content': '채팅 테스트',
                'location': '강남역',
                'latitude': 37.4979,
                'longitude': 127.0276,
            },
        )
        meetup_id = created.json()['id']

        sent = self.client.post(
            f'/api/meetups/{meetup_id}/chat',
            json={'nickname': '참가자', 'content': '만나요!'}
        )
        self.assertEqual(sent.status_code, 201)

        history = self.client.get(f'/api/meetups/{meetup_id}/chat')
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()[0]['content'], '만나요!')
        self.assertEqual(history.json()[0]['nickname'], '참가자')


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
                board_category='seoul',
                category='맛집',
                title='hello',
                content='world',
                region='강남구',
                like_count=0,
                view_count=0,
                visitor_count=0,
                comments=[],
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 0, 0),
            )
            await manager.broadcast_post(post)
            self.assertTrue(websocket.sent_messages[-1]['type'], 'new_post')

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
