import streamlit as st
from openai import OpenAI
import base64

# ================= OPENAI =================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# =========================================

st.set_page_config(page_title="MetAI", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
body { background-color:#0f0f0f; color:white; }
.chat-bubble-user {
    background:#2b2b2b; padding:10px 14px;
    border-radius:18px; margin:6px 0; text-align:right;
}
.chat-bubble-bot {
    background:#1e1e1e; padding:10px 14px;
    border-radius:18px; margin:6px 0; text-align:left;
}
</style>
""", unsafe_allow_html=True)

# ================= STATE =================
if "chats" not in st.session_state:
    st.session_state.chats = {"Sohbet 1": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Sohbet 1"
if "chat_count" not in st.session_state:
    st.session_state.chat_count = 1

# ================= SIDEBAR =================
with st.sidebar:
    st.title("💬 Sohbetler")

    if st.button("➕ Yeni Sohbet"):
        st.session_state.chat_count += 1
        name = f"Sohbet {st.session_state.chat_count}"
        st.session_state.chats[name] = []
        st.session_state.current_chat = name
        st.rerun()

    st.divider()

    for chat in st.session_state.chats:
        if st.button(chat, key=chat):
            st.session_state.current_chat = chat
            st.rerun()

# ================= MAIN =================
st.title("🤖 MetAI")

messages = st.session_state.chats[st.session_state.current_chat]

# --------- GÖRÜNTÜLE ---------
for m in messages:
    if m["role"] == "user":
        st.markdown(f'<div class="chat-bubble-user">🧑 {m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble-bot">🤖 {m["content"]}</div>', unsafe_allow_html=True)

# --------- DOSYA ---------
uploaded_image = st.file_uploader(
    "🖼️ Resim yükle (analiz edilebilir)",
    type=["png", "jpg", "jpeg"]
)

image_base64 = None
if uploaded_image:
    image_bytes = uploaded_image.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    st.image(uploaded_image, caption="Yüklenen görsel", use_column_width=True)

# --------- INPUT ---------
user_input = st.chat_input("Bir şey yaz...")

if user_input:
    messages.append({"role": "user", "content": user_input})

    with st.spinner("MetAI düşünüyor..."):
        try:
            input_content = [
                {"type": "input_text", "text": user_input}
            ]

            if image_base64:
                input_content.append({
                    "type": "input_image",
                    "image_base64": image_base64
                })

            response = client.responses.create(
                model="gpt-4.1",
                input=[{
                    "role": "user",
                    "content": input_content
                }],
                max_output_tokens=300
            )

            bot_reply = response.output_text

        except Exception as e:
            bot_reply = "⚠️ Görsel veya metin analizinde hata oluştu."

    messages.append({"role": "assistant", "content": bot_reply})
    st.rerun()
