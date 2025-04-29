import asyncio
import json
import websockets
import aiortc
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack, MediaRecorder
import cv2
import numpy as np
from av import VideoFrame
import logging
from PyQt6.QtCore import QThread, pyqtSignal

class WebRTCClient(QThread):
    video_received = pyqtSignal(int, np.ndarray)
    user_joined = pyqtSignal(int, str)
    user_left = pyqtSignal(int)
    message_received = pyqtSignal(str, str)

    def __init__(self, room_id, display_name, server_url):
        super().__init__()
        self.room_id = room_id
        self.display_name = display_name
        self.server_url = server_url
        self.peer_connections = {}
        self.video_track = VideoStreamTrack()
        self.audio_track = AudioStreamTrack()
        self.websocket = None
        self.running = True
        self.recorder = None
        self.is_recording = False
        self.data_channels = {}

    async def connect(self):
        self.websocket = await websockets.connect(self.server_url)
        await self.websocket.send(json.dumps({
            'type': 'join',
            'room_id': self.room_id,
            'name': self.display_name
        }))

    def start_recording(self, output_file):
        if not self.is_recording:
            self.recorder = MediaRecorder(output_file)
            self.recorder.addTrack(self.video_track)
            self.recorder.addTrack(self.audio_track)
            asyncio.run(self.recorder.start())
            self.is_recording = True

    def stop_recording(self):
        if self.is_recording and self.recorder:
            asyncio.run(self.recorder.stop())
            self.is_recording = False

    async def handle_signaling(self):
        while self.running:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'user-list':
                    await self.handle_user_list(data)
                elif data['type'] == 'user-joined':
                    self.user_joined.emit(data['user_id'], data['name'])
                elif data['type'] == 'user-left':
                    self.user_left.emit(data['user_id'])
                    await self.handle_user_left(data['user_id'])
                elif data['type'] == 'offer':
                    await self.handle_offer(data)
                elif data['type'] == 'answer':
                    await self.handle_answer(data)
                elif data['type'] == 'ice-candidate':
                    await self.handle_ice_candidate(data)
                    
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logging.error(f"Error handling signaling: {e}")
                break

    async def handle_user_list(self, data):
        for user in data['users']:
            await self.create_peer_connection(user['id'])

    async def handle_user_left(self, user_id):
        if user_id in self.peer_connections:
            await self.peer_connections[user_id].close()
            del self.peer_connections[user_id]

    async def create_peer_connection(self, peer_id):
        if peer_id in self.peer_connections:
            return

        pc = RTCPeerConnection()
        self.peer_connections[peer_id] = pc

        # Add data channel for chat
        data_channel = pc.createDataChannel("chat")
        self.data_channels[peer_id] = data_channel

        @data_channel.on("open")
        def on_open():
            logging.info(f"Data channel opened with {peer_id}")

        @data_channel.on("message")
        def on_message(message):
            try:
                data = json.loads(message)
                if data.get("type") == "chat":
                    self.message_received.emit(data.get("sender"), data.get("message"))
            except Exception as e:
                logging.error(f"Error processing chat message: {e}")

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            await self.websocket.send(json.dumps({
                'type': 'ice-candidate',
                'target_id': peer_id,
                'candidate': candidate.to_json()
            }))

        @pc.on("track")
        async def on_track(track):
            if track.kind == "video":
                while True:
                    try:
                        frame = await track.recv()
                        img = frame.to_ndarray(format="rgb24")
                        self.video_received.emit(peer_id, img)
                    except Exception as e:
                        logging.error(f"Error processing video frame: {e}")
                        break

        # Add local tracks
        pc.addTrack(self.video_track)
        pc.addTrack(self.audio_track)

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        await self.websocket.send(json.dumps({
            'type': 'offer',
            'target_id': peer_id,
            'offer': pc.localDescription.sdp
        }))

    async def handle_offer(self, data):
        peer_id = data['sender_id']
        if peer_id not in self.peer_connections:
            await self.create_peer_connection(peer_id)

        pc = self.peer_connections[peer_id]
        await pc.setRemoteDescription(RTCSessionDescription(
            sdp=data['offer'], type="offer"
        ))

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        await self.websocket.send(json.dumps({
            'type': 'answer',
            'target_id': peer_id,
            'answer': pc.localDescription.sdp
        }))

    async def handle_answer(self, data):
        peer_id = data['sender_id']
        if peer_id in self.peer_connections:
            pc = self.peer_connections[peer_id]
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=data['answer'], type="answer"
            ))

    async def handle_ice_candidate(self, data):
        peer_id = data['sender_id']
        if peer_id in self.peer_connections:
            pc = self.peer_connections[peer_id]
            await pc.addIceCandidate(RTCIceCandidate(
                candidate=data['candidate']['candidate'],
                sdpMid=data['candidate']['sdpMid'],
                sdpMLineIndex=data['candidate']['sdpMLineIndex']
            ))

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        await self.connect()
        await self.handle_signaling()

    def stop(self):
        self.running = False
        if self.websocket:
            asyncio.run(self.websocket.close())
            self.websocket = None
            
        for pc in self.peer_connections.values():
            asyncio.run(pc.close())
        self.peer_connections.clear()
        
        if self.recorder and self.is_recording:
            asyncio.run(self.recorder.stop())
            self.is_recording = False

    def set_mic_muted(self, muted):
        self.audio_track.set_muted(muted)

    def set_camera_muted(self, muted):
        self.video_track.set_muted(muted)

    def send_message(self, message):
        """Send chat message to all peers"""
        data = {
            "type": "chat",
            "sender": self.display_name,
            "message": message
        }
        for peer_id, data_channel in self.data_channels.items():
            if data_channel.readyState == "open":
                data_channel.send(json.dumps(data))

class VideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.muted = False
        self.cap = None
        self.start_video_capture()

    def start_video_capture(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Failed to open camera")
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
        except Exception as e:
            logging.error(f"Failed to start video capture: {e}")
            self.cap = None

    async def recv(self):
        if self.muted or not self.cap:
            return None

        try:
            ret, frame = self.cap.read()
            if not ret:
                return None

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frame = VideoFrame.from_ndarray(frame, format='rgb24')
            return video_frame

        except Exception as e:
            logging.error(f"Error processing video frame: {e}")
            return None

    def stop(self):
        if self.cap:
            self.cap.release()
        super().stop()

    def set_muted(self, muted):
        self.muted = muted

class AudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.muted = False
        self.sample_rate = 48000
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        self.stream = None
        self.start_audio_capture()

    def start_audio_capture(self):
        import sounddevice as sd
        import numpy as np
        
        def audio_callback(indata, frames, time, status):
            if status:
                logging.warning(f"Audio capture status: {status}")
            if not self.muted:
                self.audio_buffer.extend(indata[:, 0])  # Take first channel if stereo

        try:
            self.audio_buffer = []
            self.stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=audio_callback,
                blocksize=1024,
                dtype=np.float32
            )
            self.stream.start()
            
        except Exception as e:
            logging.error(f"Failed to start audio capture: {e}")
            self.stream = None

    async def recv(self):
        if self.muted or not self.stream:
            return None

        import numpy as np
        from av import AudioFrame

        if len(self.audio_buffer) < 1024:
            await asyncio.sleep(0.01)  # Wait for more audio data
            return None

        # Get audio data from buffer
        audio_data = np.array(self.audio_buffer[:1024], dtype=np.float32)
        self.audio_buffer = self.audio_buffer[1024:]

        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)

        # Create audio frame
        frame = AudioFrame.from_ndarray(audio_data, layout='mono', rate=self.sample_rate)
        return frame

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        super().stop()

    def set_muted(self, muted):
        self.muted = muted 