import camera
import network
import socket
import time

# Inisialisasi kamera (default ESP32-CAM)
try:
    camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
    camera.framesize(camera.FRAME_VGA)
    camera.quality(10)
    camera.speffect(camera.EFFECT_NONE)
    camera.whitebalance(camera.WB_NONE)
    camera.saturation(0)
    camera.brightness(0)
    camera.contrast(0)
    camera.flip(1)
    camera.mirror(1)
    print("✅ Kamera berhasil diinisialisasi.")
except Exception as e:
    print("❌ Gagal inisialisasi kamera:", e)
    raise SystemExit()

# Konfigurasi Wi-Fi
ssid = "da"
password = "password"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

print("🔌 Menghubungkan ke Wi-Fi...")
while not wifi.isconnected():
    time.sleep(1)

ip = wifi.ifconfig()[0]
print("📶 Terhubung ke Wi-Fi. IP Address:", ip)

# Membuat server HTTP
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print("🌐 Server berjalan di http://{}/".format(ip))

# Loop server HTTP
while True:
    try:
        cl, addr = s.accept()
        print("📥 Permintaan dari", addr)
        request = cl.recv(1024)
        
        # Ambil gambar dari kamera
        buf = camera.capture()
        
        # Kirim header HTTP
        cl.send(b"HTTP/1.1 200 OK\r\n")
        cl.send(b"Content-Type: image/jpeg\r\n")
        cl.send("Content-Length: {}\r\n".format(len(buf)).encode())
        cl.send(b"\r\n")
        cl.send(buf)
        cl.close()
    except Exception as e:
        print("⚠ Kesalahan saat melayani permintaan:", e)