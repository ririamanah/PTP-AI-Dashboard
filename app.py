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
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    else:
        return st.sidebar.text_input("🔑 Masukkan Google AI API Key", type="password")

# --- HEADER ---
st.title("🚀 PTP AI Dashboard")
st.markdown("""
**Sistem Analisis Cerdas Pengembang Teknologi Pembelajaran (PTP)**  
*Pusdiklat Anggaran dan Perbendaharaan*
""")
st.info("Sistem ini mengintegrasikan **Learning Analytics** dengan **Standar Kompetensi JF PTP (PermenPANRB No. 3 Tahun 2021)**.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Sistem")
    api_key = configure_api()
    
    st.divider()
    st.header("📂 Upload Data Pelatihan")
    st.warning("Format: CSV (Delimiter titik koma ';')")
    
    file_profil = st.file_uploader("1. Data Profil Peserta (Demografi)", type=['csv'])
    file_quiz = st.file_uploader("2. Data Nilai/Kuis (Evaluasi)", type=['csv'])
    file_progress = st.file_uploader("3. Data Progress (Aktivitas)", type=['csv'])
    
    st.caption("Updated with PTP Competency Standards")

# --- DATABASE KOMPETENSI PTP (HARDCODED) ---
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

# --- FUNGSI OTAK AI ---
def analyze_with_ai(data_context, prompt_instructions, key):
    if not key:
        return "⚠️ Error: API Key belum terdeteksi."
    
    try:
        genai.configure(api_key=key)
        # Menggunakan model gemini-1.5-flash yang stabil dan mendukung konteks panjang
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # System Prompt yang diperkaya dengan Standar Kompetensi
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
        2. SAAT MEMBERIKAN REKOMENDASI DESAIN, petakan solusi berdasarkan jenjang PTP.
           Contoh: "Data menunjukkan nilai rendah di materi visual. 
           - Rekomendasi untuk PTP Pertama: Perbaiki aset media video.
           - Rekomendasi untuk PTP Madya: Evaluasi ulang model e-learning yang digunakan."
        3. Gunakan Bahasa Indonesia formal dan profesional.
        """
        
        with st.spinner('🤖 AI sedang memetakan data ke Standar Kompetensi PTP...'):
            response = model.generate_content(system_prompt)
        return response.text
        
    except Exception as e:
        return f"Terjadi kesalahan pada AI: {str(e)}"

# --- LOGIKA DASHBOARD ---
if file_profil and file_quiz and file_progress:
    try:
        # Load & Clean Data
        df_profil = pd.read_csv(file_profil, sep=';')
        df_quiz = pd.read_csv(file_quiz, sep=';')
        df_progress = pd.read_csv(file_progress, sep=';')

        for df in [df_profil, df_quiz, df_progress]:
            df.columns = df.columns.str.strip()

        st.success(f"✅ Data Siap. Total Peserta: {len(df_profil)}")

        # Dashboard Statistik
        st.subheader("📊 Statistik Utama")
        col1, col2 = st.columns(2)
        
        with col1:
            nilai_cols = [c for c in df_quiz.columns if 'Quiz' in c or 'Nilai' in c]
            if nilai_cols:
                rata_total = df_quiz[nilai_cols].mean().mean()
                st.metric("Rata-rata Nilai", f"{rata_total:.2f}")
                st.bar_chart(df_quiz[nilai_cols].mean())
            else:
                st.warning("Kolom Nilai tidak ditemukan")

        with col2:
            st.markdown("**Sebaran Jabatan Peserta**")
            if 'POSITION' in df_profil.columns:
                st.bar_chart(df_profil['POSITION'].value_counts().head(5))
            elif 'Jabatan' in df_profil.columns:
                st.bar_chart(df_profil['Jabatan'].value_counts().head(5))

        # --- FITUR AI ---
        st.divider()
        st.header("🧠 Analisis & Rekomendasi Berbasis Kompetensi")
        
        # Penyiapan Data String
        data_preview = (
            "PROFIL (Sampel):\n" + df_profil.head(10).to_csv(index=False) + 
            "\n\nNILAI (Sampel):\n" + df_quiz.head(10).to_csv(index=False) +
            "\n\nPROGRESS (Sampel):\n" + df_progress.head(10).to_csv(index=False)
        )

        col_input, col_output = st.columns([1, 2])

        with col_input:
            st.markdown("### Pilih Fokus Analisis")
            mode_analisis = st.radio(
                "Jenis Laporan:",
                (
                    "📄 Laporan Analisis Kebutuhan (Needs Analysis)",
                    "💡 Rekomendasi Desain Pembelajaran (Competency Based)",
                    "⚠️ Deteksi Masalah Pembelajaran"
                )
            )
            
            if st.button("Generate Analisis AI 🚀"):
                if mode_analisis == "Laporan Analisis Kebutuhan (Needs Analysis)":
                    prompt = """
                    Lakukan analisis kebutuhan pembelajaran (Learning Needs Analysis) berdasarkan data nilai dan perilaku peserta.
                    Identifikasi kesenjangan (gap) kompetensi yang terlihat dari data.
                    Apakah materi saat ini relevan dengan profil jabatan peserta?
                    Sebutkan peran PTP Ahli Pertama dan Muda dalam menindaklanjuti data ini.
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
                
                hasil = analyze_with_ai(data_preview, prompt, api_key)
                st.session_state['hasil_ptp'] = hasil

        with col_output:
            st.markdown("### Hasil Analisis AI:")
            if 'hasil_ptp' in st.session_state:
                st.markdown(st.session_state['hasil_ptp'])
            else:
                st.info("👈 Pilih mode analisis dan klik tombol untuk memulai.")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.markdown("<br><br><center>Silakan upload data CSV di sidebar.</center>", unsafe_allow_html=True)
    st.write("Pastikan file CSV menggunakan pemisah titik koma (;)")
