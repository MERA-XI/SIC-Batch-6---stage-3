import camera       # Modul untuk mengakses kamera ESP32-CAM
import network      # Modul untuk koneksi WiFi
import socket       # Modul untuk membuat server HTTP
import time         # Modul untuk delay/waktu

# Inisialisasi kamera (default ESP32-CAM)
try:
    camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)  # Init kamera dengan format JPEG, gunakan PSRAM
    camera.framesize(camera.FRAME_VGA)       # Set resolusi VGA (640x480)
    camera.quality(10)                       # Set kualitas gambar (0-63, semakin kecil semakin bagus)
    camera.speffect(camera.EFFECT_NONE)      # Tidak pakai efek khusus
    camera.whitebalance(camera.WB_NONE)      # White balance otomatis
    camera.saturation(0)                     # Saturasi warna normal
    camera.brightness(0)                     # Brightness normal
    camera.contrast(0)                       # Kontras normal
    camera.flip(0)                           # Tidak flip gambar vertikal
    camera.mirror(1)                         # Mirror gambar horizontal (1 = aktif)
    print("✅ Kamera berhasil diinisialisasi.")
except Exception as e:
    print("❌ Gagal inisialisasi kamera:", e)
    raise SystemExit()  # Keluar program jika kamera gagal init

# Konfigurasi Wi-Fi
ssid = "enumatechz"         # Nama jaringan WiFi
password = "3numaTechn0l0gy"  # Password WiFi

wifi = network.WLAN(network.STA_IF)  # Buat objek WiFi dalam mode Station (bukan AP)
wifi.active(True)                    # Aktifkan WiFi
wifi.connect(ssid, password)         # Hubungkan ke jaringan

print("🔌 Menghubungkan ke Wi-Fi...")
while not wifi.isconnected():        # Tunggu sampai terhubung
    time.sleep(1)                    # Delay 1 detik

ip = wifi.ifconfig()[0]              # Dapatkan alamat IP
print("📶 Terhubung ke Wi-Fi. IP Address:", ip)

# Membuat server HTTP
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]  # Bind ke semua interface, port 80
s = socket.socket()                   # Buat socket TCP
s.bind(addr)                          # Bind ke alamat
s.listen(1)                           # Listen maks 1 koneksi

print("🌐 Server berjalan di http://{}/".format(ip))

# Loop server HTTP
while True:
    try:
        cl, addr = s.accept()         # Terima koneksi masuk
        print("📥 Permintaan dari", addr)
        request = cl.recv(1024)       # Baca request (maks 1024 bytes)
        
        # Ambil gambar dari kamera
        buf = camera.capture()        # Capture foto ke buffer
        
        # Kirim header HTTP
        cl.send(b"HTTP/1.1 200 OK\r\n")           # Status OK
        cl.send(b"Content-Type: image/jpeg\r\n")   # Header tipe konten
        cl.send("Content-Length: {}\r\n".format(len(buf)).encode())  # Ukuran gambar
        cl.send(b"\r\n")                           # Baris kosong penutup header
        cl.send(buf)                               # Kirim data gambar
        cl.close()                                 # Tutup koneksi
    except Exception as e:
        print("⚠ Kesalahan saat melayani permintaan:", e)
