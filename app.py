"""Streamlit main application entry point."""

import streamlit as st

# Configure page
st.set_page_config(
    page_title="OmniKnowledgeBase",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False


def init_app():
    """Initialize application state."""
    if not st.session_state.initialized:
        # Import here to avoid circular imports
        from backend.app.utils.filesystem import ensure_directories

        ensure_directories()
        st.session_state.initialized = True


def main():
    """Main application entry point."""
    init_app()

    # Sidebar navigation
    st.sidebar.title("📚 OmniKnowledgeBase")
    st.sidebar.markdown("---")

    # Main content
    st.title("📚 OmniKnowledgeBase")
    st.markdown("Welcome to your knowledge base!")

    st.markdown("### Features")
    st.markdown(
        """
        - 📄 **Document Processing**: Upload and process Markdown, PDF, and URL content
        - 📝 **Note Management**: Obsidian-style notes with bidirectional links
        - 🤖 **RAG Q&A**: Ask questions based on your documents and notes
        - ✍️ **AI Note Generation**: Generate notes automatically using LLM
        """
    )

    st.markdown("### Navigation")
    st.markdown(
        """
        Use the sidebar to navigate to different pages:
        - 📄 **Documents**: Upload and manage documents
        - 📝 **Notes**: Create and edit Obsidian-style notes
        - 🤖 **Q&A**: Ask questions using RAG
        """
    )


if __name__ == "__main__":
    main()

