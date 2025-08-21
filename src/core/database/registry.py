from beanie import init_beanie
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from core import settings
from core.database.models.channel import Channel
from core.database.models.chat_bot import ChatBot
from core.database.models.dialogue import Dialogue


async def initialize_database(test_db: str | None = None) -> None:
    logger.info("Initialising DB...")
    db_name = test_db or settings.mongo.db_name
    await init_beanie(
        database=AsyncIOMotorClient(settings.mongo.url).get_database(db_name),
        document_models=[
            ChatBot,
            Channel,
            Dialogue,
        ],
    )
    logger.success(f"DB {db_name} is ready!")
