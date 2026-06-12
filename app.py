import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Muat variabel dari file .env
load_dotenv()

# ===== KONFIGURASI HALAMAN =====
st.set_page_config(
    page_title="Produktivitas Assistant",
    page_icon="⚡",
    layout="wide"
)

# ===== FUNGSI UNTUK MEMUAT API KEY =====
@st.cache_resource
def get_gemini_client():
    """Membuat dan mengembalikan client Gemini API"""
    # Coba ambil dari st.secrets (untuk deployment cloud)
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("🚨 API Key Gemini tidak ditemukan. Tambahkan ke file .env atau Streamlit secrets.")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_gemini_client()

# ===== INISIALISASI SESSION STATE =====
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Kamu adalah asisten produktivitas yang ramah, santai, dan memotivasi. Nama kamu 'Prodo'. Gunakan bahasa Indonesia yang santai seperti ngobrol dengan teman. Jangan lupa tanyakan kabar dan beri semangat!"}
    ]

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ===== SIDEBAR UNTUK PENGATURAN =====
with st.sidebar:
    st.header("🎛️ Pengaturan")
    
    # Pengaturan Gaya Bahasa
    st.subheader("🎨 Gaya Bahasa")
    gaya = st.selectbox("Pilih gaya respons:", ["Santai & Motivasi", "Formal & Singkat"])
    if gaya == "Formal & Singkat":
        if st.session_state.messages[0]["content"] != "Kamu adalah asisten produktivitas yang formal, singkat, dan profesional. Gunakan bahasa Indonesia baku.":
            st.session_state.messages[0]["content"] = "Kamu adalah asisten produktivitas yang formal, singkat, dan profesional. Gunakan bahasa Indonesia baku."
            st.session_state.messages = st.session_state.messages[:1]
            st.rerun()
    else:
        if st.session_state.messages[0]["content"] != "Kamu adalah asisten produktivitas yang ramah, santai, dan memotivasi. Nama kamu 'Prodo'. Gunakan bahasa Indonesia yang santai seperti ngobrol dengan teman. Jangan lupa tanyakan kabar dan beri semangat!":
            st.session_state.messages[0]["content"] = "Kamu adalah asisten produktivitas yang ramah, santai, dan memotivasi. Nama kamu 'Prodo'. Gunakan bahasa Indonesia yang santai seperti ngobrol dengan teman. Jangan lupa tanyakan kabar dan beri semangat!"
            st.session_state.messages = st.session_state.messages[:1]
            st.rerun()
    
    st.divider()
    
    # Parameter kreativitas
    temperature = st.slider("🌡️ Temperatur (kreativitas)", 0.0, 2.0, 0.7, 0.05)
    st.caption("Nilai lebih tinggi = respons lebih kreatif dan bervariasi")
    
    # Parameter tambahan yang didukung Gemini
    max_tokens = st.slider("📏 Maksimal token respons", 256, 2048, 1024, 128)
    st.caption("Mengatur panjang maksimal jawaban")
    
    st.divider()
    
    # Manajemen Tugas
    st.subheader("📝 Daftar Tugas Hari Ini")
    new_task = st.text_input("Tambah tugas baru:")
    if st.button("➕ Tambah"):
        if new_task:
            st.session_state.tasks.append({"task": new_task, "done": False, "created": datetime.now()})
            st.rerun()
    
    for i, task in enumerate(st.session_state.tasks):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            done = st.checkbox(task["task"], value=task["done"], key=f"task_{i}")
            st.session_state.tasks[i]["done"] = done
        with col2:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.tasks.pop(i)
                st.rerun()
    
    if st.button("🗑️ Hapus semua tugas"):
        st.session_state.tasks = []
        st.rerun()
    
    if st.sidebar.button("🔄 Reset Percakapan"):
        st.session_state.messages = st.session_state.messages[:1]
        st.rerun()

# ===== AREA CHAT UTAMA =====
st.title("⚡ Produktivitas Assistant")
st.caption("Asisten pribadi yang membantu Anda tetap fokus dan terorganisir.")

# Tampilkan riwayat chat
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input dari pengguna
if prompt := st.chat_input("Ceritakan rencana atau tugasmu hari ini..."):
    # Tampilkan pesan pengguna
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Siapkan konteks tugas
    task_list = "\n".join([f"- {t['task']} {'✅' if t['done'] else '⏳'}" for t in st.session_state.tasks]) if st.session_state.tasks else "Belum ada tugas tercatat."
    context = f"Info tambahan: Daftar tugas pengguna saat ini:\n{task_list}\n\nRespons sebagai asisten produktivitas."
    
    # Siapkan pesan untuk model
    chat = model.start_chat(history=[])
    
    # Kirim semua pesan sebelumnya sebagai konteks
    full_context = st.session_state.messages[0]["content"] + "\n\n" + context + "\n\n"
    for msg in st.session_state.messages[1:]:
        full_context += f"{msg['role']}: {msg['content']}\n"
    
    # Panggil API Gemini
    with st.chat_message("assistant"):
        with st.spinner("Prodo sedang berpikir..."):
            try:
                response = model.generate_content(
                    full_context,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        top_p=0.95,
                    )
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
                answer = "Maaf, saya sedang error. Coba lagi ya!"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})