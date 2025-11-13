"""Vector store management CLI commands."""

import json
from typing import Optional

import click


@click.group(name="vector")
def vector_group():
    """Vector store management commands."""
    pass


@vector_group.command(name="collections")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def list_collections(json_output):
    """List all collections."""
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()

    try:
        collections = vector_service.list_collections()

        if json_output:
            # Always output JSON array, even if empty
            click.echo(json.dumps(collections if collections else [], indent=2))
        else:
            if collections:
                click.echo(f"Found {len(collections)} collections:\n")
                for collection_name in collections:
                    collection = vector_service.get_or_create_collection(collection_name)
                    count = collection.count()
                    click.echo(f"  {collection_name}: {count} documents")
            else:
                click.echo("No collections found.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@vector_group.command(name="stats")
@click.argument("collection", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def collection_stats(collection, json_output):
    """Show statistics for a collection."""
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()

    try:
        coll = vector_service.get_or_create_collection(collection)
        count = coll.count()

        # Get sample metadata to understand structure
        results = coll.get(limit=min(100, count), include=["metadatas"])

        stats = {
            "collection": collection,
            "total_documents": count,
            "sample_size": len(results.get("ids", [])) if results else 0,
        }

        if results and results.get("metadatas"):
            # Count unique doc_ids
            doc_ids = set()
            for metadata in results["metadatas"]:
                if "doc_id" in metadata:
                    doc_ids.add(metadata["doc_id"])

            stats["unique_documents"] = len(doc_ids) if doc_ids else None

        if json_output:
            click.echo(json.dumps(stats, indent=2))
        else:
            click.echo(f"Collection: {collection}")
            click.echo(f"Total documents (chunks): {stats['total_documents']}")
            if stats.get("unique_documents") is not None:
                click.echo(f"Unique documents: {stats['unique_documents']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@vector_group.command(name="delete-collection")
@click.argument("collection", type=str)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_collection(collection, yes):
    """Delete a collection."""
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()

    if not yes:
        click.confirm(f"Delete collection '{collection}'?", abort=True)

    try:
        vector_service.delete_collection(collection)
        click.echo(f"✓ Collection '{collection}' deleted successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@vector_group.command(name="delete-document")
@click.argument("collection", type=str)
@click.argument("doc_id", type=str)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_document(collection, doc_id, yes):
    """Delete a document from a collection."""
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()

    if not yes:
        click.confirm(f"Delete document '{doc_id}' from '{collection}'?", abort=True)

    try:
        vector_service.delete_document(collection, doc_id)
        click.echo(f"✓ Document '{doc_id}' deleted from '{collection}' successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@vector_group.command(name="query")
@click.argument("collection", type=str)
@click.argument("query_text", type=str)
@click.option("--k", default=5, help="Number of results to return")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def query_vector(collection, query_text, k, json_output):
    """Query a collection with semantic search."""
    from backend.app.services.embedding_service import EmbeddingService
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()
    embedding_service = EmbeddingService()

    try:
        # Generate query embedding
        query_embedding = embedding_service.embed_text(query_text)

        # Query collection
        results = vector_service.query(
            collection_name=collection,
            query_embeddings=[query_embedding],
            n_results=k,
        )

        if not results or not results.get("ids") or len(results["ids"][0]) == 0:
            click.echo("No results found.")
            return

        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if json_output:
            results_list = []
            for i, (doc_id, doc_text, metadata, distance) in enumerate(
                zip(ids, documents, metadatas, distances)
            ):
                similarity = 1.0 - distance if distance is not None else None
                results_list.append(
                    {
                        "rank": i + 1,
                        "id": doc_id,
                        "content": doc_text,
                        "metadata": metadata,
                        "distance": distance,
                        "similarity": similarity,
                    }
                )
            click.echo(json.dumps(results_list, indent=2))
        else:
            click.echo(f"Found {len(ids)} results:\n")
            for i, (doc_id, doc_text, metadata, distance) in enumerate(
                zip(ids, documents, metadatas, distances), 1
            ):
                similarity = 1.0 - distance if distance is not None else None
                click.echo(f"{i}. ID: {doc_id}")
                if metadata.get("title"):
                    click.echo(f"   Title: {metadata['title']}")
                if similarity is not None:
                    click.echo(f"   Similarity: {similarity:.3f}")
                click.echo(f"   Content: {doc_text[:200]}...")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

