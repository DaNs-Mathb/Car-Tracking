import asyncio
from concurrent.futures import ProcessPoolExecutor
from aiortc import MediaStreamError, MediaStreamTrack, VideoStreamTrack
import numpy as np
import torch
from ultralytics import YOLO
from av import VideoFrame


import asyncio
import time
import torch
from ultralytics import YOLO

class FrameProcessor:
    def __init__(self, model_path, device="cuda"):
        self._model_path = model_path
        self._device = device
        self._ready_event = asyncio.Event()
        self._input_queue = asyncio.Queue()
        self._output_queue = asyncio.Queue()
        self._task = asyncio.create_task(self._run())  # Запускаем фоновую задачу

    async def _run(self):
        """Фоновая задача загрузки модели и обработки кадров"""
        try:
            try:
                print("[MODEL] Загрузка модели...")
                self._model = YOLO(self._model_path).to(self._device)
                self._model.fuse()
                dummy = torch.zeros((1, 3, 640, 640)).to(self._device)
                self._model(dummy)
                print("[MODEL] Модель готова.")
                self._ready_event.set()
            except Exception as e:
                print(f"[MODEL ERROR] {e}")
                return

            while True:
                img = await self._input_queue.get()
                if img is None:
                    break  # Завершаем

                result = self._model.track(img, persist=False, device=self._device, verbose=False)
                plotted = result[0].plot()
                await self._output_queue.put(plotted)
        except asyncio.CancelledError:
            print("Задача корректно завершена")
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
    async def wait_ready(self, timeout=10):
        """Ждём готовности модели"""
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def process(self, img):
        """Кладём кадр, ждём результат"""
        await self._input_queue.put(img)
        return await self._output_queue.get()

    
    async def close(self):
        await self._input_queue.put(None)  # Сигнал завершения
        await self._task  # Дождаться завершения
        print("[FrameProcessor] Shutdown complete")
   





class VideoTransformTrack(MediaStreamTrack):
    kind = "video"

    # ProcessPoolExecutor(max_workers=1)  # 1 процесс на GPU
    def __init__(self, video_capture, processor: FrameProcessor):
        super().__init__()
        self.track = video_capture
        self.processor = processor



    async def recv(self):
        try:
            frame = await self.track.recv()
           
            img = frame.to_ndarray(format="bgr24")
 
            
            if not await self.processor.wait_ready(timeout=0.1):
                return frame
            processed_img = await self.processor.process(img)

            new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
 
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base

            return new_frame
        except asyncio.CancelledError:
            print("Задача корректно завершена")    
        except Exception as e:
            print(f"Error in recv: {str(e)}")
            raise MediaStreamError(str(e))
        
