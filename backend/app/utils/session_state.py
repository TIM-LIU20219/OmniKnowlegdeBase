"""Session state management utilities for Streamlit."""

import logging
from typing import Any, Dict, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class SessionStateManager:
    """Manager for Streamlit session state initialization and access."""

    # Default state keys and their initial values
    DEFAULT_STATE: Dict[str, Any] = {
        "initialized": False,
        "current_page": None,
        "document_list": [],
        "note_list": [],
        "qa_history": [],
        "selected_document": None,
        "selected_note": None,
        "search_query": "",
        "search_results": [],
    }

    @classmethod
    def init_defaults(cls) -> None:
        """
        Initialize default session state values if they don't exist.

        This should be called at the start of each page to ensure
        all required state variables are initialized.
        """
        for key, default_value in cls.DEFAULT_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.debug(f"Initialized session state: {key} = {default_value}")

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Set a session state value.

        Args:
            key: State key
            value: Value to set
        """
        st.session_state[key] = value
        logger.debug(f"Set session state: {key} = {value}")

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a session state value.

        Args:
            key: State key
            default: Default value if key doesn't exist

        Returns:
            State value or default
        """
        return st.session_state.get(key, default)

    @classmethod
    def clear(cls, key: Optional[str] = None) -> None:
        """
        Clear a session state key or all keys (except initialized).

        Args:
            key: Key to clear. If None, clears all except 'initialized'
        """
        if key:
            if key in st.session_state:
                del st.session_state[key]
                logger.debug(f"Cleared session state key: {key}")
        else:
            # Clear all except initialized
            initialized = st.session_state.get("initialized", False)
            for k in list(st.session_state.keys()):
                if k != "initialized":
                    del st.session_state[k]
            st.session_state["initialized"] = initialized
            logger.debug("Cleared all session state (except initialized)")

    @classmethod
    def reset(cls) -> None:
        """Reset all session state to defaults."""
        cls.clear()
        cls.init_defaults()
        logger.info("Reset all session state to defaults")

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the application is initialized.

        Returns:
            True if initialized
        """
        return st.session_state.get("initialized", False)

    @classmethod
    def mark_initialized(cls) -> None:
        """Mark the application as initialized."""
        st.session_state["initialized"] = True
        logger.debug("Marked application as initialized")

