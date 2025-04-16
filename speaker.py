import network
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

# Pin untuk I2S (MAX98357A)
i2s = I2S(0, sck=Pin(26), ws=Pin(22), sd=Pin(25), mode=I2S.MODE_RX | I2S.MODE_TX, bits=16, format=I2S.FORMAT_I2S, rate=44100, ibuf=2048)

# Fungsi untuk mengirim data ke server Flask
def send_data_to_server(data):
    url = 'http://192.168.1.12:5000/upload_audio'  
    try:
        response = urequests.post(url, data=data)
        print('Data sent:', response.status_code)
    except Exception as e:
        print('Error sending data:', e)

# Fungsi untuk menerima data audio dari Flask dan memutar suara ke speaker
def play_audio_from_server():
    while True:
        try:
            # Mendapatkan data audio dari Flask
            response = urequests.get('http://192.168.1.12:5000/get_audio')  # Endpoint untuk mendapatkan data audio
            audio_data = response.content  # Mengambil data audio dari server

            # Mengirim data audio ke MAX98357A untuk dimainkan
            i2s.write(audio_data)
            print('Playing audio data from server')

        except Exception as e:
            print('Error receiving or playing audio:', e)

        time.sleep(0.1)  # Menunggu sebentar sebelum mencoba lagi

# Mulai untuk menerima dan memutar audio
play_audio_from_server()
