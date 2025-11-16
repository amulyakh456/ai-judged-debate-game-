from fastapi import WebSocket
from typing import Dict, List, Set, DefaultDict
from collections import defaultdict
import asyncio

RoomTranscriptStore = DefaultDict[str, Dict[str, str]]

class ConnectionManager:
    def __init__(self):
        self.active_rooms: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self.transcripts: RoomTranscriptStore = defaultdict(lambda: defaultdict(str))
        self.lock = asyncio.Lock()

    async def connect(self, room_code: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_rooms[room_code].add(websocket)

    async def disconnect(self, room_code: str, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_rooms[room_code]:
                self.active_rooms[room_code].remove(websocket)

    def get_users_in_room(self, room_code: str) -> Set[WebSocket]:
        return self.active_rooms.get(room_code, set())
        
    def add_transcript(self, room_code: str, user_id: str, text: str):
        self.transcripts[room_code][user_id] += text + " "

    def get_final_transcripts(self, room_code: str) -> Dict[str, str]:
        return self.transcripts.get(room_code, {})

    def clear_room_data(self, room_code: str):
        if room_code in self.transcripts:
            del self.transcripts[room_code]
        
    async def broadcast_json(self, room_code: str, message: dict):
        connections = self.get_users_in_room(room_code)
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to a websocket: {e}")

    async def send_personal_json(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

manager = ConnectionManager()
