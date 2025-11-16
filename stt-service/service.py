import uvicorn
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
import time
import whisper
import os
import tempfile
from contextlib import asynccontextmanager
import asyncio
import numpy as np
import io

# --- Configuration ---
# This must match what the audio source sends. Whisper expects 16kHz mono.
SAMPLE_RATE = 16000
# Process audio in 5-second chunks for a balance of latency and context
CHUNK_DURATION_SECONDS = 5
# Calculate the number of bytes for a 5-second chunk of 16-bit (2-byte) audio
CHUNK_SIZE_BYTES = CHUNK_DURATION_SECONDS * SAMPLE_RATE * 2

# --- Model Loading ---
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Whisper model loaded successfully.")

# --- Application Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the application."""
    print("AI Debate Judge STT Service is starting up.")
    yield
    print("AI Debate Judge STT Service is shutting down.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Debate Judge - Speech-to-Text Service",
    description="An API to transcribe audio using the Whisper model via file upload or live WebSocket.",
    version="1.2.0",
    lifespan=lifespan
)

# --- Helper function for chunk transcription ---
async def transcribe_chunk(audio_data: bytes):
    """A helper function to transcribe a single chunk of audio data."""
    if not audio_data:
        return ""
    # Convert raw bytes to a NumPy array that Whisper can process
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    try:
        def run_transcription():
            return model.transcribe(audio_np, fp16=False)
        result = await asyncio.to_thread(run_transcription)
        return result["text"].strip()
    except Exception as e:
        print(f"Error during chunk transcription: {e}")
        return ""

# --- LIVE WebSocket Endpoint ---
@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """Handles real-time audio streaming and transcription over a WebSocket."""
    await websocket.accept()
    print("WebSocket connection established for live transcription.")
    audio_buffer = bytearray()
    transcription_tasks=set()
    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            # Process audio in chunks as it comes in
            while len(audio_buffer) >= CHUNK_SIZE_BYTES:
                chunk_to_process = audio_buffer[:CHUNK_SIZE_BYTES]
                audio_buffer = audio_buffer[CHUNK_SIZE_BYTES:]
                
                print(f"Processing a {CHUNK_DURATION_SECONDS}-second chunk of audio...")
                task=asyncio.create_task(transcribe_chunk(bytes(chunk_to_process)))
                transcription_tasks.add(task)
                def task_done_callback(t:asyncio.Task):
                    transcription_tasks.discard(t)
                    if t.exception():
                        print(f"Task failed: {t.exception()}")
                        return
                    transcription_text=t.result()
                    if transcription_text:
                        print(f"Partial transcript: {transcription_text}")
                        asyncio.create_task(websocket.send_json({
                            "is_final": False,
                            "text": transcription_text
                        }))
                task.add_done_callback(task_done_callback)        

    except WebSocketDisconnect:
        print("WebSocket disconnected. Processing any remaining audio.")
        if audio_buffer:
            print(f"Processing final chunck of {len(audio_buffer)} bytes...")
            final_chunk_task=asyncio.create_task(transcribe_chunk(bytes(audio_buffer)))
            transcription_tasks.add(final_chunck_task)
            if transcription_tasks:
                await asyncio.gather(*transcription_tasks, return_exceptions=True)
                print("All pending transcription tasks completed.")
            
            if 'final_chunk_task' in locals() and final_chunk_task.done():
                try:
                    transcription_text = final_chunk_task.result()
                    if transcription_text:
                        await websocket.send_json({
                            "is_final": True,
                            "text": transcription_text
                        })
                except Exception as e:
                    print(f"Error during final result retrieval: {e}")

            print("Live transcription session finished.")

# --- File Upload Endpoint ---
@app.post("/transcribe/", tags=["Transcription"])
async def transcribe_audio(file: UploadFile = File(...)):
    """Handles transcription of a single uploaded audio file."""
    start_time = time.time()
    print(f"Starting transcription for {file.filename}...")
    
    # Use asyncio.to_thread for the file writing to keep the event loop non-blocking
    def sync_write_file(content):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(content)
            return temp_file.name

    content = await file.read()
    temp_audio_path = await asyncio.to_thread(sync_write_file, content)
        
    print(f"Saved temporary audio file to {temp_audio_path}")
    
    try:
        # Use asyncio.to_thread for the main transcription call
        def sync_transcribe_file():
            return model.transcribe(temp_audio_path, fp16=False)

        result = await asyncio.to_thread(sync_transcribe_file)
        transcription_text = result["text"]
        print("Transcription completed successfully!")
    except Exception as e:
        print(f"Error occurred during transcription: {e}")
        return {"error": "Transcription failed"}
    finally:
        # Use asyncio.to_thread for file deletion too
        await asyncio.to_thread(os.remove, temp_audio_path)
        print(f"Temporary file {temp_audio_path} deleted")
        
    end_time = time.time()
    processing_time = round(end_time - start_time, 2)
    print(f"Transcription completed in {processing_time} seconds")
    
    return {
        "filename": file.filename,
        "transcription": transcription_text,
        "processing_time_seconds": processing_time,
    }
if __name__ == "__main__":
    print("Starting the Uvicorn server for the STT service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
