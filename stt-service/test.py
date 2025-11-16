# step1_test_recording.py
import pyaudio
import wave
import time

def test_microphone():
    # Audio settings
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SIZE = 1024
    RECORD_SECONDS = 5
    OUTPUT_FILE = "test_recording.wav"
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    # Check available audio devices
    print("Available audio devices:")
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            print(f"Device {i}: {device_info['name']}")
    
    print(f"\nRecording for {RECORD_SECONDS} seconds...")
    print("Speak into your microphone!")
    
    # Start recording
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK_SIZE * RECORD_SECONDS)):
        data = stream.read(CHUNK_SIZE)
        frames.append(data)
    
    # Stop recording
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save the recording
    with wave.open(OUTPUT_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    
    print(f"Recording saved as: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    test_microphone()