"""Document management CLI commands."""

import json
from pathlib import Path
from typing import Dict, List

import click


def _get_unique_documents(vector_service):
    """
    Get unique documents from vector store.

    Returns:
        Dictionary mapping doc_id to DocumentMetadata
    """
    from backend.app.models.metadata import DocumentMetadata

    collection_name = vector_service.collection_names["documents"]
    collection = vector_service.get_or_create_collection(collection_name)

    # Get all chunks
    results = collection.get(include=["metadatas"])

    if not results or not results.get("ids"):
        return {}

    metadatas = results.get("metadatas", [])
    unique_docs = {}

    # Group by doc_id and get first chunk's metadata for each document
    for metadata in metadatas:
        doc_id = metadata.get("doc_id")
        if doc_id and doc_id not in unique_docs:
            try:
                unique_docs[doc_id] = DocumentMetadata.from_chromadb_metadata(metadata)
            except Exception:
                # Fallback: create minimal metadata
                unique_docs[doc_id] = DocumentMetadata(
                    doc_id=doc_id,
                    doc_type=metadata.get("doc_type", "document"),
                    title=metadata.get("title", doc_id),
                    created_at=metadata.get("created_at", ""),
                    source=metadata.get("source", "unknown"),
                )

    return unique_docs


@click.group(name="document")
def document_group():
    """Document management commands."""
    pass


@document_group.command(name="add")
@click.option("--pdf", type=click.Path(exists=True), help="Path to PDF file")
@click.option("--markdown", type=click.Path(exists=True), help="Path to Markdown file")
@click.option("--url", type=str, help="URL to fetch and process")
def add_document(pdf, markdown, url):
    """Add a document to the knowledge base."""
    from backend.app.services.document_service import DocumentService

    doc_service = DocumentService()

    try:
        if pdf:
            file_path = Path(pdf)
            click.echo(f"Processing PDF: {file_path}")
            metadata = doc_service.process_and_store_pdf(file_path)
            click.echo(f"✓ Document added: {metadata.title}")
            click.echo(f"  ID: {metadata.doc_id}")
            click.echo(f"  Chunks: {metadata.chunk_total}")

        elif markdown:
            file_path = Path(markdown)
            content = file_path.read_text(encoding="utf-8")
            click.echo(f"Processing Markdown: {file_path}")
            metadata = doc_service.process_and_store_markdown(content, str(file_path))
            click.echo(f"✓ Document added: {metadata.title}")
            click.echo(f"  ID: {metadata.doc_id}")
            click.echo(f"  Chunks: {metadata.chunk_total}")

        elif url:
            click.echo(f"Processing URL: {url}")
            metadata = doc_service.process_and_store_url(url)
            click.echo(f"✓ Document added: {metadata.title}")
            click.echo(f"  ID: {metadata.doc_id}")
            click.echo(f"  Chunks: {metadata.chunk_total}")

        else:
            click.echo("Error: Please specify --pdf, --markdown, or --url", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@document_group.command(name="list")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def list_documents(json_output):
    """List all documents in the knowledge base."""
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()
    unique_docs = _get_unique_documents(vector_service)

    if not unique_docs:
        click.echo("No documents found.")
        return

    if json_output:
        docs_list = [
            {
                "doc_id": doc_id,
                "title": doc.title,
                "source": doc.source,
                "created_at": doc.created_at,
                "chunk_total": doc.chunk_total,
                "tags": doc.tags,
            }
            for doc_id, doc in unique_docs.items()
        ]
        click.echo(json.dumps(docs_list, indent=2))
    else:
        click.echo(f"Found {len(unique_docs)} documents:\n")
        for doc_id, doc in sorted(unique_docs.items(), key=lambda x: x[1].created_at):
            click.echo(f"  {doc_id}")
            click.echo(f"    Title: {doc.title}")
            click.echo(f"    Source: {doc.source}")
            click.echo(f"    Created: {doc.created_at}")
            click.echo(f"    Chunks: {doc.chunk_total or 0}")
            if doc.tags:
                click.echo(f"    Tags: {', '.join(doc.tags)}")
            click.echo()


@document_group.command(name="show")
@click.argument("doc_id", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_document(doc_id, json_output):
    """Show details of a specific document."""
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()
    unique_docs = _get_unique_documents(vector_service)

    if doc_id not in unique_docs:
        click.echo(f"Error: Document '{doc_id}' not found.", err=True)
        raise click.Abort()

    doc = unique_docs[doc_id]

    if json_output:
        click.echo(
            json.dumps(
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "source": doc.source,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                    "chunk_total": doc.chunk_total,
                    "tags": doc.tags,
                    "file_path": doc.file_path,
                    "author": doc.author,
                    "description": doc.description,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Document: {doc.title}")
        click.echo(f"  ID: {doc.doc_id}")
        click.echo(f"  Source: {doc.source}")
        click.echo(f"  Created: {doc.created_at}")
        if doc.updated_at:
            click.echo(f"  Updated: {doc.updated_at}")
        click.echo(f"  Chunks: {doc.chunk_total or 0}")
        if doc.file_path:
            click.echo(f"  File: {doc.file_path}")
        if doc.tags:
            click.echo(f"  Tags: {', '.join(doc.tags)}")
        if doc.author:
            click.echo(f"  Author: {doc.author}")
        if doc.description:
            click.echo(f"  Description: {doc.description}")


@document_group.command(name="delete")
@click.argument("doc_id", type=str)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_document(doc_id, yes):
    """Delete a document and all its chunks."""
    from backend.app.services.document_service import DocumentService

    doc_service = DocumentService()

    if not yes:
        click.confirm(f"Delete document '{doc_id}' and all its chunks?", abort=True)

    try:
        doc_service.delete_document(doc_id)
        click.echo(f"✓ Document '{doc_id}' deleted successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@document_group.command(name="search")
@click.argument("query", type=str)
@click.option("--k", default=5, help="Number of results to return")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def search_documents(query, k, json_output):
    """Search documents using semantic search."""
    from backend.app.services.embedding_service import EmbeddingService
    from backend.app.services.retriever import ChromaDBRetriever
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()
    embedding_service = EmbeddingService()

    retriever = ChromaDBRetriever(
        vector_service=vector_service,
        embedding_service=embedding_service,
        collection_name=vector_service.collection_names["documents"],
        k=k,
    )

    try:
        documents = retriever.get_relevant_documents(query)

        if not documents:
            click.echo("No documents found.")
            return

        if json_output:
            results = []
            for doc in documents:
                results.append(
                    {
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "doc_id": doc.metadata.get("doc_id"),
                        "title": doc.metadata.get("title", "Unknown"),
                        "distance": doc.metadata.get("distance"),
                        "content_preview": doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content,
                    }
                )
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"Found {len(documents)} relevant chunks:\n")
            for i, doc in enumerate(documents, 1):
                click.echo(f"{i}. {doc.metadata.get('title', 'Unknown')}")
                click.echo(f"   Doc ID: {doc.metadata.get('doc_id')}")
                click.echo(f"   Chunk ID: {doc.metadata.get('chunk_id')}")
                if doc.metadata.get("distance") is not None:
                    similarity = 1.0 - doc.metadata.get("distance", 0)
                    click.echo(f"   Similarity: {similarity:.3f}")
                click.echo(f"   Preview: {doc.page_content[:150]}...")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@document_group.command(name="chunks")
@click.argument("doc_id", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_chunks(doc_id, json_output):
    """Show all chunks for a document."""
    from backend.app.services.document_service import DocumentService

    doc_service = DocumentService()

    try:
        chunks = doc_service.get_document_chunks(doc_id)

        if not chunks:
            click.echo(f"No chunks found for document '{doc_id}'.")
            return

        if json_output:
            chunks_list = [
                {
                    "chunk_index": metadata.get("chunk_index", 0),
                    "chunk_total": metadata.get("chunk_total", 0),
                    "content": chunk_text,
                    "metadata": metadata,
                }
                for chunk_text, metadata in chunks
            ]
            click.echo(json.dumps(chunks_list, indent=2))
        else:
            click.echo(f"Document '{doc_id}' has {len(chunks)} chunks:\n")
            for chunk_text, metadata in chunks:
                chunk_idx = metadata.get("chunk_index", 0)
                click.echo(f"Chunk {chunk_idx + 1}/{len(chunks)}")
                click.echo("-" * 60)
                click.echo(chunk_text[:500] + ("..." if len(chunk_text) > 500 else ""))
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

