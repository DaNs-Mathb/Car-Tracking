from fastapi import APIRouter
import asyncio
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaBlackhole
from src.api.schemas import Offer
from src.middleware.broadcast_processing import VideoTransformTrack

router=APIRouter()

@router.post("/offer")
async def offer(params: Offer):
    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    pc = RTCPeerConnection()
    pcs.add(pc)
    relay = MediaRelay()
    recorder = MediaBlackhole()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # open media source
    # _, video_capture = create_local_tracks()  # Получаем cv2.VideoCapture
    # video_track = VideoTransformTrack(video_capture)

    # Добавляем трек
    # pc.addTrack(video_track)
    
    @pc.on("track")
    def on_track(track):

        # if track.kind == "audio":
        #     pc.addTrack(player.audio)
        #     recorder.addTrack(track)
        if track.kind == "video":
            pc.addTrack(
                VideoTransformTrack(relay.subscribe(track))#, transform=params.video_transform
            )
            # if args.record_to:
            #     recorder.addTrack(relay.subscribe(track))

        # @track.on("ended")
        # async def on_ended():
        #     await recorder.stop()
    
    

    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


pcs = set()


@router.on_event("shutdown")
async def on_shutdown():
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()