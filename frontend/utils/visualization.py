"""Visualization utilities for Streamlit frontend."""

from typing import Dict, List


def format_tool_call(tool_call: Dict) -> str:
    """
    Format tool call for display.

    Args:
        tool_call: Tool call dictionary

    Returns:
        Formatted string
    """
    tool_name = tool_call.get("tool_name", "Unknown")
    iteration = tool_call.get("iteration", 0)
    return f"[Iteration {iteration}] {tool_name}"


def create_note_link_graph(linked_notes: List[Dict], backlinks: List[Dict]) -> str:
    """
    Create Graphviz DOT format string for note link visualization.

    Args:
        linked_notes: List of linked notes
        backlinks: List of backlinks

    Returns:
        Graphviz DOT format string
    """
    dot_lines = ["digraph NoteLinks {", "  rankdir=LR;", "  node [shape=box];"]

    # Add nodes and edges for linked notes
    for note in linked_notes:
        note_id = note.get("note_id", "")
        title = note.get("title", note_id)
        dot_lines.append(f'  "{note_id}" [label="{title}"];')

    # Add edges (simplified - would need source note_id)
    # This is a placeholder - full implementation would track source

    dot_lines.append("}")
    return "\n".join(dot_lines)

