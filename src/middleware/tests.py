from celery import Celery
from ultralytics import YOLO
import os
import shutil

# from minio import Minio  # Для S3-совместимого хранилища


def process_video_task(input_path: str, task_id: str):
    try:
        # Загружаем модель YOLO (например, yolov8n)
        model = YOLO("src/middleware/yolo11m.pt").to('cuda')
        
        # Обрабатываем видео (трекинг объектов)
        results = model.track(
            source=input_path,
            save=True,  # Сохраняем результат
            project="results",
            name=task_id
        )
        
        # Путь к обработанному видео
        output_path = f"results/{task_id}/input.mp4"
        
        # Загружаем в S3 (пример для MinIO)
        
        
        # # Удаляем временные файлы
        # os.remove(input_path)
        # shutil.rmtree(f"results/{task_id}")
        
        return {"status": "success", "task_id": task_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
    
process_video_task('src/uploads/cars.mp4','123')