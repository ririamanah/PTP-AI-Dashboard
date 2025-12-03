import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="PTP AI Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- FUNGSI AUTH API (Otomatis baca Secrets atau Input Manual) ---
def configure_api():
    # Coba ambil dari Streamlit Secrets (untuk Cloud)
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    else:
        # Jika dijalankan di laptop (lokal), minta input manual
        return st.sidebar.text_input("🔑 Masukkan Google AI API Key", type="password")

# --- HEADER & JUDUL APLIKASI ---
st.title("🚀 PTP AI Dashboard")
st.markdown("""
**Sistem Analisis Cerdas Pengembang Teknologi Pembelajaran (PTP)**  
*Pusdiklat Anggaran dan Perbendaharaan*
""")
st.info("Aplikasi ini menggunakan **Artificial Intelligence** untuk menerjemahkan data pelatihan menjadi wawasan pedagogis berdasarkan teori *Behaviorism, Cognitivism, & Constructivism*.")

# --- SIDEBAR KONFIGURASI ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Sistem")
    api_key = configure_api()
    
    st.divider()
    st.header("📂 Upload Data Pelatihan")
    st.warning("Pastikan format file CSV (Delimiter titik koma ';')")
    
    # Uploaders
    file_profil = st.file_uploader("1. Data Profil Peserta (Demografi)", type=['csv'])
    file_quiz = st.file_uploader("2. Data Nilai/Kuis (Evaluasi)", type=['csv'])
    file_progress = st.file_uploader("3. Data Progress (Aktivitas Belajar)", type=['csv'])
    
    st.caption("Developed by PTP Team based on UCL Learning Framework")

# --- FUNGSI OTAK AI (GEMINI) ---
def analyze_with_ai(data_context, prompt_instructions, key):
    if not key:
        return "⚠️ Error: API Key belum terdeteksi. Mohon masukkan key di sidebar."
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-pro')
        
        # System Prompt yang disesuaikan untuk peran PTP
        system_prompt = f"""
        PERAN:
        Anda adalah Asisten Cerdas untuk Pengembang Teknologi Pembelajaran (PTP) di Kementerian Keuangan.
        Tugas Anda adalah menganalisis data pelatihan untuk memberikan rekomendasi perbaikan desain pembelajaran.

        KONTEKS DATA (Sampel):
        {data_context}

        INSTRUKSI KHUSUS:
        {prompt_instructions}

        PANDUAN TEORI BELAJAR (UCL Framework):
        1. Behaviorism: Analisis pola kebiasaan (durasi akses, frekuensi login) dan hubungannya dengan hasil (nilai).
        2. Cognitivism: Identifikasi beban kognitif (cognitive load). Apakah materi terlalu sulit/mudah?
        3. Social Constructivism: (Jika ada data diskusi) Analisis kolaborasi. Jika tidak, fokus pada konteks demografi peserta.

        OUTPUT:
        Berikan jawaban dalam Bahasa Indonesia yang formal, analitis, dan langsung pada poin rekomendasi (actionable insights).
        """
        
        with st.spinner('🤖 Asisten PTP sedang menganalisis data...'):
            response = model.generate_content(system_prompt)
        return response.text
        
    except Exception as e:
        return f"Terjadi kesalahan pada AI: {str(e)}"

# --- LOGIKA UTAMA DASHBOARD ---
if file_profil and file_quiz and file_progress:
    try:
        # 1. Loading Data
        df_profil = pd.read_csv(file_profil, sep=';')
        df_quiz = pd.read_csv(file_quiz, sep=';')
        df_progress = pd.read_csv(file_progress, sep=';')

        # Cleaning Nama Kolom (menghapus spasi berlebih)
        for df in [df_profil, df_quiz, df_progress]:
            df.columns = df.columns.str.strip()

        # Notifikasi Sukses
        st.success(f"✅ Data Pelatihan Berhasil Dimuat! Total Peserta: {len(df_profil)} orang.")

        # 2. Overview Dashboard (Visualisasi Statistik)
        st.subheader("📊 Ringkasan Statistik Pelatihan")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Peserta", len(df_profil))
        
        with col2:
            # Mencari kolom nilai secara dinamis
            nilai_cols = [c for c in df_quiz.columns if 'Quiz' in c or 'Nilai' in c or 'Score' in c]
            if nilai_cols:
                rata_rata = df_quiz[nilai_cols].mean().mean()
                st.metric("Rata-rata Nilai Kelas", f"{rata_rata:.2f}")
            else:
                st.warning("Kolom Nilai tidak ditemukan")

        with col3:
            # Mencari kolom durasi
            durasi_cols = [c for c in df_progress.columns if 'Duration' in c or 'Durasi' in c]
            if durasi_cols:
                # Konversi durasi sederhana (asumsi data string jam:menit:detik)
                st.metric("Total Kolom Durasi Terlacak", len(durasi_cols))
            else:
                st.write("Data durasi detail tersedia")

        # 3. Grafik Cepat
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("##### Sebaran Demografi (Jabatan)")
            if 'POSITION' in df_profil.columns:
                st.bar_chart(df_profil['POSITION'].value_counts().head(5))
            elif 'Jabatan' in df_profil.columns:
                st.bar_chart(df_profil['Jabatan'].value_counts().head(5))
                
        with col_g2:
            st.markdown("##### Tren Nilai Per Modul/Kuis")
            if nilai_cols:
                st.line_chart(df_quiz[nilai_cols].mean())

        # 4. FITUR PTP INTELLIGENCE (AI Analysis)
        st.divider()
        st.header("🧠 PTP Intelligence: Analisis Pedagogis")
        st.markdown("Pilih jenis analisis yang ingin Anda lakukan terhadap data pelatihan ini:")

        # Menyiapkan Data Context (Mengambil sampel data untuk dikirim ke AI agar token efisien)
        # Menggabungkan data profil, nilai, dan progress (hanya 15 baris pertama sebagai sampel pola)
        data_preview = (
            "--- DATA PROFIL ---\n" + df_profil.head(10).to_csv(index=False) + 
            "\n\n--- DATA NILAI ---\n" + df_quiz.head(10).to_csv(index=False) +
            "\n\n--- DATA PROGRESS ---\n" + df_progress.head(10).to_csv(index=False)
        )

        col_ai1, col_ai2 = st.columns([1, 2])

        with col_ai1:
            option = st.radio(
                "Pilih Fokus Analisis:",
                (
                    "🔍 Audit Performa (General)", 
                    "⚠️ Deteksi 'At-Risk' (Peserta Berisiko)", 
                    "🧠 Analisis Beban Kognitif (Materi)",
                    "💡 Rekomendasi Desain Pembelajaran"
                )
            )
            
            if st.button("Mulai Analisis AI", type="primary"):
                # Menentukan Prompt berdasarkan pilihan
                if "General" in option:
                    prompt = "Berikan analisis menyeluruh tentang efektivitas pelatihan ini. Hubungkan profil peserta dengan hasil nilai mereka."
                elif "At-Risk" in option:
                    prompt = "Identifikasi pola peserta yang memiliki nilai rendah atau aktivitas belajar yang tidak wajar. Apakah ada indikasi 'cramming' (belajar kebut semalam)? Siapa kelompok yang paling butuh intervensi?"
                elif "Beban Kognitif" in option:
                    prompt = "Analisis data durasi dan nilai. Apakah materi yang diakses paling lama menghasilkan nilai yang lebih baik (efektif) atau justru nilai rendah (terlalu sulit/membingungkan)?"
                else:
                    prompt = "Sebagai PTP, berikan 3 rekomendasi konkret untuk perbaikan kurikulum pelatihan berikutnya berdasarkan data ini."
                
                # Eksekusi AI
                hasil_analisis = analyze_with_ai(data_preview, prompt, api_key)
                
                # Simpan hasil di session state agar tidak hilang saat reload
                st.session_state['hasil_ai'] = hasil_analisis

        with col_ai2:
            st.markdown("### Hasil Analisis:")
            if 'hasil_ai' in st.session_state:
                st.markdown(st.session_state['hasil_ai'])
            else:
                st.info("👈 Klik tombol 'Mulai Analisis AI' untuk melihat wawasan dari data.")

    except Exception as e:
        st.error(f"Gagal memproses file. Pesan Error: {e}")
        st.warning("Tips: Pastikan file yang diupload adalah CSV dengan pemisah titik koma (;).")

else:
    # Tampilan Awal (Landing Page)
    st.markdown("---")
    st.subheader("👋 Selamat Datang di Dashboard PTP")
    st.write("Silakan upload data pelatihan (CSV) pada menu di sebelah kiri untuk memulai analisis.")
    st.image("https://img.freepik.com/free-vector/data-analysis-concept-illustration_114360-8023.jpg", width=400)
