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

st.set_page_config(page_title="Temai", layout="wide")

# ----------------- CSS -----------------
st.markdown("""
<style>
body { background-color:#0f0f0f; color:black; }

.user {
    background:#cfcfcf;
    color:black;
    padding:10px;
    border-radius:16px;
    text-align:right;
    margin:6px 0;
}

.bot {
    background:#e0e0e0;
    color:black;
    padding:10px;
    border-radius:16px;
    text-align:left;
    margin:6px 0;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.title("💬 Sohbetler")

if "chats" not in st.session_state:
    st.session_state.chats = {"Sohbet 1": []}
    st.session_state.active_chat = "Sohbet 1"

if st.sidebar.button("➕ Yeni Sohbet Ekle"):
    name = f"Sohbet {len(st.session_state.chats)+1}"
    st.session_state.chats[name] = []
    st.session_state.active_chat = name
    st.rerun()

for chat in st.session_state.chats:
    if st.sidebar.button(chat):
        st.session_state.active_chat = chat
        st.rerun()

mode = st.sidebar.radio("Mod:", ["Normal", "📖 Akademik", "😁 Troll"])

# Cevap uzunluğunu kullanıcı ayarlayabilsin (isteğe bağlı ama pratik)
max_tokens = st.sidebar.slider(
    "Cevap uzunluğu (token)",
    min_value=300,
    max_value=4000,
    value=2000,
    step=100,
    help="Yüksek değer = daha uzun cevap yazabilir, ama daha maliyetli olur."
)

# ----------------- MAIN -----------------
st.title("🧠Temai")

messages = st.session_state.chats[st.session_state.active_chat]

# Sohbet geçmişini yukarıdan aşağıya, gönderilme sırasıyla göster.
# Her satır ("user"/"bot", "text"/"image", içerik) şeklinde tutuluyor.
for role, kind, content in messages:
    css_class = "user" if role == "user" else "bot"
    if kind == "image":
        st.markdown(
            f'<div class="{css_class}">'
            f'<img src="data:image/png;base64,{content}" '
            f'style="max-width:280px;border-radius:12px;display:inline-block;"/>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(f'<div class="{css_class}">{content}</div>', unsafe_allow_html=True)

# ----------------- RESİM YÜKLEME -----------------
# key'lere sayaç ekliyoruz: mesaj gönderildikten sonra bu sayaç artınca
# widget'lar sıfırlanıyor, yani eski resim bir sonraki mesaja yapışıp kalmıyor.
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(
        "📎 Galeriden resim seç",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.upload_key}"
    )
with col2:
    camera_file = st.camera_input(
        "📷 Fotoğraf çek",
        key=f"camera_{st.session_state.upload_key}"
    )

# İkisinden hangisi doluysa onu kullan
picked_file = camera_file if camera_file is not None else uploaded_file

image_base64 = None
image_mime = "image/png"

if picked_file:
    image = Image.open(picked_file)
    st.caption("Gönderilecek resim (mesajla birlikte sohbete eklenecek):")
    st.image(image, use_container_width=True)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode()
    image_mime = "image/png"

user_input = st.chat_input("sohbete başlamak için bir şey yazın...")

def system_prompt(mode):
    if mode == "😁 Troll":
        return "Sen Temai adlı TROLL bir asistansın. Mantıklı görünen ama yanlış cevaplar ver."
    if mode == "📖 Akademik":
        return "Sen Temai adlı akademik ve ciddi bir asistansın. Daha resmi ve bilgisel cevaplar ver."
    return "Sen Temai adlı chatgpt ve openai ile hicbir alakası olmayan yardımcı bir asistansın.(chatgpt ve openai ile bağlantın olmadığını sorulmadıkça bahsetme)"

if user_input:
    # Sohbet akışında önce resim, sonra yazı görünsün (gönderme sırası).
    if image_base64:
        messages.append(("user", "image", image_base64))
    messages.append(("user", "text", user_input))

    try:
        content = [
            {"type": "input_text", "text": user_input}
        ]

        # DÜZELTME: input_image bir "image_url" (data URL) bekliyor,
        # "image_base64" diye bir alan yok — hata buradan geliyordu.
        if image_base64:
            content.append({
                "type": "input_image",
                "image_url": f"data:{image_mime};base64,{image_base64}"
            })

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": content
            }],
            instructions=system_prompt(mode),
            max_output_tokens=max_tokens  # DÜZELTME: 300 -> ayarlanabilir, default 2000
        )

        reply = response.output_text

    except Exception as e:
        reply = f"❌ Hata: {e}"

    messages.append(("bot", "text", reply))

    # Yükleme alanını temizle ki aynı resim bir sonraki mesaja yapışmasın.
    st.session_state.upload_key += 1
    st.rerun()
