import network
import ustruct
import urequests
from machine import Pin, I2S
import time

# Menghubungkan ESP32 ke Wi-Fi
ssid = 'da' 
password = 'password' 

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
    print('Connected to WiFi:', wlan.ifconfig())

connect_wifi()

# Pin untuk I2S (INMP441)
i2s = I2S(0, sck=Pin(26), ws=Pin(25), sd=Pin(22), mode=I2S.MODE_RX, bits=16, format=I2S.FORMAT_I2S, rate=44100, ibuf=1024)

# Fungsi untuk mengirim data ke server Flask
def send_data_to_server(data):
    url = 'http://192.168.1.12:5000/upload_audio' 
    try:
        response = urequests.post(url, data=data)
        print('Data sent:', response.status_code)
    except Exception as e:
        print('Error sending data:', e)

# Fungsi utama untuk merekam dan mengirim data
def record_and_send():
    while True:
        # Membaca data audio dari INMP441
        audio_data = bytearray(1024)  # Menyediakan buffer untuk data audio
        i2s.readinto(audio_data)  # Membaca data ke dalam buffer

        # Kirim data ke server
        send_data_to_server(audio_data)

        time.sleep(0.1)  # Menunggu sebentar sebelum merekam lagi

# Mulai proses perekaman dan pengiriman
record_and_send()
