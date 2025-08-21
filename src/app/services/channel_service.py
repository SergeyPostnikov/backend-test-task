from typing import Any

import httpx


async def post_to_channel(channel_url: str, channel_token: str, message_data: dict[str, Any]) -> bool:
    """
    Отправляет сообщение в канал.

    Args:
        channel_url: URL канала для отправки
        channel_token: Токен авторизации канала
        message_data: Данные сообщения для отправки

    Returns:
        bool: True если сообщение отправлено успешно, False в противном случае
    """
    try:
        headers = {
            "Authorization": f"Bearer {channel_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                channel_url,
                json=message_data,
                headers=headers,
                timeout=30.0,
            )

            # Логируем ошибку (в реальном проекте используйте proper logging)
            # print(f"Error posting to channel: {response.status_code} - {response.text}")
            return response.status_code in [200, 201, 202]

    except Exception:
        # Логируем исключение (в реальном проекте используйте proper logging)
        # print(f"Exception posting to channel: {e}")
        return False
