import streamlit as st
from openai import OpenAI
from PIL import Image
import tempfile
import cv2

# ================== OPENAI ==================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# ============================================

st.set_page_config(page_title="MetAI", layout="wide")

# ----------------- CSS -----------------
st.markdown("""
<style>
body { background-color:#0f0f0f; color:white; }
.chatbox { max-width:800px; margin:auto; }
.user { background:#2b2b2b; padding:10px; border-radius:15px; margin:6px 0; text-align:right; }
.bot { background:#1e1e1e; padding:10px; border-radius:15px; margin:6px 0; text-align:left; }
.sidebar-title { font-size:20px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
st.sidebar.markdown("<div class='sidebar-title'>💬 Sohbetler</div>", unsafe_allow_html=True)

if "chats" not in st.session_state:
    st.session_state.chats = {"Sohbet 1": []}
    st.session_state.active_chat = "Sohbet 1"

if st.sidebar.button("➕ Yeni Sohbet"):
    new_name = f"Sohbet {len(st.session_state.chats)+1}"
    st.session_state.chats[new_name] = []
    st.session_state.active_chat = new_name
    st.rerun()

for chat in st.session_state.chats:
    if st.sidebar.button(chat):
        st.session_state.active_chat = chat
        st.rerun()

# ================== MAIN ==================
st.title("🤖 MetAI")

mode = st.radio("Mod:", ["Normal", "🎓 Akademik", "😈 Troll"], horizontal=True)

messages = st.session_state.chats[st.session_state.active_chat]

# --------- CHAT HISTORY ---------
st.markdown("<div class='chatbox'>", unsafe_allow_html=True)
for role, msg in messages:
    if role == "user":
        st.markdown(f"<div class='user'>🧑 {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot'>🤖 {msg}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --------- FILE UPLOAD ---------
uploaded_file = st.file_uploader(
    "📎 Resim veya Video yükle",
    type=["png", "jpg", "jpeg", "mp4"]
)

image_for_ai = None

if uploaded_file:
    if uploaded_file.type.startswith("image"):
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", use_column_width=True)
        image_for_ai = image

    elif uploaded_file.type == "video/mp4":
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        cap = cv2.VideoCapture(tfile.name)
        success, frame = cap.read()
        if success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_for_ai = Image.fromarray(frame)
            st.image(image_for_ai, caption="Videodan alınan ilk kare", use_column_width=True)

# --------- INPUT ---------
user_input = st.chat_input("MetAI’ye bir şey sor...")

def system_prompt(mode):
    if mode == "😈 Troll":
        return "Sen MetAI adlı troll bir asistansın. Mantıklı görünen ama yanlış cevaplar ver. En fazla 5 satır."
    if mode == "🎓 Akademik":
        return "Sen akademik, ciddi ve doğru cevaplar veren bir asistansın."
    return "Sen yardımcı ve dost canlısı bir asistansın."

# --------- AI RESPONSE ---------
if user_input:
    messages.append(("user", user_input))

    content = [{"type": "text", "text": user_input}]

    if image_for_ai:
        content.append({
            "type": "input_image",
            "image_base64": st.image_to_base64(image_for_ai)
        })

    with st.spinner("MetAI düşünüyor..."):
        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": system_prompt(mode)},
                    {"role": "user", "content": content}
                ],
                max_output_tokens=300
            )
            reply = response.output_text
        except Exception:
            reply = "⚠️ Yapay zekâya bağlanılamadı. API veya dosya hatası."

    messages.append(("bot", reply))
    st.rerun()
