"""Streamlit main application entry point."""

import logging

import streamlit as st

from backend.app.components.layout import render_page_header, render_section_header
from backend.app.components.sidebar import render_sidebar_navigation
from backend.app.utils.logging_config import setup_logging
from backend.app.utils.session_state import SessionStateManager

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="OmniKnowledgeBase",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
SessionStateManager.init_defaults()


def init_app():
    """Initialize application state."""
    if not SessionStateManager.is_initialized():
        # Import here to avoid circular imports
        from backend.app.utils.filesystem import ensure_directories

        logger.info("Initializing application...")
        ensure_directories()
        SessionStateManager.mark_initialized()
        logger.info("Application initialized successfully")


def main():
    """Main application entry point."""
    # Initialize app
    init_app()

    # Render sidebar navigation
    render_sidebar_navigation()

    # Render page header
    render_page_header(
        title="OmniKnowledgeBase",
        icon="📚",
        description="Welcome to your knowledge base!",
        show_breadcrumb=False,
    )

    # Features section
    render_section_header("Features", icon="✨")
    st.markdown(
        """
        - 📄 **Document Processing**: Upload and process Markdown, PDF, and URL content
        - 📝 **Note Management**: Obsidian-style notes with bidirectional links
        - 🤖 **RAG Q&A**: Ask questions based on your documents and notes
        - ✍️ **AI Note Generation**: Generate notes automatically using LLM
        """
    )

    # Quick start section
    render_section_header("Quick Start", icon="🚀")
    st.markdown(
        """
        Use the sidebar to navigate to different pages:
        - 📄 **Documents**: Upload and manage documents
        - 📝 **Notes**: Create and edit Obsidian-style notes
        - 🤖 **Q&A**: Ask questions using RAG
        """
    )

    # Stats section (placeholder for future stats)
    render_section_header("Statistics", icon="📊")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents", "0", "Coming soon")
    with col2:
        st.metric("Notes", "0", "Coming soon")
    with col3:
        st.metric("QA Sessions", "0", "Coming soon")


if __name__ == "__main__":
    main()

