import streamlit as st
import pandas as pd
from openai import OpenAI

# ====== CONFIG ======
st.set_page_config(page_title="Hướng Nghiệp AI", layout="wide")

# ====== CUSTOM CSS ======
st.markdown("""
<style>
.chat-container {
    border-radius: 20px;
    padding: 20px;
    background-color: #f5f7fb;
}
.user-bubble {
    background-color: #4CAF50;
    color: white;
    padding: 10px 15px;
    border-radius: 15px;
    margin: 5px 0;
    text-align: right;
}
.bot-bubble {
    background-color: #ffffff;
    padding: 10px 15px;
    border-radius: 15px;
    margin: 5px 0;
    border: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ====== HEADER ======
st.title("🎓 AI Hướng Nghiệp")
st.caption("Trải nghiệm tư vấn nghề nghiệp như người thật")

# ====== LOAD DATA ======
@st.cache_data
def load_data():
    return pd.read_excel("kho_du_lieu_300_nghe.xlsx")

df = load_data()

# ====== SIDEBAR ======
with st.sidebar:
    st.header("⚙️ Tùy chọn")
    mode = st.radio("Chế độ:", ["Hỏi đáp", "Khám phá nghề", "Gợi ý nghề"])

    st.divider()
    st.write("📊 Tổng số nghề:", len(df))

# ====== INIT CHAT ======
if "messages" not in st.session_state:
    st.session_state.messages = []

# ====== MAIN LAYOUT ======
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# ====== INPUT ======
user_input = st.chat_input("💬 Hỏi về nghề bạn quan tâm...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ====== SEARCH ======
    matched = df[df.apply(lambda row: user_input.lower() in str(row).lower(), axis=1)]
    context = matched.head(3).to_string() if not matched.empty else ""

       # ====== AI ======
    import os
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    if mode == "Gợi ý nghề":
        system_prompt = "Bạn là chuyên gia hướng nghiệp. Hãy gợi ý nghề phù hợp với học sinh dựa trên câu hỏi."
    elif mode == "Khám phá nghề":
        system_prompt = "Giải thích nghề chi tiết, dễ hiểu, có ví dụ thực tế."
    else:
        system_prompt = "Trả lời ngắn gọn, dễ hiểu cho học sinh."

    prompt = f"""
{system_prompt}

Dữ liệu:
{context}

Câu hỏi: {user_input}
"""

    response = client.chat.completions.create(
    model="openchat/openchat-3.5-0106",
    messages=[{"role": "user", "content": prompt}]
)

    answer = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ====== FOOTER ======
st.divider()
st.caption("🚀 Demo bởi AI - Có thể nâng cấp thành app thật")
