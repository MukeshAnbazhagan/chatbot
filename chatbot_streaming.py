import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import groq
import time  # 🔹 Added to slow down streaming

# ---- Hardcoded Confluence & API Credentials ---- #
CONFLUENCE_URL = "https://mukeshanbazhagan.atlassian.net/wiki/rest/api/content/"
PAGE_ID = "98496"
EMAIL = "mukeshanbazhagan@gmail.com"
API_TOKEN = "ATATT3xFfGF0rejtoNUvh3g_6juoEzCWycl4bM9SJxX0FZF3M_GsmGwLbRgDC3kqHIfMrQfCxyTJUAANv2tIuZom3c-b_DdMzC1y7NjtJfsVYD-7Rr29GEoCWM2Rpk508CreEknDfKoO3YZvq_N6TPdeqth5z7cff6an5n_Zps9zXTcc5Hw3Yfs=D9AE43E7"
GROQ_API_KEY = "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"

# ---- Initialize Chat History ---- #
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "system", "content": "You are an AI assistant for Confluence pages."}
    ]

# ---- Function to Fetch Confluence Page ---- #
def fetch_confluence_page():
    url = f"{CONFLUENCE_URL}{PAGE_ID}?expand=body.storage"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(EMAIL, API_TOKEN),
        headers={"Content-Type": "application/json"},
    )
    if response.status_code == 200:
        data = response.json()
        return data["body"]["storage"]["value"]
    else:
        st.error(f"❌ Error fetching page: {response.status_code} {response.text}")
        return None

# ---- Function to Extract Text from HTML ---- #
def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n").strip()

# ---- Function to Stream AI Response (with Slower Speed) ---- #
def stream_response():
    client = groq.Client(api_key=GROQ_API_KEY)
    
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=st.session_state["chat_history"],
        temperature=0.3,
        stream=True,  # Enable streaming
    )

    for chunk in response:
        content = chunk.choices[0].delta.content  # 🔹 Ensure content is valid
        if content:  # 🔹 Prevent NoneType error
            yield content
            time.sleep(0.05)  # 🔹 Slow down streaming (Adjust speed as needed)

# ---- Streamlit UI ---- #
st.title("🤖 Confluence AI Assistant")
st.write("Ask questions based on the Confluence page content!")

# ---- Fetch & Process Confluence Page ---- #
with st.spinner("Fetching Confluence page..."):
    page_html = fetch_confluence_page()

if page_html:
    page_text = extract_text_from_html(page_html)
    
    if "summary" not in st.session_state:
        with st.spinner("Summarizing..."):
            summary = "".join(stream_response())  # Stream summary response
        st.session_state["summary"] = summary
    
    st.subheader("📌 Summary")
    st.write(st.session_state["summary"])

    # ---- Display Chat History in Modern UI ---- #
    st.subheader("💬 Chat with AI")
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(f"**You:** {msg['content']}")
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(f"🤖 **AI:** {msg['content']}")

    # ---- User Input Field ---- #
    user_question = st.chat_input("Ask a question...")

    if user_question:
        st.session_state["chat_history"].append({"role": "user", "content": user_question})
        
        # Stream AI response with slower speed
        with st.chat_message("assistant"):
            st.markdown("🤖 **AI:** ", unsafe_allow_html=True)
            response_placeholder = st.empty()
            
            streamed_text = ""
            for chunk in stream_response():
                streamed_text += chunk  # Append chunk to full response
                response_placeholder.markdown(f"🤖 **AI:** {streamed_text}")  
        
        # Store AI response in history
        st.session_state["chat_history"].append({"role": "assistant", "content": streamed_text})

    # ---- Reset Chat Button ---- #
    if st.button("🔄 Reset Chat"):
        st.session_state["chat_history"] = [
            {"role": "system", "content": "You are an AI assistant for Confluence pages."}
        ]
        st.experimental_rerun()
