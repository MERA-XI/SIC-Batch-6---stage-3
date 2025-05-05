# Impor library yang diperlukan
import network      # Untuk koneksi WiFi
import urequests    # Untuk HTTP requests ke server audio
import time         # Untuk delay dan timing
import ubinascii    # Untuk konversi data (tidak dipakai di kode ini)
from machine import Pin, I2S  # Untuk mengontrol pin dan interface I2S
import urandom      # Untuk generate angka random

# Konfigurasi WiFi
WIFI_SSID = "enumatechz"            # Nama jaringan WiFi
WIFI_PASSWORD = "3numaTechn0l0gy"   # Password WiFi

# Konfigurasi Server Audio
AUDIO_SERVER = "http://192.168.43.170:5000/mp3"  # Alamat server audio

# Konfigurasi I2S (Interface untuk audio digital)
I2S_BCLK_PIN = 27   # Pin untuk bit clock
I2S_LRC_PIN = 26     # Pin untuk left/right clock
I2S_DOUT_PIN = 25    # Pin untuk data output
SAMPLE_RATE = 16000  # Sample rate audio (16kHz)
BUFFER_SIZE = 1024   # Ukuran buffer untuk penyimpanan sementara data audio

# Inisialisasi WiFi
wifi = network.WLAN(network.STA_IF)  # Set mode Station (bukan Access Point)

def connect_wifi():
    wifi.active(True)  # Aktifkan interface WiFi
    if not wifi.isconnected():  # Jika belum terhubung
        print("Connecting to WiFi...")
        wifi.connect(WIFI_SSID, WIFI_PASSWORD)  # Coba connect
        while not wifi.isconnected():  # Tunggu sampai connected
            time.sleep(1)  # Delay 1 detik
    print("WiFi connected:", wifi.ifconfig())  # Tampilkan IP address

def setup_i2s():
    i2s = I2S(  # Buat objek I2S
        0,      # ID hardware I2S (biasanya 0)
        sck=Pin(I2S_BCLK_PIN),  # Set pin clock
        ws=Pin(I2S_LRC_PIN),    # Set pin left/right clock
        sd=Pin(I2S_DOUT_PIN),    # Set pin data output
        mode=I2S.TX,            # Mode transmit (mengirim audio)
        bits=16,               # 16 bit per sample
        format=I2S.STEREO,      # Format stereo (2 channel)
        rate=SAMPLE_RATE,       # Sample rate yang ditentukan
        ibuf=40000             # Ukuran buffer internal
    )
    return i2s  # Kembalikan objek I2S yang sudah disetup

def play_audio_from_server(i2s):
    try:
        # Tambah parameter random di URL untuk hindari cache
        url = AUDIO_SERVER + "?t=" + str(urandom.getrandbits(32))
        print("Fetching audio from:", url)
        
        # Lakukan HTTP GET request ke server
        response = urequests.get(url, stream=True)
        
        if response.status_code == 200:  # Jika request sukses (kode 200)
            print("Audio stream started")
            
            # Baca data audio secara streaming
            while True:
                data = response.raw.read(BUFFER_SIZE)  # Baca sekian byte
                if not data:  # Jika data habis
                    break      # Keluar dari loop
                i2s.write(data)  # Kirim data ke output I2S
            
            print("Audio playback finished")
        else:
            print("Failed to fetch audio:", response.status_code)
        
        response.close()  # Tutup koneksi
    except Exception as e:
        print("Error during playback:", str(e))  # Tangani error

def main():
    connect_wifi()  # Hubungkan ke WiFi
    i2s = setup_i2s()  # Setup I2S
    
    last_check_time = 0  # Waktu terakhir cek
    check_interval = 10  # Interval cek (10 detik)
    
    while True:  # Loop utama
        current_time = time.time()  # Waktu sekarang
        if current_time - last_check_time > check_interval:
            last_check_time = current_time  # Update waktu terakhir cek
            play_audio_from_server(i2s)  # Mainkan audio
        
        # Delay kecil untuk hemat CPU
        time.sleep(0.1)

if __name__ == "__main__":
    main()  # Jalankan program utama
