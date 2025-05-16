from flask import Flask, request, jsonify, abort, send_file, make_response
import os
import threading
import time
from datetime import datetime
from utils.audio import AudioProcessor
from utils.camera import Camera
from ai.deteksiObjek import ObjectDetector
from ai.deteksiWajah import EmotionDetector
from ai.bacaTex import TextReader
from ai.tanys import GeminiAI
from databse import Database
import base64
import cv2

app = Flask(__name__)

# Inisialisasi modul
audio_processor  = AudioProcessor()
object_detector  = ObjectDetector()
emotion_detector = EmotionDetector()
text_reader      = TextReader()
gemini_ai        = GeminiAI()
database         = Database()

# Coba inisialisasi kamera
try:
    camera = Camera()
    print("✅ Modul kamera diinisialisasi")
except Exception as e:
    print(f"⚠ Gagal inisialisasi kamera: {e}")
    camera = None

current_mode = {
    "mode": None,
    "last_processed": None,
    "last_result": None,
    "last_image": None,
    "detected_image": None
}

@app.route("/set_mode/<mode>", methods=["GET"])
def set_mode(mode):
    valid_modes = ["wajah", "objek", "baca", "tanya"]
    if mode in valid_modes:
        current_mode.update({
            "mode": mode,
            "last_processed": None,
            "last_image": None,
            "detected_image": None
        })
        return jsonify({"status": "success", "mode": mode})
    return jsonify({"status": "error", "message": "Mode tidak valid"}), 400

@app.route("/mp3", methods=["GET"])
def serve_latest_mp3():
    latest = audio_processor.get_latest_audio()
    if not latest:
        return abort(404, "No audio available")
    path = os.path.join(audio_processor.AUDIO_DIR, latest)
    if not os.path.isfile(path):
        return abort(404, "File not found")

    response = make_response(send_file(
        path,
        mimetype="audio/mpeg",
        as_attachment=False,
        conditional=False
    ))
    response.headers["Content-Disposition"] = "inline"
    return response

def process_mode_image(mode, img_data):
    result = ""
    detected_image = None

    if mode == "wajah":
        result = f"Ekspresi terdeteksi: {emotion_detector.detect(img_data)}"
    elif mode == "objek":
        objects, detections = object_detector.detect(img_data)
        result = "Objek terdeteksi: " + (", ".join(objects) if objects else "tidak ada objek")
        detected_image = detections.render()[0] if detections else None
    elif mode == "baca":
        text, processed_img = text_reader.read(img_data)
        result = "Teks terbaca: " + (text if text else "tidak terdeteksi")
        detected_image = processed_img
    elif mode == "tanya":
        result = "Silakan gunakan endpoint /upload untuk berinteraksi dengan sistem."
    else:
        result = "Mode tidak dikenali."

    return result, detected_image

@app.route("/process_current_mode", methods=["GET"])
def process_current_mode():
    try:
        mode = current_mode.get("mode")
        if not mode:
            return jsonify({"status": "error", "message": "Mode belum dipilih"}), 400
        if not camera:
            return jsonify({"status": "error", "message": "Kamera tidak tersedia"}), 500

        img_data = camera.capture(mode)
        if img_data is None:
            return jsonify({
                "status": "error",
                "message": "Gagal mendapatkan gambar dari kamera",
                "details": {
                    "camera_ip": camera.CAMERA_IP,
                    "timestamp": datetime.now().isoformat()
                }
            }), 500

        result, detected_image = process_mode_image(mode, img_data)
        response_data = audio_processor.process_mode_response(mode, result, detected_image)

        # Sertakan transcript mode-based jika pernah di-upload
        response_data["transcript"] = current_mode.get("last_transcript", "")

        current_mode.update({
            "last_processed": response_data.get("audio_path"),
            "last_result": result,
            "last_image": img_data,
            "detected_image": detected_image
        })

        return jsonify({
            "status": "success",
            "data": response_data,
            "image_captured": True,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error saat memproses mode: {e}")
        return jsonify({"status": "error", "message": "Kesalahan internal", "error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_audio():
    try:
        if not request.data or len(request.data) < 1000:
            return jsonify({"status": "error", "message": "Data audio tidak valid"}), 400

        # Proses audio, ambil prompt (what you said)
        prompt, audio_path = audio_processor.process_audio_input(request.data)
        if not prompt:
            return jsonify({"status": "error", "message": "Tidak dapat mengenali suara"}), 400

        # Simpan transcript untuk mode-based
        current_mode["last_transcript"] = prompt

        app.logger.info(f"Prompt: {prompt}")
        answer = ""
        detected_image = None
        tl = prompt.lower()

        if camera:
            if "wajah" in tl:
                img = camera.capture("wajah")
                if img is not None:
                    answer = f"Ekspresi terdeteksi: {emotion_detector.detect(img)}"
                    detected_image = img
                else:
                    answer = "Gagal mendapatkan gambar wajah"
            elif "objek" in tl or "foto" in tl:
                img = camera.capture("objek")
                if img is not None:
                    objs, dets = object_detector.detect(img)
                    answer = "Objek terdeteksi: " + (", ".join(objs) if objs else "tidak ada objek")
                    detected_image = dets.render()[0] if dets else None
                else:
                    answer = "Gagal mendapatkan gambar objek"
            elif "baca" in tl:
                img = camera.capture("baca")
                if img is not None:
                    txt, proc = text_reader.read(img)
                    answer = "Teks terbaca: " + (txt if txt else "tidak terdeteksi")
                    detected_image = proc
                else:
                    answer = "Gagal mendapatkan gambar teks"
            else:
                answer = gemini_ai.ask(prompt)
        else:
            answer = gemini_ai.ask(prompt)

        # Generate TTS & simpan MP3
        response_data = audio_processor.generate_full_response(prompt, answer)

        # Sertakan transcript yang Anda ucapkan
        response_data["transcript"] = prompt

        # Sertakan image jika ada
        if detected_image is not None:
            _, buf = cv2.imencode('.jpg', detected_image)
            response_data["image_url"] = (
                "data:image/jpeg;base64," +
                base64.b64encode(buf).decode('utf-8')
            )

        database.save_interaction({
            "prompt": prompt,
            "response": answer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Error pada upload: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def background_data_task():
    while True:
        try:
            database.update_background_data()
            time.sleep(60)
        except Exception as e:
            print(f"Error di background task: {e}")

if __name__ == "__main__":
    threading.Thread(target=background_data_task, daemon=True).start()
    app.run(host="0.0.0.0", port=2000, debug=True)