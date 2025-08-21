from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas import IncomingMessage, OutgoingMessage
from app.services.dialogue_service import DialogueService

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/new_message", response_model=OutgoingMessage)
async def receive_webhook(msg: IncomingMessage, request: Request) -> JSONResponse:
    return await DialogueService(request).process_message(msg)
