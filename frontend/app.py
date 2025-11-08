"""Main Streamlit application entry point."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

st.set_page_config(
    page_title="OmniKnowledgeBase",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📚 OmniKnowledgeBase")
st.markdown("Multi-functional knowledge base with RAG and Agentic Search")

st.info("""
Welcome to OmniKnowledgeBase! 

Use the sidebar to navigate to different pages:
- **📊 Dashboard**: System overview and statistics
- **📚 Documents**: Upload and manage documents
- **📝 Notes**: Create and manage Obsidian-style notes
- **💬 RAG Query**: Query documents using RAG
- **🤖 Agentic Search**: Advanced agentic search with tool calling
- **📊 Vector Store**: Explore vector collections
""")

# Quick links
st.subheader("Quick Links")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📚 Documents", use_container_width=True):
        st.switch_page("pages/1_📚_Documents.py")
with col2:
    if st.button("💬 RAG Query", use_container_width=True):
        st.switch_page("pages/3_💬_RAG_Query.py")
with col3:
    if st.button("🤖 Agentic Search", use_container_width=True):
        st.switch_page("pages/4_🤖_Agentic_Search.py")

