import streamlit as st
import requests
import pandas as pd
from typing import List
from pathlib import Path

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="NetOps AI Sentinel",
    page_icon="🛡️",
    layout="wide"
)

# --- STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .report-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def call_api(endpoint: str, method: str = "GET", data: dict = None):
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=20)
        else:
            response = requests.post(url, json=data, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to Backend. Is FastAPI running at localhost:8000?")
        return None
    except requests.exceptions.ReadTimeout:
        st.error("Backend request timed out. The server is still busy or blocked; check the FastAPI terminal logs.")
        return None

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("NetOps Sentinel")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Knowledge Brain (Chat)", "Anomaly Scanner", "RCA Generator"])
st.sidebar.markdown("---")
st.sidebar.info("Status: Backend Connected")

# --- PAGE 1: KNOWLEDGE BRAIN (RAG) ---
if page == "Knowledge Brain (Chat)":
    st.title("Knowledge Brain")
    st.markdown("Ask questions about historical tickets, SBC configs, or CUCM errors.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("e.g., How do we fix a SIP 503 error on the London SBC?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                res = call_api("/chat/ask", "POST", {"query": prompt})
                if res:
                    answer = res.get("answer", "No answer found.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

# --- PAGE 2: ANOMALY SCANNER ---
elif page == "Anomaly Scanner":
    st.title("Log Anomaly Scanner")
    st.markdown("Paste your system logs below to detect critical failures.")
    
    log_input = st.text_area("System Logs", height=300, placeholder="Paste log lines here...")
    
    if st.button("Scan for Anomalies"):
        if log_input:
            with st.spinner("Analyzing log patterns..."):
                logs_list = log_input.split("\n")
                res = call_api("/anomalies/scan", "POST", {"logs": logs_list})
                
                if res and res.get("anomalies"):
                    st.success(f"Detected {len(res['anomalies'])} anomalies!")
                    for item in res['anomalies']:
                        count_label = f" x{item.get('count', 1)}" if item.get("count", 1) > 1 else ""
                        with st.expander(f"{item['label']} - {item['type']}{count_label}"):
                            st.code(item['line'], language="log")
                            st.markdown(f"**AI Insight:** {item['ai_insight']}")
                else:
                    st.info("No anomalies detected. System appears healthy.")
        else:
            st.warning("Please provide log data first.")

# --- PAGE 3: RCA GENERATOR ---
elif page == "RCA Generator":
    st.title("Auto-RCA Generator")
    st.markdown("Generate a professional PDF Root Cause Analysis report.")
    
    col1, col2 = st.columns(2)
    with col1:
        ticket_id = st.text_input("Ticket ID", placeholder="e.g. TICKET-1001")
    with col2:
        # Use a mock log for the demo
        logs_mock = st.text_area("Associate Logs", height=150, placeholder="Paste logs related to this ticket...")

    if st.button("Generate Final RCA Report"):
        if ticket_id and logs_mock:
            with st.spinner("Synthesizing RCA Report via Groq..."):
                res = call_api("/rca/generate", "POST", {
                    "ticket_id": ticket_id, 
                    "logs": logs_mock.split("\n")
                })
                
                if res:
                    st.balloons()
                    st.success("RCA Report Generated Successfully!")
                    st.markdown(f"**File Path:** `{res['path']}`")
                    pdf_path = Path(res["path"])
                    if pdf_path.exists():
                        st.download_button(
                            label="Download RCA PDF",
                            data=pdf_path.read_bytes(),
                            file_name=pdf_path.name,
                            mime="application/pdf"
                        )
                    else:
                        st.warning("Report generated, but the PDF file was not found on the Streamlit host.")
                    st.info("The PDF has been saved to `data/processed/rca_reports/` on the server.")
        else:
            st.warning("Please enter both Ticket ID and Logs.")
