import streamlit as st
from openai import OpenAI

# ================== OPENAI ==================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# ============================================

st.set_page_config(page_title="Met AI", layout="wide")

# ----------------- CSS -----------------
st.markdown("""
<style>
body { background-color:#0f0f0f; color:white; }

.chat { max-width:700px; margin:auto; }

.user {
    background:#2b2b2b; color:white; padding:10px 14px;
    border-radius:18px; margin:8px 0; text-align:right;
}
.bot {
    background:#1e1e1e; color:white; padding:10px 14px;
    border-radius:18px; margin:8px 0; text-align:left;
}

.small {
    color:#888; font-size:13px;
}
</style>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown("## 🧠 Sohbetler")

    if "chat_titles" not in st.session_state:
        st.session_state.chat_titles = ["Yeni Sohbet"]

    for title in st.session_state.chat_titles:
        st.button(f"💬 {title}", use_container_width=True)

    if st.button("➕ Yeni Sohbet", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_titles.append("Yeni Sohbet")

    st.markdown("---")
    st.markdown("### 📎 Dosya Yükle (Deneysel)")
    st.file_uploader("Dosya", label_visibility="collapsed")
    st.file_uploader("🖼️ Görsel", type=["png", "jpg", "jpeg"])
    st.file_uploader("🎥 Video", type=["mp4", "mov"])

    st.markdown(
        "<div class='small'>Bu özellikler deneysel moddadır.</div>",
        unsafe_allow_html=True
    )

# ================== ANA EKRAN ==================
st.title("🤖 Met AI")
st.markdown("<div class='small'>Deneysel Akademik Yapay Zekâ</div>", unsafe_allow_html=True)

# --------- MOD ---------
mode = st.radio(
    "Mod:",
    ["Normal", "🎓 Akademik", "😈 Troll"],
    horizontal=True
)

# --------- HAFIZA ---------
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------- GEÇMİŞ ---------
st.markdown('<div class="chat">', unsafe_allow_html=True)
for role, msg in st.session_state.messages:
    if role == "user":
        st.markdown(f'<div class="user">🧑 {msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot">🤖 {msg}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --------- GİRİŞ ---------
user_input = st.chat_input("Met AI’ye bir şey sor...")

def get_system_prompt(mode, user_input):
    list_words = ["say", "listele", "sırala", "isimlerini", "kaç tane", "nelerdir"]
    is_list = any(w in user_input.lower() for w in list_words)

    if mode == "😈 Troll":
        if is_list:
            return (
                "Sen Met AI adlı TROLL bir asistansın. "
                "Liste istenince TAM bir liste ver ama bilerek eksik veya yanlış olsun. "
                "Mantıklı görünsün. Listeyi yarıda kesme."
            )
        return (
            "Sen Met AI adlı TROLL bir asistansın. "
            "Mantıklı GÖRÜNEN ama yanlış cevaplar ver. "
            "En fazla 4–5 satır yaz."
        )

    if mode == "🎓 Akademik":
        return (
            "Sen Met AI adlı akademik bir asistansın. "
            "Bilimsel, net ve ciddi cevaplar ver. "
            "Gereksiz uzatma yapma."
        )

    return "Sen Met AI adlı yardımcı bir asistansın. Kısa ve net cevaplar ver."

# --------- CEVAP ---------
if user_input:
    st.session_state.messages.append(("user", user_input))

    system_prompt = get_system_prompt(mode, user_input)

    with st.spinner("🤖 Met AI düşünüyor..."):
        try:
            resp = client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_output_tokens=220
            )
            bot_reply = resp.output_text
        except Exception:
            bot_reply = "⚠️ Yapay zekâya bağlanılamadı. (API / Secrets kontrol et)"

    st.session_state.messages.append(("bot", bot_reply))
    st.rerun()
