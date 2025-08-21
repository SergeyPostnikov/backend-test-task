from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status

from app.schemas import ChannelBase, ChannelRead
from core.database.models.channel import Channel

router = APIRouter()


async def get_channel_or_404(channel_id: str) -> Channel:
    try:
        oid = PydanticObjectId(channel_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid channel id")
    channel = await Channel.get(oid)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_channel(channel_payload: ChannelBase) -> ChannelRead:
    channel_token = "generate_token"  # todo implement # noqa: S105
    channel = Channel(
        channel_token=channel_token,
        channel_url=str(channel_payload.channel_url),
        bot_id=channel_payload.bot_id,
    )
    await channel.insert()
    return ChannelRead.model_validate(channel)  # from_attributes=True


@router.get("/")
async def get_list_channels() -> list[ChannelRead]:
    channels = await Channel.find_all().to_list()
    return [ChannelRead.model_validate(channel) for channel in channels]


@router.get("/{channel_id}")
async def get_channel(channel_id: str) -> ChannelRead:
    channel = await get_channel_or_404(channel_id)
    return ChannelRead.model_validate(channel)


@router.patch("/{channel_id}")
async def update_channel(channel_id: str, channel_update: ChannelBase) -> ChannelRead:
    channel = await get_channel_or_404(channel_id)
    update_fields = channel_update.model_dump(exclude_unset=True)
    for k, v in update_fields.items():
        setattr(channel, k, v)
    await channel.save()
    return ChannelRead.model_validate(channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(channel_id: str) -> None:
    channel = await get_channel_or_404(channel_id)
    await channel.delete()
