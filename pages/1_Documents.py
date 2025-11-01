"""Documents management page."""

import tempfile
from pathlib import Path

import streamlit as st

from backend.app.components.layout import (
    render_info_section,
    render_page_header,
    render_section_header,
    render_loading_spinner,
)
from backend.app.components.sidebar import render_sidebar_navigation
from backend.app.services.document_service import DocumentService
from backend.app.utils.filesystem import ensure_directories
from backend.app.utils.session_state import SessionStateManager

# Initialize session state
SessionStateManager.init_defaults()

# Ensure directories exist
ensure_directories()

# Initialize document service
if "document_service" not in st.session_state:
    st.session_state.document_service = DocumentService()

document_service = st.session_state.document_service

# Render sidebar navigation
render_sidebar_navigation()

# Render page header
render_page_header(
    title="Documents",
    icon="📄",
    description="Upload and manage your documents",
)

# Upload section
render_section_header("Upload Documents", icon="📤")

# Tabs for different upload methods
tab1, tab2, tab3 = st.tabs(["📄 PDF File", "📝 Markdown", "🔗 URL"])

with tab1:
    st.markdown("Upload a PDF file to process and add to the knowledge base.")
    uploaded_file = st.file_uploader(
        "Choose a PDF file", type=["pdf"], key="pdf_uploader"
    )

    if uploaded_file is not None:
        if st.button("Process PDF", key="process_pdf"):
            try:
                with render_loading_spinner("Processing PDF file..."):
                    # Save uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = Path(tmp_file.name)

                    # Process PDF
                    metadata = document_service.process_and_store_pdf(tmp_path)

                    # Clean up temporary file
                    tmp_path.unlink()

                    st.success(
                        f"✅ Successfully processed PDF: **{metadata.title}**\n\n"
                        f"- Document ID: `{metadata.doc_id}`\n"
                        f"- Chunks created: {metadata.chunk_total or 0}\n"
                        f"- Source: {metadata.source.value}"
                    )

            except Exception as e:
                st.error(f"❌ Error processing PDF: {str(e)}")

with tab2:
    st.markdown("Paste or type Markdown content to add to the knowledge base.")
    markdown_content = st.text_area(
        "Markdown Content", height=300, key="markdown_content"
    )

    if st.button("Process Markdown", key="process_markdown"):
        if not markdown_content.strip():
            st.warning("Please enter some Markdown content.")
        else:
            try:
                with render_loading_spinner("Processing Markdown content..."):
                    metadata = document_service.process_and_store_markdown(
                        markdown_content
                    )

                    st.success(
                        f"✅ Successfully processed Markdown: **{metadata.title}**\n\n"
                        f"- Document ID: `{metadata.doc_id}`\n"
                        f"- Chunks created: {metadata.chunk_total or 0}\n"
                        f"- Source: {metadata.source.value}"
                    )

                    # Clear the text area
                    st.session_state.markdown_content = ""

            except Exception as e:
                st.error(f"❌ Error processing Markdown: {str(e)}")

with tab3:
    st.markdown("Enter a URL to fetch and process content from a web page.")
    url_input = st.text_input("URL", placeholder="https://example.com/article", key="url_input")

    if st.button("Process URL", key="process_url"):
        if not url_input.strip():
            st.warning("Please enter a valid URL.")
        else:
            try:
                with render_loading_spinner("Fetching and processing URL..."):
                    metadata = document_service.process_and_store_url(url_input)

                    st.success(
                        f"✅ Successfully processed URL: **{metadata.title}**\n\n"
                        f"- Document ID: `{metadata.doc_id}`\n"
                        f"- Chunks created: {metadata.chunk_total or 0}\n"
                        f"- Source: {metadata.source.value}\n"
                        f"- URL: {url_input}"
                    )

                    # Clear the input
                    st.session_state.url_input = ""

            except Exception as e:
                st.error(f"❌ Error processing URL: {str(e)}")

# Info section
st.markdown("---")
render_info_section(
    "Documents are automatically chunked and vectorized for semantic search. "
    "You can search and retrieve them in the Q&A section.",
    message_type="info",
)

