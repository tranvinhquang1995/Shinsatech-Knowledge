import streamlit as st
import os
from dotenv import load_dotenv
from google.genai.errors import APIError
from gamegate import fetch_gamegate_data, get_gamegate_chat_session
from btc import fetch_btc_data, get_btc_chat_session

# Load biến môi trường
load_dotenv()

st.set_page_config(page_title="Shinsa - QC Virtual Assistant", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# UI RENDERING: SIDEBAR ROUTING (ĐIỀU HƯỚNG TEAM)
# ---------------------------------------------------------
st.sidebar.title("⚙️ Bảng Điều Khiển")
selected_team = st.sidebar.selectbox("Lựa chọn Workspace:", ["GameGate", "BTC"])

st.title(f"🤖 Shinsa - Trợ lý Team {selected_team}")

# Risk Assessment: Ngăn chặn lỗi chéo Data (Cross-talk) khi switch team.
# Bắt buộc xóa Session AI cũ và clear lịch sử Chat hiện tại.
if st.session_state.get("current_team") != selected_team:
    st.session_state.messages = []
    st.session_state.current_team = selected_team
    st.session_state.chat_session = None 

# ---------------------------------------------------------
# CACHING MODULE: ISOLATED TTL (BỘ NHỚ ĐỆM TÁCH BIỆT)
# ---------------------------------------------------------
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
# STATE MANAGEMENT & AI INITIALIZATION
# ---------------------------------------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ [QC Alert] Thiếu biến môi trường GEMINI_API_KEY")
    st.stop()

# Đẩy luồng kéo Data dựa vào Option sếp chọn trên Sidebar
if selected_team == "GameGate":
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

# Cơ chế Reload AI Session khi Hash Data thay đổi (Sau 1 tiếng TTL Expire)
current_hash = hash(current_data)
if st.session_state.get("chat_session") is None or st.session_state.get(hash_key) != current_hash:
    with st.spinner(f"Đang đồng bộ Knowledge Base mới nhất của team {selected_team}..."):
        try:
            # Hứng cả client và chat_session từ module, ném vào st.session_state để chống Garbage Collection
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

if prompt := st.chat_input(f"Nhập câu hỏi cho Shinsa {selected_team}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except APIError as e:
            # Handle Edge Case Rate Limit
            if e.code == 429 or "429" in str(e):
                st.error("⚠️ Shinsa đang bị quá tải do nhận quá nhiều câu hỏi cùng lúc. Bạn chờ 1 phút rồi thử lại nhé!")
            else:
                st.error(f"❌ Lỗi API từ Google: {str(e)}")
        except Exception as e:
            st.error(f"❌ Lỗi hệ thống: {str(e)}")
