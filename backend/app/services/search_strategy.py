"""Search strategies for Agentic Search."""

import logging
from typing import Any, Dict, List, Optional

from backend.app.services.agent_tools import AgentTools

logger = logging.getLogger(__name__)


class SearchStrategy:
    """Base class for search strategies."""

    def __init__(self, tools: AgentTools):
        """
        Initialize search strategy.

        Args:
            tools: AgentTools instance
        """
        self.tools = tools

    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute search strategy.

        Args:
            query: Search query
            context: Optional context from previous steps

        Returns:
            List of search results
        """
        raise NotImplementedError


class NoteFirstStrategy(SearchStrategy):
    """
    Note-first search strategy.

    Strategy:
    1. Search notes by title
    2. If relevant notes found, get their metadata and linked notes
    3. Read content of most relevant notes
    """

    def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute note-first search.

        Args:
            query: Search query
            context: Optional context from previous steps

        Returns:
            List of search results with note content
        """
        results = []

        # Step 1: Search notes by title
        notes = self.tools.search_notes_by_title(query, limit=5)
        if not notes:
            logger.debug("No notes found by title search")
            return results

        # Step 2: Get metadata and linked notes for top results
        for note in notes[:3]:  # Top 3 notes
            note_id = note["note_id"]

            # Get full metadata
            metadata = self.tools.get_note_metadata(note_id)
            if metadata:
                note["metadata"] = metadata

            # Get linked notes
            linked_notes = self.tools.get_linked_notes(note_id)
            note["linked_notes"] = linked_notes

            # Read note content
            content = self.tools.read_note_content(note_id)
            if content:
                note["content"] = content

            results.append(note)

        logger.debug(f"Note-first strategy found {len(results)} results")
        return results


class LinkExpansionStrategy(SearchStrategy):
    """
    Link expansion search strategy.

    Strategy:
    1. Start from a seed note
    2. Follow links to related notes
    3. Read content of linked notes
    """

    def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute link expansion search.

        Args:
            query: Search query (used to find seed note)
            context: Optional context with seed note_id

        Returns:
            List of search results from linked notes
        """
        results = []

        # Get seed note from context or search
        seed_note_id = None
        if context and "seed_note_id" in context:
            seed_note_id = context["seed_note_id"]
        else:
            # Find seed note by searching
            notes = self.tools.search_notes_by_title(query, limit=1)
            if notes:
                seed_note_id = notes[0]["note_id"]

        if not seed_note_id:
            logger.debug("No seed note found for link expansion")
            return results

        # Get linked notes
        linked_notes = self.tools.get_linked_notes(seed_note_id)
        if not linked_notes:
            logger.debug(f"No linked notes found for note {seed_note_id}")
            return results

        # Read content of linked notes
        for linked_note in linked_notes[:5]:  # Limit to 5 linked notes
            note_id = linked_note["note_id"]
            content = self.tools.read_note_content(note_id)
            if content:
                linked_note["content"] = content
                results.append(linked_note)

        logger.debug(f"Link expansion strategy found {len(results)} results")
        return results


class TagFilterStrategy(SearchStrategy):
    """
    Tag filter search strategy.

    Strategy:
    1. Extract tags from query or context
    2. Get all notes with matching tags
    3. Read content of tagged notes
    """

    def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute tag filter search.

        Args:
            query: Search query (may contain tags)
            context: Optional context with explicit tags

        Returns:
            List of search results from tagged notes
        """
        results = []

        # Extract tags from context or query
        tags = []
        if context and "tags" in context:
            tags = context["tags"]
            # Normalize tags to Obsidian style (#tag)
            tags = [tag if tag.startswith("#") else f"#{tag}" for tag in tags]
        else:
            # Try to extract tags from query (simple heuristic)
            # Look for #tag patterns
            # Support Unicode characters (including Chinese, Japanese, Korean, etc.)
            import re
            tag_pattern = r"#([^\s#]+)"
            found_tags = re.findall(tag_pattern, query)
            tags = [f"#{tag}" for tag in found_tags]

        if not tags:
            logger.debug("No tags found in query or context")
            return results

        # Get notes for each tag
        all_tagged_notes = []
        for tag in tags:
            notes = self.tools.get_notes_by_tag(tag)
            all_tagged_notes.extend(notes)

        # Remove duplicates by note_id
        seen = set()
        unique_notes = []
        for note in all_tagged_notes:
            if note["note_id"] not in seen:
                seen.add(note["note_id"])
                unique_notes.append(note)

        # Read content of tagged notes
        for note in unique_notes[:10]:  # Limit to 10 notes
            note_id = note["note_id"]
            content = self.tools.read_note_content(note_id)
            if content:
                note["content"] = content
                results.append(note)

        logger.debug(f"Tag filter strategy found {len(results)} results")
        return results


class FallbackStrategy(SearchStrategy):
    """
    Fallback search strategy.

    Strategy:
    1. If notes don't contain information, search PDF/document chunks
    2. Return document chunks as results
    """

    def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute fallback search.

        Args:
            query: Search query
            context: Optional context (unused for fallback)

        Returns:
            List of document chunk results
        """
        results = []

        # Search PDF/document chunks
        chunks = self.tools.search_pdf_chunks(query, limit=5)
        results.extend(chunks)

        logger.debug(f"Fallback strategy found {len(results)} results")
        return results


class HybridStrategy(SearchStrategy):
    """
    Hybrid search strategy combining multiple strategies.

    Strategy:
    1. Try note-first search
    2. If insufficient results, try link expansion
    3. If still insufficient, try PDF/document search
    """

    def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute hybrid search.

        Args:
            query: Search query
            context: Optional context from previous steps

        Returns:
            Combined list of search results
        """
        all_results = []
        seen_ids = set()

        # Step 1: Note-first search
        note_strategy = NoteFirstStrategy(self.tools)
        note_results = note_strategy.execute(query, context)
        for result in note_results:
            note_id = result.get("note_id")
            if note_id and note_id not in seen_ids:
                seen_ids.add(note_id)
                all_results.append(result)

        # Step 2: If we have a seed note, try link expansion
        if note_results and len(all_results) < 5:
            link_strategy = LinkExpansionStrategy(self.tools)
            link_context = {"seed_note_id": note_results[0]["note_id"]}
            link_results = link_strategy.execute(query, link_context)
            for result in link_results:
                note_id = result.get("note_id")
                if note_id and note_id not in seen_ids:
                    seen_ids.add(note_id)
                    all_results.append(result)

        # Step 3: Fallback to PDF/document search if still insufficient
        if len(all_results) < 3:
            fallback_strategy = FallbackStrategy(self.tools)
            pdf_results = fallback_strategy.execute(query, context)
            # PDF results don't have note_id, so we use doc_id
            for result in pdf_results:
                doc_id = result.get("doc_id")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append(result)

        logger.debug(f"Hybrid strategy found {len(all_results)} total results")
        return all_results

