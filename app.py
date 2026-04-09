import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from datetime import datetime

# ====== FILE THỐNG KÊ ======
stats_file = "stats.csv"

if not os.path.exists(stats_file):
    df_stats = pd.DataFrame(columns=["date", "visits", "questions"])
    df_stats.to_csv(stats_file, index=False)

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

# ====== TRACK VISITS ======
today = datetime.now().strftime("%Y-%m-%d")
df_stats = pd.read_csv(stats_file)

if today in df_stats["date"].values:
    df_stats.loc[df_stats["date"] == today, "visits"] += 1
else:
    new_row = pd.DataFrame([{
        "date": today,
        "visits": 1,
        "questions": 0
    }])
    df_stats = pd.concat([df_stats, new_row], ignore_index=True)

df_stats.to_csv(stats_file, index=False)

# ====== SIDEBAR ======
with st.sidebar:
    st.header("⚙️ Tùy chọn")
    mode = st.radio("Chế độ:", ["Hỏi đáp", "Khám phá nghề", "Gợi ý nghề"])

    st.divider()
    st.write("📊 Tổng số nghề:", len(df))

    # Nút xoá chat
    if st.button("🗑️ Xóa chat"):
        st.session_state.messages = []
        st.rerun()

    # ====== THỐNG KÊ ======
    st.divider()
    st.subheader("📊 Thống kê")

    df_stats = pd.read_csv(stats_file)
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
col1, col2, col3 = st.columns(3)

if col1.button("Nghề IT là gì?"):
    user_input = "Nghề IT là gì?"

elif col2.button("Ngành nào lương cao?"):
    user_input = "Ngành nào lương cao?"

elif col3.button("Tôi hợp nghề gì?"):
    user_input = "Tôi hợp nghề gì?"

# ====== XỬ LÝ ======
if user_input and user_input.strip() != "":

    # TRACK QUESTIONS
    df_stats = pd.read_csv(stats_file)
    df_stats.loc[df_stats["date"] == today, "questions"] += 1
    df_stats.to_csv(stats_file, index=False)

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

        if mode == "Gợi ý nghề":
            system_prompt = "Bạn là chuyên gia hướng nghiệp. LUÔN trả lời bằng tiếng Việt, dễ hiểu."
        elif mode == "Khám phá nghề":
            system_prompt = "Giải thích nghề chi tiết, dễ hiểu, LUÔN bằng tiếng Việt."
        else:
            system_prompt = """
Bạn là chuyên gia hướng nghiệp cho học sinh.

YÊU CẦU:
- Luôn trả lời bằng tiếng Việt
- Viết rõ ràng, dễ hiểu
- Có ví dụ thực tế
"""

        prompt = f"""
{system_prompt}

⚠️ BẮT BUỘC: Trả lời hoàn toàn bằng tiếng Việt.

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
