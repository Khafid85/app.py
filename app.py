import streamlit as st
import os
from datetime import datetime
from groq import Groq

# Konfigurasi halaman
st.set_page_config(
    page_title="Produktivitas Assistant",
    page_icon="⚡",
    layout="wide"
)

# Judul aplikasi
st.title("⚡ Produktivitas Assistant")
st.caption("Asisten pribadi yang membantu Anda tetap fokus dan terorganisir.")

# Inisialisasi session state untuk memory percakapan
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Kamu adalah asisten produktivitas yang ramah, santai, dan memotivasi. Nama kamu 'Prodo'. Tugasmu membantu pengguna mengatur tugas, mengingatkan deadline, memberikan tips fokus, dan menyemangati. Gunakan bahasa Indonesia yang santai seperti ngobrol dengan teman. Jangan lupa tanyakan kabar dan beri semangat!"}
    ]

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Sidebar untuk parameter kreatif dan tools
with st.sidebar:
    st.header("🎛️ Pengaturan")
    
    # Parameter kreatif: gaya bahasa (sudah di system prompt)
    st.subheader("🎨 Gaya Bahasa")
    gaya = st.selectbox("Pilih gaya respons:", ["Santai & Motivasi", "Formal & Singkat"])
    if gaya == "Formal & Singkat":
        # Update system prompt jika perlu
        if st.session_state.messages[0]["content"] != "Kamu adalah asisten produktivitas yang formal, singkat, dan profesional. Gunakan bahasa Indonesia baku.":
            st.session_state.messages[0]["content"] = "Kamu adalah asisten produktivitas yang formal, singkat, dan profesional. Gunakan bahasa Indonesia baku."
            # Hapus riwayat chat agar konsisten
            st.session_state.messages = st.session_state.messages[:1]
            st.rerun()
    else:
        if st.session_state.messages[0]["content"] != "Kamu adalah asisten produktivitas yang ramah, santai, dan memotivasi. Nama kamu 'Prodo'. Tugasmu membantu pengguna mengatur tugas, mengingatkan deadline, memberikan tips fokus, dan menyemangati. Gunakan bahasa Indonesia yang santai seperti ngobrol dengan teman. Jangan lupa tanyakan kabar dan beri semangat!":
            st.session_state.messages[0]["content"] = "Kamu adalah asisten produktivitas yang ramah, santai, dan memotivasi. Nama kamu 'Prodo'. Tugasmu membantu pengguna mengatur tugas, mengingatkan deadline, memberikan tips fokus, dan menyemangati. Gunakan bahasa Indonesia yang santai seperti ngobrol dengan teman. Jangan lupa tanyakan kabar dan beri semangat!"
            st.session_state.messages = st.session_state.messages[:1]
            st.rerun()
    
    st.divider()
    
    # Parameter suhu (temperature) untuk kreativitas
    temperature = st.slider("🌡️ Temperatur (kreativitas)", 0.0, 1.5, 0.7, 0.05)
    st.caption("Nilai lebih tinggi = respons lebih kreatif dan bervariasi")
    
    st.divider()
    
    # Fitur tambahan: manajemen tugas sederhana
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
    
    if st.button("Hapus semua tugas"):
        st.session_state.tasks = []
        st.rerun()
    
    st.divider()
    st.caption("🔑 API Key Groq disimpan di secrets (Streamlit Cloud) atau environment variable.")

# Ambil API Key dari secrets atau environment
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except:
    groq_api_key = os.environ.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("🚨 API Key Groq tidak ditemukan. Tambahkan ke .env atau Streamlit secrets.")
    st.stop()

# Inisialisasi client Groq
client = Groq(api_key=groq_api_key)

# Tampilkan riwayat chat
for msg in st.session_state.messages[1:]:  # skip system prompt
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input dari user
if prompt := st.chat_input("Ceritakan rencana atau tugasmu hari ini..."):
    # Tambahkan pesan user ke session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Siapkan konteks: daftar tugas saat ini
    task_list = "\n".join([f"- {t['task']} {'✅' if t['done'] else '⏳'}" for t in st.session_state.tasks]) if st.session_state.tasks else "Belum ada tugas tercatat."
    context = f"Info tambahan: Daftar tugas pengguna saat ini:\n{task_list}\n\nRespons sebagai asisten produktivitas."
    
    # Panggil LLM
    with st.chat_message("assistant"):
        with st.spinner("Prodo sedang berpikir..."):
            try:
                # Siapkan messages untuk API (system + history + context + user prompt)
                api_messages = [st.session_state.messages[0]]  # system prompt
                # Tambahkan riwayat terakhir (max 10 pesan untuk hemat token)
                history = st.session_state.messages[1:-1]  # semua kecuali system dan pesan terakhir user
                # Tambahkan context sebagai pesan system tambahan
                api_messages.append({"role": "system", "content": context})
                api_messages.extend(history)
                api_messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=api_messages,
                    temperature=temperature,
                    max_tokens=1024,
                    top_p=0.9
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                # Simpan respons assistant
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
                answer = "Maaf, saya sedang error. Coba lagi ya!"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# Tombol reset percakapan
if st.sidebar.button("🔄 Reset Percakapan"):
    st.session_state.messages = st.session_state.messages[:1]  # hanya system prompt
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** Tanyakan tentang prioritas tugas, tips fokus, atau minta rekomendasi jadwal.")