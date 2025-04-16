from flask import Flask, render_template, request, jsonify
import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
import sys
import pyttsx3
from pathlib import Path
import requests
import io
import pytesseract
import faster_whisper
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import time
import threading
import pandas as pd
import os
import json

app = Flask(__name__)

camera_url = "http://192.168.1.12:2000/capture"
camera_url_sensor = camera_url
current_mode = "deteksi wajah"
hasil_terakhir = "Belum ada hasil."
upload_data_mode = "semua"

engine = pyttsx3.init()
engine.setProperty('rate', 150)

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
model_emotion.load_state_dict(torch.load("model/emotion_model.pth", map_location=device))
model_emotion.eval()

transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((48, 48)),
    transforms.ToTensor()
])
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
face_cascade = cv2.CascadeClassifier("model/haarcascade_frontalface_default.xml")

yolov5_path = Path("model/yolov5")
sys.path.append(str(yolov5_path))
from utils.torch_utils import select_device
from utils.general import non_max_suppression, scale_boxes
from utils.augmentations import letterbox
from models.common import DetectMultiBackend

weights = yolov5_path / "yolov5s.pt"
device_yolo = select_device('')
model_yolo = DetectMultiBackend(weights, device=device_yolo)
stride, names, pt = model_yolo.stride, model_yolo.names, model_yolo.pt

whisper_model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")

def audio_to_text(audio_data):
    try:
        audio_file = io.BytesIO(audio_data)
        segments, info = whisper_model.transcribe(audio_file)
        text = ""
        for segment in segments:
            text += segment.text
        return text.strip()
    except Exception as e:
        return f"Error: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    global current_mode, hasil_terakhir, upload_data_mode
    if request.method == "POST":
        if 'audio' in request.files:
            audio_data = request.files['audio'].read()
            text = audio_to_text(audio_data)
            print("Teks yang dikenali:", text)
            pilihan = ["tanya", "baca", "foto", "wajah"]
            if text.lower() in pilihan:
                current_mode = text.lower().replace("tanya","deteksi objek").replace("foto", "deteksi objek").replace("wajah", "deteksi wajah").replace("baca", "baca teks")

    return render_template("index.html", mode=current_mode, hasil=hasil_terakhir)

@app.route("/ambil_foto", methods=["POST"])
def ambil_foto():
    global hasil_terakhir
    try:
        print(f"Mengambil gambar dari: {camera_url}")
        response = requests.get(camera_url, timeout=10)
        print(f"Status Code ESP32: {response.status_code}")

        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            print("Gambar berhasil diambil. Mengirim ke /proses_gambar")
            send_response = requests.post(
                "http://192.168.1.12:2000/proses_gambar",
                files={"image": ("frame.jpg", image_bytes, "image/jpeg")},
                data={"mode": current_mode}
            )
            print(f"Status Code Flask Internal: {send_response.status_code}")
            print(f"Response Flask: {send_response.text}")
            if send_response.status_code == 200:
                hasil_terakhir = send_response.json()["hasil"]
                return jsonify({"status": "sukses", "hasil": hasil_terakhir})
            else:
                return jsonify({"status": "gagal", "error": "Gagal memproses gambar."})
        else:
            return jsonify({"status": "gagal", "error": "Gagal mengambil gambar dari ESP32-CAM."})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/proses_gambar", methods=["POST"])
def proses_gambar():
    file = request.files['image']
    mode = request.form.get('mode')
    img = Image.open(file.stream).convert('RGB')
    frame = np.array(img)

    response = ""

    if mode == "deteksi wajah":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            roi = gray[y:y + h, x:x + w]
            pil_img = Image.fromarray(roi)
            img_tensor = transform(pil_img).unsqueeze(0).to(device)
            with torch.no_grad():
                output = model_emotion(img_tensor)
                _, predicted = torch.max(output, 1)
                label = emotion_labels[predicted.item()]
                response_line = f"Wajah: {label}"
                response += response_line + "\n"
                engine.say(response_line)

    elif mode == "deteksi objek":
        img_yolo = letterbox(frame, 640, stride=stride, auto=True)[0]
        img_yolo = img_yolo.transpose((2, 0, 1))[::-1]
        img_yolo = np.ascontiguousarray(img_yolo)
        img_yolo = torch.from_numpy(img_yolo).to(device_yolo).float() / 255.0
        if img_yolo.ndimension() == 3:
            img_yolo = img_yolo.unsqueeze(0)

        pred = model_yolo(img_yolo, augment=False)
        pred = non_max_suppression(pred, 0.25, 0.45)
        for det in pred:
            if len(det):
                for *xyxy, conf, cls in reversed(det):
                    label = names[int(cls)]
                    response_line = f"Objek: {label}"
                    response += response_line + "\n"
                    engine.say(response_line)

    elif mode == "baca teks":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang='ind+eng').strip()
        response = f"Teks Terbaca:\n{text}"
        if text:
            engine.say(text)

    engine.runAndWait()
    return jsonify({"hasil": response})

data_file = "data_penggunaan.csv"

if not os.path.exists(data_file):
    df_init = pd.DataFrame(columns=["timestamp", "komponen"])
    df_init.to_csv(data_file, index=False)

def get_mongo_client():
    url = "mongodb+srv://meraXi:1234@sicbatch6.1o8uifx.mongodb.net/?retryWrites=true&w=majority&appName=SICBATCH6"
    client = MongoClient(url, server_api=ServerApi('1'))
    client.admin.command('ping')
    return client

def kirim_data_ke_ubidots(payload):
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/spider-sense/"
    headers = {"X-Auth-Token": "BBUS-5mJfbNMiM5BrRSQOWiIO4H0qLH0qJi", "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Data Ubidots terkirim: {payload}")
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengirim data Ubidots: {e}")
        if response is not None:
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")

def kirim_data_otomatis():
    global upload_data_mode
    while True:
        try:
            client = get_mongo_client()
            db = client['SPIDER-SENSE']
            penggunaan_collection = db['PenggunaanAlat']
            emosi_collection = db['DataEmosi']

            now = datetime.now()
            hari = now.strftime("%A")
            tanggal = now.strftime("%Y-%m-%d")
            waktu = now.strftime("%H.%M")
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            jumlah_foto = 0
            waktu_mulai = time.time()
            while time.time() - waktu_mulai < 5:
                try:
                    response = requests.get(camera_url_sensor, timeout=1)
                    if response.status_code == 200:
                        jumlah_foto += 1
                except requests.exceptions.RequestException:
                    pass

            try:
                esp32_response = requests.get(camera_url_sensor, timeout=5)
                if esp32_response.status_code == 200 and "application/json" in esp32_response.headers.get("Content-Type", ""):
                    try:
                        esp32_data = json.loads(esp32_response.text)
                        esp32_status = "Alat Hidup"
                    except json.JSONDecodeError:
                        esp32_data = {}
                        esp32_status = "Alat Hidup, Data JSON Error"
                else:
                    esp32_status = "Alat Mati"
                    esp32_data = {}
            except requests.exceptions.RequestException:
                esp32_status = "Alat Mati"
                esp32_data = {}

            data = {
                "timestamp": timestamp,
                "status": esp32_status,
                "jumlah_foto": jumlah_foto,
                "mode": upload_data_mode,
                "kamera": esp32_data
            }

            kirim_data_ke_ubidots(data)

            df = pd.read_csv(data_file)
            df = df.append({"timestamp": timestamp, "komponen": "kamera " + esp32_status}, ignore_index=True)
            df.to_csv(data_file, index=False)

            time.sleep(5)

        except Exception as e:
            print(f"Error dalam pengiriman data otomatis: {e}")

thread = threading.Thread(target=kirim_data_otomatis)
thread.daemon = True
thread.start()

if __name__ == "__main__":
    app.run(host="192.168.1.12", port=2000, debug=True)
