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

# --- FUNGSI AUTH API ---
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
st.info("Sistem ini mengintegrasikan **Learning Analytics** dengan **Standar Kompetensi JF PTP (PermenPANRB No. 3 Tahun 2021)**.")

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

# --- DATABASE KOMPETENSI PTP (Knowledge Base) ---
ptp_competency_standards = """
REFERENSI STANDAR KOMPETENSI PTP (Analisis Kebutuhan - PermenPANRB No 3 Tahun 2021):

1. PTP Ahli Pertama (Fokus: MEDIA PEMBELAJARAN):
   - Mampu melakukan analisis kebutuhan pengembangan media pembelajaran melalui proses sistematis dengan dukungan konsep teori yang relevan.
   - Mampu merekomendasikan hasil analisis kebutuhan sebagai dasar pengembangan media pembelajaran.

2. PTP Ahli Muda (Fokus: HYPERMEDIA PEMBELAJARAN):
   - Mampu menganalisis dan mengkaji kebutuhan pengembangan hypermedia pembelajaran melalui proses sistematis dengan dukungan konsep teori yang relevan.
   - Mampu merekomendasikan hasil analisis kebutuhan sebagai dasar pengembangan hypermedia.
   - Mampu melakukan studi kelayakan pengembangan hypermedia sesuai prosedur.

3. PTP Ahli Madya (Fokus: MODEL E-LEARNING & APLIKASI):
   - Mampu menganalisis dan mengkaji kebutuhan pengembangan model dan aplikasi e-pembelajaran.
   - Mampu membuat rekomendasi dari hasil analisis data kebutuhan pengembangan model dan aplikasi e-pembelajaran.
   - Mampu memimpin studi kelayakan pengembangan model dan aplikasi e-pembelajaran sesuai tahapan dan landasan teori.

4. PTP Ahli Utama (Fokus: MODEL KOMPLEKS, INOVASI & KEBIJAKAN):
   - Melakukan analisis kebutuhan sesuai pengetahuan komprehensif tentang isu publik, kebijakan program, dan peraturan terkait pengembangan model pembelajaran kompleks dan inovasi teknologi.
   - Merekomendasikan hasil analisis kebutuhan sebagai dasar pengembangan model pembelajaran kompleks dan inovasi yang dapat digunakan untuk membuat kebijakan.
"""

# --- FUNGSI OTAK AI (GEMINI) ---
def analyze_with_ai(data_context, prompt_instructions, key):
    if not key:
        return "⚠️ Error: API Key belum terdeteksi. Mohon masukkan key di sidebar."
    
    try:
        genai.configure(api_key=key)
        # Menggunakan model 'gemini-1.5-flash' yang stabil
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # System Prompt yang disesuaikan
        system_prompt = f"""
        PERAN:
        Anda adalah Konsultan Senior Pengembangan Teknologi Pembelajaran di Kemenkeu.
        Anda bekerja berpedoman pada Teori Belajar (UCL) dan Standar Kompetensi Jabatan Fungsional PTP (PermenPANRB).

        KONTEKS DATA PELATIHAN (Sampel):
        {data_context}

        REFERENSI KOMPETENSI PTP (Gunakan ini untuk membagi tugas rekomendasi):
        {ptp_competency_standards}

        INSTRUKSI TUGAS:
        {prompt_instructions}

        ATURAN JAWABAN:
        1. Analisis data menggunakan teori belajar (Behaviorism/Cognitivism).
        2. SAAT MEMBERIKAN REKOMENDASI DESAIN, petakan solusi berdasarkan jenjang PTP (Pertama/Muda/Madya/Utama).
        3. Gunakan Bahasa Indonesia formal dan profesional.
        """
        
        with st.spinner('🤖 AI sedang memetakan data ke Standar Kompetensi PTP...'):
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

        # Cleaning Nama Kolom
        for df in [df_profil, df_quiz, df_progress]:
            df.columns = df.columns.str.strip()

        # Notifikasi Sukses
        st.success(f"✅ Data Pelatihan Berhasil Dimuat! Total Peserta: {len(df_profil)} orang.")

        # 2. Overview Dashboard (Visualisasi Statistik)
        st.subheader("📊 Statistik Utama")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Mencari kolom nilai secara dinamis
            nilai_cols = [c for c in df_quiz.columns if 'Quiz' in c or 'Nilai' in c or 'Score' in c]
            if nilai_cols:
                rata_total = df_quiz[nilai_cols].mean().mean()
                st.metric("Rata-rata Nilai Kelas", f"{rata_total:.2f}")
                st.bar_chart(df_quiz[nilai_cols].mean())
            else:
                st.warning("Kolom Nilai tidak ditemukan")

        with col2:
            st.markdown("**Sebaran Jabatan Peserta**")
            if 'POSITION' in df_profil.columns:
                st.bar_chart(df_profil['POSITION'].value_counts().head(5))
            elif 'Jabatan' in df_profil.columns:
                st.bar_chart(df_profil['Jabatan'].value_counts().head(5))

        # 3. FITUR PTP INTELLIGENCE (AI Analysis)
        st.divider()
        st.header("🧠 Analisis & Rekomendasi Berbasis Kompetensi")
        st.markdown("Pilih jenis analisis yang ingin Anda lakukan:")

        # Menyiapkan Data Context (Sampel 10 baris agar ringan)
        data_preview = (
            "--- DATA PROFIL ---\n" + df_profil.head(10).to_csv(index=False) + 
            "\n\n--- DATA NILAI ---\n" + df_quiz.head(10).to_csv(index=False) +
            "\n\n--- DATA PROGRESS ---\n" + df_progress.head(10).to_csv(index=False)
        )

        col_ai1, col_ai2 = st.columns([1, 2])

        with col_ai1:
            mode_analisis = st.radio(
                "Jenis Laporan:",
                (
                    "📄 Laporan Analisis Kebutuhan (Needs Analysis)",
                    "💡 Rekomendasi Desain Pembelajaran (Competency Based)",
                    "⚠️ Deteksi Masalah Pembelajaran"
                )
            )
            
            if st.button("Generate Analisis AI 🚀", type="primary"):
                # Menentukan Prompt berdasarkan pilihan
                if mode_analisis == "Laporan Analisis Kebutuhan (Needs Analysis)":
                    prompt = """
                    Lakukan analisis kebutuhan pembelajaran (Learning Needs Analysis) berdasarkan data nilai dan perilaku peserta.
                    Identifikasi kesenjangan (gap) kompetensi yang terlihat dari data.
                    Apakah materi saat ini relevan dengan profil jabatan peserta?
                    Sebutkan peran PTP Ahli Pertama dan Muda dalam menindaklanjuti data ini sesuai standar kompetensi.
                    """
                elif mode_analisis == "Rekomendasi Desain Pembelajaran (Competency Based)":
                    prompt = """
                    Berikan rekomendasi perbaikan desain pembelajaran yang konkret.
                    WAJIB membagi rekomendasi berdasarkan jenjang PTP:
                    1. Apa yang harus diperbaiki pada aspek MEDIA (Tugas PTP Pertama)?
                    2. Apa yang harus diperbaiki pada aspek HYPERMEDIA/Interaktivitas (Tugas PTP Muda)?
                    3. Apa yang harus dievaluasi pada MODEL E-LEARNING (Tugas PTP Madya)?
                    4. Apakah ada rekomendasi KEBIJAKAN/INOVASI (Tugas PTP Utama)?
                    """
                else:
                    prompt = """
                    Identifikasi masalah kritis dalam pelatihan ini (misal: SKS, nilai rendah, drop-out).
                    Analisis menggunakan teori Kognitivisme (beban kognitif).
                    Berikan solusi berjenjang dari sisi teknis (media) hingga strategis (kebijakan).
                    """
                
                # Eksekusi AI
                hasil_analisis = analyze_with_ai(data_preview, prompt, api_key)
                
                # Simpan hasil di session state
                st.session_state['hasil_ptp'] = hasil_analisis

        with col_ai2:
            st.markdown("### Hasil Analisis AI:")
            if 'hasil_ptp' in st.session_state:
                st.markdown(st.session_state['hasil_ptp'])
            else:
                st.info("👈 Pilih mode analisis dan klik tombol untuk memulai.")

    except Exception as e:
        st.error(f"Gagal memproses data. Detail Error: {e}")
        st.warning("Tips: Pastikan semua file CSV sudah diupload dengan format yang benar.")

else:
    # Tampilan Awal (Landing Page)
    st.markdown("---")
    st.subheader("👋 Selamat Datang di Dashboard PTP")
    st.write("Silakan upload data pelatihan (CSV) pada menu di sebelah k
