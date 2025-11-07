"""RAG Q&A CLI commands."""

import json
from typing import Optional

import click


@click.group(name="rag")
def rag_group():
    """RAG Q&A commands."""
    pass


@rag_group.command(name="query")
@click.argument("question", type=str)
@click.option("--collection", default="documents", help="Collection name to query")
@click.option("--k", default=4, help="Number of documents to retrieve")
@click.option("--threshold", type=float, help="Similarity score threshold (0-1)")
@click.option("--stream", is_flag=True, help="Stream response")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--show-source-info", is_flag=True, help="Show source file information")
def query_rag(question, collection, k, threshold, stream, json_output, show_source_info):
    """Query the RAG system with a question."""
    from backend.app.services.embedding_service import EmbeddingService
    from backend.app.services.llm_service import LLMService
    from backend.app.services.rag_service import RAGService
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()
    embedding_service = EmbeddingService()
    llm_service = LLMService()

    rag_service = RAGService(
        vector_service=vector_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        collection_name=collection,
        k=k,
        score_threshold=threshold,
    )

    try:
        if stream:
            if json_output:
                click.echo("Error: --stream and --json cannot be used together", err=True)
                raise click.Abort()

            click.echo("Answer: ", nl=False)
            for chunk in rag_service.stream_query(question):
                click.echo(chunk, nl=False)
            click.echo()  # New line after streaming
        else:
            result = rag_service.query(question)

            if json_output:
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo("\nAnswer:")
                click.echo(result["answer"])
                click.echo(f"\nRetrieved {result['metadata']['retrieved_count']} documents")
                if result["sources"]:
                    click.echo("\nSources:")
                    for i, source in enumerate(result["sources"], 1):
                        click.echo(f"  {i}. {source['title']} (ID: {source['doc_id']})")
                        if show_source_info:
                            # Try to get source info from metadata if available
                            source_meta = source.get("metadata", {})
                            if source_meta.get("original_path"):
                                click.echo(f"      Original path: {source_meta['original_path']}")
                            if source_meta.get("storage_path"):
                                click.echo(f"      Storage path: {source_meta['storage_path']}")
                            if source_meta.get("import_batch"):
                                click.echo(f"      Import batch: {source_meta['import_batch']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@rag_group.command(name="interactive")
@click.option("--collection", default="documents", help="Collection name to query")
@click.option("--k", default=4, help="Number of documents to retrieve")
@click.option("--threshold", type=float, help="Similarity score threshold (0-1)")
def interactive_rag(collection, k, threshold):
    """Start interactive Q&A session."""
    from backend.app.services.embedding_service import EmbeddingService
    from backend.app.services.llm_service import LLMService
    from backend.app.services.rag_service import RAGService
    from backend.app.services.vector_service import VectorService

    vector_service = VectorService()
    embedding_service = EmbeddingService()
    llm_service = LLMService()

    rag_service = RAGService(
        vector_service=vector_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        collection_name=collection,
        k=k,
        score_threshold=threshold,
    )

    click.echo("RAG Interactive Q&A Session")
    click.echo("Type 'exit' or 'quit' to end the session\n")

    while True:
        try:
            question = click.prompt("Question", type=str)

            if question.lower() in ["exit", "quit", "q"]:
                click.echo("Goodbye!")
                break

            if not question.strip():
                continue

            click.echo("\nAnswer: ", nl=False)
            for chunk in rag_service.stream_query(question):
                click.echo(chunk, nl=False)
            click.echo("\n")

        except KeyboardInterrupt:
            click.echo("\n\nGoodbye!")
            break
        except EOFError:
            click.echo("\n\nGoodbye!")
            break
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


@rag_group.command(name="history")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def history_rag(json_output):
    """Show query history (placeholder - not yet implemented)."""
    click.echo("Query history feature not yet implemented.")
    click.echo("This will store and display previous RAG queries.")

