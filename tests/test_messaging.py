import pytest
from httpx import AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.all_models import User, Conversation, ConversationParticipant, Message
from src.core.security import get_password_hash

@pytest.fixture
async def test_users(db_session: AsyncSession):
    u1 = User(email="test1@example.com", username="testuser1", hashed_password=get_password_hash("pass"))
    u2 = User(email="test2@example.com", username="testuser2", hashed_password=get_password_hash("pass"))
    db_session.add_all([u1, u2])
    await db_session.commit()
    return u1, u2

@pytest.fixture
async def auth_headers(test_users, async_client: AsyncClient):
    u1, u2 = test_users
    
    # Login u1 (OAuth2PasswordRequestForm expects form data)
    r1 = await async_client.post("/api/v1/auth/login/access-token", data={"username": "testuser1", "password": "pass"})
    if r1.status_code != 200:
        raise Exception(f"Login failed: {r1.text}")
    t1 = r1.json()["access_token"]
    
    # Login u2
    r2 = await async_client.post("/api/v1/auth/login/access-token", data={"username": "testuser2", "password": "pass"})
    t2 = r2.json()["access_token"]
    
    return {"Authorization": f"Bearer {t1}"}, {"Authorization": f"Bearer {t2}"}

@pytest.mark.asyncio
async def test_conversation_flow_and_messaging(
    async_client: AsyncClient, 
    auth_headers, 
    test_users
):
    h1, h2 = auth_headers
    u1, u2 = test_users
    
    # User 1 creates a conversation with User 2
    create_resp = await async_client.post(
        "/api/v1/conversations/",
        json={"title": "Test Chat", "is_group": False, "participant_ids": [str(u2.id)]},
        headers=h1
    )
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    # User 1 sends a message
    msg_resp = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hello User 2!"},
        headers=h1
    )
    assert msg_resp.status_code == 201
    msg_id = msg_resp.json()["id"]

    # User 2 lists messages
    list_resp = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=h2
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["content"] == "Hello User 2!"
    
    # User 2 lists conversations (should have 1 unread count)
    conv_list_resp = await async_client.get("/api/v1/conversations/", headers=h2)
    assert conv_list_resp.status_code == 200
    assert conv_list_resp.json()[0]["unread_count"] == 1
    
    # User 2 marks as read
    read_resp = await async_client.put(
        f"/api/v1/conversations/{conv_id}/messages/read",
        json={"last_seen_message_id": msg_id},
        headers=h2
    )
    assert read_resp.status_code == 200
    
    # User 2 lists conversations again (unread should be 0)
    conv_list_resp2 = await async_client.get("/api/v1/conversations/", headers=h2)
    assert conv_list_resp2.json()[0]["unread_count"] == 0
    
    # User 2 tries to delete User 1's message (Should fail)
    del_fail = await async_client.delete(f"/api/v1/conversations/{conv_id}/messages/{msg_id}", headers=h2)
    assert del_fail.status_code == 403
    
    # User 1 deletes their own message (Should succeed)
    del_succ = await async_client.delete(f"/api/v1/conversations/{conv_id}/messages/{msg_id}", headers=h1)
    assert del_succ.status_code == 200
    
    # List messages again to ensure it's hidden because `is_deleted=True` by default in the repo query
    list_resp2 = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=h1
    )
    assert len(list_resp2.json()["items"]) == 0
