from fastapi import APIRouter
from fastapi import File, UploadFile, status
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from src.middleware.processing import processing_video
import uuid


router=APIRouter()
MAX_VIDEO_SIZE_MB = 100
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime"]  # MP4, MOV и т.д.

@router.post("/upload-validated-video/")
async def upload_validated_video(video: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    # Проверка типа
    if video.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Только MP4 или MOV!",
        )
    
    # Проверка размера (например, не больше 100 МБ)
    max_size = MAX_VIDEO_SIZE_MB * 1024 * 1024
    if video.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Видео не должно превышать {MAX_VIDEO_SIZE_MB} МБ!",
        )
    
    
    # Сохранение...
    
    with open(f"src/uploads/{task_id}.mp4", "wb") as buffer:
        buffer.write(await video.read())
    
    processing_video.delay(f"{task_id}.mp4")
    return JSONResponse(
        status_code=202,  # Accepted (задача принята в обработку)
        content={"task_id": task_id, "status": "queued"}
    )

@router.get("/get_video/{video_name}")
async def get_video(video_name:str):
    return FileResponse(f"src/uploads/{video_name}")


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    # Здесь проверяем статус в Redis/БД (пример упрощен)
    return {"task_id": task_id, "status": "processing"}












