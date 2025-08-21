from datetime import UTC, datetime
from enum import StrEnum, auto

from beanie import Document, PydanticObjectId, Replace, Save, before_event
from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    ASSISTANT = auto()
    SYSTEM = auto()
    USER = auto()


class DialogueMessage(BaseModel):
    """Модель сообщения в диалоге."""

    message_id: str = Field(..., description="Уникальный ID сообщения")
    chat_id: str = Field(..., description="ID чата")
    text: str = Field(..., description="Текст сообщения")
    role: MessageRole = Field(..., description="Роль отправителя")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Dialogue(Document):
    """Модель диалога между пользователем и ботом."""

    chat_bot_id: PydanticObjectId = Field(..., description="ID чат-бота в БД")
    chat_id: str = Field(..., description="ID чата")
    message_list: list[DialogueMessage] = Field(default_factory=list, description="Список сообщений")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "dialogues"
        indexes = [
            [("chat_bot_id", 1), ("chat_id", 1)],
        ]

    @before_event([Save, Replace])
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(UTC)
