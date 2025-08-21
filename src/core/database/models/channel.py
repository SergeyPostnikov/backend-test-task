from beanie import Document
from pydantic import Field


class Channel(Document):
    """Модель канала для подключения к внешним платформам."""

    bot_id: str = Field(..., description="ID бота, к которому подключен канал")
    channel_url: str = Field(..., description="URL канала для отправки сообщений")
    channel_token: str = Field(..., description="Токен авторизации канала")

    class Settings:
        name = "channels"
        indexes = [("bot_id",)]
