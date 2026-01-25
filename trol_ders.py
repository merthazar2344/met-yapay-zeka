import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io

# ================== OPENAI ==================
# API KEY KODDA YOK!
# Streamlit Cloud > Settings > Secrets:
# OPENAI_API_KEY = "sk-xxxx"
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
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
.sidebar-title { font-weight:bold; margin-top:10px; }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.title("💬 Metai Sohbetler")

if "chats" not in st.session_state:
    st.session_state.chats = {"Sohbet 1": []}
    st.session_state.active_chat = "Sohbet 1"

if st.sidebar.button("➕ Yeni Sohbet"):
    new_name = f"Sohbet {len(st.session_state.chats)+1}"
    st.session_state.chats[new_name] = []
    st.session_state.active_chat = new_name
    st.rerun()

for chat_name in st.session_state.chats:
    if st.sidebar.button(chat_name):
        st.session_state.active_chat = chat_name
        st.rerun()

st.sidebar.markdown("---")

# ----------------- MODE -----------------
mode = st.sidebar.radio(
    "Mod Seç:",
    ["Normal", "🎓 Akademik", "😈 Troll"]
)

# ----------------- MAIN -----------------
st.title("🤖 Metai")

messages = st.session_state.chats[st.session_state.active_chat]

st.markdown('<div class="chatbox">', unsafe_allow_html=True)
for role, msg in messages:
    if role == "user":
        st.markdown(f'<div class="user">🧑 {msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot">🤖 {msg}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- FILE UPLOAD -----------------
uploaded_file = st.file_uploader(
    "📎 Resim yükle (yorumlatabilirsin)",
    type=["png", "jpg", "jpeg"]
)

image_base64 = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Yüklenen görsel", use_column_width=True)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode()

# ----------------- INPUT -----------------
user_input = st.chat_input("Bir şey yaz...")

def system_prompt(mode):
    if mode == "😈 Troll":
        return (
            "Sen Metai adlı TROLL bir asistansın. "
            "Mantıklı görünen ama yanlış cevaplar ver. "
            "4-5 satırı geçme."
        )
    if mode == "🎓 Akademik":
        return (
            "Sen akademik, ciddi bir asistansın. "
            "Bilimsel, net ve açıklayıcı cevap ver."
        )
    return "Sen yardımcı, dost canlısı bir asistansın."

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
                input=[{
                    "role": "user",
                    "content": content
                }],
                instructions=system_prompt(mode),
                max_output_tokens=300
            )

            reply = response.output_text

        except Exception:
            reply = "⚠️ Yapay zekâya bağlanılamadı. (API/Secrets kontrol et)"

    messages.append(("bot", reply))
    st.rerun()
