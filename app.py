import streamlit as st
import pandas as pd
import os
from openai import OpenAI

import os
from datetime import datetime

stats_file = "stats.csv"

# Nếu chưa có file thì tạo
if not os.path.exists(stats_file):
    df_stats = pd.DataFrame(columns=["date", "visits", "questions"])
    df_stats.to_csv(stats_file, index=False)

# ====== CONFIG ======
st.set_page_config(page_title="Hướng Nghiệp AI", layout="wide")

# ====== CUSTOM CSS ======
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}
<style>
.chat-container {
    max-height: 70vh;
    overflow-y: auto;
    padding: 20px;
    background: #f7f9fc;
    border-radius: 15px;
}

.user-bubble {
    background: linear-gradient(135deg, #4CAF50, #2e7d32);
    color: white;
    padding: 12px 16px;
    border-radius: 18px;
    margin: 8px 0;
    text-align: right;
    max-width: 70%;
    margin-left: auto;
}

.bot-bubble {
    background: white;
    padding: 12px 16px;
    border-radius: 18px;
    margin: 8px 0;
    border: 1px solid #ddd;
    max-width: 70%;
}
</style>
""", unsafe_allow_html=True)

# ====== HEADER ======
st.markdown("""
<h1 style='text-align: center; font-size: 42px;'>
🎓 AI Hướng Nghiệp
</h1>

<p style='text-align: center; font-size:18px; color: gray;'>
Khám phá nghề nghiệp phù hợp với bạn bằng AI 🚀
</p>

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
    if st.button("🗑️ Xóa chat"):
        st.session_state.messages = []
        st.rerun()
# ====== INIT CHAT ======
if "messages" not in st.session_state:
    st.session_state.messages = []

# ====== MAIN LAYOUT ======
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# ====== CHAT KIỂU CHATGPT ======
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

if user_input and user_input.strip() != "":
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("🤖 AI đang suy nghĩ..."):

        # SEARCH
        keywords = user_input.lower().split()

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

        # AI
        import os
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )

        if mode == "Gợi ý nghề":
            system_prompt = "Bạn là chuyên gia hướng nghiệp. LUÔN trả lời bằng tiếng Việt, dễ hiểu cho học sinh."
        elif mode == "Khám phá nghề":
            system_prompt = "Giải thích nghề chi tiết, dễ hiểu, LUÔN bằng tiếng Việt."
        else:
            system_prompt = """
Bạn là chuyên gia hướng nghiệp cho học sinh.

YÊU CẦU:
- Luôn trả lời bằng tiếng Việt
- Viết rõ ràng, dễ hiểu
- Chia ý bằng bullet hoặc số
- Có ví dụ thực tế
- Giọng thân thiện, như thầy cô hướng dẫn

CẤU TRÚC TRẢ LỜI:
1. Giải thích ngắn gọn
2. Ví dụ thực tế
3. Gợi ý thêm (nếu có)
"""

        prompt = f"""
{system_prompt}

⚠️ BẮT BUỘC: Trả lời hoàn toàn bằng tiếng Việt. Không dùng tiếng Anh và các ngôn ngữ khác.

Dữ liệu:
{context}

Câu hỏi: {user_input}
"""

        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content

        # ✅ DÒNG QUAN TRỌNG (phải cùng cấp với response)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ====== FOOTER ======
st.divider()
st.caption("🚀 Được tạo bởi Hồ Xuân Hiệp - Tiếp tục được nâng cấp để hoàn thiện")
