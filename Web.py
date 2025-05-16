import streamlit as st
import pandas as pd
import altair as alt
from pymongo import MongoClient
import google.generativeai as genai
from gtts import gTTS
import base64
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi halaman
st.set_page_config(
    page_title="Spider Sense - Asisten AI untuk Tunanetra",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Koneksi ke database MongoDB
@st.cache_resource
def get_database_connection():
    try:
        client = MongoClient("mongodb+srv://meraXi:1234@sicbatch6.1o8uifx.mongodb.net/?retryWrites=true&w=majority&appName=SICBATCH6")
        db = client["SPIDER-SENSE"]
        # Periksa koneksi dengan mencoba operasi sederhana
        # Ini akan memicu exception jika koneksi gagal
        client.admin.command('ping')
        return {"connected": True, "db": db, "error": None}
    except Exception as e:
        return {"connected": False, "db": None, "error": str(e)}

# Dapatkan informasi koneksi database
db_info = get_database_connection()
db = db_info["db"] if db_info["connected"] else None

# Sidebar dengan logo dan menu
with st.sidebar:
    st.title("Spider Sense")
    st.caption("Asisten AI untuk Tunanetra")
    st.divider()
    
    menu_options = {
        "Beranda": "🏠",
        "Statistik Penggunaan": "📊", 
        "Analisis Ekspresi": "😊",
        "Tanya AI": "🤖"
    }
    
    icons = [v for k, v in menu_options.items()]
    labels = [k for k, v in menu_options.items()]
    
    Opsi = st.radio(
        "Navigasi",
        labels,
        format_func=lambda x: f"{menu_options[x]} {x}"
    )
    
    st.divider()
    st.caption("© 2025 MERA XI Development")

# -------------------- HALAMAN BERANDA --------------------
if Opsi == "Beranda":
    st.title("🕷️ Spider Sense")
    st.subheader("Asisten AI Inovatif untuk Tunanetra")
    
    # Intro section
    with st.container():
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown("""
            **Spider Sense** adalah alat bantu pintar yang menggunakan teknologi kamera dan kecerdasan buatan 
            untuk membantu penyandang tunanetra "melihat" dunia dengan cara yang baru. Alat ini dapat mendeteksi 
            objek, mengenali ekspresi wajah, dan membaca teks menjadi suara.
            """)
            
            # Menampilkan metrik penggunaan utama
            if db_info["connected"]:
                try:
                    penggunaan_collection = db["PenggunaanAlat"]
                    emosi_collection = db["DataEmosi"]
                    
                    total_penggunaan = penggunaan_collection.count_documents({})
                    jenis_fitur = penggunaan_collection.distinct("komponen")
                    total_emosi = emosi_collection.count_documents({})
                    
                    metric_cols = st.columns(3)
                    with metric_cols[0]:
                        st.metric("Total Penggunaan", f"{total_penggunaan:,}")
                    with metric_cols[1]:
                        st.metric("Fitur Tersedia", len(jenis_fitur))
                    with metric_cols[2]:
                        st.metric("Ekspresi Terdeteksi", f"{total_emosi:,}")
                except Exception as e:
                    st.warning(f"Tidak dapat memuat metrik: {e}")
            
        with col2:
            st.image("img3.jpg", caption="Perangkat Spider Sense")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    # Fitur utama
    st.header("Kemampuan Utama")
    
    tab1, tab2, tab3 = st.tabs(["👁️ Deteksi Emosi Wajah", "🎯 Identifikasi Objek", "🗣️ Pembacaan Teks"])
    
    with tab1:
        cols = st.columns(2)
        with cols[0]:
            st.image("gambar/imgWajah.jpg", width=300)
        with cols[1]:
            st.subheader("Deteksi Emosi Wajah")
            st.markdown("""
            Kamera cerdas mendeteksi dan menginterpretasikan ekspresi wajah orang yang 
            berinteraksi dengan pengguna. Fitur ini membantu tunanetra memahami respons 
            emosional lawan bicara, meningkatkan kualitas interaksi sosial.
            
            **Emosi yang dapat dikenali:**
            - Senang 😊
            - Sedih 😢
            - Marah 😠
            - Terkejut 😲
            - Netral 😐
            """)
    
    with tab2:
        cols = st.columns(2)
        with cols[0]:
            st.image("gambar/imgObjek.jpg", width=300)
        with cols[1]:
            st.subheader("Identifikasi Objek")
            st.markdown("""
            Sistem vision AI mengenali objek di sekitar pengguna dan memberitahukan 
            melalui output suara. Fitur ini membantu navigasi dan pengenalan 
            lingkungan secara real-time.
            
            **Kemampuan deteksi:**
            - Objek sehari-hari
            - Rintangan dan bahaya
            - Pengenalan orang
            - Estimasi jarak
            """)
    
    with tab3:
        cols = st.columns(2)
        with cols[0]:
            st.image("gambar/imgTeks.jpg", width=300)
        with cols[1]:
            st.subheader("Pembacaan Teks")
            st.markdown("""
            Mengubah teks tercetak menjadi suara yang jelas. Memungkinkan pengguna 
            untuk 'membaca' dokumen, tanda, label produk, dan berbagai informasi tekstual lainnya.
            
            **Dukungan pembacaan:**
            - Dokumen cetakan
            - Tanda dan petunjuk
            - Label produk
            - Layar digital
            """)
    
    # Hardware
    st.markdown("<br>", unsafe_allow_html=True)  
    st.divider()
    st.header("Komponen Hardware")
    
    st.image("gambar/kamera.jpg", width=150)
    st.subheader("Kamera")
    st.markdown("""
    <div style="padding-bottom: 50px;">
    Modul kamera dengan kemampuan pemrosesan gambar real-time.
    </div>
    """, unsafe_allow_html=True)

    st.image("gambar/speaker.jpg", width=150)
    st.subheader("Speaker")
    st.markdown("""
    <div>
    Output audio untuk panduan suara yang jelas.
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.header("Dashboard Monitoring")
    st.image("gambar/ubidot.png", caption="https://stem.ubidots.com/app/dashboards/67fbb22b28c095762cc156dd")
    
    # Kontak
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    contact_col1, contact_col2 = st.columns([1, 2])
    
    with contact_col1:
        st.subheader("Kontak Pengembang")
        st.markdown("""
        **MERA XI Development Team**  
        📧 Email: merasmkn2@gmail.com  
        📱 WhatsApp: 085877158827  
        🌐 Website: www.meradev.id
        """)
    
    with contact_col2:
        with st.expander("Kirim Pesan", expanded=False):
            with st.form("contact_form"):
                nama = st.text_input("Nama Lengkap")
                email = st.text_input("Email")
                pesan = st.text_area("Pesan")
                kirim = st.form_submit_button("Kirim Pesan")
                
                if kirim:
                    st.success("Terima kasih! Pesan Anda telah dikirim.")

# -------------------- HALAMAN STATISTIK PENGGUNAAN --------------------
elif Opsi == "Statistik Penggunaan":
    st.title("📊 Analisis Penggunaan Alat")
    
    if db_info["connected"] and db is not None:
        try:
            # Dapatkan data dari database
            penggunaan_collection = db["PenggunaanAlat"]
            data_penggunaan = list(penggunaan_collection.find())
            
            if data_penggunaan:
                df_penggunaan = pd.DataFrame(data_penggunaan)
                
                try:
                    df_penggunaan['timestamp'] = pd.to_datetime(df_penggunaan['timestamp'], errors='coerce')
                    df_penggunaan = df_penggunaan.dropna(subset=['timestamp'])
                    
                    df_penggunaan['tanggal'] = df_penggunaan['timestamp'].dt.date
                    df_penggunaan['hari'] = df_penggunaan['timestamp'].dt.day_name()
                    df_penggunaan['jam'] = df_penggunaan['timestamp'].dt.hour
                except Exception as e:
                    st.error(f"Error memproses data waktu: {str(e)}")
                
                
                try:
                    min_date = df_penggunaan['tanggal'].min()
                    max_date = df_penggunaan['tanggal'].max()
                    date_range = st.date_input(
                        "Rentang Tanggal",
                        [min_date, max_date],
                        min_value=min_date,
                        max_value=max_date
                    )
                except Exception as e:
                    st.error(f"Error membuat input tanggal: {str(e)}")
                    date_range = [min_date, max_date]
                
                
                # Terapkan filter dengan penanganan error
                try:
                    if len(date_range) == 2:
                        df_filtered = df_penggunaan[
                            (df_penggunaan['tanggal'] >= date_range[0]) & 
                            (df_penggunaan['tanggal'] <= date_range[1])
                        ].copy()
                    else:
                        df_filtered = df_penggunaan.copy()
                except Exception as e:
                    st.error(f"Error menerapkan filter: {str(e)}")
                    df_filtered = df_penggunaan.copy()
                
                # Tampilkan tabel penggunaan mingguan seperti yang diminta
                st.subheader("Penggunaan Mingguan")
                
                # Mapping hari ke bahasa Indonesia
                day_mapping = {
                    'Monday': 'Senin',
                    'Tuesday': 'Selasa',
                    'Wednesday': 'Rabu',
                    'Thursday': 'Kamis',
                    'Friday': 'Jumat',
                    'Saturday': 'Sabtu',
                    'Sunday': 'Minggu'
                }
                
                # Hitung penggunaan per hari
                weekly_usage = df_filtered['hari'].value_counts().reset_index()
                weekly_usage.columns = ['hari', 'Jumlah']
                weekly_usage['hari'] = weekly_usage['hari'].map(day_mapping)
                
                # Urutkan sesuai urutan hari
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                weekly_usage = weekly_usage.set_index('hari').reindex(day_order).reset_index()
                
                # Tampilkan dalam dua format: tabel dan bar chart
                col1, col2 = st.columns(2)
                
                with col1:
                    # Tabel horizontal seperti yang diminta
                    st.markdown("**Tabel Penggunaan**")
                    st.table(weekly_usage.set_index('hari').T)
                
                with col2:
                    # Visualisasi batang
                    fig_weekly = px.bar(
                        weekly_usage,
                        x='hari',
                        y='Jumlah',
                        text_auto=True,
                        title="Penggunaan per Hari dalam Minggu"
                    )
                    st.plotly_chart(fig_weekly, use_container_width=True)
                
                
                
                # Dashboard dengan dua chart di baris pertama
                chart_cols = st.columns(2)
                
                with chart_cols[0]:
                    st.subheader("Penggunaan Harian")
                    penggunaan_harian = df_filtered.groupby(['tanggal', 'komponen']).size().reset_index(name='jumlah')
                    fig1 = px.bar(
                        penggunaan_harian, 
                        x='tanggal', 
                        y='jumlah', 
                        color='komponen',
                        title="Penggunaan per Hari",
                        labels={'tanggal': 'Tanggal', 'jumlah': 'Jumlah Penggunaan'}
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                    
                with chart_cols[1]:
                    st.subheader("Distribusi Fitur")
                    komponen_count = df_filtered['komponen'].value_counts().reset_index()
                    komponen_count.columns = ['komponen', 'jumlah']
                    
                    fig2 = px.pie(
                        komponen_count, 
                        values='jumlah', 
                        names='komponen',
                        title="Distribusi Penggunaan Fitur",
                        hole=0.4
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Chart di baris kedua
                st.subheader("Aktivitas per Jam")
                hourly_usage = df_filtered.groupby(['jam', 'komponen']).size().reset_index(name='jumlah')
                fig3 = px.line(
                    hourly_usage, 
                    x='jam', 
                    y='jumlah', 
                    color='komponen',
                    markers=True,
                    title="Pola Penggunaan Selama Hari",
                    labels={'jam': 'Jam', 'jumlah': 'Jumlah Penggunaan'}
                )
                fig3.update_layout(xaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 1))
                st.plotly_chart(fig3, use_container_width=True)
                
                # Data mentah dengan opsi download
                with st.expander("Lihat Data Mentah"):
                    st.dataframe(df_filtered, use_container_width=True)
                    
                    csv = df_filtered.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Data (CSV)",
                        data=csv,
                        file_name=f"penggunaan_alat_{date_range[0]}_sd_{date_range[1]}.csv",
                        mime="text/csv",
                    )
            else:
                st.warning("Tidak ada data penggunaan yang tersedia.")
                
        except Exception as e:
            st.error(f"Terjadi error saat memproses data: {str(e)}")
            st.exception(e)  # Tampilkan traceback untuk debugging
    else:
        st.error("Tidak dapat mengakses database. Pastikan koneksi internet dan kredensial benar.")
# -------------------- HALAMAN EKSPRESI WAJAH --------------------
elif Opsi == "Analisis Ekspresi":
    st.title("😊 Analisis Ekspresi Wajah")
    
    if db_info["connected"] and db is not None:
        try:
            emosi_collection = db["DataEmosi"]
            data_emosi = list(emosi_collection.find())
            
            if data_emosi:
                df_emosi = pd.DataFrame(data_emosi)
                
                # Preprocessing data
                if 'timestamp' in df_emosi.columns:
                    try:
                        # Konversi timestamp ke datetime dan ekstrak tanggal
                        df_emosi['timestamp'] = pd.to_datetime(df_emosi['timestamp'])
                        df_emosi['tanggal'] = df_emosi['timestamp'].dt.date
                        
                        # Pastikan tidak ada nilai NaN dalam kolom tanggal
                        df_emosi = df_emosi.dropna(subset=['tanggal'])
                    except Exception as e:
                        st.error(f"Error memproses timestamp: {str(e)}")
                        df_emosi['tanggal'] = None
                
                # Filter dan kontrol
                date_filter = None
                if 'tanggal' in df_emosi.columns and not df_emosi['tanggal'].isnull().all():
                    col1, col2 = st.columns(2)
                    with col1:
                        try:
                            min_date = df_emosi['tanggal'].min()
                            max_date = df_emosi['tanggal'].max()
                            date_filter = st.date_input(
                                "Filter Tanggal",
                                [min_date, max_date],
                                min_value=min_date,
                                max_value=max_date
                            )
                        except Exception as e:
                            st.error(f"Error membuat date input: {str(e)}")
                            date_filter = None
                    
                    # Terapkan filter jika valid
                    if date_filter and len(date_filter) == 2:
                        try:
                            df_emosi_filtered = df_emosi[
                                (df_emosi['tanggal'] >= date_filter[0]) & 
                                (df_emosi['tanggal'] <= date_filter[1])
                            ].copy()
                        except Exception as e:
                            st.error(f"Error menerapkan filter tanggal: {str(e)}")
                            df_emosi_filtered = df_emosi
                    else:
                        df_emosi_filtered = df_emosi
                else:
                    df_emosi_filtered = df_emosi
                    st.warning("Kolom tanggal tidak tersedia atau tidak valid untuk filtering")
                
                # Tampilkan metrik utama
                total_deteksi = len(df_emosi_filtered)
                emosi_dominan = "Tidak tersedia"
                
                if 'Ekspresi' in df_emosi_filtered.columns:
                    emosi_counts = df_emosi_filtered['Ekspresi'].value_counts()
                    if not emosi_counts.empty:
                        emosi_dominan = emosi_counts.idxmax()
                
                metrics_cols = st.columns(2)
                with metrics_cols[0]:
                    st.metric("Total Ekspresi Terdeteksi", total_deteksi)
                with metrics_cols[1]:
                    st.metric("Ekspresi Dominan", emosi_dominan)
                
                # Visualisasi distribusi emosi
                if 'Ekspresi' in df_emosi_filtered.columns:
                    st.subheader("Distribusi Ekspresi Wajah")
                    
                    ekspresi_count = df_emosi_filtered['Ekspresi'].value_counts().reset_index()
                    ekspresi_count.columns = ['Ekspresi', 'Jumlah']
                    
                    if not ekspresi_count.empty:
                        chart_col1, chart_col2 = st.columns(2)
                        
                        with chart_col1:
                            fig1 = px.bar(
                                ekspresi_count,
                                x='Ekspresi',
                                y='Jumlah',
                                color='Ekspresi',
                                title="Frekuensi Ekspresi",
                                text_auto=True
                            )
                            fig1.update_layout(xaxis_title="Ekspresi", yaxis_title="Jumlah Terdeteksi")
                            st.plotly_chart(fig1, use_container_width=True)
                        
                        with chart_col2:
                            fig2 = px.pie(
                                ekspresi_count,
                                values='Jumlah',
                                names='Ekspresi',
                                title="Proporsi Ekspresi",
                                hole=0.4
                            )
                            st.plotly_chart(fig2, use_container_width=True)
                
                # Tren deteksi emosi
                if 'timestamp' in df_emosi_filtered.columns and 'Ekspresi' in df_emosi_filtered.columns:
                    st.subheader("Tren Ekspresi Seiring Waktu")
                    
                    try:
                        # Agregasi data per hari dan ekspresi
                        df_tren = df_emosi_filtered.copy()
                        df_tren['Tanggal'] = df_tren['timestamp'].dt.date
                        
                        tren_harian = df_tren.groupby(['Tanggal', 'Ekspresi']).size().reset_index(name='Jumlah')
                        
                        if not tren_harian.empty:
                            fig3 = px.line(
                                tren_harian,
                                x='Tanggal',
                                y='Jumlah',
                                color='Ekspresi',
                                markers=True,
                                title="Tren Ekspresi Harian"
                            )
                            st.plotly_chart(fig3, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error membuat visualisasi tren: {str(e)}")
                
                # Analisis tingkat kepercayaan
                if 'Confidence' in df_emosi_filtered.columns and 'Ekspresi' in df_emosi_filtered.columns:
                    st.subheader("Tingkat Kepercayaan Deteksi")
                    
                    try:
                        fig4 = px.box(
                            df_emosi_filtered,
                            x='Ekspresi',
                            y='Confidence',
                            color='Ekspresi',
                            title="Distribusi Confidence per Ekspresi"
                        )
                        st.plotly_chart(fig4, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error membuat box plot confidence: {str(e)}")
                
                # Data mentah
                with st.expander("Lihat Data Mentah"):
                    st.dataframe(df_emosi_filtered, use_container_width=True)
                    
                    try:
                        csv = df_emosi_filtered.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Data Ekspresi (CSV)",
                            data=csv,
                            file_name="data_ekspresi.csv",
                            mime="text/csv",
                        )
                    except Exception as e:
                        st.error(f"Error membuat file CSV: {str(e)}")
            else:
                st.warning("Tidak ada data ekspresi wajah yang tersedia.")
                
        except Exception as e:
            st.error(f"Terjadi error saat memproses data: {str(e)}")
            st.exception(e)  # Menampilkan traceback untuk debugging
    else:
        st.error("Tidak dapat mengakses database. Pastikan koneksi internet dan kredensial benar.")

# -------------------- HALAMAN TANYA AI --------------------
elif Opsi == "Tanya AI":
    st.title("🤖 Asisten AI Spider Sense")
    
    # Konfigurasi Gemini
    @st.cache_resource
    def load_gemini_model():
        try:
            genai.configure(api_key="AIzaSyBPddmxJ5KDxoqhm0FfhUUU9IWtek0dyFs")
            return genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction="""
                Anda adalah asisten AI Spider Sense yang membantu pengguna tunanetra.
                Berikan jawaban yang jelas, ringkas dan informatif dalam bahasa Indonesia.
                Fokus pada membantu pengguna dengan informasi praktis tentang:
                1. Cara penggunaan alat Spider Sense
                2. Tips dan trik untuk penyandang tunanetra
                3. Informasi umum yang berguna dalam format yang mudah dimengerti
                """
            )
        except Exception as e:
            st.error(f"Gagal memuat model AI: {e}")
            return None
    
    model = load_gemini_model()
    
    # Fungsi untuk mengubah teks menjadi suara
    def text_to_speech(text, lang='id'):
        try:
            tts = gTTS(text=text, lang=lang)
            audio_file = "response.mp3"
            tts.save(audio_file)
            
            with open(audio_file, "rb") as file:
                audio_bytes = file.read()
            
            b64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
            <audio autoplay controls>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
            os.remove(audio_file)
            return audio_html
        except Exception as e:
            return f"Error mengubah teks ke suara: {e}"
    
    # Inisialisasi riwayat chat dalam session state jika belum ada
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Tampilkan riwayat chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "audio" in message:
                st.markdown(message["audio"], unsafe_allow_html=True)
    
    # Area input chat
    if model:
        user_input = st.chat_input("Tanyakan sesuatu tentang Spider Sense atau bantuan untuk tunanetra...")
        
        if user_input:
            # Tambahkan pesan pengguna ke riwayat
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Tampilkan pesan pengguna
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Tampilkan indikator loading
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                st.spinner("Memproses...")
                
                try:
                    # Dapatkan respons dari AI
                    response = model.generate_content(
                        user_input,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=800,
                            temperature=0.7
                        )
                    )
                    
                    response_text = response.text
                    
                    # Tampilkan respons teks
                    message_placeholder.markdown(response_text)
                    
                    # Ubah respons menjadi suara dan tambahkan ke tampilan
                    audio_html = text_to_speech(response_text)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Simpan respons ke riwayat
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response_text,
                        "audio": audio_html
                    })
                
                except Exception as e:
                    message_placeholder.error(f"Error: {str(e)}")
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": f"Maaf, terjadi kesalahan: {str(e)}"
                    })
    else:
        st.error("Model AI tidak dapat dimuat. Periksa koneksi internet dan API key.")
        
    # Tambahkan opsi untuk menghapus riwayat chat
    if st.session_state.chat_history:
        if st.button("Hapus Riwayat Chat"):
            st.session_state.chat_history = []
            st.rerun()
