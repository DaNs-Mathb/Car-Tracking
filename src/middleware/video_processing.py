import cv2 
from ultralytics import YOLO
import torch
from celery import Celery
from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv() 

celery_app = Celery("tasks", broker=os.getenv("REDIS_URL"))


client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False  # True для HTTPS
)


@celery_app.task(name="src.middleware.processing.processing_video")
def processing_video(input_video: str ,classe:int=2):
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        # print(f"Using device: {device}")
        model = YOLO("src/middleware/yolo11m.pt").to(device)  # Замените "yolov8n.pt" на путь к вашей модели
        # Открываем видео через OpenCV
        cap = cv2.VideoCapture(f"src/uploads/{input_video}")
    


        # Проверка, что видеофайл открылся
        if not cap.isOpened():
            print("Ошибка: не удалось открыть видеофайл")
            exit()

        
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        output_name=f'output_{input_video}'
        # Создаем VideoWriter для сохранения видео
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(f'src/uploads/{output_name}', fourcc, fps, (frame_width, frame_height))

        frame_count = 0
        skip_frames = 2
        last_processed_frame = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break  # Выход из цикла, если видео закончилось

            frame_count += 1
            if frame_count % (skip_frames + 1) == 0:
                # Обрабатываем каждый (skip_frames+1)-й кадр
                results = model.track(frame, classes=[classe], persist=True, device=device, imgsz=640)
                last_processed_frame = results[0].plot()  # Сохраняем обработанный кадр
        
            # Записываем последний обработанный кадр для всех кадров
            if last_processed_frame is not None:
                out.write(last_processed_frame)

        # Освобождение ресурсов
        cap.release()
        out.release()
        
        
        client.fput_object(
            "processed-videos",  # Бакет
            output_name,      # Имя файла в MinIO
            f"src/uploads/{output_name}"    # Локальный путь
        )
        for file_path in [f'src/uploads/{output_name}',f"src/uploads/{input_video}"]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return {"status": "success", "task_id": input_video}
    except Exception as e:
        return {"status": "error", "error": str(e)}
# print(torch.cuda.is_available())
# processing_video(input_video="cars.mp4")

# print(f"PyTorch version: {torch.__version__}")
# print(f"CUDA available: {torch.cuda.is_available()}")
# print(f"GPU device: {torch.cuda.get_device_name(0)}")
# print(torch.backends.cudnn.enabled)  # Должно быть True
# docker run -p 9000:9000 -p 9001:9001 --name minio -v D:\programm\minio_storage:/data -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" minio/minio server /data --console-address ":9001"