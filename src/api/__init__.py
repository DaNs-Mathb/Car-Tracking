from fastapi import APIRouter
from src.api.videos import router as videos_router
from src.api.broadcast import router as broadcast_router


main_router=APIRouter()
main_router.include_router(videos_router)
main_router.include_router(broadcast_router)