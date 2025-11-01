"""Document processing service for parsing various document formats."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import markdown
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from backend.app.models.metadata import DocumentMetadata, SourceType

logger = logging.getLogger(__name__)

# Maximum content length for URL fetching
MAX_URL_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB


class DocumentProcessor:
    """Service for processing documents in various formats."""

    def __init__(self):
        """Initialize document processor."""
        self.markdown_extensions = [
            "extra",
            "codehilite",
            "fenced_code",
            "tables",
            "toc",
        ]

    def process_markdown(
        self, content: str, file_path: Optional[str] = None
    ) -> Tuple[str, DocumentMetadata]:
        """
        Process markdown content.

        Args:
            content: Markdown content string
            file_path: Optional file path for metadata

        Returns:
            Tuple of (processed_text, metadata)
        """
        try:
            # Extract frontmatter if present
            frontmatter, content_clean = self._extract_frontmatter(content)

            # Extract metadata from frontmatter
            title = frontmatter.get("title") or self._extract_title_from_content(content_clean)
            tags = frontmatter.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",")]
            author = frontmatter.get("author")
            description = frontmatter.get("description")

            # Convert markdown to plain text (keeping structure)
            md = markdown.Markdown(extensions=self.markdown_extensions)
            html = md.convert(content_clean)
            soup = BeautifulSoup(html, "html.parser")
            processed_text = soup.get_text(separator="\n", strip=True)

            # Create metadata
            doc_id = self._generate_doc_id()
            metadata = DocumentMetadata(
                doc_id=doc_id,
                doc_type="document",
                file_path=file_path,
                title=title,
                created_at=datetime.utcnow().isoformat(),
                tags=tags,
                source=SourceType.MARKDOWN,
                author=author,
                description=description,
            )

            logger.info(f"Processed markdown document: {title}")
            return processed_text, metadata

        except Exception as e:
            logger.error(f"Error processing markdown: {e}")
            raise

    def process_pdf(self, file_path: Path) -> Tuple[str, DocumentMetadata]:
        """
        Process PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (processed_text, metadata)
        """
        try:
            reader = PdfReader(str(file_path))

            # Extract text from all pages
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            processed_text = "\n\n".join(text_parts)

            # Extract metadata from PDF
            metadata_dict = reader.metadata if reader.metadata else {}
            title = (
                metadata_dict.get("/Title")
                or metadata_dict.get("Title")
                or file_path.stem
            )
            author = (
                metadata_dict.get("/Author")
                or metadata_dict.get("Author")
                or None
            )

            # Create metadata
            doc_id = self._generate_doc_id()
            metadata = DocumentMetadata(
                doc_id=doc_id,
                doc_type="document",
                file_path=str(file_path),
                title=title,
                created_at=datetime.utcnow().isoformat(),
                tags=[],
                source=SourceType.PDF,
                author=author,
            )

            logger.info(f"Processed PDF document: {title} ({len(reader.pages)} pages)")
            return processed_text, metadata

        except Exception as e:
            logger.error(f"Error processing PDF '{file_path}': {e}")
            raise

    def process_url(self, url: str) -> Tuple[str, DocumentMetadata]:
        """
        Fetch and process content from URL.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (processed_text, metadata)
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Fetch content
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30, stream=True)

            # Check content length
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_URL_CONTENT_LENGTH:
                raise ValueError(f"Content too large: {content_length} bytes")

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else url

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc.get("content") if meta_desc else None

            # Extract main content (prefer article, main, or body)
            content_selectors = ["article", "main", '[role="main"]', "body"]
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break

            if content_element:
                processed_text = content_element.get_text(separator="\n", strip=True)
            else:
                processed_text = soup.get_text(separator="\n", strip=True)

            # Extract tags from meta keywords if available
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            tags = []
            if meta_keywords:
                keywords_content = meta_keywords.get("content", "")
                tags = [tag.strip() for tag in keywords_content.split(",") if tag.strip()]

            # Create metadata
            doc_id = self._generate_doc_id()
            metadata = DocumentMetadata(
                doc_id=doc_id,
                doc_type="document",
                file_path=None,
                title=title,
                created_at=datetime.utcnow().isoformat(),
                tags=tags,
                source=SourceType.URL,
                description=description,
            )

            logger.info(f"Processed URL: {title} ({url})")
            return processed_text, metadata

        except Exception as e:
            logger.error(f"Error processing URL '{url}': {e}")
            raise

    def extract_metadata(
        self, content: str, source_type: SourceType
    ) -> Dict[str, any]:
        """
        Extract metadata from document content.

        Args:
            content: Document content
            source_type: Source type

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}

        # Extract title
        metadata["title"] = self._extract_title_from_content(content)

        # Extract tags (from markdown or text)
        metadata["tags"] = self._extract_tags(content)

        # Extract links
        metadata["links"] = self._extract_links(content)

        return metadata

    def _extract_frontmatter(
        self, content: str
    ) -> Tuple[Dict[str, any], str]:
        """
        Extract YAML frontmatter from content.

        Args:
            content: Content with optional frontmatter

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        frontmatter = {}
        content_clean = content

        # Check for frontmatter pattern
        if content.startswith("---"):
            try:
                import yaml

                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_str = parts[1].strip()
                    content_clean = parts[2].strip()
                    frontmatter = yaml.safe_load(frontmatter_str) or {}
            except Exception as e:
                logger.warning(f"Error parsing frontmatter: {e}")

        return frontmatter, content_clean

    def _extract_title_from_content(self, content: str) -> str:
        """
        Extract title from content.

        Args:
            content: Document content

        Returns:
            Extracted title
        """
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                # Check for markdown headers
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    if title:
                        return title
                # Use first non-empty line as title
                return line[:100]  # Limit length

        return "Untitled Document"

    def _extract_tags(self, content: str) -> List[str]:
        """
        Extract tags from content.

        Args:
            content: Document content

        Returns:
            List of tags
        """
        tags = []

        # Extract markdown tags: #tag or tags: [tag1, tag2]
        tag_pattern = r"#(\w+)"
        found_tags = re.findall(tag_pattern, content)
        tags.extend(found_tags)

        # Extract frontmatter tags
        frontmatter, _ = self._extract_frontmatter(content)
        if "tags" in frontmatter:
            frontmatter_tags = frontmatter["tags"]
            if isinstance(frontmatter_tags, list):
                tags.extend(frontmatter_tags)
            elif isinstance(frontmatter_tags, str):
                tags.extend([t.strip() for t in frontmatter_tags.split(",")])

        # Remove duplicates and return
        return list(set(tags))

    def _extract_links(self, content: str) -> List[str]:
        """
        Extract links from content.

        Args:
            content: Document content

        Returns:
            List of link URLs
        """
        links = []

        # Extract markdown links: [text](url)
        markdown_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        markdown_links = re.findall(markdown_link_pattern, content)
        links.extend([url for _, url in markdown_links])

        # Extract Obsidian-style links: [[note-name]]
        obsidian_link_pattern = r"\[\[([^\]]+)\]\]"
        obsidian_links = re.findall(obsidian_link_pattern, content)
        links.extend(obsidian_links)

        # Extract plain URLs
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, content)
        links.extend(urls)

        return list(set(links))

    def _generate_doc_id(self) -> str:
        """
        Generate unique document ID.

        Returns:
            Unique document ID
        """
        import uuid

        return str(uuid.uuid4())

