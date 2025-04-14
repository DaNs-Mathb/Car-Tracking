from datetime import timedelta
from celery import Celery
from ultralytics import YOLO
import os
import shutil
from minio import Minio





# url = client.presigned_get_object("processed-videos", "video123.mp4", expires=timedelta(minutes=1))
# print(url)
# from minio import Minio  # Для S3-совместимого хранилища


# def process_video_task(input_path: str, task_id: str):
#     try:
#         # Загружаем модель YOLO (например, yolov8n)
#         model = YOLO("src/middleware/yolo11m.pt").to('cuda')
        
#         # Обрабатываем видео (трекинг объектов)
#         results = model.track(
#             source=input_path,
#             save=True,  # Сохраняем результат
#             project="results",
#             name=task_id
#         )
        
#         # Путь к обработанному видео
#         output_path = f"results/{task_id}/input.mp4"
        
#         # Загружаем в S3 (пример для MinIO)
        
        
#         # # Удаляем временные файлы
#         # os.remove(input_path)
#         # shutil.rmtree(f"results/{task_id}")
        
#         return {"status": "success", "task_id": task_id}
#     except Exception as e:
#         return {"status": "error", "error": str(e)}
    
    
# process_video_task('src/uploads/cars.mp4','123')
import cv2

def get_video_codec(input_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Не удалось открыть видеофайл")
    
    # Получаем FOURCC код кодека
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = (
        chr(fourcc_int & 0xFF) +
        chr((fourcc_int >> 8) & 0xFF) +
        chr((fourcc_int >> 16) & 0xFF) +
        chr((fourcc_int >> 24) & 0xFF)
    )
    
    # Дополнительная информация
    codec_name = {
        'avc1': 'H.264/AVC',
        'h264': 'H.264',
        'mp4v': 'MPEG-4',
        'XVID': 'XVID',
        'MJPG': 'Motion-JPEG',
        'VP80': 'VP8/WebM'
    }.get(fourcc_str.lower(), f"Неизвестный кодек ({fourcc_str})")
    
    cap.release()
    return fourcc_str, codec_name

# Использование:
input_video = "src/uploads/83da3a5b-4cd5-4abf-92fd-b3b9fa4d1022.mp4"
codec, codec_name = get_video_codec(input_video)
print(f"Кодек видео: {codec} ({codec_name})")