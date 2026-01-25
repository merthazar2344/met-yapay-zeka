import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io

# ================== OPENAI ==================
api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = "BURAYA_KENDI_API_KEYINI_YAZ"

client = OpenAI(api_key=api_key)
# ============================================

st.set_page_config(page_title="Metai", layout="wide")

st.markdown("""
<style>
body { background-color:#0f0f0f; color:white; }
.user { background:#2b2b2b; padding:10px; border-radius:16px; text-align:right; margin:6px 0; }
.bot { background:#1e1e1e; padding:10px; border-radius:16px; text-align:left; margin:6px 0; }
</style>
""", unsafe_allow_html=True)


# ----------------- SIDEBAR -----------------
st.sidebar.title("💬 Sohbetler")

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

mode = st.sidebar.radio("Mod:", ["Normal", "🎓 Akademik", "😈 Troll"])

# ----------------- MAIN -----------------
st.title("🤖 Metai")

messages = st.session_state.chats[st.session_state.active_chat]

for role, msg in messages:
    if role == "user":
        st.markdown(f'<div class="user">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot">{msg}</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📎 Resim yükle", type=["png", "jpg", "jpeg"])
image_base64 = None

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_column_width=True)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode()

user_input = st.chat_input("Bir şey yaz...")

def system_prompt(mode):
    if mode == "😈 Troll":
        return "Sen Metai adlı TROLL bir asistansın. Mantıklı görünen ama yanlış cevaplar ver."
    if mode == "🎓 Akademik":
        return "Sen akademik ve ciddi bir asistansın."
    return "Sen yardımcı bir asistansın."

if user_input:
    messages.append(("user", user_input))

    try:
        content = [
            {"type": "input_text", "text": user_input}
        ]

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

    except Exception as e:
        reply = f"❌ Hata: {e}"

    messages.append(("bot", reply))
    st.rerun()

