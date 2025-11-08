"""Agentic Search page."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from frontend.utils.api_client import get_client
from frontend.utils.stream_handler import process_agentic_stream

st.set_page_config(page_title="Agentic Search", page_icon="🤖", layout="wide")

st.title("🤖 Agentic Search")

client = get_client()

# Initialize chat history
if "agentic_messages" not in st.session_state:
    st.session_state.agentic_messages = []

if "agentic_tool_calls" not in st.session_state:
    st.session_state.agentic_tool_calls = []

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    strategy = st.selectbox("Search Strategy", ["hybrid", "note-first"], index=0)
    max_iterations = st.slider("Max iterations", 1, 10, 5)
    use_streaming = st.checkbox("Use streaming response", value=True)
    show_tool_calls = st.checkbox("Show tool calls", value=True)

# Display chat history
for message in st.session_state.agentic_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if message.get("sources"):
            with st.expander("Sources"):
                for i, source in enumerate(message["sources"], 1):
                    source_type = source.get("type", "unknown")
                    if source_type == "note":
                        st.write(f"{i}. **Note:** {source.get('title', 'Unknown')}")
                        st.write(f"   Note ID: {source.get('note_id')}")
                        if source.get("tags"):
                            st.write(f"   Tags: {', '.join(source['tags'])}")
                    elif source_type == "document":
                        st.write(f"{i}. **Document:** {source.get('title', 'Unknown')}")
                        st.write(f"   Doc ID: {source.get('doc_id')}")
                        if source.get("distance"):
                            st.write(f"   Distance: {source.get('distance'):.3f}")

# Display tool calls
if show_tool_calls and st.session_state.agentic_tool_calls:
    with st.expander("🔧 Tool Calls", expanded=False):
        for tool_call in st.session_state.agentic_tool_calls:
            iteration = tool_call.get("iteration", 0)
            tool_name = tool_call.get("tool_name", "Unknown")
            
            with st.expander(f"[Iteration {iteration}] {tool_name}"):
                st.write("**Arguments:**")
                st.json(tool_call.get("tool_args", {}))
                
                result = tool_call.get("result")
                if result:
                    st.write("**Result:**")
                    if isinstance(result, dict) and len(str(result)) < 500:
                        st.json(result)
                    elif isinstance(result, list) and len(result) < 10:
                        st.json(result)
                    else:
                        result_str = str(result)
                        st.text(result_str[:500] + ("..." if len(result_str) > 500 else ""))

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Clear previous tool calls
    st.session_state.agentic_tool_calls = []
    
    # Add user message to chat history
    st.session_state.agentic_messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        if use_streaming:
            # Streaming response
            message_placeholder = st.empty()
            tool_calls_placeholder = st.empty()
            full_response = ""
            current_tool_calls = []
            
            try:
                stream_generator = client.stream_agentic_query(
                    question=prompt,
                    strategy=strategy,
                    max_iterations=max_iterations,
                )
                
                for event in process_agentic_stream(stream_generator):
                    if event.get("type") == "chunk":
                        chunk = event.get("content", "")
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    
                    elif event.get("type") == "tool_call":
                        tool_data = event.get("data", {})
                        current_tool_calls.append(tool_data)
                        st.session_state.agentic_tool_calls.append(tool_data)
                        
                        # Display tool call in real-time
                        if show_tool_calls:
                            with tool_calls_placeholder.container():
                                for tc in current_tool_calls:
                                    iteration = tc.get("iteration", 0)
                                    tool_name = tc.get("tool_name", "Unknown")
                                    st.info(f"🔧 [Iteration {iteration}] {tool_name}")
                    
                    elif event.get("type") == "done":
                        result = event.get("result", {})
                        message_placeholder.markdown(full_response)
                        
                        # Display sources
                        if result.get("sources"):
                            with st.expander("Sources"):
                                for i, source in enumerate(result["sources"], 1):
                                    source_type = source.get("type", "unknown")
                                    if source_type == "note":
                                        st.write(f"{i}. **Note:** {source.get('title', 'Unknown')}")
                                        st.write(f"   Note ID: {source.get('note_id')}")
                                        if source.get("tags"):
                                            st.write(f"   Tags: {', '.join(source['tags'])}")
                                    elif source_type == "document":
                                        st.write(f"{i}. **Document:** {source.get('title', 'Unknown')}")
                                        st.write(f"   Doc ID: {source.get('doc_id')}")
                                        if source.get("distance"):
                                            st.write(f"   Distance: {source.get('distance'):.3f}")
                        
                        # Display metadata
                        metadata = result.get("metadata", {})
                        st.caption(f"Iterations: {metadata.get('iterations', 0)} | "
                                 f"Tool calls: {metadata.get('tool_call_count', 0)} | "
                                 f"Strategy: {metadata.get('strategy', strategy)}")
                        
                        # Add assistant message to chat history
                        st.session_state.agentic_messages.append({
                            "role": "assistant",
                            "content": result.get("answer", full_response),
                            "sources": result.get("sources", []),
                        })
                        break
                    
                    elif event.get("type") == "error":
                        error_msg = event.get("error", "Unknown error")
                        st.error(f"Error: {error_msg}")
                        st.session_state.agentic_messages.append({
                            "role": "assistant",
                            "content": f"Error: {error_msg}",
                        })
                        break
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.agentic_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
        else:
            # Non-streaming response
            try:
                result = client.agentic_query(
                    question=prompt,
                    strategy=strategy,
                    max_iterations=max_iterations,
                )
                
                st.markdown(result["answer"])
                
                # Store tool calls
                st.session_state.agentic_tool_calls = result.get("tool_calls", [])
                
                # Display sources
                if result.get("sources"):
                    with st.expander("Sources"):
                        for i, source in enumerate(result["sources"], 1):
                            source_type = source.get("type", "unknown")
                            if source_type == "note":
                                st.write(f"{i}. **Note:** {source.get('title', 'Unknown')}")
                                st.write(f"   Note ID: {source.get('note_id')}")
                                if source.get("tags"):
                                    st.write(f"   Tags: {', '.join(source['tags'])}")
                            elif source_type == "document":
                                st.write(f"{i}. **Document:** {source.get('title', 'Unknown')}")
                                st.write(f"   Doc ID: {source.get('doc_id')}")
                                if source.get("distance"):
                                    st.write(f"   Distance: {source.get('distance'):.3f}")
                
                # Display metadata
                metadata = result.get("metadata", {})
                st.caption(f"Iterations: {metadata.get('iterations', 0)} | "
                         f"Tool calls: {metadata.get('tool_call_count', 0)} | "
                         f"Strategy: {metadata.get('strategy', strategy)}")
                
                # Add assistant message to chat history
                st.session_state.agentic_messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.agentic_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.agentic_messages = []
    st.session_state.agentic_tool_calls = []
    st.rerun()

