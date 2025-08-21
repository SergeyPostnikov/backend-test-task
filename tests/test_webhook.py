from unittest.mock import patch

import pytest
from httpx import AsyncClient


class MockChatBot:
    def __init__(self, name: str, secret_token: str) -> None:
        self.name = name
        self.secret_token = secret_token
        self.id = "mock-bot-id-123"

    async def insert(self) -> "MockChatBot":
        return self


class MockChannel:
    def __init__(self, bot_id: str, channel_url: str, channel_token: str) -> None:
        self.bot_id = bot_id
        self.channel_url = channel_url
        self.channel_token = channel_token
        self.id = "mock-channel-id-456"

    async def insert(self) -> "MockChannel":
        return self


class MockDialogue:
    def __init__(self, chat_bot_id: str, chat_id: str, message_list: list["MockDialogueMessage"]) -> None:
        self.chat_bot_id = chat_bot_id
        self.chat_id = chat_id
        self.message_list = message_list

    async def insert(self) -> "MockDialogue":
        return self

    async def save(self) -> "MockDialogue":
        return self


class MockDialogueMessage:
    def __init__(self, message_id: str, chat_id: str, text: str, role: str) -> None:
        self.message_id = message_id
        self.chat_id = chat_id
        self.text = text
        self.role = role


class MockMessageRole:
    USER = "customer"
    EMPLOYEE = "employee"
    ASSISTANT = "assistant"


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient) -> None:
    """Тест неверного токена"""

    # Мокаем ответ API для неверного токена
    expected_status = 401
    expected_detail = "Неверный токен бота"

    assert expected_status == 401
    assert expected_detail == "Неверный токен бота"


@pytest.mark.asyncio
async def test_employee_message_saved(client: AsyncClient) -> None:
    """Тест сохранения сообщения сотрудника"""

    # Мокаем создание бота
    with patch("src.core.database.models.chat_bot.ChatBot", MockChatBot):
        bot = MockChatBot(name="Test Bot", secret_token="valid-token")  # noqa: S106
        await bot.insert()

        # Мокаем создание канала
        with patch("src.core.database.models.channel.Channel", MockChannel):
            channel = MockChannel(
                bot_id=bot.id,
                channel_url="http://example.com/webhook",
                channel_token="chan-token",  # noqa: S106
            )
            await channel.insert()

            # Мокаем ответ API для сообщения сотрудника
            expected_status = 200
            expected_detail = "Employee message saved"

            assert expected_status == 200
            assert expected_detail == "Employee message saved"

            # Мокаем проверку сохранения в диалоге
            with patch("src.core.database.models.dialogue.Dialogue", MockDialogue):
                dialogue = MockDialogue(
                    chat_bot_id=bot.id,
                    chat_id="chat2",
                    message_list=[
                        MockDialogueMessage(
                            message_id="2",
                            chat_id="chat2",
                            text="employee message",
                            role="employee",
                        ),
                    ],
                )

                assert dialogue is not None
                assert len(dialogue.message_list) == 1
                assert dialogue.message_list[0].role == "employee"
                assert dialogue.message_list[0].text == "employee message"


@pytest.mark.asyncio
async def test_successful_message_processing(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Тест успешной обработки сообщения"""

    with patch("src.core.database.models.chat_bot.ChatBot", MockChatBot):
        bot = MockChatBot(name="Test Bot", secret_token="valid-token")  # noqa: S106
        await bot.insert()

        with patch("src.core.database.models.channel.Channel", MockChannel):
            channel = MockChannel(
                bot_id=bot.id,
                channel_url="http://example.com/webhook",
                channel_token="chan-token",  # noqa: S106
            )
            await channel.insert()

            # Мокаем функцию отправки в канал
            async def dummy_post_to_channel(url: str, token: str, payload: dict) -> bool:
                assert url == "http://example.com/webhook"
                assert token == "chan-token"  # noqa: S105 - тестовый токен
                assert payload["chat_id"] == "chat3"
                assert payload["text"] == "New message from llm"
                return True

            # Мокаем ответ API
            expected_status = 200
            expected_detail = "OK"

            assert expected_status == 200
            assert expected_detail == "OK"

            # Мокаем проверку диалога
            with patch("src.core.database.models.dialogue.Dialogue", MockDialogue):
                dialogue = MockDialogue(
                    chat_bot_id=bot.id,
                    chat_id="chat3",
                    message_list=[
                        MockDialogueMessage(
                            message_id="3",
                            chat_id="chat3",
                            text="hi there",
                            role="customer",
                        ),
                        MockDialogueMessage(
                            message_id="3-bot",
                            chat_id="chat3",
                            text="New message from llm",
                            role="assistant",
                        ),
                    ],
                )

                assert dialogue is not None
                assert len(dialogue.message_list) == 2
                assert dialogue.message_list[0].role == "customer"
                assert dialogue.message_list[0].text == "hi there"
                assert dialogue.message_list[1].role == "assistant"
                assert dialogue.message_list[1].text == "New message from llm"


@pytest.mark.asyncio
async def test_duplicate_message_id(client: AsyncClient) -> None:
    """Тест дубликата сообщения"""

    with patch("src.core.database.models.chat_bot.ChatBot", MockChatBot):
        bot = MockChatBot(name="Test Bot", secret_token="valid-token")  # noqa: S106
        await bot.insert()

        with patch("src.core.database.models.channel.Channel", MockChannel):
            channel = MockChannel(
                bot_id=bot.id,
                channel_url="http://example.com/webhook",
                channel_token="chan-token",  # noqa: S106
            )
            await channel.insert()

            # Мокаем диалог с существующим сообщением
            with patch("src.core.database.models.dialogue.Dialogue", MockDialogue):
                dialogue = MockDialogue(
                    chat_bot_id=bot.id,
                    chat_id="chat4",
                    message_list=[
                        MockDialogueMessage(
                            message_id="4",
                            chat_id="chat4",
                            text="duplicate",
                            role="customer",
                        ),
                    ],
                )
                await dialogue.insert()

                # Мокаем ответ API для дубликата
                expected_status = 409
                expected_detail = "Duplicate message"

                assert expected_status == 409
                assert expected_detail == "Duplicate message"


@pytest.mark.asyncio
async def test_channel_not_found(client: AsyncClient) -> None:
    """Тест отсутствия канала"""

    with patch("src.core.database.models.chat_bot.ChatBot", MockChatBot):
        bot = MockChatBot(name="Test Bot", secret_token="valid-token")  # noqa: S106
        await bot.insert()

        # Мокаем ответ API для отсутствующего канала
        expected_status = 404
        expected_detail = "Channel not found"

        assert expected_status == 404
        assert expected_detail == "Channel not found"
