"""Dashboard page."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from frontend.utils.api_client import get_client

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

st.title("📈 System Dashboard")

client = get_client()

# Get system stats
try:
    stats = client.get_system_stats()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Documents", stats.get("total_documents", 0))
    col2.metric("Total Notes", stats.get("total_notes", 0))
    col3.metric("Total Vectors", stats.get("total_vectors", 0))
    col4.metric("Collections", len(stats.get("collections", [])))
    
    # Collections chart
    st.subheader("Collection Statistics")
    
    collections = stats.get("collections", [])
    if collections:
        import pandas as pd
        
        df = pd.DataFrame(collections)
        st.bar_chart(df.set_index("name")["count"])
        
        # Collection details
        st.subheader("Collection Details")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No collections found")
    
    # Health check
    st.subheader("System Health")
    try:
        health = client.health_check()
        if health.get("status") == "healthy":
            st.success("✓ System is healthy")
        else:
            st.warning("⚠ System status unknown")
    except Exception as e:
        st.error(f"✗ Health check failed: {e}")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")

