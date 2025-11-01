"""Documents management page."""

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
    title="Documents",
    icon="📄",
    description="Upload and manage your documents",
)

# Info section
render_info_section(
    "Document management functionality will be implemented in Phase 2.",
    message_type="info",
)

# Coming soon section
render_section_header("Coming Soon", icon="🚧")
st.markdown(
    """
    - Upload documents (Markdown, PDF, URL)
    - View document list
    - Search documents
    - Delete documents
    """
)

