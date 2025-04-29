import asyncio
import websockets
import json
import logging
from typing import Dict, Set
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from datetime import datetime
from database import get_session
from json_storage import json_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class SignalingServer:
    def __init__(self):
        self.rooms: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.user_info: Dict[websockets.WebSocketServerProtocol, dict] = {}

    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        try:
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get('type')

                if message_type == 'join':
                    await self.handle_join(websocket, data)
                elif message_type == 'offer':
                    await self.handle_offer(websocket, data)
                elif message_type == 'answer':
                    await self.handle_answer(websocket, data)
                elif message_type == 'ice-candidate':
                    await self.handle_ice_candidate(websocket, data)
                elif message_type == 'leave':
                    await self.handle_leave(websocket)
        except websockets.exceptions.ConnectionClosed:
            await self.handle_leave(websocket)
        except Exception as e:
            logger.error(f"Error handling connection: {e}")

    async def handle_join(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        room_id = data['room_id']
        user_info = {
            'name': data.get('name', 'Anonymous'),
            'room_id': room_id
        }
        self.user_info[websocket] = user_info

        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

        # Notify others in the room
        for peer in self.rooms[room_id]:
            if peer != websocket:
                await peer.send(json.dumps({
                    'type': 'user-joined',
                    'user_id': id(websocket),
                    'name': user_info['name']
                }))

        # Send list of existing users to the new user
        users = [
            {'id': id(peer), 'name': self.user_info[peer]['name']}
            for peer in self.rooms[room_id]
            if peer != websocket
        ]
        await websocket.send(json.dumps({
            'type': 'user-list',
            'users': users
        }))

    async def handle_offer(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        target_id = data['target_id']
        for peer in self.rooms[self.user_info[websocket]['room_id']]:
            if id(peer) == target_id:
                await peer.send(json.dumps({
                    'type': 'offer',
                    'sender_id': id(websocket),
                    'offer': data['offer']
                }))
                break

    async def handle_answer(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        target_id = data['target_id']
        for peer in self.rooms[self.user_info[websocket]['room_id']]:
            if id(peer) == target_id:
                await peer.send(json.dumps({
                    'type': 'answer',
                    'sender_id': id(websocket),
                    'answer': data['answer']
                }))
                break

    async def handle_ice_candidate(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        target_id = data['target_id']
        for peer in self.rooms[self.user_info[websocket]['room_id']]:
            if id(peer) == target_id:
                await peer.send(json.dumps({
                    'type': 'ice-candidate',
                    'sender_id': id(websocket),
                    'candidate': data['candidate']
                }))
                break

    async def handle_leave(self, websocket: websockets.WebSocketServerProtocol):
        if websocket in self.user_info:
            user_info = self.user_info[websocket]
            room_id = user_info['room_id']
            
            if room_id in self.rooms:
                self.rooms[room_id].remove(websocket)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]

                # Notify others in the room
                for peer in self.rooms.get(room_id, set()):
                    await peer.send(json.dumps({
                        'type': 'user-left',
                        'user_id': id(websocket)
                    }))

            del self.user_info[websocket]

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{data["name"]} has entered the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{data["name"]} has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = {
        'room': room,
        'user': data['name'],
        'content': data['message'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Save message to both SQLite and JSON storage
    asyncio.run(json_storage.save_message(message))
    
    emit('message', message, room=room)

@app.route('/messages/<room>', methods=['GET'])
def get_messages(room):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get messages from JSON storage
    messages = asyncio.run(json_storage.get_messages(
        group_id=room,
        start_date=start_date,
        end_date=end_date
    ))
    return jsonify(messages)

@app.route('/messages/<room>', methods=['DELETE'])
def delete_messages(room):
    # Delete messages from JSON storage
    asyncio.run(json_storage.delete_messages(group_id=room))
    return jsonify({'status': 'success'})

async def main():
    server = SignalingServer()
    async with websockets.serve(server.handle_connection, "26.34.237.219", 8765):
        logger.info("Signaling server started on ws://26.34.237.219:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
