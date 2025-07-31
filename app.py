import streamlit as st
import requests
from PyPDF2 import PdfReader

# -------------------------------
# Kelas BusinessPlanAnalyzer
# -------------------------------
class BusinessPlanAnalyzer:
    def __init__(self, api_key: str, model: str, doc_text: str = ""):
        self.api_key = api_key
        self.model = model
        self.doc_text = doc_text

    def extract_text_from_pdf(self, file) -> str:
        """Mengekstrak teks dari file PDF yang diunggah pengguna."""
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        self.doc_text = text
        return text

    def ask_ai(self, prompt: str) -> str:
        """Mengirim pertanyaan ke model AI melalui OpenRouter API."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [
            {
                "role": "system",
                "content": "Anda adalah asisten AI yang ahli dalam bidang bisnis. Berikut adalah isi dokumen business plan:\n\n" + self.doc_text
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        payload = {"model": self.model, "messages": messages}
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        return result['choices'][0]['message']['content']

    def generate_section(self, section: str) -> str:
        """Membuat ringkasan bagian tertentu dari dokumen dengan batasan maksimal 3 kalimat."""
        prompt = f"Tuliskan {section.lower()} dari business plan ini. Buatlah ringkas, maksimal 3 kalimat:\n\n{self.doc_text}"
        return self.ask_ai(prompt)

# -------------------------------
# Aplikasi Streamlit
# -------------------------------
st.set_page_config(page_title="Business Plan Reviewer", layout="wide")
st.title("📊 Business Plan Reviewer berbasis AI")
st.caption("Analisis dokumen proposal bisnis secara otomatis menggunakan teknologi AI")

# Sidebar: Pengaturan API
st.sidebar.header("🔐 Konfigurasi API OpenRouter")
api_key = st.sidebar.text_input("Masukkan API Key OpenRouter Anda", type="password")
model = st.sidebar.selectbox("Pilih Model AI yang Akan Digunakan", [
    "mistralai/mistral-7b-instruct",
    "openchat/openchat-3.5-1210"
])

# Simpan API dan model ke sesi pengguna
if api_key and model:
    st.session_state.api_key = api_key
    st.session_state.model = model
    st.sidebar.success("API Key dan Model berhasil disimpan")

# Upload file PDF business plan
uploaded_file = st.file_uploader("📄 Unggah Dokumen Business Plan (format PDF)", type="pdf")

# Proses saat file pertama kali diunggah
if uploaded_file and "analyzer" not in st.session_state:
    analyzer = BusinessPlanAnalyzer(api_key, model)
    doc_text = analyzer.extract_text_from_pdf(uploaded_file)
    st.session_state.analyzer = analyzer
    st.session_state.doc_text = doc_text

    with st.spinner("🔍 Sistem sedang menganalisis dokumen..."):
        st.session_state.summary_sections = {
            "Ringkasan Kekuatan Proposal": analyzer.generate_section("Ringkasan kekuatan proposal"),
            "Kelemahan Utama": analyzer.generate_section("Kelemahan utama"),
            "Rekomendasi Perbaikan": analyzer.generate_section("Rekomendasi perbaikan"),
            "Penilaian Kelayakan": analyzer.generate_section("Penilaian kelayakan ide secara keseluruhan")
        }

# Tampilkan hasil ringkasan analisis
if "summary_sections" in st.session_state:
    st.subheader("📌 Ringkasan Evaluasi Proposal")
    for title, content in st.session_state.summary_sections.items():
        with st.expander(title, expanded=True):
            st.markdown(content)

# Inisialisasi chat interaktif (hanya berlaku untuk sesi ini)
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

# Fitur Tanya Jawab berbasis Chat AI
if "analyzer" in st.session_state:
    st.subheader("💬 Tanya Jawab Seputar Business Plan")

    # Tampilkan percakapan sebelumnya dalam sesi ini
    for message in st.session_state.chat_log:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Form chat input
    user_input = st.chat_input("Ketik pertanyaan Anda di sini...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.spinner("✍️ AI sedang menyiapkan jawaban..."):
            answer = st.session_state.analyzer.ask_ai(user_input)

        # Simpan chat ke memori sesi
        st.session_state.chat_log.append({"role": "user", "content": user_input})
        st.session_state.chat_log.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.markdown(answer)
