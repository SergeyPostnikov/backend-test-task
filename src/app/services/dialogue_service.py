from typing import cast

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import IncomingMessage
from app.services.channel_service import post_to_channel
from core.database.models.channel import Channel
from core.database.models.chat_bot import ChatBot
from core.database.models.dialogue import Dialogue, DialogueMessage, MessageRole
from predict.mock_llm_call import mock_llm_call

bearer_scheme = HTTPBearer()


class DialogueService:
    def __init__(self, request: Request):
        self.request = request

    async def validate_bot(self) -> ChatBot:
        credentials: HTTPAuthorizationCredentials | None = await bearer_scheme(self.request)
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bot token")
        bot = await ChatBot.find_one(ChatBot.secret_token == credentials.credentials)
        if not bot:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bot token")
        return bot

    async def get_channel(self, bot: ChatBot) -> Channel:
        channel = await Channel.find_one(Channel.bot_id == bot.id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        return channel

    async def get_or_create_dialogue(self, bot: ChatBot, msg: IncomingMessage) -> Dialogue:
        dialogue = await Dialogue.find_one(
            Dialogue.chat_bot_id == bot.id,
            Dialogue.chat_id == msg.chat_id,
        )
        if dialogue:
            return dialogue

        if not bot.id:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Bot ID is None")

        dialogue = cast(
            "Dialogue",
            Dialogue.model_validate(
                {
                    "chat_bot_id": bot.id,
                    "chat_id": msg.chat_id,
                },
            ),
        )
        await dialogue.insert()
        return dialogue

    async def process_message(self, msg: IncomingMessage) -> JSONResponse:
        bot = await self.validate_bot()
        channel = await self.get_channel(bot)
        dialogue = await self.get_or_create_dialogue(bot, msg)

        if any(m.message_id == msg.message_id for m in dialogue.message_list):
            return JSONResponse(status_code=409, content={"detail": "Duplicate message"})

        role = MessageRole.USER if msg.message_sender == "customer" else MessageRole.ASSISTANT
        dialogue.message_list.append(
            DialogueMessage(message_id=msg.message_id, chat_id=msg.chat_id, text=msg.text, role=role),
        )
        await dialogue.save()

        if msg.message_sender == MessageRole.ASSISTANT:
            return JSONResponse(status_code=200, content={"detail": "Employee message saved"})

        llm_response = await mock_llm_call(dialogue.message_list)

        success = await post_to_channel(
            str(channel.channel_url),
            channel.channel_token,
            {
                "event_type": "new_message",
                "chat_id": msg.chat_id,
                "text": llm_response,
            },
        )
        if not success:
            # todo: add logger
            pass

        dialogue.message_list.append(
            DialogueMessage(
                message_id=f"{msg.message_id}-bot",
                chat_id=msg.chat_id,
                text=llm_response,
                role=MessageRole.ASSISTANT,
            ),
        )
        await dialogue.save()

        return JSONResponse(status_code=200, content={"detail": "OK"})
