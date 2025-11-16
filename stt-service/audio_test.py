# step2_test_whisper.py
import whisper
import os

def test_whisper_transcription():
    # Load Whisper model (this downloads the model first time)
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # ~74MB download
    print("Model loaded!")
    
    # Test with your recorded file
    audio_file = "test_recording.wav"
    
    if not os.path.exists(audio_file):
        print(f"Error: {audio_file} not found. Run step1_test_recording.py first!")
        return
    
    print(f"Transcribing: {audio_file}")
    
    # Transcribe
    result = model.transcribe(audio_file)
    
    print("\n" + "="*50)
    print("TRANSCRIPTION RESULT:")
    print("="*50)
    print(f"Detected Language: {result['language']}")
    print(f"Text: {result['text']}")
    
    # Show detailed segments with timestamps
    print("\nDetailed Segments:")
    for segment in result['segments']:
        start = segment['start']
        end = segment['end']
        text = segment['text']
        print(f"[{start:.2f}s - {end:.2f}s]: {text}")

if __name__ == "__main__":
    test_whisper_transcription()


