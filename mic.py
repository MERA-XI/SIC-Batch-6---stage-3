# Impor library yang diperlukan
import network      # Untuk koneksi WiFi
import urequests    # Untuk HTTP requests ke server
import esp32        # Fungsi khusus ESP32
import machine     # Fungsi dasar hardware
import time        # Untuk delay dan timing
import os          # Untuk operasi file sistem
import math        # Fungsi matematika (sqrt untuk RMS)
from machine import I2S, Pin  # Untuk interface I2S dan pin GPIO

# Konfigurasi WiFi
SSID = "enumatechz"         # Nama jaringan WiFi
PASSWORD = "3numaTechn0l0gy" # Password WiFi
SERVER_URL = "http://192.168.43.170:5000/upload"  # Alamat server tujuan

# Konfigurasi Audio
SAMPLE_RATE = 16000         # Jumlah sample per detik (16kHz)
RECORD_TIME = 5             # Durasi rekaman (detik)
BITS_PER_SAMPLE = 16        # Resolusi audio (16-bit)
CHANNELS = 1                # Jumlah channel (mono)
BYTES_PER_SAMPLE = BITS_PER_SAMPLE // 8  # Hitung byte per sample
TOTAL_BYTES = SAMPLE_RATE * RECORD_TIME * BYTES_PER_SAMPLE  # Total data
I2S_READ_LEN = 1024         # Buffer baca I2S
VOLUME_THRESHOLD = 80       # Batas volume minimum

# Konfigurasi Pin I2S
I2S_SCK = Pin(14)  # Pin clock
I2S_WS = Pin(15)   # Pin word select
I2S_SD = Pin(34)   # Pin data input

def setup_wifi():
    """Fungsi untuk menghubungkan ke WiFi"""
    print("🔌 Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)  # Buat objek WiFi
    wlan.active(True)                    # Aktifkan WiFi
    wlan.connect(SSID, PASSWORD)         # Koneksi ke jaringan
    
    # Tunggu sampai terhubung
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    
    print("\n✅ WiFi connected!")
    print("IP:", wlan.ifconfig()[0])  # Tampilkan alamat IP

def setup_i2s():
    """Fungsi untuk setup modul I2S"""
    print("🎧 Initializing I2S...")
    i2s = I2S(
        0,                         # Gunakan I2S0
        sck=I2S_SCK,               # Pin clock
        ws=I2S_WS,                 # Pin word select
        sd=I2S_SD,                 # Pin data input
        mode=I2S.RX,               # Mode penerima (RX)
        bits=BITS_PER_SAMPLE,      # Resolusi 16-bit
        format=I2S.MONO,           # Format mono
        rate=SAMPLE_RATE,          # Sample rate 16kHz
        ibuf=4096                  # Buffer size
    )
    print("✅ I2S ready.")
    return i2s

def create_wav_header(data_size):
    """Buat header file WAV"""
    file_size = data_size + 36  # Total ukuran file
    byte_rate = SAMPLE_RATE * CHANNELS * BITS_PER_SAMPLE // 8  # Byte per detik
    block_align = CHANNELS * BITS_PER_SAMPLE // 8  # Block alignment
    
    header = bytearray(44)  # Header WAV selalu 44 byte
    # Format header sesuai spesifikasi WAV
    header[0:4] = b'RIFF'  # Chunk ID
    header[4:8] = (file_size).to_bytes(4, 'little')  # Ukuran file
    header[8:12] = b'WAVE'  # Format WAVE
    header[12:16] = b'fmt '  # Subchunk fmt
    header[16:20] = (16).to_bytes(4, 'little')  # Ukuran subchunk
    header[20:22] = (1).to_bytes(2, 'little')  # Format audio (PCM)
    header[22:24] = (CHANNELS).to_bytes(2, 'little')  # Jumlah channel
    header[24:28] = (SAMPLE_RATE).to_bytes(4, 'little')  # Sample rate
    header[28:32] = (byte_rate).to_bytes(4, 'little')  # Byte rate
    header[32:34] = (block_align).to_bytes(2, 'little')  # Block align
    header[34:36] = (BITS_PER_SAMPLE).to_bytes(2, 'little')  # Bits per sample
    header[36:40] = b'data'  # Subchunk data
    header[40:44] = (data_size).to_bytes(4, 'little')  # Ukuran data
    
    return header

def calculate_rms(samples):
    """Hitung RMS (Root Mean Square) untuk mengukur volume"""
    sum_squares = 0
    for sample in samples:
        sum_squares += sample * sample  # Jumlahkan kuadrat sample
    return math.sqrt(sum_squares / len(samples))  # Akar dari rata-rata

def record_audio(i2s, filename):
    """Fungsi untuk merekam audio ke file"""
    print(f"🎙 Recording {RECORD_TIME} seconds of audio...")
    
    total_rms = 0  # Total RMS
    blocks = 0     # Jumlah blok audio
    total_written = 0  # Total byte yang ditulis
    
    with open(filename, 'wb') as f:  # Buka file untuk ditulis
        # Tulis header kosong dulu (akan diupdate nanti)
        f.write(create_wav_header(0))
        
        # Rekam sampai dapat total byte yang dibutuhkan
        while total_written < TOTAL_BYTES:
            samples = bytearray(I2S_READ_LEN)  # Buffer untuk sample
            bytes_read = i2s.readinto(samples)  # Baca data dari I2S
            
            if bytes_read > 0:
                f.write(samples[:bytes_read])  # Tulis ke file
                total_written += bytes_read
                
                # Hitung RMS untuk blok ini
                sample_count = bytes_read // 2
                samples_int = [int.from_bytes(samples[i:i+2], 'little', signed=True) 
                              for i in range(0, bytes_read, 2)]
                rms = calculate_rms(samples_int)
                total_rms += rms
                blocks += 1
    
    # Hitung rata-rata RMS
    avg_rms = total_rms / blocks if blocks > 0 else 0
    print(f"🔊 Average RMS: {avg_rms:.2f}")
    
    # Update header WAV dengan ukuran sebenarnya
    with open(filename, 'r+b') as f:
        f.seek(0)
        f.write(create_wav_header(total_written))
    
    # Cek apakah volume cukup
    if avg_rms >= VOLUME_THRESHOLD:
        print("✅ Volume sufficient, file will be sent")
        return True
    else:
        print("🔇 Volume too low, file discarded")
        os.remove(filename)  # Hapus file jika volume kecil
        return False

def send_to_server(filename):
    """Fungsi untuk mengirim file ke server"""
    try:
        with open(filename, 'rb') as f:  # Buka file dalam mode baca
            print("📡 Sending audio to server...")
            # Kirim POST request dengan data file
            response = urequests.post(SERVER_URL, data=f)
            print(f"HTTP Code: {response.status_code}")  # Tampilkan status
            response.close()  # Tutup koneksi
    except Exception as e:
        print(f"❌ Error sending file: {e}")  # Tangani error

def setup():
    """Fungsi setup awal"""
    print("=== STARTING AUDIO SYSTEM ===")
    setup_wifi()  # Hubungkan WiFi
    i2s = setup_i2s()  # Setup I2S
    return i2s

def main():
    """Program utama"""
    i2s = setup()  # Jalankan setup
    filename = "/audio.wav"  # Nama file
    
    while True:  # Loop utama
        if record_audio(i2s, filename):  # Rekam audio
            send_to_server(filename)     # Kirim ke server jika volume cukup
        time.sleep(2)  # Jeda 2 detik

if __name__ == "__main__":
    main()  # Jalankan program utama
