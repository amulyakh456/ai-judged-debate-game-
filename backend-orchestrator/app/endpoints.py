from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
from .services import stt_client_handler, mock_llm_judge
from .models import WsMsg_Transcript, WsMsg_DebateState, WsMsg_Error
import asyncio
import secrets
import json

router = APIRouter()

@router.post("/api/v1/rooms/create", status_code=201)
async def create_room():
    room_code = secrets.token_urlsafe(6).upper().replace("_", "-")
    return {"room_code": room_code}

@router.websocket("/ws/{room_code}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, user_id: str):
    await manager.connect(room_code, websocket)
    print(f"User {user_id} connected to room {room_code}")

    await manager.broadcast_json(room_code, WsMsg_DebateState(
        user_id="system",
        message=f"{user_id} has joined the debate."
    ).dict())

    audio_to_stt_queue = asyncio.Queue()

    async def on_transcript_received(transcript_data: dict):
        if transcript_data.get("type") == "error":
            await manager.send_personal_json(websocket, WsMsg_Error(
                user_id="system",
                error=transcript_data.get("error")
            ).dict())
            return
            
        msg = WsMsg_Transcript(
            user_id=user_id,
            text=transcript_data.get("text", ""),
            is_final=transcript_data.get("is_final", False)
        )
        
        if msg.is_final and msg.text:
            manager.add_transcript(room_code, user_id, msg.text)

        await manager.broadcast_json(room_code, msg.dict())
    
    stt_task = asyncio.create_task(
        stt_client_handler(audio_to_stt_queue, on_transcript_received)
    )

    try:
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                await audio_to_stt_queue.put(data["bytes"])
            
            elif "text" in data:
                message = json.loads(data["text"])
                
                if message.get("event") == "debate_end":
                    print(f"Debate end triggered by {user_id} in room {room_code}.")
                    await audio_to_stt_queue.put(None) 
                    await stt_task
                    
                    final_transcripts = manager.get_final_transcripts(room_code)
                    
                    await manager.broadcast_json(room_code, WsMsg_DebateState(
                        user_id="system",
                        message="Debate ended. Awaiting judgment..."
                    ).dict())
                    
                    judge_result = await mock_llm_judge(final_transcripts)
                    
                    await manager.broadcast_json(room_code, {
                        "type": "judge_result",
                        "user_id": "system",
                        "data": judge_result.dict()
                    })
                    
                    manager.clear_room_data(room_code)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected from room {room_code}")
    
    finally:
        if not stt_task.done():
            await audio_to_stt_queue.put(None)
            stt_task.cancel()
        
        await manager.broadcast_json(room_code, WsMsg_DebateState(
            user_id="system",
            message=f"{user_id} has left the debate."
        ).dict())
        manager.disconnect(room_code, websocket)
