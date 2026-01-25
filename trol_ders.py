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
.user {
    background:#2b2b2b; padding:10px 14px;
    border-radius:18px; margin:6px 0; text-align:right;
}
.bot {
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

# --------- MOD ---------
mode = st.radio("Mod:", ["Normal", "🎓 Akademik", "😈 Troll"], horizontal=True)

def system_prompt(mode):
    if mode == "🎓 Akademik":
        return "Sen akademik, ciddi ve net cevaplar veren bir asistansın."
    if mode == "😈 Troll":
        return (
            "Sen MetAI adlı TROLL bir asistansın. "
            "Mantıklı görünen ama yanlış cevaplar ver. "
            "En fazla 4-5 cümle yaz."
        )
    return "Sen yardımcı, kısa ve net cevap veren bir asistansın."

messages = st.session_state.chats[st.session_state.current_chat]

# --------- MESAJLAR ---------
for m in messages:
    if m["role"] == "user":
        st.markdown(f'<div class="user">🧑 {m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot">🤖 {m["content"]}</div>', unsafe_allow_html=True)

# --------- GÖRSEL ---------
uploaded_image = st.file_uploader(
    "🖼️ Resim yükle",
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
            content = [{"type": "input_text", "text": user_input}]

            if image_base64:
                content.append({
                    "type": "input_image",
                    "image_base64": image_base64
                })

            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {"role": "system", "content": system_prompt(mode)},
                    {"role": "user", "content": content}
                ],
                max_output_tokens=300
            )

            bot_reply = response.output_text

        except Exception:
            bot_reply = "⚠️ Bir hata oluştu."

    messages.append({"role": "assistant", "content": bot_reply})
    st.rerun()
