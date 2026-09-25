import streamlit as st
import os
from dotenv import load_dotenv
from google.genai.errors import APIError
from gamegate import fetch_gamegate_data, get_gamegate_chat_session
from btc import fetch_btc_data, get_btc_chat_session
from shinsatech import fetch_shinsatech_data, get_shinsatech_chat_session

# Load biến môi trường
load_dotenv()

def aggressive_clean_ui():
    """
    Workaround: Ép ẩn toàn bộ Header và Footer.
    Lưu ý (Risk): Sẽ mất luôn menu dấu '...', bù lại UI siêu sạch ở góc trên.
    """
    st.markdown("""
        <style>
        /* Tận dụng code của sếp: Xóa sạch header, toolbar, menu và đường kẻ trang trí */
        #MainMenu {visibility: hidden; display: none !important;}
        header {visibility: hidden; display: none !important;}
        div[data-testid="stToolbar"] {visibility: hidden; display: none !important;}
        div[data-testid="stDecoration"] {display: none !important;}
        
        /* Xóa Footer mặc định */
        footer {visibility: hidden; display: none !important;}
        
        /* Bonus: Cố gắng chèn thêm CSS để đè các iframe quảng cáo (hên xui tùy đợt update của Cloud) */
        iframe[title="streamlit-badge"], iframe[src*="badge"] {
            display: none !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Setup Config giao diện (Đã bật layout wide để UI thoáng hơn)
st.set_page_config(page_title="Shinsa - QC Assistant", page_icon="🤖", layout="wide")
aggressive_clean_ui()

# ---------------------------------------------------------
# UI RENDERING: SIDEBAR ROUTING (ĐIỀU HƯỚNG TEAM & TRANG TRÍ)
# ---------------------------------------------------------
st.sidebar.title("⚙️ Workspace")
selected_team = st.sidebar.selectbox("Bạn là member của team:", ["Shinsatech", "GameGate", "BTC"])

st.sidebar.divider() # Dòng kẻ phân cách

# Trang trí thêm phần System Status (Tăng độ xịn sò)
st.sidebar.caption("🔧 **System Status:** 🟢 Online")

# Footer Copyright (Requirement của sếp Nobita)
st.sidebar.markdown("<br>" * 15, unsafe_allow_html=True) # Đẩy copyright xuống đáy
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>Developed by <b>Nobita</b></p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# UI RENDERING: MAIN CHAT AREA (TITLE & GREETING)
# ---------------------------------------------------------
st.title(f"🤖 Shinsa - {selected_team}")

# Lời chào thân thiện (Dynamic theo team)
st.markdown(f"*> 👋 Xin chào các bạn **{selected_team}**! Hôm nay mọi người cần Shinsa support việc gì nào?*")

# Expander hướng dẫn sử dụng (Trang trí cho UI đỡ trống)
with st.expander("💡 Mẹo tương tác với Shinsa (Click để xem)"):
    st.markdown("""
    - **Nhớ chọn đúng Workspace ở side-menu để được hỗ trợ thông tin chính xác nhất bạn nhé**
    - **Lấy Template:** Gõ *"Cho xin template báo cáo daily"*.
    - **Check Quy trình:** Gõ *"Quy trình test alive là gì?"*.
    - Shinsa cũng biết được pass Wifi luôn đó nhé!
    """)

st.divider()

# ---------------------------------------------------------
# LOGIC: STATE MANAGEMENT & CROSS-TALK PREVENTION
# ---------------------------------------------------------
# Bắt buộc xóa Session AI cũ khi đổi Team
if st.session_state.get("current_team") != selected_team:
    st.session_state.messages = []
    st.session_state.current_team = selected_team
    st.session_state.chat_session = None 

# ---------------------------------------------------------
# CACHING MODULE: ISOLATED TTL (BỘ NHỚ ĐỆM TÁCH BIỆT)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_cached_shinsatech_data():
    sheet_url = os.getenv("SHEET_URL_SHINSATECH")
    if not sheet_url: return "ERROR: Thiếu biến SHEET_URL_SHINSATECH"
    return fetch_shinsatech_data(sheet_url)

@st.cache_data(ttl=3600)
def get_cached_gamegate_data():
    sheet_url = os.getenv("SHEET_URL_GAMEGATE")
    if not sheet_url: return "ERROR: Thiếu biến SHEET_URL_GAMEGATE"
    return fetch_gamegate_data(sheet_url)

@st.cache_data(ttl=3600)
def get_cached_btc_data():
    sheet_url = os.getenv("SHEET_URL_BTC")
    if not sheet_url: return "ERROR: Thiếu biến SHEET_URL_BTC"
    return fetch_btc_data(sheet_url)

# ---------------------------------------------------------
# AI INITIALIZATION
# ---------------------------------------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ [QC Alert] Thiếu biến môi trường GEMINI_API_KEY")
    st.stop()

if selected_team == "Shinsatech":
    current_data = get_cached_shinsatech_data()
    init_session_func = get_shinsatech_chat_session
    hash_key = "hash_shinsatech"
elif selected_team == "GameGate":
    current_data = get_cached_gamegate_data()
    init_session_func = get_gamegate_chat_session
    hash_key = "hash_gamegate"
else:
    current_data = get_cached_btc_data()
    init_session_func = get_btc_chat_session
    hash_key = "hash_btc"

if "ERROR" in current_data:
    st.error(f"⚠️ [QC Alert] Lỗi hệ thống: {current_data}")
    st.stop()

# Cơ chế Reload AI Session 
current_hash = hash(current_data)
if st.session_state.get("chat_session") is None or st.session_state.get(hash_key) != current_hash:
    with st.spinner(f"⏳ Đang nạp Knowledge Base mới nhất của {selected_team}..."):
        try:
            api_client, chat_session = init_session_func(api_key, current_data)
            st.session_state.api_client = api_client 
            st.session_state.chat_session = chat_session
            st.session_state[hash_key] = current_hash
        except Exception as e:
            st.error(f"❌ Lỗi boot hệ thống AI: {str(e)}")
            st.stop()

# ---------------------------------------------------------
# CHAT EXECUTION
# ---------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(f"Nhập yêu cầu cho Shinsa ở đây nha..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except APIError as e:
            if e.code == 429 or "429" in str(e):
                st.error("⚠️ [QC Alert] Shinsa đang bị quá tải do nhận quá nhiều câu hỏi cùng lúc. Bạn chờ 1 phút rồi thử lại nhé!")
            else:
                st.error(f"❌ Lỗi API từ Google: {str(e)}")
        except Exception as e:
            st.error(f"❌ Lỗi hệ thống: {str(e)}")
