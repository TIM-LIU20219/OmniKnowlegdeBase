"""Notes management page."""

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
    title="Notes",
    icon="📝",
    description="Create and manage Obsidian-style notes",
)

# Info section
render_info_section(
    "Note management functionality will be implemented in Phase 3.",
    message_type="info",
)

# Coming soon section
render_section_header("Coming Soon", icon="🚧")
st.markdown(
    """
    - Create and edit Obsidian-style notes
    - Bidirectional link support
    - Note visualization
    - Search notes
    """
)

