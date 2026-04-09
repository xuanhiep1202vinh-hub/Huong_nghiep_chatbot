import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from datetime import datetime

# ====== GOOGLE SHEET ======
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client_gs = gspread.authorize(creds)
try:
sheet = client_gs.open_by_url(
    "https://docs.google.com/spreadsheets/d/1NUv2oLQhGjMjXKJNOXbq36JCnkKjtE9OvKQ5UIvCor8/edit"
).sheet1
except Exception as e:
    st.error(f"❌ Lỗi kết nối Google Sheet: {e}")

# ====== CONFIG ======
st.set_page_config(page_title="Hướng Nghiệp AI", layout="wide")

# ====== CSS ======
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}

.chat-container {
    max-height: 70vh;
    overflow-y: auto;
    padding: 20px;
    background: #f7f9fc;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

# ====== HEADER ======
st.markdown("""
<h1 style='text-align: center; font-size: 42px;'>🎓 AI Hướng Nghiệp</h1>
<p style='text-align: center; color: gray;'>Khám phá nghề nghiệp phù hợp với bạn bằng AI 🚀</p>
<hr>
""", unsafe_allow_html=True)

# ====== LOAD DATA ======
@st.cache_data
def load_data():
    return pd.read_excel("kho_du_lieu_1000_nghe.xlsx")

df = load_data()

# ====== LOAD STATS FROM GOOGLE SHEET ======
today = datetime.now().strftime("%Y-%m-%d")

data = sheet.get_all_records()
df_stats = pd.DataFrame(data)

if df_stats.empty or today not in df_stats["date"].values:
    sheet.append_row([today, 1, 0])
else:
    row_index = df_stats.index[df_stats["date"] == today][0] + 2
    current_visits = int(df_stats.loc[df_stats["date"] == today, "visits"].values[0])
    sheet.update_cell(row_index, 2, current_visits + 1)

# Reload
data = sheet.get_all_records()
df_stats = pd.DataFrame(data)

# ====== SIDEBAR ======
with st.sidebar:
    st.header("⚙️ Tùy chọn")
    mode = st.radio("Chế độ:", ["Hỏi đáp", "Khám phá nghề", "Gợi ý nghề"])

    st.divider()
    st.write("📊 Tổng số nghề:", len(df))

    if st.button("🗑️ Xóa chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("📊 Thống kê")

    today_data = df_stats[df_stats["date"] == today]

    if not today_data.empty:
        st.write("👀 Hôm nay:", int(today_data["visits"].values[0]))
        st.write("💬 Hỏi hôm nay:", int(today_data["questions"].values[0]))

    st.write("📈 Tổng truy cập:", int(df_stats["visits"].sum()))
    st.write("📈 Tổng câu hỏi:", int(df_stats["questions"].sum()))

# ====== INIT CHAT ======
if "messages" not in st.session_state:
    st.session_state.messages = []

# ====== CHAT UI ======
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ====== INPUT ======
user_input = st.chat_input("💬 Hỏi về nghề bạn quan tâm...")

# ====== GỢI Ý ======
st.write("💡 Bạn có thể hỏi:")
col1, col2, col3, col4 = st.columns(4)

if col1.button("💰 Top ngành lương cao nhất hiện nay là gì?"):
    user_input = "Top ngành lương cao nhất hiện nay là gì?"

if col2.button("🧠 Test nhanh: Bạn hợp nghề nào?"):
    user_input = "Test nhanh: Tôi hợp nghề gì?"

if col3.button("🤖 Nghề nào không bị AI thay thế?"):
    user_input = "Nghề nào ít bị AI thay thế?"

if col4.button("🎓 Học lực trung bình nên chọn ngành gì?"):
    user_input = "Học lực trung bình nên chọn ngành gì?"

# ====== XỬ LÝ ======
if user_input and user_input.strip() != "":

    # ====== UPDATE QUESTIONS ======
    data = sheet.get_all_records()
    df_stats = pd.DataFrame(data)

    if today in df_stats["date"].values:
        row_index = df_stats.index[df_stats["date"] == today][0] + 2
        current_q = int(df_stats.loc[df_stats["date"] == today, "questions"].values[0])
        sheet.update_cell(row_index, 3, current_q + 1)

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("🤖 AI đang suy nghĩ..."):

        # ====== SEARCH ======
        matched = df[df.apply(lambda row: user_input.lower() in str(row).lower(), axis=1)]

        if not matched.empty:
            rows = matched.head(3).to_dict(orient="records")
            context = ""

            for r in rows:
                context += f"""
Tên nghề: {r.get('Tên nghề', '')}
Mô tả: {r.get('Mô tả', '')}
Kỹ năng: {r.get('Kỹ năng', '')}
Lương: {r.get('Mức lương', '')}
-----------------
"""
        else:
            context = ""

        # ====== AI ======
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )

        system_prompt = """
Bạn là chuyên gia hướng nghiệp cho học sinh.

YÊU CẦU:
- Luôn trả lời bằng tiếng Việt
- Rõ ràng, dễ hiểu
- Có ví dụ thực tế
- Trình bày dạng gạch đầu dòng
"""

        prompt = f"""
{system_prompt}

Dữ liệu:
{context}

Câu hỏi: {user_input}
"""

        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ====== FOOTER ======
st.divider()
st.caption("🚀 Được tạo bởi Hồ Xuân Hiệp - AI Career Assistant")
