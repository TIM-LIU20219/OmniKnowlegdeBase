"""Document management page."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from frontend.utils.api_client import get_client

st.set_page_config(page_title="Documents", page_icon="📚", layout="wide")

st.title("📚 Document Management")

client = get_client()

# Sidebar for document upload
with st.sidebar:
    st.header("Upload Document")
    
    upload_type = st.radio("Upload type", ["File", "URL"])
    
    if upload_type == "File":
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "md", "markdown"],
            help="Upload PDF or Markdown file"
        )
        
        skip_duplicates = st.checkbox("Skip duplicates", value=True)
        import_batch = st.text_input("Import batch ID (optional)")
        
        if st.button("Upload", type="primary"):
            if uploaded_file:
                with st.spinner("Uploading and processing document..."):
                    try:
                        file_bytes = uploaded_file.read()
                        file_type = "pdf" if uploaded_file.type == "application/pdf" else "markdown"
                        
                        if file_type == "pdf":
                            result = client.create_document(
                                pdf_file=file_bytes,
                                filename=uploaded_file.name,
                                skip_duplicates=skip_duplicates,
                                import_batch=import_batch if import_batch else None,
                            )
                        else:
                            result = client.create_document(
                                markdown_file=file_bytes,
                                filename=uploaded_file.name,
                                skip_duplicates=skip_duplicates,
                                import_batch=import_batch if import_batch else None,
                            )
                        
                        st.success(f"✓ Document added: {result['title']}")
                        st.info(f"Document ID: {result['doc_id']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error uploading document: {e}")
            else:
                st.warning("Please select a file")
    
    elif upload_type == "URL":
        url = st.text_input("URL")
        import_batch = st.text_input("Import batch ID (optional)")
        
        if st.button("Fetch and Process", type="primary"):
            if url:
                with st.spinner("Fetching and processing URL..."):
                    try:
                        result = client.create_document(
                            url=url,
                            import_batch=import_batch if import_batch else None,
                        )
                        st.success(f"✓ Document added: {result['title']}")
                        st.info(f"Document ID: {result['doc_id']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing URL: {e}")
            else:
                st.warning("Please enter a URL")

# Main content area
tab1, tab2, tab3 = st.tabs(["📋 Document List", "🔍 Search", "🔗 Duplicates"])

with tab1:
    st.header("Document List")
    
    # Filter by batch
    batch_filter = st.text_input("Filter by batch ID (optional)", key="batch_filter")
    
    if st.button("Refresh", key="refresh_list"):
        st.rerun()
    
    try:
        params = {"by_batch": batch_filter} if batch_filter else {}
        response = client.list_documents(by_batch=batch_filter if batch_filter else None)
        documents = response.get("documents", [])
        total = response.get("total", 0)
        
        st.metric("Total Documents", total)
        
        if documents:
            # Display as dataframe
            import pandas as pd
            
            df_data = []
            for doc in documents:
                df_data.append({
                    "ID": doc["doc_id"],
                    "Title": doc["title"],
                    "Source": doc["source"],
                    "Created": doc["created_at"],
                    "Chunks": doc.get("chunk_total", 0),
                    "Tags": ", ".join(doc.get("tags", [])),
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Document details
            st.subheader("Document Details")
            selected_doc_id = st.selectbox("Select document", [doc["doc_id"] for doc in documents])
            
            if selected_doc_id:
                doc = next((d for d in documents if d["doc_id"] == selected_doc_id), None)
                if doc:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Title:**", doc["title"])
                        st.write("**Source:**", doc["source"])
                        st.write("**Created:**", doc["created_at"])
                        if doc.get("updated_at"):
                            st.write("**Updated:**", doc["updated_at"])
                        st.write("**Chunks:**", doc.get("chunk_total", 0))
                    
                    with col2:
                        if doc.get("tags"):
                            st.write("**Tags:**", ", ".join(doc["tags"]))
                        if doc.get("original_path"):
                            st.write("**Original Path:**", doc["original_path"])
                        if doc.get("storage_path"):
                            st.write("**Storage Path:**", doc["storage_path"])
                        if doc.get("file_hash"):
                            st.write("**File Hash:**", doc["file_hash"][:16] + "...")
                    
                    # View chunks button
                    if st.button("View Chunks", key=f"view_chunks_{selected_doc_id}"):
                        st.session_state[f"show_chunks_{selected_doc_id}"] = True
                    
                    if st.session_state.get(f"show_chunks_{selected_doc_id}"):
                        try:
                            chunks = client.get_document_chunks(selected_doc_id)
                            st.subheader("Document Chunks")
                            for chunk in chunks:
                                with st.expander(f"Chunk {chunk['chunk_index'] + 1}/{chunk['chunk_total']}"):
                                    st.text(chunk["content"][:500] + ("..." if len(chunk["content"]) > 500 else ""))
                        except Exception as e:
                            st.error(f"Error loading chunks: {e}")
                    
                    # Delete button
                    if st.button("Delete Document", type="secondary", key=f"delete_{selected_doc_id}"):
                        try:
                            client.delete_document(selected_doc_id)
                            st.success("Document deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting document: {e}")
        else:
            st.info("No documents found")
    
    except Exception as e:
        st.error(f"Error loading documents: {e}")

with tab2:
    st.header("Document Search")
    
    query = st.text_input("Search query")
    k = st.slider("Number of results", 1, 20, 5)
    show_source_info = st.checkbox("Show source file information")
    
    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Searching..."):
                try:
                    results = client.search_documents(query, k=k, show_source_info=show_source_info)
                    
                    if results:
                        st.success(f"Found {len(results)} results")
                        
                        for i, result in enumerate(results, 1):
                            with st.expander(f"Result {i}: {result['metadata'].get('title', 'Unknown')}"):
                                st.write("**Similarity Score:**", f"{result.get('score', 0):.3f}" if result.get('score') else "N/A")
                                st.write("**Doc ID:**", result["metadata"].get("doc_id"))
                                st.write("**Chunk ID:**", result["metadata"].get("chunk_id"))
                                
                                if show_source_info and result.get("source_info"):
                                    st.write("**Source Info:**")
                                    st.json(result["source_info"])
                                
                                st.write("**Content:**")
                                st.text(result["text"])
                    else:
                        st.info("No results found")
                except Exception as e:
                    st.error(f"Error searching: {e}")
        else:
            st.warning("Please enter a search query")

with tab3:
    st.header("Duplicate Documents")
    
    if st.button("Find Duplicates", type="primary"):
        with st.spinner("Searching for duplicates..."):
            try:
                duplicates = client.find_duplicates()
                
                total_groups = duplicates.get("total_duplicate_groups", 0)
                st.metric("Duplicate Groups", total_groups)
                
                if total_groups > 0:
                    for file_hash, docs in duplicates.get("duplicates", {}).items():
                        with st.expander(f"Hash: {file_hash[:16]}... ({len(docs)} documents)"):
                            for doc in docs:
                                st.write(f"- **{doc['title']}** (ID: {doc['doc_id']})")
                                if doc.get("original_path"):
                                    st.write(f"  Original: {doc['original_path']}")
                else:
                    st.info("No duplicate documents found")
            except Exception as e:
                st.error(f"Error finding duplicates: {e}")

