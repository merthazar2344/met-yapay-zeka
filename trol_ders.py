import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import json
import os
from datetime import datetime

# ================== OPENAI ==================
api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = "BURAYA_KENDI_API_KEYINI_YAZ"

client = OpenAI(api_key=api_key)
# ============================================

# ================== BELGE OKUMA (PDF / Word) ==================
def extract_pdf_text(file_obj):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
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


st.set_page_config(page_title="Temai", page_icon="🧠", layout="wide")

# ----------------- CSS (genel görünüm cilası) -----------------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #1a1a1a 0%, #0f0f0f 60%);
}
section[data-testid="stSidebar"] {
    background-color: #161616;
    border-right: 1px solid #2a2a2a;
}
h1 {
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}
.stChatMessage {
    border-radius: 16px;
    padding: 4px 6px;
}
.temai-toolbar {
    background: #1b1b1b;
    border: 1px solid #2a2a2a;
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 14px;
}
.temai-timestamp {
    font-size: 11px;
    color: #8a8a8a;
    margin-top: -6px;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: SADECE SOHBET LİSTESİ -----------------
st.sidebar.title("💬 Sohbetler")

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()
    st.session_state.active_chat = list(st.session_state.chats.keys())[0]

if st.sidebar.button("➕ Yeni Sohbet Ekle", use_container_width=True):
    name = f"Sohbet {len(st.session_state.chats)+1}"
    st.session_state.chats[name] = default_chat()
    st.session_state.active_chat = name
    save_chats()
    st.rerun()

st.sidebar.markdown("---")

if "renaming_chat" not in st.session_state:
    st.session_state.renaming_chat = None

for chat in list(st.session_state.chats.keys()):
    if st.session_state.renaming_chat == chat:
        new_name = st.sidebar.text_input(
            "Yeni isim", value=chat, key=f"rename_input_{chat}", label_visibility="collapsed"
        )
        col_ok, col_cancel = st.sidebar.columns(2)
        with col_ok:
            if st.button("✅ Kaydet", key=f"rename_save_{chat}", use_container_width=True):
                new_name = new_name.strip()
                if new_name and (new_name == chat or new_name not in st.session_state.chats):
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
            if st.button("✖ Vazgeç", key=f"rename_cancel_{chat}", use_container_width=True):
                st.session_state.renaming_chat = None
                st.rerun()
    else:
        col_a, col_b, col_c = st.sidebar.columns([3, 1, 1])
        with col_a:
            label = f"🟢 {chat}" if chat == st.session_state.active_chat else chat
            if st.button(label, key=f"select_{chat}", use_container_width=True):
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

# ----------------- MAIN -----------------
st.title("🧠 Temai")

active_data = st.session_state.chats[st.session_state.active_chat]

# ----------------- ARAÇ ÇUBUĞU (mod, token, belge) -----------------
with st.container():
    st.markdown('<div class="temai-toolbar">', unsafe_allow_html=True)
    tool_col1, tool_col2, tool_col3 = st.columns([2, 1.4, 2])

    with tool_col1:
        mode = st.radio(
            "Mod:",
            ["Normal", "📖 Akademik", "😁 Troll"],
            horizontal=True,
            label_visibility="collapsed"
        )

    with tool_col2:
        with st.popover("⚙️ Ayarlar"):
            max_tokens = st.slider(
                "Cevap uzunluğu (token)",
                min_value=300,
                max_value=4000,
                value=2000,
                step=100,
                help="Yüksek değer = daha uzun cevap yazabilir, ama daha maliyetli olur."
            )

    with tool_col3:
        if active_data.get("document_name"):
            doc_col1, doc_col2 = st.columns([3, 1])
            with doc_col1:
                st.markdown(f"📄 **{active_data['document_name']}**")
            with doc_col2:
                if st.button("🗑️", key="remove_doc"):
                    active_data["document_name"] = None
                    active_data["document_text"] = ""
                    save_chats()
                    st.rerun()
        else:
            st.caption("📄 Belge eklenmedi")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- SOHBET GEÇMİŞİ -----------------
messages = active_data["messages"]

for msg in messages:
    if len(msg) == 4:
        role, kind, content, ts = msg
    else:
        role, kind, content = msg
        ts = ""

    display_role = "user" if role == "user" else "assistant"
    avatar = "🙂" if role == "user" else "🧠"

    with st.chat_message(display_role, avatar=avatar):
        if kind == "image":
            st.image(io.BytesIO(base64.b64decode(content)))
        else:
            st.markdown(content)
        if ts:
            st.markdown(f'<div class="temai-timestamp">{ts}</div>', unsafe_allow_html=True)

# ----------------- TEK BUTON: RESİM + BELGE EKLEME -----------------
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "camera_open" not in st.session_state:
    st.session_state.camera_open = False

attach_col1, attach_col2 = st.columns([4, 1])
with attach_col1:
    picked_upload = st.file_uploader(
        "📎 Resim veya Belge Ekle (PNG, JPG, PDF, DOCX)",
        type=["png", "jpg", "jpeg", "pdf", "docx"],
        key=f"uploader_{st.session_state.upload_key}"
    )
with attach_col2:
    if not st.session_state.camera_open:
        if st.button("📷 Kamera", use_container_width=True):
            st.session_state.camera_open = True
            st.rerun()
        camera_file = None
    else:
        if st.button("✖ Kapat", use_container_width=True):
            st.session_state.camera_open = False
            st.rerun()
        camera_file = st.camera_input(
            "Fotoğraf çek",
            key=f"camera_{st.session_state.upload_key}"
        )

picked_file = camera_file if camera_file is not None else picked_upload

image_base64 = None
image_mime = "image/png"

if picked_file is not None:
    file_name = getattr(picked_file, "name", "kamera.png").lower()
    is_image = camera_file is not None or file_name.endswith((".png", ".jpg", ".jpeg"))

    if is_image:
        image = Image.open(picked_file)
        st.caption("Gönderilecek resim (mesajla birlikte sohbete eklenecek):")
        st.image(image, use_container_width=True)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_base64 = base64.b64encode(buf.getvalue()).decode()
    else:
        # PDF veya DOCX - sadece daha önce eklenmemişse işle (her rerun'da tekrar işlemesin diye)
        if active_data.get("document_name") != picked_file.name:
            try:
                if file_name.endswith(".pdf"):
                    extracted_text = extract_pdf_text(picked_file)
                else:
                    extracted_text = extract_docx_text(picked_file)

                if extracted_text.strip():
                    active_data["document_name"] = picked_file.name
                    active_data["document_text"] = extracted_text
                    save_chats()
                    st.success(
                        f"📄 '{picked_file.name}' belge olarak eklendi "
                        f"({len(extracted_text)} karakter). Artık sorularını bu belgeye göre cevaplayabilirim."
                    )
                else:
                    st.warning("Belgeden metin çıkarılamadı (taranmış/görsel bir PDF olabilir).")
            except Exception as e:
                st.error(
                    f"Belge okunamadı: {e}\n\n"
                    "Gerekli kütüphaneler yüklü mü kontrol et: pip install pypdf python-docx"
                )

user_input = st.chat_input("sohbete başlamak için bir şey yazın...")

def system_prompt(mode):
    if mode == "😁 Troll":
        base = "Sen Temai adlı TROLL bir asistansın. Mantıklı görünen ama yanlış cevaplar ver."
    elif mode == "📖 Akademik":
        base = "Sen Temai adlı akademik ve ciddi bir asistansın. Daha resmi ve bilgisel cevaplar ver."
    else:
        base = "Sen Temai adlı chatgpt ve openai ile hicbir alakası olmayan yardımcı bir asistansın."

    doc_text = active_data.get("document_text", "")
    if doc_text:
        base += (
            "\n\nKullanıcı aşağıdaki belgeyi yükledi. Sorularını mümkün olduğunca "
            "bu belgeye dayanarak cevapla, belgede olmayan bir şey soruluyorsa bunu belirt.\n\n"
            f"--- BELGE İÇERİĞİ ---\n{doc_text[:12000]}\n--- BELGE SONU ---"
        )
    return base


def ask_temai(user_content, instructions, previous_response_id, max_tokens, placeholder):
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
                    placeholder.markdown(full_text + "▌")
            final_response = stream.get_final_response()
            new_response_id = final_response.id
            if not full_text:
                full_text = final_response.output_text
    except AttributeError:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": user_content}],
            instructions=instructions,
            previous_response_id=previous_response_id,
            max_output_tokens=max_tokens,
        )
        full_text = response.output_text
        new_response_id = response.id

    placeholder.markdown(full_text)
    return full_text, new_response_id


if user_input:
    now_str = datetime.now().strftime("%H:%M")

    if image_base64:
        messages.append(["user", "image", image_base64, now_str])
        with st.chat_message("user", avatar="🙂"):
            st.image(io.BytesIO(base64.b64decode(image_base64)))
    messages.append(["user", "text", user_input, now_str])
    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_input)
    save_chats()

    with st.chat_message("assistant", avatar="🧠"):
        placeholder = st.empty()
        placeholder.markdown("✍️ Temai yazıyor...")

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
            placeholder.markdown(reply)

    messages.append(["bot", "text", reply, datetime.now().strftime("%H:%M")])
    save_chats()

    st.session_state.upload_key += 1
    st.session_state.camera_open = False
    st.rerun()
