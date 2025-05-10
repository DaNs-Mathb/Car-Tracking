import asyncio
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import File, UploadFile, status
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from src.api.schemas import TaskStatusResponse
from src.middleware.video_processing import processing_video
import uuid
from celery.result import AsyncResult


router=APIRouter()
MAX_VIDEO_SIZE_MB = 100
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime"]  # MP4, MOV и т.д.

@router.post("/upload-validated-video/")
async def upload_validated_video(video: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    
    try:
        # Проверка типа
        if video.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Только MP4 или MOV!",
            )
        
        # Проверка размера
        max_size = MAX_VIDEO_SIZE_MB * 1024 * 1024
        if video.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Видео не должно превышать {MAX_VIDEO_SIZE_MB} МБ!",
            )
        
        # Создаем директорию, если её нет
        os.makedirs("src/uploads", exist_ok=True)
        
        # Сохранение файла
        file_path = f"src/uploads/{video_id}.mp4"
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(await video.read())
        except IOError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка сохранения файла: {str(e)}"
            )
        
        # Запуск задачи Celery
        try:
            celery_task = processing_video.delay(f"{video_id}.mp4")
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "task_id": celery_task.id,
                    "status": "queued",
                    "video_id": video_id,
                    "status_url": f"/tasks/{celery_task.id}/status"
                }
            )
        except Exception as e:
            # Удаляем сохраненный файл, если не удалось поставить задачу в очередь
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка запуска обработки видео: {str(e)}"
            )
            
    except HTTPException:
        # Перебрасываем уже созданные HTTPException
        raise
    except Exception as e:
        # Ловим все непредвиденные ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.get("/get_video/{video_name}")
async def get_video(video_name:str):
    return FileResponse(f"src/uploads/{video_name}")


@router.get("/tasks/{task_id}/status")#response_model=TaskStatusResponse
async def get_task_status(task_id: str):
    try:
        task = AsyncResult(task_id)
        
        if not task.ready():
            response = {
                "task_id": task_id,
                "status": task.status,
                "progress": task.info.get('progress', 0) if task.status == 'PROGRESS' else None,
                "current": task.info.get('current', 0),
                "total": task.info.get('total', 1)
            }
        else:
            response = {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.successful() else None,
                "error": str(task.result) if task.failed() else None
            }  # Или более детальное сообщение об ошибке
        
        return response
    except Exception as e:
        # Ловим все непредвиденные ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
        
@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            try:
                task = AsyncResult(task_id)
                
                # Формируем ответ
                response = {
                    "task_id": task_id,
                    "status": task.status,
                }
                
                if task.status == "PROGRESS":
                    response.update({
                        "progress": task.info.get("progress", 0),
                        "current": task.info.get("current", 0),
                        "total": task.info.get("total", 1)
                    })
                elif task.ready():
                    if task.successful():
                        response["result"] = task.result
                    else:
                        response["error"] = str(task.result)
                    await websocket.send_json(response)
                    break
                
                await websocket.send_json(response)
                await asyncio.sleep(1)  # Интервал обновлений
                
            except TimeoutError:
                await websocket.send_json({
                    "error": "Timeout checking task status"
                })
            except Exception as e:
                await websocket.send_json({
                    "error": f"Internal error: {str(e)}"
                })
                break
                
    except WebSocketDisconnect:
        print(f"Client disconnected from task {task_id}")
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


