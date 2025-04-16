import streamlit as st
import pandas as pd
import altair as alt
from pymongo import MongoClient

# Menghubungkan ke MongoDB
client = MongoClient("mongodb+srv://meraXi:1234@sicbatch6.1o8uifx.mongodb.net/?retryWrites=true&w=majority&appName=SICBATCH6")
db = client["SPIDER-SENSE"]
penggunaan_collection = db["PenggunaanAlat"]  
emosi_collection = db["DataEmosi"] 

st.sidebar.title("Menu")
Opsi = st.sidebar.radio("Pilih Halaman", ["Beranda", "Statistik Penggunaan Alat", "Ekspresi Wajah Pengguna", "Tanya AI"])

if Opsi == "Beranda":
    st.title("🕷️ Selamat Datang di Web Spider Sense")
    st.subheader("🤖 Asisten AI untuk Tunanetra")
    st.markdown("---")
    st.subheader("📸 Gambar Alat")
    col1, col2 = st.columns(2)
    with col1:
        st.image("gambar/alat1.jpeg", caption="Gambar 1", width=300)
        st.image("gambar/alat2.jpeg", caption="Gambar 2", width=300)
    with col2:
        st.image("gambar/alat3.jpeg", caption="Gambar 3", width=300)
        st.image("gambar/alat4.jpeg", caption="Gambar 4", width=300)
    st.markdown("-----")
    st.header("Dilengkapi dengan kamera yang dapat:")
    st.markdown("- Mendeteksi emosi wajah 👁️")
    col1, col2 = st.columns(2)
    with col1:
        st.image("gambar/imgWajah.jpg")
    with col2:
        st.image("gambar/imgWajah2.jpg")
    st.markdown("-----")
    st.markdown("- Mendeteksi objek 🎯")
    col1, col2 = st.columns(2)
    with col1:
        st.image("gambar/imgObjek.jpg")
    with col2:
        st.empty()
    st.markdown("-----")
    st.markdown("- Membaca teks lalu mengubahnya menjadi suara 🗣️")
    col1, col2 = st.columns(2)
    with col1:
        st.image("gambar/imgTeks.jpg")
    with col2:
        st.empty()
    st.markdown("-----")
    st.header("Web Interaktif Untuk Memantau Alat dan Pengguna")
    col1, col2 = st.columns(2)
    st.image("gambar/ubidot.png")
    st.markdown("-----")
    st.header("Alat Memiliki Hasil yang Dapat Didengar Melalui Speaker")
    col1, col2 = st.columns(2)
    with col1:
        st.image("gambar/speaker.jpeg")
    with col2:
        st.empty()
    st.markdown("---")
    st.subheader("📬 Kontak Developer")
    st.write("dibuat oleh MERA XI")
    st.write("EMAIL: merasmkn2@gmail.com")
    st.write("WhatsApp: 085877158827")
    st.markdown("---")
    st.write("© 2025 MERA XI Dev. All rights reserved.")
    st.markdown("<center><small>--Spider Sense - Asisten AI untuk Tunanetra--</small></center>", unsafe_allow_html=True)

elif Opsi == "Statistik Penggunaan Alat":
    st.title("📊 Statistik Penggunaan Alat")
    try:
        # Mengambil data dari MongoDB
        data_penggunaan = list(penggunaan_collection.find())
        if data_penggunaan:
            df_penggunaan = pd.DataFrame(data_penggunaan)
            df_penggunaan['timestamp'] = pd.to_datetime(df_penggunaan['timestamp'])
            df_penggunaan['tanggal'] = df_penggunaan['timestamp'].dt.date
            df_penggunaan['hari'] = df_penggunaan['timestamp'].dt.day_name()
            st.subheader("Statistik Harian")
            penggunaan_harian = df_penggunaan.groupby(['tanggal', 'komponen']).size().unstack(fill_value=0)
            st.bar_chart(penggunaan_harian)
            st.subheader("Statistik Mingguan")
            penggunaan_mingguan = df_penggunaan.groupby('hari').size().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                fill_value=0
            )
            penggunaan_mingguan.index = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            st.line_chart(penggunaan_mingguan)
            st.subheader("Tabel Data Penggunaan")
            st.dataframe(df_penggunaan)
            csv_download = df_penggunaan.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data Penggunaan (CSV)",
                data=csv_download,
                file_name="data_penggunaan.csv",
                mime='text/csv'
            )
        else:
            st.error("Data penggunaan tidak ditemukan di MongoDB.")
    except Exception as e:
        st.error(f"Terjadi error saat mengambil data: {e}")

elif Opsi == "Ekspresi Wajah Pengguna":
    st.title("😊 Statistik Ekspresi Wajah Pengguna")
    try:
        # Mengambil data dari MongoDB
        data_emosi = list(emosi_collection.find())
        if data_emosi:
            df_emosi = pd.DataFrame(data_emosi)
            st.subheader("Distribusi Ekspresi Wajah")
            chart = alt.Chart(df_emosi).mark_bar().encode(
                x='Ekspresi',
                y='Jumlah',
                tooltip=['Ekspresi', 'Jumlah']
            ).interactive()
            st.altair_chart(chart)
            st.subheader("Tabel Data Ekspresi")
            st.dataframe(df_emosi)
            csv_download = df_emosi.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data Ekspresi (CSV)",
                data=csv_download,
                file_name="data_emosi.csv",
                mime='text/csv'
            )
        else:
            st.error("Data ekspresi wajah tidak ditemukan di MongoDB.")
    except Exception as e:
        st.error(f"Terjadi error saat mengambil data: {e}")

elif Opsi == "Tanya AI":
    import google.generativeai as genai
    from gtts import gTTS
    import base64
    import os
    
    # Konfigurasi Gemini AI
    genai.configure(api_key="AIzaSyBPddmxJ5KDxoqhm0FfhUUU9IWtek0dyFs")  # Ganti dengan API key Anda
    
    # Inisialisasi model Gemini
    @st.cache_resource
    def load_gemini_model():
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Anda adalah asisten AI yang membantu pengguna dalam bahasa Indonesia."
        )
    
    model = load_gemini_model()
    
    # Tampilan Streamlit
    st.title("🧠 Chatbot AI Bahasa Indonesia")
    
    def text_to_speech(text, lang='id'):
        """Konversi teks ke suara dan putar otomatis"""
        tts = gTTS(text=text, lang=lang)
        tts.save("response.mp3")
        
        with open("response.mp3", "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <audio autoplay>
          <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        os.remove("response.mp3")  # Hapus file setelah digunakan
    
    # Fungsi Chatbot
    def tanya_model():
        with st.form("chat_form"):
            user_input = st.text_input("Tanyakan sesuatu:")
            submit_button = st.form_submit_button("Kirim")
            
            if submit_button and user_input:
                with st.spinner("Memproses..."):
                    try:
                        response = model.generate_content(
                            user_input,
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=500,
                                temperature=0.7
                            )
                        )
                        
                        st.markdown("**🤖 Jawaban:**")
                        st.write(response.text)
                        
                        # Konversi ke suara
                        text_to_speech(response.text)
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    tanya_model()
