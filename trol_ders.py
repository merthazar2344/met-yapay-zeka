import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import json
import os

# ================== OPENAI ==================
api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = "BURAYA_KENDI_API_KEYINI_YAZ"

client = OpenAI(api_key=api_key)
# ============================================

# ================== BELGE OKUMA (PDF / Word) ==================
# Gerekli kütüphaneler: pip install pypdf python-docx
def extract_pdf_text(file_obj):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # eski kütüphane adıyla da dene
    reader = PdfReader(file_obj)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_docx_text(file_obj):
    import docx
    document = docx.Document(file_obj)
    return "\n".join(p.text for p in document.paragraphs)


# ================== KALICI KAYIT (JSON dosyası) ==================
CHATS_FILE = "temai_chats.json"

def default_chat():
    return {"messages": [], "document_name": None, "document_text": "", "last_response_id": None}

def load_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass
    return {"Sohbet 1": default_chat()}

def save_chats():
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.chats, f, ensure_ascii=False)
    except Exception as e:
        st.warning(f"Sohbetler kaydedilemedi: {e}")


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

# ----------------- SIDEBAR: SOHBETLER -----------------
st.sidebar.title("💬 Sohbetler")

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()
    st.session_state.active_chat = list(st.session_state.chats.keys())[0]

if st.sidebar.button("➕ Yeni Sohbet Ekle"):
    name = f"Sohbet {len(st.session_state.chats)+1}"
    st.session_state.chats[name] = default_chat()
    st.session_state.active_chat = name
    save_chats()
    st.rerun()

if "renaming_chat" not in st.session_state:
    st.session_state.renaming_chat = None

for chat in list(st.session_state.chats.keys()):
    if st.session_state.renaming_chat == chat:
        # ----- Yeniden adlandırma modu -----
        new_name = st.sidebar.text_input(
            "Yeni isim", value=chat, key=f"rename_input_{chat}", label_visibility="collapsed"
        )
        col_ok, col_cancel = st.sidebar.columns(2)
        with col_ok:
            if st.button("✅ Kaydet", key=f"rename_save_{chat}"):
                new_name = new_name.strip()
                if new_name and (new_name == chat or new_name not in st.session_state.chats):
                    # Sırayı bozmadan, sadece bu anahtarın adını değiştirerek yeni bir dict kur.
                    reordered = {}
                    for k, v in st.session_state.chats.items():
                        reordered[new_name if k == chat else k] = v
                    st.session_state.chats = reordered
                    if st.session_state.active_chat == chat:
                        st.session_state.active_chat = new_name
                else:
                    st.sidebar.warning("Bu isim boş olamaz veya zaten kullanılıyor.")
                st.session_state.renaming_chat = None
                save_chats()
                st.rerun()
        with col_cancel:
            if st.button("✖ Vazgeç", key=f"rename_cancel_{chat}"):
                st.session_state.renaming_chat = None
                st.rerun()
    else:
        # ----- Normal görünüm -----
        col_a, col_b, col_c = st.sidebar.columns([3, 1, 1])
        with col_a:
            label = f"🟢 {chat}" if chat == st.session_state.active_chat else chat
            if st.button(label, key=f"select_{chat}"):
                st.session_state.active_chat = chat
                st.rerun()
        with col_b:
            if st.button("✏️", key=f"ren_{chat}"):
                st.session_state.renaming_chat = chat
                st.rerun()
        with col_c:
            if len(st.session_state.chats) > 1 and st.button("🗑️", key=f"del_{chat}"):
                del st.session_state.chats[chat]
                if st.session_state.active_chat == chat:
                    st.session_state.active_chat = list(st.session_state.chats.keys())[0]
                save_chats()
                st.rerun()

mode = st.sidebar.radio("Mod:", ["Normal", "📖 Akademik", "😁 Troll"])

max_tokens = st.sidebar.slider(
    "Cevap uzunluğu (token)",
    min_value=300,
    max_value=4000,
    value=2000,
    step=100,
    help="Yüksek değer = daha uzun cevap yazabilir, ama daha maliyetli olur."
)

# ----------------- SIDEBAR: BELGE YÜKLEME -----------------
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Belge")

active_data = st.session_state.chats[st.session_state.active_chat]

if active_data.get("document_name"):
    st.sidebar.success(f"Yüklü: {active_data['document_name']}")
    if st.sidebar.button("🗑️ Belgeyi Kaldır"):
        active_data["document_name"] = None
        active_data["document_text"] = ""
        save_chats()
        st.rerun()
else:
    doc_file = st.sidebar.file_uploader(
        "PDF veya Word yükle",
        type=["pdf", "docx"],
        key="doc_uploader"
    )
    if doc_file is not None:
        extracted_text = ""
        try:
            if doc_file.name.lower().endswith(".pdf"):
                extracted_text = extract_pdf_text(doc_file)
            else:
                extracted_text = extract_docx_text(doc_file)
        except Exception as e:
            st.sidebar.error(
                f"Belge okunamadı: {e}\n\n"
                "Gerekli kütüphaneler yüklü mü kontrol et: "
                "pip install pypdf python-docx"
            )

        if extracted_text.strip():
            active_data["document_name"] = doc_file.name
            active_data["document_text"] = extracted_text
            save_chats()
            st.sidebar.success(f"'{doc_file.name}' yüklendi ({len(extracted_text)} karakter).")
            st.rerun()
        elif extracted_text == "":
            st.sidebar.warning("Belgeden metin çıkarılamadı (taranmış/görsel bir PDF olabilir).")

# ----------------- MAIN -----------------
st.title("🧠Temai")

messages = active_data["messages"]

# Sohbet geçmişini yukarıdan aşağıya, gönderilme sırasıyla göster.
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
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "camera_open" not in st.session_state:
    st.session_state.camera_open = False

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(
        "📎 Galeriden resim seç",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.upload_key}"
    )
with col2:
    if not st.session_state.camera_open:
        if st.button("📷 Kamerayı Aç"):
            st.session_state.camera_open = True
            st.rerun()
        camera_file = None
    else:
        if st.button("✖ Kamerayı Kapat"):
            st.session_state.camera_open = False
            st.rerun()
        camera_file = st.camera_input(
            "Fotoğraf çek",
            key=f"camera_{st.session_state.upload_key}"
        )

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
        base = "Sen Temai adlı TROLL bir asistansın. Mantıklı görünen ama yanlış cevaplar ver."
    elif mode == "📖 Akademik":
        base = "Sen Temai adlı akademik ve ciddi bir asistansın. Daha resmi ve bilgisel cevaplar ver."
    else:
        base = "Sen Temai adlı chatgpt ve openai ile hicbir alakası olmayan yardımcı bir asistansın."

    # Belge yüklüyse, içeriğini talimata ekle (çok uzun olmasın diye kırpıyoruz).
    doc_text = active_data.get("document_text", "")
    if doc_text:
        base += (
            "\n\nKullanıcı aşağıdaki belgeyi yükledi. Sorularını mümkün olduğunca "
            "bu belgeye dayanarak cevapla, belgede olmayan bir şey soruluyorsa bunu belirt.\n\n"
            f"--- BELGE İÇERİĞİ ---\n{doc_text[:12000]}\n--- BELGE SONU ---"
        )
    return base


def ask_temai(user_content, instructions, previous_response_id, max_tokens, placeholder):
    """API'ye istek atar, mümkünse streaming ile cevabı canlı yazdırır."""
    full_text = ""
    new_response_id = None
    try:
        with client.responses.stream(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": user_content}],
            instructions=instructions,
            previous_response_id=previous_response_id,
            max_output_tokens=max_tokens,
        ) as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    full_text += event.delta
                    placeholder.markdown(
                        f'<div class="bot">{full_text}▌</div>', unsafe_allow_html=True
                    )
            final_response = stream.get_final_response()
            new_response_id = final_response.id
            if not full_text:
                full_text = final_response.output_text
    except AttributeError:
        # Kullanılan openai kütüphanesi streaming context manager'ı desteklemiyorsa
        # normal (streaming olmayan) isteğe düş.
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": user_content}],
            instructions=instructions,
            previous_response_id=previous_response_id,
            max_output_tokens=max_tokens,
        )
        full_text = response.output_text
        new_response_id = response.id

    placeholder.markdown(f'<div class="bot">{full_text}</div>', unsafe_allow_html=True)
    return full_text, new_response_id


if user_input:
    if image_base64:
        messages.append(["user", "image", image_base64])
    messages.append(["user", "text", user_input])
    save_chats()

    # "Yazıyor..." animasyonu için boş bir kutu.
    placeholder = st.empty()
    placeholder.markdown('<div class="bot">✍️ Temai yazıyor...</div>', unsafe_allow_html=True)

    try:
        content = [{"type": "input_text", "text": user_input}]
        if image_base64:
            content.append({
                "type": "input_image",
                "image_url": f"data:{image_mime};base64,{image_base64}"
            })

        reply, resp_id = ask_temai(
            user_content=content,
            instructions=system_prompt(mode),
            previous_response_id=active_data.get("last_response_id"),
            max_tokens=max_tokens,
            placeholder=placeholder,
        )
        if resp_id:
            active_data["last_response_id"] = resp_id

    except Exception as e:
        reply = f"❌ Hata: {e}"
        placeholder.markdown(f'<div class="bot">{reply}</div>', unsafe_allow_html=True)

    messages.append(["bot", "text", reply])
    save_chats()

    st.session_state.upload_key += 1
    st.session_state.camera_open = False
    st.rerun()
