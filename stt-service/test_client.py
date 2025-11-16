def send_for_transcription(audio_filename):
    """Sends the audio file to the FastAPI service and prints the response."""
    print(f"\n🚀 Sending '{audio_filename}' to the transcription service at {API_URL}...")
    
    try:
        # Prepare the file for the POST request
        with open(audio_filename, 'rb') as f:
            files = {'file': (audio_filename, f, 'audio/wav')}
            response = requests.post(API_URL, files=files)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # --- NEW: Check for a server-side error message ---
            if result.get("error"):
                print("\n" + "="*50)
                print("❌ SERVER-SIDE TRANSCRIPTION FAILED")
                print("="*50)
                print(f"   The STT service returned this error: {result['error']}")
            
            # If no error, print the success
            elif result.get("transcription") is not None:
                print("\n" + "="*50)
                print("✅ TRANSCRIPTION SUCCESSFUL")
                print("="*50)
                print(f"🗣️ Text: '{result.get('transcription')}'")
                print(f"⏱️ Processing Time: {result.get('processing_time_seconds')} seconds")
            else:
                print("\n" + "="*50)
                print("❌ UNKNOWN ERROR")
                print("="*50)
                print(f"   The server returned an unexpected JSON: {result}")
            # --- END OF NEW CODE ---
                
        else:
            print(f"❌ Error: Server returned status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Could not connect to the server.")
        print("Please make sure your 'stt_service.py' is running in another terminal.")
    finally:
        # Clean up the created audio file
        if os.path.exists(audio_filename):
            os.remove(audio_filename)
            print(f"\n🗑️ Cleaned up temporary file '{audio_filename}'.")