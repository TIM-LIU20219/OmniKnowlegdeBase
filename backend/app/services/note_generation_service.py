"""Note generation service for LLM-powered note creation."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from backend.app.services.agentic_rag_service import AgenticRAGService
from backend.app.services.agent_tools import AgentTools
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.note_vectorization_service import NoteVectorizationService
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

# Prompt templates
NOTE_GENERATION_PROMPT_LLM = """You are a helpful assistant that generates well-structured notes in Markdown format.

Based on your knowledge, generate a comprehensive note about: {topic}

Requirements:
1. Use Markdown format with proper headings
2. Include a clear title (as H1)
3. Structure the content logically with sections and subsections
4. Use bullet points or numbered lists where appropriate
5. Include relevant details and explanations
6. Do NOT include frontmatter (YAML) - just the markdown content
7. Use Obsidian-style links [[note-name]] for related concepts if you know of them

Generate the note now:"""

NOTE_GENERATION_PROMPT_RAG = """You are a helpful assistant that generates well-structured notes in Markdown format based on retrieved information.

Based on the following retrieved context, generate a comprehensive note about: {question}

Retrieved Context:
{context}

Requirements:
1. Use Markdown format with proper headings
2. Include a clear title (as H1)
3. Structure the content logically with sections and subsections
4. Use bullet points or numbered lists where appropriate
5. Include relevant details from the retrieved context
6. Cite sources when referencing specific information (use [Source: title] format)
7. Do NOT include frontmatter (YAML) - just the markdown content
8. Use Obsidian-style links [[note-name]] for related concepts mentioned in the context

Generate the note now:"""

SIMILARITY_REVIEW_PROMPT = """You are analyzing a newly generated note and comparing it with similar existing notes.

New Note:
{new_note}

Similar Notes Found:
{similar_notes}

Please analyze:
1. What concepts overlap between the new note and existing notes?
2. What unique information does the new note add?
3. What suggestions do you have for improving the new note based on similar notes?
4. Which existing notes should be linked to the new note?

Format your response as a Markdown comment block with suggestions:
<!-- 
相似笔记建议:
- [[note-title-1]]: Related concept X, suggestion: ...
- [[note-title-2]]: Related concept Y, suggestion: ...
-->"""

LINK_IDENTIFICATION_PROMPT = """You are analyzing a note to identify concepts that should be linked to existing notes.

Note Content:
{note_content}

Available Notes (titles only):
{available_note_titles}

Please identify:
1. Key concepts in the note that match existing note titles
2. Related topics that should be linked

For each match, provide:
- The concept/keyword in the note
- The matching note title
- Confidence level (high/medium/low)

Format as JSON list:
[
  {{"concept": "concept in note", "note_title": "matching title", "confidence": "high"}},
  ...
]"""


class NoteGenerationService:
    """
    Service for generating notes using LLM with optional RAG retrieval.
    
    Supports two modes:
    - LLM knowledge mode: Generate using LLM's own knowledge, retrieval only for similarity review
    - RAG mode: Retrieve information first, then generate based on retrieved context
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        agentic_rag_service: Optional[AgenticRAGService] = None,
        note_vectorization_service: Optional[NoteVectorizationService] = None,
        note_file_service: Optional[NoteFileService] = None,
        note_metadata_service: Optional[NoteMetadataService] = None,
        agent_tools: Optional[AgentTools] = None,
    ):
        """
        Initialize note generation service.

        Args:
            llm_service: Optional LLMService instance
            agentic_rag_service: Optional AgenticRAGService instance
            note_vectorization_service: Optional NoteVectorizationService instance
            note_file_service: Optional NoteFileService instance
            note_metadata_service: Optional NoteMetadataService instance
            agent_tools: Optional AgentTools instance
        """
        self.llm_service = llm_service or LLMService()
        self.agentic_rag_service = (
            agentic_rag_service
            or AgenticRAGService()
        )
        self.note_vectorization_service = (
            note_vectorization_service or NoteVectorizationService()
        )
        self.note_file_service = note_file_service or NoteFileService()
        self.note_metadata_service = (
            note_metadata_service or NoteMetadataService()
        )

        # Initialize AgentTools if not provided
        if agent_tools is None:
            from backend.app.services.embedding_service import EmbeddingService
            from backend.app.services.vector_service import VectorService

            embedding_service = EmbeddingService()
            vector_service = VectorService()
            agent_tools = AgentTools(
                note_metadata_service=self.note_metadata_service,
                note_file_service=self.note_file_service,
                vector_service=vector_service,
                embedding_service=embedding_service,
            )
        self.agent_tools = agent_tools

        logger.info("Initialized NoteGenerationService")

    def generate_with_llm_knowledge(
        self,
        topic: str,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        style: Optional[str] = None,
    ) -> Dict:
        """
        Generate note using LLM's own knowledge (without RAG retrieval).

        Args:
            topic: Topic or question for note generation
            file_path: Optional file path for the note
            tags: Optional tags for the note
            style: Optional style instructions

        Returns:
            Dictionary with generated note and metadata
        """
        logger.info(f"Generating note with LLM knowledge: {topic[:50]}...")

        try:
            # Stage 1: Generate draft using LLM's own knowledge
            draft_content = self._generate_draft(
                topic=topic,
                context=None,
                use_rag=False,
            )

            # Stage 2: Review similarity with existing notes
            similarity_result = self._review_similarity(draft_content)

            # Stage 3: Add links to existing notes
            linked_content, added_links = self._add_links(draft_content)

            # Extract title from content
            title = self._extract_title(linked_content)

            return {
                "title": title,
                "content": linked_content,
                "suggestions": similarity_result.get("suggestions", ""),
                "similar_notes": similarity_result.get("similar_notes", []),
                "added_links": added_links,
                "file_path": file_path,
                "tags": tags,
            }

        except Exception as e:
            logger.error(f"Error generating note with LLM knowledge: {e}")
            raise

    def generate_with_rag(
        self,
        question: str,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        strategy: Optional[str] = None,
    ) -> Dict:
        """
        Generate note using RAG retrieval first, then generate based on retrieved context.

        Args:
            question: Question for RAG retrieval and note generation
            file_path: Optional file path for the note
            tags: Optional tags for the note
            strategy: Optional RAG search strategy

        Returns:
            Dictionary with generated note and metadata
        """
        logger.info(f"Generating note with RAG: {question[:50]}...")

        try:
            # Stage 1: RAG retrieval
            rag_result = self.agentic_rag_service.query(
                question=question,
                strategy=strategy or "hybrid",
            )

            rag_answer = rag_result.get("answer", "")
            rag_sources = rag_result.get("sources", [])
            rag_context = self._format_rag_context(rag_answer, rag_sources)

            # Stage 2: Generate draft based on retrieved context
            draft_content = self._generate_draft(
                topic=question,
                context=rag_context,
                use_rag=True,
            )

            # Stage 3: Review similarity with existing notes
            similarity_result = self._review_similarity(draft_content)

            # Stage 4: Add links to existing notes
            linked_content, added_links = self._add_links(draft_content)

            # Extract title from content
            title = self._extract_title(linked_content)

            return {
                "title": title,
                "content": linked_content,
                "suggestions": similarity_result.get("suggestions", ""),
                "similar_notes": similarity_result.get("similar_notes", []),
                "added_links": added_links,
                "sources": rag_sources,
                "rag_context": rag_context[:500] + "..." if len(rag_context) > 500 else rag_context,
                "file_path": file_path,
                "tags": tags,
            }

        except Exception as e:
            logger.error(f"Error generating note with RAG: {e}")
            raise

    def _generate_draft(
        self,
        topic: str,
        context: Optional[str] = None,
        use_rag: bool = False,
    ) -> str:
        """
        Generate note draft using LLM.

        Args:
            topic: Topic or question
            context: Optional retrieved context (for RAG mode)
            use_rag: Whether to use RAG prompt template

        Returns:
            Generated note content
        """
        if use_rag and context:
            prompt = NOTE_GENERATION_PROMPT_RAG.format(
                question=topic, context=context
            )
        else:
            prompt = NOTE_GENERATION_PROMPT_LLM.format(topic=topic)

        try:
            content = self.llm_service.invoke(prompt)
            logger.debug(f"Generated draft content: {len(content)} characters")
            return content.strip()
        except Exception as e:
            logger.error(f"Error generating draft: {e}")
            raise

    def _review_similarity(self, draft_content: str) -> Dict:
        """
        Review similarity with existing notes and generate suggestions.

        Args:
            draft_content: Draft note content

        Returns:
            Dictionary with suggestions and similar notes
        """
        try:
            # Search for similar notes
            similar_notes = self.note_vectorization_service.search_notes(
                query=draft_content[:500],  # Use first 500 chars for search
                limit=5,
            )

            if not similar_notes:
                logger.debug("No similar notes found")
                return {
                    "suggestions": "<!-- 未找到相似笔记 -->",
                    "similar_notes": [],
                }

            # Format similar notes for LLM analysis
            similar_notes_text = self._format_similar_notes(similar_notes)

            # Generate suggestions using LLM
            prompt = SIMILARITY_REVIEW_PROMPT.format(
                new_note=draft_content[:2000],  # Limit length
                similar_notes=similar_notes_text,
            )

            suggestions = self.llm_service.invoke(prompt)

            return {
                "suggestions": suggestions.strip(),
                "similar_notes": similar_notes,
            }

        except Exception as e:
            logger.warning(f"Error reviewing similarity: {e}")
            return {
                "suggestions": "<!-- 相似性检阅失败 -->",
                "similar_notes": [],
            }

    def _add_links(self, content: str) -> Tuple[str, List[str]]:
        """
        Identify concepts and add Obsidian-style links to existing notes.

        Args:
            content: Note content

        Returns:
            Tuple of (content_with_links, list_of_added_links)
        """
        try:
            # Get all note titles
            all_notes = self.note_metadata_service.list_all_notes()
            available_titles = [note.title for note in all_notes]

            if not available_titles:
                logger.debug("No existing notes found for linking")
                return content, []

            # Use LLM to identify linkable concepts
            titles_text = "\n".join(f"- {title}" for title in available_titles[:50])  # Limit to 50 titles

            prompt = LINK_IDENTIFICATION_PROMPT.format(
                note_content=content[:2000],  # Limit length
                available_note_titles=titles_text,
            )

            llm_response = self.llm_service.invoke(prompt)

            # Parse LLM response to extract links
            links_to_add = self._parse_link_suggestions(llm_response, available_titles)

            # Add links to content
            content_with_links = content
            added_links = []

            for link_info in links_to_add:
                concept = link_info.get("concept", "")
                note_title = link_info.get("note_title", "")
                confidence = link_info.get("confidence", "medium")

                if confidence == "low":
                    continue  # Skip low confidence links

                # Find the concept in content and add link
                # Use regex to find the concept (case-insensitive, whole word)
                pattern = r"\b" + re.escape(concept) + r"\b"
                replacement = f"[[{note_title}]]"

                if re.search(pattern, content_with_links, re.IGNORECASE):
                    content_with_links = re.sub(
                        pattern, replacement, content_with_links, count=1, flags=re.IGNORECASE
                    )
                    added_links.append(note_title)
                    logger.debug(f"Added link: {concept} -> [[{note_title}]]")

            return content_with_links, list(set(added_links))  # Remove duplicates

        except Exception as e:
            logger.warning(f"Error adding links: {e}")
            return content, []

    def _format_rag_context(self, answer: str, sources: List[Dict]) -> str:
        """
        Format RAG retrieval results into context string.

        Args:
            answer: RAG answer
            sources: List of source dictionaries

        Returns:
            Formatted context string
        """
        context_parts = [f"Answer: {answer}\n\nSources:"]

        for i, source in enumerate(sources[:10], 1):  # Limit to 10 sources
            source_type = source.get("type", "unknown")
            title = source.get("title", "Unknown")
            file_path = source.get("file_path", "")

            context_parts.append(f"\n[{i}] {title} ({source_type})")
            if file_path:
                context_parts.append(f"   Path: {file_path}")

        return "\n".join(context_parts)

    def _format_similar_notes(self, similar_notes: List[Dict]) -> str:
        """
        Format similar notes for LLM analysis.

        Args:
            similar_notes: List of similar note dictionaries

        Returns:
            Formatted string
        """
        formatted_parts = []

        for i, note in enumerate(similar_notes[:5], 1):  # Limit to 5 notes
            title = note.get("title", "Unknown")
            file_path = note.get("file_path", "")
            content_preview = note.get("content", "")[:300]  # Limit preview length
            similarity = note.get("similarity")

            part = f"[Note {i}] {title}\n"
            if file_path:
                part += f"Path: {file_path}\n"
            if similarity is not None:
                part += f"Similarity: {similarity:.2f}\n"
            if content_preview:
                part += f"Content preview: {content_preview}...\n"

            formatted_parts.append(part)

        return "\n\n".join(formatted_parts)

    def _parse_link_suggestions(
        self, llm_response: str, available_titles: List[str]
    ) -> List[Dict]:
        """
        Parse LLM response to extract link suggestions.

        Args:
            llm_response: LLM response string (should be JSON)
            available_titles: List of available note titles

        Returns:
            List of link suggestion dictionaries
        """
        import json

        try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            json_match = re.search(r"\[.*\]", llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                links = json.loads(json_str)

                # Validate and filter links
                valid_links = []
                for link in links:
                    note_title = link.get("note_title", "")
                    if note_title in available_titles:
                        valid_links.append(link)

                return valid_links
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Error parsing link suggestions: {e}")

        return []

    def _extract_title(self, content: str) -> str:
        """
        Extract title from note content.

        Args:
            content: Note content

        Returns:
            Extracted title
        """
        # Try to find H1 heading
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Fallback: use first line
        first_line = content.split("\n")[0].strip()
        if first_line:
            # Remove markdown formatting
            title = re.sub(r"^#+\s+", "", first_line)
            return title[:100]  # Limit length

        return "Untitled Note"


