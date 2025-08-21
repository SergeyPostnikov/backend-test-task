import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas import ChannelRead
from core.database.models.channel import Channel
from core.database.models.chat_bot import ChatBot


@pytest.mark.asyncio
async def test_create_channel_success(client: AsyncClient) -> None:
    """Тест успешного создания канала"""

    bot = ChatBot(name="Test Bot", secret_token="bot-token")  # noqa: S106
    await bot.insert()

    payload = {
        "bot_id": str(bot.id),
        "channel_url": "http://example.com/webhook",
    }

    response = await client.post("/api/channels/", json=payload)
    created_channel = ChannelRead.model_validate_json(response.content)
    assert response.status_code == status.HTTP_201_CREATED
    assert created_channel


@pytest.mark.asyncio
async def test_list_channels_success(client: AsyncClient) -> None:
    """Тест получения списка каналов"""

    bot = ChatBot(name="List Bot", secret_token="list-bot-token")  # noqa: S106
    await bot.insert()

    channels_prepared = [
        Channel(
            bot_id=str(bot.id),
            channel_url="http://example1.com",
            channel_token="token123",  # noqa: S106
        ),
        Channel(
            bot_id=str(bot.id),
            channel_url="http://example2.com",
            channel_token="token123",  # noqa: S106
        ),
    ]
    channels_inserted = [await channel.insert() for channel in channels_prepared]

    response = await client.get("/api/channels/")
    assert response.status_code == status.HTTP_200_OK

    channels_response = [ChannelRead.model_validate(item) for item in response.json()]
    channels_serialized = [ChannelRead.model_validate(channel) for channel in channels_inserted]
    assert channels_response == channels_serialized


@pytest.mark.asyncio
async def test_get_channel_success(client: AsyncClient) -> None:
    """Тест успешного получения канала по ID"""

    bot = ChatBot(name="Get Bot", secret_token="get-bot-token")  # noqa: S106
    await bot.insert()

    channel = Channel(
        bot_id=str(bot.id),
        channel_url="http://example.com",
        channel_token="token123",  # noqa: S106
    )
    await channel.insert()

    response = await client.get(f"/api/channels/{channel.id}")
    assert response.status_code == status.HTTP_200_OK

    channel_response = ChannelRead.model_validate(response.json())
    assert channel_response == ChannelRead.model_validate(channel)


@pytest.mark.asyncio
async def test_get_channel_not_found(client: AsyncClient) -> None:
    """Тест получения несуществующего канала"""
    response = await client.get("/channels/non-existent-id")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_channel_success(client: AsyncClient) -> None:
    """Тест успешного обновления канала"""

    bot = ChatBot(name="Update Bot", secret_token="update-bot-token")  # noqa: S106
    await bot.insert()

    channel = Channel(
        bot_id=str(bot.id),
        channel_url="http://old.example.com/",
        channel_token="old-token",  # noqa: S106
    )
    await channel.insert()

    update_payload = {
        "channel_url": "http://new.example.com/",
        "bot_id": "new-id",
    }

    response = await client.patch(f"/api/channels/{channel.id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK

    updated_channel = response.json()
    assert updated_channel.get("channel_url") == "http://new.example.com/"
    assert updated_channel.get("bot_id") == "new-id"


@pytest.mark.asyncio
async def test_update_channel_not_found(client: AsyncClient) -> None:
    """Тест обновления несуществующего канала"""

    update_payload = {"channel_url": "http://new.example.com"}
    response = await client.patch("/channels/non-existent-id", json=update_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_channel_success(client: AsyncClient) -> None:
    """Тест успешного удаления канала"""
    mock_channel = Channel(
        bot_id="bot-123",
        channel_url="http://example.com",
        channel_token="token123",  # noqa: S106
    )
    await mock_channel.insert()
    response = await client.delete(f"/api/channels/{mock_channel.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_channel_not_found(client: AsyncClient) -> None:
    """Тест удаления несуществующего канала"""
    response = await client.delete("/channels/non-existent-id")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_channel_invalid_data(client: AsyncClient) -> None:
    """Тест создания канала с невалидными данными"""
    invalid_payload = {
        "bot_id": "invalid-bot-id",
        "channel_url": "invalid-url",
    }

    response = await client.post("/api/channels/", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_channel_partial_data_fail(client: AsyncClient) -> None:
    """Тест частичного обновления канала"""
    mock_channel = Channel(
        bot_id="bot-123",
        channel_url="http://old.example.com",
        channel_token="old-token",  # noqa: S106
    )
    await mock_channel.insert()

    update_payload = {"channel_url": "http://new.example.com"}

    response = await client.patch(f"/api/channels/{mock_channel.id}", json=update_payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_channel_invalid_url(client: AsyncClient) -> None:
    """Тест создания канала с невалидным URL"""

    bot = ChatBot(name="Test Bot", secret_token="bot-token")  # noqa: S106
    await bot.insert()

    invalid_url = "example.com/webhook"  # Нет http
    create_payload = {
        "bot_id": str(bot.id),
        "channel_url": invalid_url,
    }

    response = await client.post("/api/channels/", json=create_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_channel_invalid_url(client: AsyncClient) -> None:
    """Тест обновления канала с невалидным URL"""
    mock_channel = Channel(
        bot_id="bot-123",
        channel_url="http://example.com/webhook",
        channel_token="chan-token",  # noqa: S106
    )
    await mock_channel.insert()

    update_payload = {"channel_url": "example.com/new"}
    response = await client.patch(f"/api/channels/{mock_channel.id}", json=update_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_empty_channels_list(client: AsyncClient) -> None:
    """Тест получения пустого списка каналов"""

    response = await client.get("/api/channels/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == []
