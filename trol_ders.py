import streamlit as st
from openai import OpenAI

# ================== OPENAI ==================
# API KEY KODDA YOK!
# Streamlit Cloud > Settings > Secrets içine şunu ekle:
# OPENAI_API_KEY = "sk-xxxx"
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# ============================================

st.set_page_config(page_title="Metai", layout="centered")

# ----------------- CSS -----------------
st.markdown("""
<style>
body { background-color:#0f0f0f; color:white; }
.chat { max-width:720px; margin:auto; }
.user {
    background:#2b2b2b; color:white; padding:10px 14px;
    border-radius:18px; margin:8px 0; text-align:right;
}
.bot {
    background:#1e1e1e; color:white; padding:10px 14px;
    border-radius:18px; margin:8px 0; text-align:left;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Metai")

# --------- MOD ---------
mode = st.radio("Mod:", ["Normal", "🎓 Akademik", "😈 Troll"], horizontal=True)

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
user_input = st.chat_input("Bir şey yaz...")

def get_system_prompt(mode, user_input):
    list_words = ["say", "listele", "sırala", "isimlerini", "kaç tane", "nelerdir"]
    is_list = any(w in user_input.lower() for w in list_words)

    if mode == "😈 Troll":
        if is_list:
            return (
                "Sen Metai adlı TROLL bir asistansın. "
                "Liste istenince TAM bir liste ver ama bilerek eksik/yanlış olsun. "
                "Mantıklı görünsün. Listeyi YARIDA KESME."
            )
        return (
            "Sen Metai adlı TROLL bir asistansın. "
            "Doğru cevap verme. Mantıklı GÖRÜNEN ama yanlış cevap ver. "
            "EN FAZLA 4–5 SATIR yaz."
        )
    if mode == "🎓 Akademik":
        return (
            "Sen akademik, ciddi bir asistansın. "
            "Doğru, kısa ve net cevap ver. Gereksiz uzatma yapma."
        )
    return "Sen yardımcı, normal bir asistansın. Kısa ve net cevap ver."

if user_input:
    st.session_state.messages.append(("user", user_input))

    system_prompt = get_system_prompt(mode, user_input)

    with st.spinner("Metai düşünüyor..."):
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
        except Exception as e:
            bot_reply = "⚠️ Yapay zekâya bağlanılamadı. (API/Secrets kontrol et)"

    st.session_state.messages.append(("bot", bot_reply))
    st.rerun()
