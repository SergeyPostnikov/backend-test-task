from fastapi import APIRouter

from app.routers.api.channels import router as channels_router
from app.routers.api.hello_world import router as hello_world_router
from app.routers.api.webhook import router as webhook_router

router = APIRouter(prefix="/api")

router.include_router(hello_world_router)
router.include_router(channels_router, prefix="/channels", tags=["channels"])
router.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
