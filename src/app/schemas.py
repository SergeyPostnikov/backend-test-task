from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ChannelBase(BaseModel):
    channel_url: HttpUrl = Field(..., title="URL канала")
    bot_id: str = Field(..., title="ID чат-бота")

    model_config = ConfigDict(validate_by_name=True, from_attributes=True, populate_by_name=True)


class ChannelRead(ChannelBase):
    channel_id: PydanticObjectId = Field(..., alias="id")
    channel_token: str | None = Field(None, min_length=8, title="Токен канала")


class IncomingMessage(BaseModel):
    message_id: str
    chat_id: str
    text: str
    message_sender: Literal["customer", "employee"]


class OutgoingMessage(BaseModel):
    event_type: Literal["new_message"]
    chat_id: str
    text: str
