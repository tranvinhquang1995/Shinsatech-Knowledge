import streamlit as st
from gamegate import fetch_gamegate_data, generate_gamegate_answer
from btc import fetch_btc_data, generate_btc_answer

# Setup cấu hình trang
st.set_page_config(page_title="QC Knowledge Base", page_icon="🛡️", layout="centered")

def main():
    # Setup UI Sidebar (Routing)
    st.sidebar.title("🏢 Team Workspace")
    team_selection = st.sidebar.radio(
        "Chọn Team để truy vấn quy trình:",
        ("Team GameGate", "Team BTC")
    )
    
    # Render Copyright vào Side menu
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='text-align: center; color: gray; font-size: 13px;'>Developed by Nobita</p>", 
        unsafe_allow_html=True
    )
    
    # Load Secrets
    try:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        SHEET_URL_GAMEGATE = st.secrets["SHEET_URL_GAMEGATE"]
        SHEET_URL_BTC = st.secrets["SHEET_URL_BTC"]
    except KeyError:
        st.error("⚠️ Missing Configuration trong Streamlit Secrets!")
        st.stop()

    # Xử lý State & Cache độc lập cho từng team để tránh Data mix-up
    current_team_key = "gamegate" if team_selection == "Team GameGate" else "btc"
    
    # Khởi tạo Chat History riêng cho từng team
    if f"messages_{current_team_key}" not in st.session_state:
        st.session_state[f"messages_{current_team_key}"] = []

    # Caching data độc lập theo team
    @st.cache_data(ttl=3600)
    def get_data_gamegate(url):
        return fetch_gamegate_data(url)

    @st.cache_data(ttl=3600)
    def get_data_btc(url):
        return fetch_btc_data(url)

    # Render Header
    st.title(f"🤖 Trợ lý QC - {team_selection}")
    st.markdown(f"Hệ thống truy vấn quy trình làm việc nội bộ dành riêng cho **{team_selection}**.")
    
    # Fetch Context Data tùy theo team được chọn
    with st.spinner(f"Đang đồng bộ dữ liệu từ {team_selection}..."):
        if current_team_key == "gamegate":
            context = get_data_gamegate(SHEET_URL_GAMEGATE)
        else:
            context = get_data_btc(SHEET_URL_BTC)
            
        if "Error" in context:
            st.error(f"Lỗi load Data: {context}")
            st.stop()

    # Render Chat History
    for message in st.session_state[f"messages_{current_team_key}"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Xử lý User Input (Test Execution)
    if prompt := st.chat_input(f"Hỏi tôi về quy trình của {team_selection}..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state[f"messages_{current_team_key}"].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Đang tra cứu Knowledge Base..."):
                if current_team_key == "gamegate":
                    answer = generate_gamegate_answer(GEMINI_API_KEY, context, prompt)
                else:
                    answer = generate_btc_answer(GEMINI_API_KEY, context, prompt)
                st.markdown(answer)
        st.session_state[f"messages_{current_team_key}"].append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()
