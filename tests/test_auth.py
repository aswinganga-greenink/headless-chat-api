import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user):
    response = await async_client.post(
        "/api/v1/auth/login/access-token",
        data={
            "username": test_user.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_incorrect_password(async_client: AsyncClient, test_user):
    response = await async_client.post(
        "/api/v1/auth/login/access-token",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 400
    assert "Incorrect email or password" in response.text

@pytest.mark.asyncio
async def test_get_current_user_profile(async_client: AsyncClient, test_user):
    # Login to get token
    login_response = await async_client.post(
        "/api/v1/auth/login/access-token",
        data={"username": test_user.username, "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Get Profile
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username
