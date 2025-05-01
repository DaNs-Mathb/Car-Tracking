import asyncio
from aiortc import MediaStreamError, MediaStreamTrack
import cv2 
import torch
from ultralytics import YOLO
from av import VideoFrame


class VideoTransformTrack(MediaStreamTrack):
    kind = "video"
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # ProcessPoolExecutor(max_workers=1)  # 1 процесс на GPU
    
    
    
    model = YOLO("src/middleware/yolo11m.pt").to(device) 
    def __init__(self, video_capture):
        super().__init__()
        self.track = video_capture
        self.frame_count = 0
        self._executor = None
        


    async def recv(self):
        try:
            frame = await self.track.recv()
            img = frame.to_ndarray(format="bgr24")  # Конвертируем в BGR (как ожидает YOLO)
            
            # Обработка через YOLO (синхронная часть)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor,
                self._process_frame,
                img
            )
            
            # Получаем обработанный кадр (в BGR)
            rgb_frame = cv2.cvtColor(results, cv2.COLOR_BGR2RGB)
            
            # Создаем новый VideoFrame
            new_frame = VideoFrame.from_ndarray(rgb_frame, format="rgb24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            
            self.frame_count += 1
            print(f"Frame {self.frame_count} processed")
            return new_frame
            
        except Exception as e:
            print(f"Error in recv: {str(e)}")
            raise MediaStreamError(str(e))
        
        
    def _process_frame(self, img):
        """Синхронная обработка кадра через YOLO."""
        return self.model.track(
            img,
            classes=[2],
            persist=True,
            device=self.device,
            imgsz=640
        )[0].plot()