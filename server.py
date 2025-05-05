import os
import io
import time
import threading
import requests
import cv2
from threading import Lock
import torch
import numpy as np
import google.generativeai as genai
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_file
from PIL import Image
from torchvision import transforms
from gtts import gTTS
import speech_recognition as sr
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from yolov5 import YOLOv5
import easyocr

# ==================== KONFIGURASI AWAL ====================

app = Flask(__name__)

# ========== Konfigurasi Direktori ========== #
AUDIO_DIR = "audio_storage"
PROMPT_DIR = "prompts"
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(PROMPT_DIR, exist_ok=True)

# Variabel global dengan lock
last_played = None
is_playing = False
last_audio_path = None
lock = Lock()

# ==================== INISIALISASI MODEL ====================

# 1. Model YOLOv5
DIRECTORIES = {
    'models': "model"
}
os.makedirs(DIRECTORIES['models'], exist_ok=True)

YOLOV5_MODEL_PATH = os.path.join(DIRECTORIES['models'], "yolov5n.pt")
if not os.path.exists(YOLOV5_MODEL_PATH):
    raise FileNotFoundError(f"Model YOLOv5 tidak ditemukan di {YOLOV5_MODEL_PATH}")

yolov5_model = YOLOv5(YOLOV5_MODEL_PATH, device='cpu')

# 2. Model Deteksi Emosi
class SmallEmotionCNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(32, 64, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
        )
        self.fc = torch.nn.Sequential(
            torch.nn.Linear(64 * 12 * 12, 128), torch.nn.ReLU(),
            torch.nn.Linear(128, 7)
        )

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_emotion = SmallEmotionCNN().to(device)
model_emotion.load_state_dict(torch.load(os.path.join(DIRECTORIES['models'], "emotion_model.pth"), map_location=device))
model_emotion.eval()
emotion_labels = ['marah', 'jijik', 'takut', 'senang', 'sedih', 'kaget', 'netral']

# Transformasi gambar untuk model emosi
transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((48, 48)),
    transforms.ToTensor()
])

# 3. Model Deteksi Teks Real-time
class RealTimeTextDetector:
    def __init__(self, language='en+id', min_confidence=0.5):
        self.language = language
        self.min_confidence = min_confidence
        self.reader = easyocr.Reader(language.split('+'))
        self.last_results = []
        self.processing_fps = 0
        self.last_process_time = 0

    def _image_preprocessing(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        return sharpened

    def detect_text(self, frame):
        start_time = time.time()
        processed = self._image_preprocessing(frame)
        
        try:
            results = self.reader.readtext(processed)
            filtered_results = [(box, text, conf) for (box, text, conf) in results if conf > self.min_confidence]
            
            process_time = time.time() - start_time
            self.processing_fps = 1.0 / process_time if process_time > 0 else 0
            self.last_results = filtered_results
            
            result_frame = self._draw_results(frame.copy())
            return filtered_results, result_frame
            
        except Exception as e:
            print(f"Error dalam OCR: {e}")
            return [], frame

    def _draw_results(self, frame):
        for (box, text, conf) in self.last_results:
            box = np.array(box, dtype=np.int32)
            cv2.polylines(frame, [box], True, (0, 255, 0), 2)
            
            (x, y) = (box[0][0], box[0][1])
            (w, h) = (box[2][0] - box[0][0], box[2][1] - box[0][1])
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y - 30), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            cv2.putText(frame, f"{text} ({conf:.2f})", (x, y - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame

text_detector = RealTimeTextDetector(language='en+id')

# ==================== KONFIGURASI LAYANAN EKSTERNAL ====================

# ESP32-CAM
CAMERA_BASE = "http://192.168.43.248/capture"
CAP_ENDPOINTS = {
    "wajah": f"{CAMERA_BASE}",
    "objek": f"{CAMERA_BASE}",
    "baca": f"{CAMERA_BASE}",
    "stream": f"{CAMERA_BASE}"
}

# Gemini AI
genai.configure(api_key="AIzaSyBPddmxJ5KDxoqhm0FfhUUU9IWtek0dyFs")
gemini = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="Anda adalah asisten AI bahasa Indonesia, jawab ringkas tanpa tanda baca"
)

# MongoDB
MONGO_URI = "mongodb+srv://meraXi:1234@sicbatch6.1o8uifx.mongodb.net/?retryWrites=true&w=majority"
UBIDOTS_TOKEN = "BBUS-5mJfbNMiM5BrRSQOWiIO4H0qLH0qJi"

def get_mongo_client():
    """Membuat koneksi baru ke MongoDB"""
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"Gagal terhubung ke MongoDB: {e}")
        return None

def send_ubidots(payload):
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/spider-sense/"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error saat mengirim data ke Ubidots: {e}")
        return False

# ==================== FUNGSI UTILITAS ====================

def get_image_from_esp32(endpoint):
    try:
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 200:
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            return img if img is not None else None
        return None
    except Exception as e:
        print(f"Exception when getting image: {e}")
        return None

def detect_expression(img_data):
    if isinstance(img_data, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB))
    else:
        img = img_data
    
    img = img.convert('L')
    t = transform(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        out = model_emotion(t)
        _, p = torch.max(out, 1)
        
    return emotion_labels[p.item()]

def cleanup_old_audio_files(max_files=10):
    mp3_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    if len(mp3_files) > max_files:
        mp3_files.sort(key=lambda f: os.path.getmtime(os.path.join(AUDIO_DIR, f)))
        for old_file in mp3_files[:-max_files]:
            try:
                os.remove(os.path.join(AUDIO_DIR, old_file))
            except Exception as e:
                print(f"Gagal menghapus file audio lama: {e}")

def detect_objects(img_data):
    results = yolov5_model.predict(img_data)
    return [f"{results.names[int(cls)]} ({float(conf):.2f})" 
            for *_, conf, cls in results.pred[0]], results

def extract_text(img_data):
    results, processed_img = text_detector.detect_text(img_data)
    texts = [text for (_, text, _) in results]
    return " ".join(texts) if texts else "Tidak ada teks terdeteksi", processed_img

def stt_from_wav(filepath):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filepath) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="id-ID")
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return f"Error: {e}"

def generate_tts(text, lang='id'):
    tts = gTTS(text=text, lang=lang)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

def get_latest_audio_file():
    mp3_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    if not mp3_files:
        return None
    latest = max(mp3_files, key=lambda f: os.path.getmtime(os.path.join(AUDIO_DIR, f)))
    return os.path.join(AUDIO_DIR, latest)

# ==================== SISTEM MODE ALAT ====================

current_mode = {
    "mode": None,
    "last_processed": None,
    "last_result": None,
    "last_image": None,
    "detected_image": None
}

# ==================== BACKGROUND TASK ====================

def background_data():
    days_map = {
        "Monday": "senin", "Tuesday": "selasa", "Wednesday": "rabu",
        "Thursday": "kamis", "Friday": "jumat", "Saturday": "sabtu", "Sunday": "minggu"
    }

    while True:
        try:
            now = datetime.now()
            day = days_map.get(now.strftime("%A"), "unknown")
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            
            client = get_mongo_client()
            if client:
                db = client['SPIDER-SENSE']
                
                # Simpan data penggunaan alat
                db['PenggunaanAlat'].insert_one({
                    "hari": day,
                    "timestamp": timestamp,
                    "komponen": "Alat Aktif",
                    "jumlah": 1
                })
                
                # Simpan data emosi dummy (contoh)
                db['DataEmosi'].insert_one({
                    "Ekspresi": "netral",
                    "Jumlah": 1,
                    "hari": day,
                    "timestamp": timestamp
                })
                
                client.close()
            
            # Kirim data ke Ubidots
            send_ubidots({
                day: {"value": 1},
                "jumlah_emosi": {"value": 1},
                "netral": {"value": 1}
            })
            
        except Exception as e:
            print(f"Error dalam background task: {e}")
        
        time.sleep(60)  # Update setiap 1 menit

# ==================== ROUTES UTAMA ====================

@app.route("/set_mode/<mode>", methods=["GET"])
def set_mode(mode):
    valid_modes = ["wajah", "objek", "baca", "tanya"]
    if mode in valid_modes:
        current_mode["mode"] = mode
        current_mode["last_processed"] = None
        current_mode["last_image"] = None
        current_mode["detected_image"] = None
        return jsonify({"status": "success", "mode": mode})
    return jsonify({"status": "error", "message": "Mode tidak valid"}), 400

@app.route("/process_current_mode", methods=["GET"])
def process_current_mode():
    try:
        if not current_mode["mode"]:
            return jsonify({"error": "Tidak ada mode yang dipilih"}), 400

        mode = current_mode["mode"]
        result = ""
        detected_image = None
        
        img_data = get_image_from_esp32(CAP_ENDPOINTS[mode])
        if img_data is None:
            result = "Gagal mendapatkan gambar dari kamera"
        else:
            current_mode["last_image"] = img_data
            
            if mode == "wajah":
                result = f"Ekspresi terdeteksi: {detect_expression(img_data)}"
            elif mode == "objek":
                objects, detections = detect_objects(img_data)
                result = "Objek terdeteksi: " + (", ".join(objects) if objects else "tidak ada objek")
                detected_image = detections.render()[0]  # Gambar dengan bounding box
            elif mode == "baca":
                text, processed_img = extract_text(img_data)
                result = "Teks terbaca: " + (text if text else "tidak terdeteksi")
                detected_image = processed_img
            elif mode == "tanya":
                result = "Silakan gunakan endpoint /upload untuk berinteraksi dengan sistem"
        
        # Generate audio response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp3_path = os.path.join(AUDIO_DIR, f"mode_{mode}_{timestamp}.mp3")
        audio_buffer = generate_tts(result)
        
        with open(mp3_path, 'wb') as f:
            f.write(audio_buffer.getbuffer())
        
        # Update current mode state
        current_mode.update({
            "last_processed": mp3_path,
            "last_result": result,
            "detected_image": detected_image
        })
        
        response_data = {
            "status": "success",
            "result": result,
            "audio_url": f"/get_mode_audio?t={timestamp}",
        }
        
        if detected_image is not None:
            _, buffer = cv2.imencode('.jpg', detected_image)
            response_data["image_url"] = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_mode_audio", methods=["GET"])
def get_mode_audio():
    if not current_mode["last_processed"]:
        return jsonify({"error": "Belum ada hasil pemrosesan"}), 404

    try:
        return send_file(current_mode["last_processed"], mimetype="audio/mpeg")
    except FileNotFoundError:
        return jsonify({"error": "File audio tidak ditemukan"}), 404

@app.route("/upload", methods=["POST"])
def upload_audio():
    global is_playing, last_audio_path, last_played

    with lock:
        if is_playing:
            return jsonify({
                "status": "wait",
                "message": "System sedang memproses permintaan sebelumnya"
            }), 423

        is_playing = True

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_path = os.path.join(AUDIO_DIR, f"input_{timestamp}.wav")
        
        with open(wav_path, "wb") as f:
            f.write(request.data)
        
        prompt = stt_from_wav(wav_path)
        if not prompt:
            return jsonify({"error": "Tidak dapat mengenali suara"}), 400

        answer = ""
        if "wajah" in prompt.lower():
            img_data = get_image_from_esp32(CAP_ENDPOINTS["wajah"])
            answer = f"Ekspresi terdeteksi: {detect_expression(img_data)}" if img_data else "Gagal mendapatkan gambar"
        elif "objek" in prompt.lower() or "foto" in prompt.lower():
            img_data = get_image_from_esp32(CAP_ENDPOINTS["objek"])
            objects, _ = detect_objects(img_data) if img_data else (None, None)
            answer = "Objek terdeteksi: " + (", ".join(objects) if objects else "tidak ada objek") if img_data else "Gagal mendapatkan gambar"
        elif "baca" in prompt.lower():
            img_data = get_image_from_esp32(CAP_ENDPOINTS["baca"])
            text, _ = extract_text(img_data) if img_data else (None, None)
            answer = "Teks terbaca: " + (text if text else "tidak terdeteksi") if img_data else "Gagal mendapatkan gambar"
        else:
            try:
                response = gemini.generate_content(prompt)
                answer = response.text
            except Exception as e:
                answer = "Maaf, terjadi kesalahan saat memproses pertanyaan"

        combined_response = f"Permintaan: {prompt}. {answer}"
        mp3_path = os.path.join(AUDIO_DIR, f"response_{timestamp}.mp3")
        audio_buffer = generate_tts(combined_response)
        
        with open(mp3_path, 'wb') as f:
            f.write(audio_buffer.getbuffer())
        
        cleanup_old_audio_files(max_files=10)

        with lock:
            last_audio_path = mp3_path
            last_played = None
            is_playing = False

        return jsonify({
            "status": "success",
            "audio_url": f"/mp3?t={timestamp}",
            "transcript": prompt,
            "response": answer
        })

    except Exception as e:
        with lock:
            is_playing = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mp3')
def stream_audio():
    global last_played, is_playing, last_audio_path

    last_audio_path = get_latest_audio_file()
    if not last_audio_path:
        return Response(
            generate_tts("Tidak ada audio tersedia").getvalue(),
            mimetype='audio/mpeg'
        )

    if last_audio_path == last_played:
        return Response(status=304)

    try:
        with open(last_audio_path, 'rb') as f:
            audio_data = f.read()

        last_played = last_audio_path
        is_playing = True

        def generate():
            try:
                yield audio_data
            finally:
                global is_playing
                is_playing = False

        return Response(
            generate(),
            mimetype='audio/mpeg',
            headers={
                'Content-Length': str(len(audio_data)),
                'Cache-Control': 'no-store'
            }
        )

    except Exception as e:
        return Response(
            generate_tts("Terjadi kesalahan sistem").getvalue(),
            mimetype='audio/mpeg',
            status=500
        )

# ==================== MAIN ====================

if __name__ == "__main__":
    # Jalankan background task sebagai daemon
    threading.Thread(target=background_data, daemon=True).start()
    
    # Jalankan server Flask
    app.run(host="0.0.0.0", port=2000, debug=True)
