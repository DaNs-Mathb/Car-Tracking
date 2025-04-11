import cv2 
from ultralytics import YOLO
import torch
from celery import Celery



async def processing_video(input_video: str ,classe:int=2):
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
    output_name='output.mp4'
    # Создаем VideoWriter для сохранения видео
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Кодек для MP4
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
    return output_name

# print(torch.cuda.is_available())
# processing_video(input_video="cars.mp4")

# print(f"PyTorch version: {torch.__version__}")
# print(f"CUDA available: {torch.cuda.is_available()}")
# print(f"GPU device: {torch.cuda.get_device_name(0)}")
# print(torch.backends.cudnn.enabled)  # Должно быть True
