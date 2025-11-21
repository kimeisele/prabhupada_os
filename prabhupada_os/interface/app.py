import streamlit as st
import sys
import os
import json

# Add parent directory to path to import kernel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from prabhupada_os.knowledge.query_engine import PrabhupadaKernel

# Page Config
st.set_page_config(
    page_title="PrabhupadaOS",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Cyborg Sage" aesthetic
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #fafafa;
        border-color: #4e4e4e;
    }
    .verse-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff9900;
        margin-bottom: 20px;
    }
    .sanskrit {
        font-family: 'Noto Sans Devanagari', sans-serif;
        color: #ffcc00;
        font-size: 1.1em;
        white-space: pre-wrap;
    }
    .translation {
        font-style: italic;
        color: #e0e0e0;
        margin-top: 10px;
        font-size: 1.1em;
    }
    .purport {
        color: #b0b0b0;
        margin-top: 10px;
        font-size: 0.9em;
        border-top: 1px solid #333;
        padding-top: 10px;
    }
    .citation {
        font-size: 0.8em;
        color: #666;
        text-align: right;
        margin-top: 5px;
    }
    .smriti-box {
        background-color: #1a2634;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3d5a80;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Kernel
@st.cache_resource
def get_kernel():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, '../knowledge/store/vedabase.db')
    return PrabhupadaKernel(db_path)

kernel = get_kernel()

# Sidebar
with st.sidebar:
    st.title("PrabhupadaOS")
    st.caption("v1.0.0 • Offline Mode")
    
    st.markdown("---")
    st.markdown("**Status**")
    st.success("Kernel Active")
    st.success("Database Loaded (700 Verses)")
    st.info("AI Synthesis: Disabled (No API)")
    
    st.markdown("---")
    st.markdown("### The Protocol")
    st.markdown("1. **Sruti First**: Raw verses are the authority.")
    st.markdown("2. **No Speculation**: All answers cite the text.")
    
# Main Interface
st.title("The Cyborg Sage")
st.markdown("> *\"I give the understanding by which they can come to Me.\"* — BG 10.10")

query = st.text_input("Ask a question or search for a concept:", placeholder="e.g., intelligence, karma, devotion...")

if query:
    with st.spinner("Consulting the Vedabase..."):
        response = kernel.query(query)
    
    # Smriti Section (Synthesis)
    st.markdown("### 🧠 Smriti (Synthesis)")
    with st.container():
        st.markdown(f"""
        <div class="smriti-box">
            <strong>System Note:</strong> {response['smriti']['synthesis']}<br><br>
            <em>(In a full deployment, a local LLM would synthesize the verses below into a coherent answer here.)</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Sruti Section (Verses)
    st.markdown("### 📖 Sruti (Evidence)")
    
    results = response['sruti']
    if not results:
        st.warning("No verses found matching your query.")
    else:
        for verse in results:
            st.markdown(f"""
            <div class="verse-card">
                <div class="sanskrit">{verse['sanskrit']}</div>
                <div class="translation">{verse['translation']}</div>
                <div class="purport">{verse['purport_snippet']} <a href="#">Read more</a></div>
                <div class="citation">{verse['id']} • {verse['source']}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.markdown("### Sample Queries")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What is the soul?"):
            pass # User needs to type it for now
    with col2:
        if st.button("How to control the mind?"):
            pass
    with col3:
        if st.button("Purpose of yoga"):
            pass

# Footer
st.markdown("---")
st.caption("PrabhupadaOS • Built with Python & SQLite • No External APIs Required")
