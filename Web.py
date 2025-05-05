# -------------------- IMPORT LIBRARY --------------------
# Mengambil alat bantu dari pustaka Python yang diperlukan untuk aplikasi ini
import streamlit as st               # Untuk membuat tampilan web interaktif
import pandas as pd                 # Untuk mengolah data
import altair as alt                # Untuk membuat grafik yang menarik
from pymongo import MongoClient     # Untuk mengambil data dari database MongoDB

# -------------------- KONEKSI KE DATABASE --------------------
# Menghubungkan ke database MongoDB tempat data disimpan
client = MongoClient("mongodb+srv://meraXi:1234@sicbatch6.1o8uifx.mongodb.net/?retryWrites=true&w=majority&appName=SICBATCH6")
db = client["SPIDER-SENSE"]  # Nama database
penggunaan_collection = db["PenggunaanAlat"]  # Tabel untuk data pemakaian alat
emosi_collection = db["DataEmosi"]            # Tabel untuk data ekspresi wajah

# -------------------- MENU HALAMAN --------------------
# Menampilkan pilihan halaman di sisi kiri layar
st.sidebar.title("Menu")
Opsi = st.sidebar.radio("Pilih Halaman", ["Beranda", "Statistik Penggunaan Alat", "Ekspresi Wajah Pengguna", "Tanya AI"])

# -------------------- HALAMAN BERANDA --------------------
if Opsi == "Beranda":
    st.title("🕷️ Selamat Datang di Web Spider Sense")
    st.subheader("🤖 Asisten AI untuk Tunanetra")

    # Menampilkan gambar alat dan fungsinya
    st.subheader("📸 Gambar Alat")
    col1, col2 = st.columns(2)
    with col1:
        st.image("gambar/alat1.jpeg", caption="Gambar 1", width=300)
        st.image("gambar/alat2.jpeg", caption="Gambar 2", width=300)
    with col2:
        st.image("gambar/alat3.jpeg", caption="Gambar 3", width=300)
        st.image("gambar/alat4.jpeg", caption="Gambar 4", width=300)

    # Menjelaskan fitur-fitur alat beserta gambarnya
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

    # Penjelasan tentang alat dan tim pengembang
    st.markdown("-----")
    st.header("Web Interaktif Untuk Memantau Alat dan Pengguna")
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

# -------------------- HALAMAN STATISTIK PENGGUNAAN ALAT --------------------
elif Opsi == "Statistik Penggunaan Alat":
    st.title("📊 Statistik Penggunaan Alat")
    try:
        # Mengambil data dari database
        data_penggunaan = list(penggunaan_collection.find())
        if data_penggunaan:
            df_penggunaan = pd.DataFrame(data_penggunaan)

            # Mengubah kolom waktu menjadi format tanggal
            df_penggunaan['timestamp'] = pd.to_datetime(df_penggunaan['timestamp'])
            df_penggunaan['tanggal'] = df_penggunaan['timestamp'].dt.date
            df_penggunaan['hari'] = df_penggunaan['timestamp'].dt.day_name()

            # Menampilkan grafik batang berdasarkan tanggal
            st.subheader("Statistik Harian")
            penggunaan_harian = df_penggunaan.groupby(['tanggal', 'komponen']).size().unstack(fill_value=0)
            st.bar_chart(penggunaan_harian)

            # Menampilkan grafik garis berdasarkan hari
            st.subheader("Statistik Mingguan")
            penggunaan_mingguan = df_penggunaan.groupby('hari').size().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                fill_value=0
            )
            penggunaan_mingguan.index = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            st.line_chart(penggunaan_mingguan)

            # Tampilkan data mentah dan sediakan tombol untuk mengunduh
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
            st.error("Data penggunaan tidak ditemukan.")
    except Exception as e:
        st.error(f"Terjadi error saat mengambil data: {e}")

# -------------------- HALAMAN EKSPRESI WAJAH PENGGUNA --------------------
elif Opsi == "Ekspresi Wajah Pengguna":
    st.title("😊 Statistik Ekspresi Wajah Pengguna")
    try:
        data_emosi = list(emosi_collection.find())
        if data_emosi:
            df_emosi = pd.DataFrame(data_emosi)

            # Menampilkan grafik batang berdasarkan jenis emosi
            st.subheader("Distribusi Ekspresi Wajah")
            chart = alt.Chart(df_emosi).mark_bar().encode(
                x='Ekspresi',
                y='Jumlah',
                tooltip=['Ekspresi', 'Jumlah']
            ).interactive()
            st.altair_chart(chart)

            # Menampilkan tabel dan tombol unduh
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
            st.error("Data ekspresi wajah tidak ditemukan.")
    except Exception as e:
        st.error(f"Terjadi error saat mengambil data: {e}")

# -------------------- HALAMAN TANYA AI / CHATBOT --------------------
elif Opsi == "Tanya AI":
    import google.generativeai as genai  # Untuk mengakses AI Gemini
    from gtts import gTTS                # Untuk ubah teks ke suara
    import base64, os                    # Untuk pengolahan file audio

    # Mengakses AI Gemini (API Key)
    genai.configure(api_key="AIzaSyBPddmxJ5KDxoqhm0FfhUUU9IWtek0dyFs")  # Ganti dengan milikmu

    # Memanggil model Gemini sekali saja dan menyimpannya di cache
    @st.cache_resource
    def load_gemini_model():
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Anda adalah asisten AI yang membantu pengguna dalam bahasa Indonesia."
        )

    model = load_gemini_model()

    st.title("🧠 Chatbot AI Bahasa Indonesia")

    # Mengubah jawaban AI menjadi suara dan langsung diputar di halaman web
    def text_to_speech(text, lang='id'):
        # 1. Membuat suara dari teks menggunakan Google Text-to-Speech (gTTS)
        tts = gTTS(text=text, lang=lang)

        # 2. Menyimpan hasil suara ke file sementara bernama "response.mp3"
        tts.save("response.mp3")

        # 3. Membuka file audio yang baru saja dibuat
        with open("response.mp3", "rb") as audio_file:
            audio_bytes = audio_file.read()

        # 4. Mengubah data audio menjadi format base64 agar bisa ditampilkan di HTML
        b64 = base64.b64encode(audio_bytes).decode()

        # 5. Membuat HTML audio player dengan autoplay
        audio_html = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """

        # 6. Menampilkan suara di halaman web secara langsung
        st.markdown(audio_html, unsafe_allow_html=True)

        # 7. Menghapus file sementara "response.mp3"
        os.remove("response.mp3")

    # Form untuk menanyakan pertanyaan ke AI
    def tanya_model():
        # Membuat form bernama "chat_form" untuk menampung input dari pengguna
        with st.form("chat_form"):
            # Kolom input teks agar pengguna bisa mengetik pertanyaan
            user_input = st.text_input("Tanyakan sesuatu:")

            # Tombol untuk mengirim pertanyaan ke AI
            submit_button = st.form_submit_button("Kirim")

            # Jika tombol ditekan dan input tidak kosong, lanjutkan proses
            if submit_button and user_input:
                # Menampilkan animasi "Memproses..." saat AI sedang berpikir
                with st.spinner("Memproses..."):
                    try:
                        # Mengirim pertanyaan ke model AI Gemini
                        response = model.generate_content(
                            user_input,
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=500,  # Batas panjang jawaban
                                temperature=0.7         # Kreativitas jawaban (0 = kaku, 1 = bebas)
                            )
                        )

                        # Menampilkan hasil jawaban dari AI
                        st.markdown("**🤖 Jawaban:**")
                        st.write(response.text)

                        # Memutar jawaban dalam bentuk suara
                        text_to_speech(response.text)

                    # Menangani error
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Menjalankan fungsi chatbot
    tanya_model()
