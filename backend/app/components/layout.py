"""Page layout components for Streamlit."""

import streamlit as st
from typing import Optional

from backend.app.utils.session_state import SessionStateManager


def render_page_header(
    title: str,
    icon: Optional[str] = None,
    description: Optional[str] = None,
    show_breadcrumb: bool = True,
) -> None:
    """
    Render a standardized page header.

    Args:
        title: Page title
        icon: Optional icon emoji
        description: Optional description text
        show_breadcrumb: Whether to show breadcrumb navigation
    """
    # Breadcrumb navigation
    if show_breadcrumb:
        current_page = SessionStateManager.get("current_page")
        if current_page:
            st.markdown(f"**Home** / **{title}**")
            st.markdown("---")

    # Title with icon
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)

    # Description
    if description:
        st.markdown(description)
        st.markdown("---")


def render_page_container(use_columns: bool = False) -> Optional[tuple]:
    """
    Render a page container with optional column layout.

    Args:
        use_columns: Whether to use a two-column layout

    Returns:
        Column tuple if use_columns is True, else None
    """
    if use_columns:
        return st.columns([2, 1])
    return None


def render_section_header(title: str, icon: Optional[str] = None) -> None:
    """
    Render a section header.

    Args:
        title: Section title
        icon: Optional icon emoji
    """
    if icon:
        st.markdown(f"### {icon} {title}")
    else:
        st.markdown(f"### {title}")


def render_info_section(message: str, message_type: str = "info") -> None:
    """
    Render an info/warning/error section.

    Args:
        message: Message text
        message_type: Type of message ('info', 'warning', 'error', 'success')
    """
    if message_type == "info":
        st.info(message)
    elif message_type == "warning":
        st.warning(message)
    elif message_type == "error":
        st.error(message)
    elif message_type == "success":
        st.success(message)
    else:
        st.info(message)


def render_footer() -> None:
    """Render a standardized page footer."""
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888;'>"
        "OmniKnowledgeBase © 2024 | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )


def render_loading_spinner(message: str = "Loading..."):
    """
    Context manager for rendering a loading spinner.

    Args:
        message: Loading message

    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(message)

