"""RAG Q&A page."""

import streamlit as st

from backend.app.components.layout import render_info_section, render_page_header, render_section_header
from backend.app.components.sidebar import render_sidebar_navigation
from backend.app.utils.session_state import SessionStateManager

# Initialize session state
SessionStateManager.init_defaults()

# Render sidebar navigation
render_sidebar_navigation()

# Render page header
render_page_header(
    title="Q&A",
    icon="🤖",
    description="Ask questions based on your documents and notes",
)

# Info section
render_info_section(
    "RAG Q&A functionality will be implemented in Phase 4.",
    message_type="info",
)

# Coming soon section
render_section_header("Coming Soon", icon="🚧")
st.markdown(
    """
    - Ask questions based on documents and notes
    - Semantic search
    - Stream response
    - Conversation history
    """
)

