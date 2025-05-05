from flask import Flask, request
import os
import datetime
import wave
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'wav'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    if file and allowed_file(file.filename):
        # Generate a timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        
        # Save the file
        file.save(filepath)
        
        # Analyze the audio file
        try:
            analyze_audio(filepath)
        except Exception as e:
            print(f"Error analyzing audio: {e}")
        
        return 'File received successfully', 200
    
    return 'Invalid file type', 400

def analyze_audio(filepath):
    """Analyze the received WAV file"""
    print(f"\nAnalyzing audio file: {filepath}")
    
    with wave.open(filepath, 'rb') as wav_file:
        # Get audio parameters
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        print(f"Channels: {n_channels}")
        print(f"Sample width: {sample_width} bytes")
        print(f"Frame rate: {frame_rate} Hz")
        print(f"Duration: {n_frames/frame_rate:.2f} seconds")
        
        # Read audio data
        frames = wav_file.readframes(n_frames)
        
        # Convert to numpy array based on sample width
        if sample_width == 2:
            audio_data = np.frombuffer(frames, dtype=np.int16)
        elif sample_width == 1:
            audio_data = np.frombuffer(frames, dtype=np.int8)
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")
        
        # Calculate RMS (Root Mean Square) volume
        rms = np.sqrt(np.mean(np.square(audio_data)))
        print(f"RMS Volume: {rms:.2f}")
        
        # Calculate max amplitude
        max_amp = np.max(np.abs(audio_data))
        print(f"Max Amplitude: {max_amp}")
        
        # You can add more analysis here as needed

if __name__ == '__main__':
    print("Audio Receiver Server starting...")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    app.run(host='0.0.0.0', port=5000, debug=True)