"""Sidebar navigation component for Streamlit."""

import streamlit as st
from typing import Dict, List, Optional

from backend.app.utils.session_state import SessionStateManager


class NavigationItem:
    """Represents a navigation menu item."""

    def __init__(self, label: str, icon: str, page: str, description: Optional[str] = None):
        """
        Initialize navigation item.

        Args:
            label: Display label
            icon: Icon emoji or symbol
            page: Page identifier (filename without extension)
            description: Optional description text
        """
        self.label = label
        self.icon = icon
        self.page = page
        self.description = description

    def __str__(self) -> str:
        """Return formatted navigation item string."""
        return f"{self.icon} {self.label}"


def get_navigation_items() -> List[NavigationItem]:
    """
    Get list of navigation items.

    Returns:
        List of NavigationItem objects
    """
    return [
        NavigationItem(
            label="Home",
            icon="🏠",
            page="app",
            description="Main dashboard",
        ),
        NavigationItem(
            label="Documents",
            icon="📄",
            page="1_Documents",
            description="Manage documents",
        ),
        NavigationItem(
            label="Notes",
            icon="📝",
            page="2_Notes",
            description="Obsidian-style notes",
        ),
        NavigationItem(
            label="Q&A",
            icon="🤖",
            page="3_QA",
            description="RAG-powered Q&A",
        ),
    ]


def get_current_page_name() -> str:
    """
    Get current page name from Streamlit's page context.

    Returns:
        Current page name or "app" for main page
    """
    # Streamlit automatically provides page information
    # We can detect the current page by checking the script path
    import sys
    from pathlib import Path

    if len(sys.argv) > 0:
        script_path = Path(sys.argv[0])
        script_name = script_path.stem

        # Map script names to page identifiers
        if script_name == "app":
            return "app"
        elif script_name.startswith("1_"):
            return "1_Documents"
        elif script_name.startswith("2_"):
            return "2_Notes"
        elif script_name.startswith("3_"):
            return "3_QA"

    # Default to app if we can't determine
    return "app"


def render_sidebar_navigation() -> Optional[str]:
    """
    Render sidebar navigation menu.

    Returns:
        Selected page identifier or None
    """
    # Initialize session state
    SessionStateManager.init_defaults()

    # Sidebar header
    st.sidebar.title("📚 OmniKnowledgeBase")
    st.sidebar.markdown("---")

    # Get navigation items
    nav_items = get_navigation_items()

    # Get current page name
    current_page = get_current_page_name()

    # Render navigation menu
    st.sidebar.markdown("### Navigation")

    selected_page = None
    for item in nav_items:
        # Determine if this item is selected
        is_selected = current_page == item.page

        # Create button/link for navigation
        if is_selected:
            st.sidebar.markdown(f"**{item}**")
            if item.description:
                st.sidebar.caption(item.description)
            selected_page = item.page
        else:
            # Display as regular text (Streamlit handles navigation automatically)
            st.sidebar.markdown(f"- {item}")
            if item.description:
                st.sidebar.caption(f"  _{item.description}_")

    # Update session state
    if selected_page:
        SessionStateManager.set("current_page", selected_page)

    st.sidebar.markdown("---")

    # App info section
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "OmniKnowledgeBase: A powerful knowledge management system with "
        "document processing, note management, and RAG-powered Q&A."
    )

    # Status section
    st.sidebar.markdown("### Status")
    if SessionStateManager.is_initialized():
        st.sidebar.success("✓ Initialized")
    else:
        st.sidebar.warning("⚠ Not initialized")

    return selected_page

