import os
import asyncio
import aiohttp
import json
from .models import JudgeResult, JudgeScores, ScoreSet, JudgeFeedback

# --- 1. Real STT Service Client ---
STT_SERVICE_URL = os.getenv("STT_SERVICE_WS_URL", "ws://localhost:8000/ws/transcribe")

async def stt_client_handler(
    audio_stream: asyncio.Queue, 
    on_transcript: callable
):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(STT_SERVICE_URL) as ws:
                print("Connected to STT service.")
                
                async def send_audio():
                    while True:
                        audio_chunk = await audio_stream.get()
                        if audio_chunk is None: 
                            break
                        await ws.send_bytes(audio_chunk)
                    await ws.close(code=1000, message=b'Finished')

                async def receive_transcripts():
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await on_transcript(data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"STT WS Error: {ws.exception()}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            break
                
                send_task = asyncio.create_task(send_audio())
                receive_task = asyncio.create_task(receive_transcripts())
                await asyncio.gather(send_task, receive_task)
                
    except Exception as e:
        print(f"Could not connect to STT service: {e}")
        await on_transcript({"type": "error", "error": "STT Service connection failed."})
    finally:
        print("STT client handler finished.")

# --- 2. Mock LLM Judge Service ---
async def mock_llm_judge(transcripts: dict) -> JudgeResult:
    print("Mock LLM Judge is 'evaluating' transcripts...")
    await asyncio.sleep(3) 

    user_ids = list(transcripts.keys())
    user_a_id = user_ids[0] if len(user_ids) > 0 else "user_a"
    user_b_id = user_ids[1] if len(user_ids) > 1 else "user_b"

    mock_scores = JudgeScores(
        user_a=ScoreSet(clarity=8, logic=9, evidence=7, emotional_appeal=5),
        user_b=ScoreSet(clarity=7, logic=6, evidence=5, emotional_appeal=8)
    )
    
    mock_feedback = JudgeFeedback(
        user_a="User A had stronger evidence and a more logical flow.",
        user_b="User B had a powerful emotional appeal but lacked supporting facts."
    )
    
    result = JudgeResult(
        winner=user_a_id,
        scores=mock_scores,
        feedback=mock_feedback
    )
    
    print("Mock LLM Judge has 'decided'.")
    return result
