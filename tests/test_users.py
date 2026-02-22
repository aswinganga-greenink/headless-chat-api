import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/users/",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_duplicate_user(async_client: AsyncClient):
    # First creation
    await async_client.post(
        "/api/v1/users/",
        json={"email": "dup@example.com", "username": "dup", "password": "password123"}
    )
    # Second creation expecting failure
    response = await async_client.post(
        "/api/v1/users/",
        json={"email": "dup@example.com", "username": "dup2", "password": "password123"}
    )
    assert response.status_code == 400
    assert "already exists" in response.text
