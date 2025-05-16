#include <WiFi.h>
#include <HTTPClient.h>
#include "Audio.h"
#include "driver/i2s.h"

// ——— WiFi & Server Config ———
const char* ssid       = "enumatechz";
const char* password   = "3numaTechn0l0gy";
const char* mp3Url     = "http://192.168.1.19:2000/mp3";

// ——— I2S Speaker (MAX98357A) ———
#define I2S_DOUT  25
#define I2S_BCLK  27
#define I2S_LRC   26

Audio audio;
unsigned long lastCheckMs    = 0;
const unsigned long interval = 5000;  // cek setiap 5 detik
long lastContentLength       = -1;

// ——— Forward declaration ———
long getMp3ContentLength();
void playMp3Stream();

void setup() {
  Serial.begin(115200);
  delay(500);

  // 1) Connect Wi-Fi
  Serial.print("🔌 Connecting to WiFi ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("✅ WiFi OK, IP=");
  Serial.println(WiFi.localIP());

  // 2) Setup I2S speaker pins
  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(90);

  // 3) Ambil initial Content-Length supaya tidak auto-play saat start
  lastContentLength = getMp3ContentLength();
  Serial.printf("Initial MP3 size = %ld bytes\n", lastContentLength);
}

void loop() {
  unsigned long now = millis();
  if (now - lastCheckMs >= interval) {
    lastCheckMs = now;

    long len = getMp3ContentLength();
    if (len > 0) {
      Serial.printf("Check MP3 size: %ld\n", len);
      if (len != lastContentLength) {
        Serial.println("🔔 Terdeteksi file baru! Memutar MP3...");
        playMp3Stream();
        lastContentLength = len;
      }
    } else {
      Serial.println("⚠ Gagal cek MP3");
    }
  }
}

// ——— HEAD request untuk Content-Length ———
long getMp3ContentLength() {
  HTTPClient http;
  http.begin(mp3Url);
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  int code = http.sendRequest("HEAD");
  long len = -1;
  if (code == HTTP_CODE_OK) {
    len = http.getSize();
  } else {
    Serial.printf("HEAD gagal, HTTP Code: %d\n", code);
  }
  http.end();
  return len;
}

// ——— Streaming & Playback dengan debug logs ———
void playMp3Stream() {
  Serial.println("▶️ playMp3Stream(): re-init speaker pins");
  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(90);

  Serial.printf("▶️ Connecting to %s\n", mp3Url);
  bool ok = audio.connecttohost(mp3Url);
  Serial.printf("    connecttohost returned %s\n", ok ? "true" : "false");
  if (!ok) {
    Serial.println("❌ Gagal connecttohost()");
    return;
  }

  Serial.println("🔊 Streaming started, entering loop...");
  unsigned long start = millis();
  unsigned long lastDot = start;
  while (audio.isRunning()) {
    audio.loop();
    // print dot setiap 1 detik untuk tunjukkan loop masih terjadi
    if (millis() - lastDot > 1000) {
      Serial.print(".");
      lastDot = millis();
    }
  }
  Serial.println("\n✅ Playback finished");
  audio.stopSong();
}