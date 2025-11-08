"""RAG Query page."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from frontend.utils.api_client import get_client
from frontend.utils.stream_handler import process_rag_stream

st.set_page_config(page_title="RAG Query", page_icon="💬", layout="wide")

st.title("💬 RAG Query")

client = get_client()

# Initialize chat history
if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = []

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    collection = st.selectbox("Collection", ["documents", "notes"], index=0)
    k = st.slider("Number of documents to retrieve", 1, 20, 4)
    threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.0, 0.1)
    use_streaming = st.checkbox("Use streaming response", value=True)

# Display chat history
for message in st.session_state.rag_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if message.get("sources"):
            with st.expander("Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.write(f"{i}. **{source.get('title', 'Unknown')}**")
                    st.write(f"   Doc ID: {source.get('doc_id')}")
                    if source.get("distance"):
                        st.write(f"   Distance: {source.get('distance'):.3f}")

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Add user message to chat history
    st.session_state.rag_messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        if use_streaming:
            # Streaming response
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                stream_generator = client.stream_rag_query(
                    question=prompt,
                    collection=collection,
                    k=k,
                    threshold=threshold if threshold > 0 else None,
                )
                
                for chunk in process_rag_stream(stream_generator):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # Get final result for sources
                result = client.query_rag(
                    question=prompt,
                    collection=collection,
                    k=k,
                    threshold=threshold if threshold > 0 else None,
                )
                
                # Display sources
                if result.get("sources"):
                    with st.expander("Sources"):
                        for i, source in enumerate(result["sources"], 1):
                            st.write(f"{i}. **{source.get('title', 'Unknown')}**")
                            st.write(f"   Doc ID: {source.get('doc_id')}")
                            if source.get("distance"):
                                st.write(f"   Distance: {source.get('distance'):.3f}")
                
                # Add assistant message to chat history
                st.session_state.rag_messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": result.get("sources", []),
                })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.rag_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
        else:
            # Non-streaming response
            try:
                result = client.query_rag(
                    question=prompt,
                    collection=collection,
                    k=k,
                    threshold=threshold if threshold > 0 else None,
                )
                
                st.markdown(result["answer"])
                
                # Display sources
                if result.get("sources"):
                    with st.expander("Sources"):
                        for i, source in enumerate(result["sources"], 1):
                            st.write(f"{i}. **{source.get('title', 'Unknown')}**")
                            st.write(f"   Doc ID: {source.get('doc_id')}")
                            if source.get("distance"):
                                st.write(f"   Distance: {source.get('distance'):.3f}")
                
                # Add assistant message to chat history
                st.session_state.rag_messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.rag_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.rag_messages = []
    st.rerun()

