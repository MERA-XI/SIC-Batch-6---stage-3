import os
import io
import time
import threading
from threading import Lock
from datetime import datetime
from gtts import gTTS
import speech_recognition as sr
import base64
import cv2

class AudioProcessor:
    def __init__(self):
        self.AUDIO_DIR = "audio_storage"
        os.makedirs(self.AUDIO_DIR, exist_ok=True)
        self.lock = Lock()
        self.is_playing = False
        self.last_audio_path = None
        self.last_played = None
     
    def process_audio_input(self, audio_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_path = os.path.join(self.AUDIO_DIR, f"input_{timestamp}.wav")
        
        with open(wav_path, "wb") as f:
            f.write(audio_data)
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        
        try:
            prompt = recognizer.recognize_google(audio, language="id-ID")
            return prompt, wav_path
        except sr.UnknownValueError:
            return None, None
        except sr.RequestError as e:
            return f"Error: {e}", None
    
    def generate_tts(self, text, lang='id'):
        tts = gTTS(text=text, lang=lang)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    
    def _play_audio(self, path):
        # Server tidak memutar audio; ESP32 yang akan memutar
        pass
    
    def process_mode_response(self, mode, result, detected_image=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp3_path = os.path.join(self.AUDIO_DIR, f"mode_{mode}_{timestamp}.mp3")
        audio_buffer = self.generate_tts(result)
        
        with open(mp3_path, 'wb') as f:
            f.write(audio_buffer.getbuffer())

        # Tidak memutar di server

        response_data = {
            "status": "success",
            "result": result,
            "audio_path": mp3_path,
            "audio_url": "/mp3"  # Route Flask untuk streaming latest MP3
        }
        
        if detected_image is not None:
            _, buffer = cv2.imencode('.jpg', detected_image)
            response_data["image_url"] = (
                "data:image/jpeg;base64," +
                base64.b64encode(buffer).decode('utf-8')
            )
        
        return response_data
    
    def generate_full_response(self, prompt, answer):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_response = f"Permintaan: {prompt}. {answer}"
        mp3_path = os.path.join(self.AUDIO_DIR, f"response_{timestamp}.mp3")
        audio_buffer = self.generate_tts(combined_response)
        
        with open(mp3_path, 'wb') as f:
            f.write(audio_buffer.getbuffer())

        # Tidak memutar di server

        self._cleanup_old_files()
        
        return {
            "status": "success",
            "audio_url": "/mp3",  # Route Flask untuk streaming latest MP3
            "transcript": prompt,
            "response": answer,
            "audio_path": mp3_path
        }
    
    def _cleanup_old_files(self, max_files=10):
        mp3_files = [
            f for f in os.listdir(self.AUDIO_DIR)
            if f.endswith('.mp3')
        ]
        if len(mp3_files) > max_files:
            mp3_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(self.AUDIO_DIR, f))
            )
            for old_file in mp3_files[:-max_files]:
                try:
                    os.remove(os.path.join(self.AUDIO_DIR, old_file))
                except Exception as e:
                    print(f"Failed to delete old audio file: {e}")
    
    def get_latest_audio(self):
        mp3_files = [
            f for f in os.listdir(self.AUDIO_DIR)
            if f.endswith('.mp3')
        ]
        if not mp3_files:
            return None
        return max(
            mp3_files,
            key=lambda f: os.path.getmtime(os.path.join(self.AUDIO_DIR, f))
        )