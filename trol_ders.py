import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import os

# ================== OPENAI ==================
# 1) Önce Streamlit Secrets'e bak
api_key = None

if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    # 2) Secrets yoksa buraya ELLE YAZ (GEÇİCİ ÇÖZÜM)
    api_key = "BURAYA_KENDI_API_KEYINI_YAZ"

client = OpenAI(api_key=api_key)
# ============================================

st.set_page_config(page_title="Metai", layout="wide")

# ----------------- CSS -----------------
st.markdown("""
<style>
body { background-color:#0f0f0f; color:white; }
.chatbox { max-width:900px; margin:auto; }
.user {
    background:#2b2b2b; padding:10px 14px; border-radius:18px;
    margin:8px 0; text-align:right;
}
.bot {
    background:#1e1e1e; padding:10px 14px; border-radius:18px;
    margin:8px 0; text-align:left;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.title("💬 Metai Sohbetler")

if "chats" not in st.session_state:
    st.session_state.chats = {"Sohbet 1": []}
    st.session_state.active_chat = "Sohbet 1"

if st.sidebar.button("➕ Yeni Sohbet"):
    name = f"Sohbet {len(st.session_state.chats)+1}"
    st.session_state.chats[name] = []
    st.session_state.active_chat = name
    st.rerun()

for chat in st.session_state.chats:
    if st.sidebar.button(chat):
        st.session_state.active_chat = chat
        st.rerun()

st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Mod Seç:",
    ["Normal", "🎓 Akademik", "😈 Troll"]
)

# ----------------- MAIN -----------------
st.title("🤖 Metai")

messages = st.session_state.chats[st.session_state.active_chat]

for role, msg in messages:
    if role == "user":
        st.markdown(f'<div class="user">🧑 {msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot">🤖 {msg}</div>', unsafe_allow_html=True)

# ----------------- FILE UPLOAD -----------------
uploaded_file = st.file_uploader(
    "📎 Resim yükle (yorumlatabilirsin)",
    type=["png", "jpg", "jpeg"]
)

image_base64 = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_column_width=True)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode()

# ----------------- INPUT -----------------
user_input = st.chat_input("Bir şey yaz...")

def system_prompt(mode):
    if mode == "😈 Troll":
        return "Sen Metai adlı TROLL bir asistansın. Mantıklı görünen ama yanlış cevaplar ver."
    if mode == "🎓 Akademik":
        return "Sen akademik, ciddi ve bilimsel bir asistansın."
    return "Sen yardımcı ve dost canlısı bir asistansın."

if user_input:
    messages.append(("user", user_input))

    with st.spinner("Metai düşünüyor..."):
        try:
            content = [{"type": "text", "text": user_input}]
            if image_base64:
                content.append({
                    "type": "input_image",
                    "image_base64": image_base64
                })

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=[{"role": "user", "content": content}],
                instructions=system_prompt(mode),
                max_output_tokens=300
            )

            reply = response.output_text

        except Exception as e:
            reply = f"❌ Hata: {str(e)}"

    messages.append(("bot", reply))
    st.rerun()
