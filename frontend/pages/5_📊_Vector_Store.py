"""Vector Store visualization page."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from frontend.utils.api_client import get_client

st.set_page_config(page_title="Vector Store", page_icon="📊", layout="wide")

st.title("📊 Vector Store")

client = get_client()

# Get collections
try:
    collections = client.list_collections()
    
    if collections:
        st.header("Collections")
        
        selected_collection = st.selectbox("Select collection", collections)
        
        if selected_collection:
            # Collection stats
            try:
                stats = client.get_collection_stats(selected_collection)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Documents", stats.get("total_documents", 0))
                if stats.get("unique_documents"):
                    col2.metric("Unique Documents", stats.get("unique_documents"))
                col3.metric("Collection", selected_collection)
                
                # Query test
                st.subheader("Query Test")
                query_text = st.text_input("Query text")
                query_k = st.slider("Number of results", 1, 20, 5)
                
                if st.button("Query", type="primary"):
                    if query_text:
                        try:
                            results = client.query_collection(
                                name=selected_collection,
                                query_text=query_text,
                                k=query_k,
                            )
                            
                            if results:
                                st.success(f"Found {len(results)} results")
                                
                                for i, result in enumerate(results, 1):
                                    with st.expander(f"Result {i}: {result['id']}"):
                                        st.write("**Rank:**", result["rank"])
                                        st.write("**ID:**", result["id"])
                                        if result.get("similarity"):
                                            st.write("**Similarity:**", f"{result['similarity']:.3f}")
                                        if result.get("distance"):
                                            st.write("**Distance:**", f"{result['distance']:.3f}")
                                        
                                        st.write("**Metadata:**")
                                        st.json(result["metadata"])
                                        
                                        st.write("**Content:**")
                                        st.text(result["content"][:500] + ("..." if len(result["content"]) > 500 else ""))
                            else:
                                st.info("No results found")
                        except Exception as e:
                            st.error(f"Error querying: {e}")
                    else:
                        st.warning("Please enter a query")
            except Exception as e:
                st.error(f"Error getting stats: {e}")
    else:
        st.info("No collections found")
except Exception as e:
    st.error(f"Error loading collections: {e}")

