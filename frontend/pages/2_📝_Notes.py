"""Notes management page."""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from frontend.utils.api_client import get_client

st.set_page_config(page_title="Notes", page_icon="📝", layout="wide")

st.title("📝 Notes Management")

client = get_client()

# Sidebar for note creation and generation
with st.sidebar:
    tab_create, tab_generate = st.tabs(["✏️ Create", "🤖 Generate"])
    
    with tab_create:
        st.header("Create Note")
        
        note_title = st.text_input("Title")
        note_content = st.text_area("Content", height=200)
        note_file_path = st.text_input("File path (optional)")
        note_tags = st.text_input("Tags (comma-separated)")
        
        if st.button("Create Note", type="primary"):
            if note_title and note_content:
                try:
                    tags_list = [t.strip() for t in note_tags.split(",")] if note_tags else None
                    result = client.create_note(
                        title=note_title,
                        content=note_content,
                        file_path=note_file_path if note_file_path else None,
                        tags=tags_list,
                    )
                    st.success(f"✓ Note created: {result['file_path']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating note: {e}")
            else:
                st.warning("Please provide title and content")
    
    with tab_generate:
        st.header("Generate Note")
        
        gen_mode = st.radio(
            "Generation Mode",
            ["ask", "new"],
            help="'ask' uses RAG retrieval, 'new' uses LLM knowledge only",
            horizontal=True
        )
        
        gen_topic = st.text_area("Topic/Question", height=100, help="Enter the topic or question for note generation")
        gen_file_path = st.text_input("File path (optional)", key="gen_file_path")
        gen_tags = st.text_input("Tags (comma-separated)", key="gen_tags")
        gen_style = st.text_input("Style instructions (optional)", key="gen_style")
        
        col1, col2 = st.columns(2)
        with col1:
            generate_btn = st.button("Generate", type="primary", use_container_width=True)
        with col2:
            generate_save_btn = st.button("Generate & Save", use_container_width=True)
        
        if generate_btn or generate_save_btn:
            if gen_topic:
                try:
                    with st.spinner("Generating note..."):
                        tags_list = [t.strip() for t in gen_tags.split(",")] if gen_tags else None
                        
                        if generate_save_btn:
                            result = client.generate_and_save_note(
                                topic=gen_topic,
                                mode=gen_mode,
                                file_path=gen_file_path if gen_file_path else None,
                                tags=tags_list,
                                style=gen_style if gen_style else None,
                            )
                            st.success(f"✓ Note generated and saved: {result['file_path']}")
                            st.rerun()
                        else:
                            result = client.generate_note(
                                topic=gen_topic,
                                mode=gen_mode,
                                file_path=gen_file_path if gen_file_path else None,
                                tags=tags_list,
                                style=gen_style if gen_style else None,
                            )
                            
                            # Store result in session state for display
                            st.session_state['generated_note'] = result
                            st.success("✓ Note generated successfully!")
                            
                            # Show preview
                            st.subheader("Generated Note Preview")
                            st.write(f"**Title:** {result.get('title', 'N/A')}")
                            st.write(f"**Mode:** {result.get('mode', 'unknown')}")
                            
                            if result.get('suggestions'):
                                with st.expander("📋 Similarity Suggestions"):
                                    st.markdown(result['suggestions'])
                            
                            if result.get('similar_notes'):
                                st.write(f"**Similar notes found:** {len(result['similar_notes'])}")
                                for note in result['similar_notes'][:3]:
                                    st.write(f"- {note.get('title', 'Unknown')}")
                            
                            if result.get('added_links'):
                                st.write(f"**Links added:** {len(result['added_links'])}")
                                for link in result['added_links'][:5]:
                                    st.write(f"- [[{link}]]")
                            
                            if result.get('sources'):
                                st.write(f"**RAG sources:** {len(result['sources'])}")
                                for source in result['sources'][:3]:
                                    st.write(f"- {source.get('title', 'Unknown')} ({source.get('type', 'unknown')})")
                            
                            with st.expander("📄 Generated Content"):
                                st.markdown(result.get('content', ''))
                            
                            # Option to save
                            if st.button("Save Generated Note", type="primary"):
                                try:
                                    full_content = result.get('content', '')
                                    if result.get('suggestions'):
                                        full_content = f"{result['suggestions']}\n\n{full_content}"
                                    
                                    save_path = result.get('file_path') or gen_file_path
                                    if not save_path:
                                        title = result.get('title', 'Untitled')
                                        safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title)
                                        save_path = f"{safe_title.replace(' ', '_')}.md"
                                    
                                    saved = client.create_note(
                                        title=result.get('title', 'Untitled'),
                                        content=full_content,
                                        file_path=save_path,
                                        tags=result.get('tags') or tags_list,
                                    )
                                    st.success(f"✓ Note saved: {saved['file_path']}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error saving note: {e}")
                except Exception as e:
                    st.error(f"Error generating note: {e}")
            else:
                st.warning("Please provide a topic or question")

# Main content
tab1, tab2, tab3 = st.tabs(["📋 Note List", "🔍 Search", "🔗 Links"])

with tab1:
    st.header("Note List")
    
    try:
        notes = client.list_notes()
        
        if notes:
            st.metric("Total Notes", len(notes))
            
            selected_note = st.selectbox("Select note", notes)
            
            if selected_note:
                try:
                    note = client.get_note(selected_note)
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("View Mode")
                        st.write("**Title:**", note["title"])
                        st.write("**Path:**", note["file_path"])
                        
                        if note.get("frontmatter"):
                            st.write("**Frontmatter:**")
                            st.json(note["frontmatter"])
                        
                        st.write("**Content:**")
                        st.markdown(note["content"])
                    
                    with col2:
                        st.subheader("Edit Mode")
                        edit_title = st.text_input("Title", value=note["title"], key="edit_title")
                        edit_content = st.text_area("Content", value=note["content"], height=400, key="edit_content")
                        edit_tags = st.text_input("Tags", value=", ".join(note.get("frontmatter", {}).get("tags", [])), key="edit_tags")
                        
                        if st.button("Update Note", type="primary"):
                            try:
                                tags_list = [t.strip() for t in edit_tags.split(",")] if edit_tags else None
                                updated = client.update_note(
                                    file_path=selected_note,
                                    title=edit_title,
                                    content=edit_content,
                                    tags=tags_list,
                                )
                                st.success("✓ Note updated")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating note: {e}")
                        
                        if st.button("Delete Note", type="secondary"):
                            try:
                                client.delete_note(selected_note)
                                st.success("Note deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting note: {e}")
                except Exception as e:
                    st.error(f"Error loading note: {e}")
        else:
            st.info("No notes found")
    except Exception as e:
        st.error(f"Error loading notes: {e}")

with tab2:
    st.header("Search Notes")
    
    search_query = st.text_input("Search query (semantic)")
    search_tag = st.text_input("Filter by tag")
    search_limit = st.slider("Limit", 1, 50, 10)
    
    if st.button("Search", type="primary"):
        if search_query or search_tag:
            try:
                results = client.search_notes(
                    query=search_query if search_query else None,
                    tag=search_tag if search_tag else None,
                    limit=search_limit,
                )
                
                if results:
                    st.success(f"Found {len(results)} results")
                    
                    for i, result in enumerate(results, 1):
                        with st.expander(f"{i}. {result.get('title', 'Unknown')}"):
                            st.write("**Path:**", result.get("file_path"))
                            if result.get("tags"):
                                st.write("**Tags:**", ", ".join(result["tags"]))
                            if result.get("similarity"):
                                st.write("**Similarity:**", f"{result['similarity']:.3f}")
                            if result.get("content"):
                                st.text(result["content"][:200] + "...")
                else:
                    st.info("No results found")
            except Exception as e:
                st.error(f"Error searching: {e}")
        else:
            st.warning("Please provide a query or tag")

with tab3:
    st.header("Note Links")
    
    note_id = st.text_input("Note ID")
    
    if st.button("Get Links", type="primary"):
        if note_id:
            try:
                # Try to get links by file_path first
                links_data = client.get_note_links(note_id)
                
                st.write("**File Path:**", links_data.get("file_path"))
                
                if links_data.get("links"):
                    st.write("**Links:**")
                    for link in links_data["links"]:
                        st.write(f"- [[{link}]]")
                
                if links_data.get("linked_notes"):
                    st.write("**Linked Notes:**")
                    for note in links_data["linked_notes"]:
                        st.write(f"- {note['title']} ({note['file_path']})")
                
                if links_data.get("backlinks"):
                    st.write("**Backlinks:**")
                    for note in links_data["backlinks"]:
                        st.write(f"- {note['title']} ({note['file_path']})")
            except Exception as e:
                st.error(f"Error getting links: {e}")
        else:
            st.warning("Please enter a note ID")

