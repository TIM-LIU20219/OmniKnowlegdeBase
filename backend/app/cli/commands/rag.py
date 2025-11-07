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


@rag_group.command(name="agentic-query")
@click.argument("question", type=str)
@click.option(
    "--strategy",
    type=click.Choice(["note-first", "hybrid"], case_sensitive=False),
    default="hybrid",
    help="Search strategy hint: note-first (prioritize notes), hybrid (combine strategies). Note: LLM will autonomously decide tool usage.",
)
@click.option("--max-iterations", default=5, help="Maximum number of tool calling iterations")
@click.option("--stream", is_flag=True, help="Stream response")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--verbose", is_flag=True, help="Show detailed tool calls")
def agentic_query(question, strategy, max_iterations, stream, json_output, verbose):
    """Query using Agentic Search with LLM tool calling."""
    from backend.app.services.agentic_rag_service import AgenticRAGService

    try:
        # Initialize Agentic RAG service
        agentic_rag_service = AgenticRAGService(
            max_iterations=max_iterations,
            default_strategy=strategy,
        )

        if stream:
            if json_output:
                click.echo("Error: --stream and --json cannot be used together", err=True)
                raise click.Abort()

            click.echo(f"Querying (strategy: {strategy}): {question}\n")
            click.echo("Answer: ", nl=False)
            for chunk in agentic_rag_service.stream_query(question, strategy=strategy):
                click.echo(chunk, nl=False)
            click.echo()  # New line after streaming
        else:
            click.echo(f"Querying (strategy: {strategy}): {question}\n")

            # Execute query
            result = agentic_rag_service.query(question, strategy=strategy)

            if json_output:
                # Convert to serializable format
                serializable_result = {
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "tool_calls": result["tool_calls"],
                    "metadata": result["metadata"],
                }
                click.echo(json.dumps(serializable_result, indent=2, ensure_ascii=False))
            else:
                # Show tool calls if verbose
                if verbose and result["tool_calls"]:
                    click.echo("Tool Calls:")
                    for i, tool_call in enumerate(result["tool_calls"], 1):
                        click.echo(f"\n  [{i}] Iteration {tool_call['iteration']}")
                        click.echo(f"      Tool: {tool_call['tool_name']}")
                        click.echo(
                            f"      Args: {json.dumps(tool_call['tool_args'], indent=8, ensure_ascii=False)}"
                        )
                        if isinstance(tool_call.get("result"), dict) and len(
                            str(tool_call["result"])
                        ) < 200:
                            click.echo(
                                f"      Result: {json.dumps(tool_call['result'], indent=8, ensure_ascii=False)}"
                            )
                        else:
                            result_preview = str(tool_call.get("result", ""))[:100]
                            click.echo(f"      Result: {result_preview}...")
                    click.echo()

                # Show answer
                click.echo("Answer:")
                click.echo(result["answer"])

                # Show sources
                if result["sources"]:
                    click.echo(f"\nSources ({len(result['sources'])}):")
                    for i, source in enumerate(result["sources"], 1):
                        source_type = source.get("type", "unknown")
                        if source_type == "note":
                            click.echo(
                                f"  {i}. Note: {source.get('title', 'Unknown')} "
                                f"(ID: {source.get('note_id')})"
                            )
                            if source.get("tags"):
                                click.echo(f"      Tags: {', '.join(source['tags'])}")
                            if source.get("similarity"):
                                click.echo(f"      Similarity: {source['similarity']:.3f}")
                        elif source_type == "document":
                            click.echo(
                                f"  {i}. Document: {source.get('title', 'Unknown')} "
                                f"(ID: {source.get('doc_id')})"
                            )
                            if source.get("distance"):
                                click.echo(f"      Distance: {source['distance']:.3f}")
                else:
                    click.echo("\nNo sources found")

                # Show metadata
                metadata = result["metadata"]
                click.echo(f"\nCompleted in {metadata['iterations']} iteration(s)")
                click.echo(f"Strategy: {metadata['strategy']}")
                click.echo(f"Tool calls: {metadata['tool_call_count']}")

                if metadata.get("max_iterations_reached"):
                    click.echo("⚠️  Maximum iterations reached", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback

        if verbose:
            click.echo(traceback.format_exc(), err=True)
        raise click.Abort()
