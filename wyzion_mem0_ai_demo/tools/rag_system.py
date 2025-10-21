"""
RAG (Retrieval Augmented Generation) System
Uses loan documents as knowledge base to enhance AI responses
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from wyzion_mem0_ai_demo.utils.logger import get_logger

logger = get_logger(__name__)


class SimpleRAGSystem:
    """
    Simple RAG system using OpenAI embeddings for semantic search.
    Uses loan documents as knowledge base.
    """

    def __init__(self, openai_client: OpenAI, data_dir: str = ""):
        """
        Initialize RAG system with OpenAI client and data directory.

        Args:
            openai_client: OpenAI client instance
            data_dir: Path to data directory containing knowledge base documents
        """
        self.client = openai_client

        if not data_dir:
            # Default to data directory in project
            current_dir = Path(__file__).parent.parent
            data_dir = os.path.join(current_dir, "data")

        self.data_dir = data_dir
        self.knowledge_base: List[Tuple[str, Dict[str, Any], Optional[List[float]]]] = (
            []
        )  # List of (text_chunk, metadata, embedding) tuples
        self.query_cache: Dict = {}  # Cache query embeddings and results

        logger.info(f"RAG System initialized with data_dir: {data_dir}")

    def load_documents(self):
        """
        Load all text documents from data directory and split into chunks.
        Pre-computes embeddings for all chunks for faster retrieval.
        """
        logger.info("Loading documents for knowledge base")

        # Documents to load
        documents = ["mutual_fund_sip.txt", "preventative_wellness.txt"]

        for doc_name in documents:
            doc_path = os.path.join(self.data_dir, doc_name)

            if not os.path.exists(doc_path):
                logger.warning(f"Document not found: {doc_path}")
                continue

            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split document into chunks
                chunks = self._chunk_document(content, doc_name)
                self.knowledge_base.extend(chunks)

                logger.info(f"Loaded {len(chunks)} chunks from {doc_name}")

            except Exception as e:
                logger.error(f"Error loading document {doc_name}: {e}", exc_info=True)

        logger.info(f"Total knowledge base chunks: {len(self.knowledge_base)}")

        # Pre-compute embeddings for all chunks
        logger.info("Pre-computing embeddings for all chunks...")
        self._precompute_embeddings()
        logger.info("Embeddings pre-computed successfully")

    def _chunk_document(
        self, content: str, source: str, chunk_size: int = 800, overlap_ratio: float = 0.2
    ) -> List[Tuple[str, Dict]]:
        """
        Split document into semantic chunks with overlapping for better context continuity.

        Args:
            content: Document content
            source: Source document name
            chunk_size: Target size for each chunk (characters)
            overlap_ratio: Overlap between chunks (default 0.2 = 20%)

        Returns:
            List of (chunk_text, metadata) tuples
        """
        chunks = []
        overlap_size = int(chunk_size * overlap_ratio)

        # Better split: Capture section header + divider patterns
        # Matches patterns like:
        #   ===
        #   SECTION TITLE
        #   ===
        # or just stand-alone headers with = or - dividers
        section_pattern = r"(?:\n={3,}\n([A-Z\s&\-\(\)]+)\n={3,}\n|\n-{3,}\n([A-Z\s&\-\(\)]+)\n-{3,}\n)"

        # Split content by section headers
        parts = re.split(section_pattern, content)

        # Process the parts: parts[0] is intro, then alternates between section_title and section_content
        sections_data = []

        # First part might be document intro/title
        if parts[0].strip():
            intro_lines = parts[0].strip().split("\n", 1)
            doc_title = intro_lines[0] if intro_lines else "Introduction"
            intro_content = intro_lines[1].strip() if len(intro_lines) > 1 else ""
            if intro_content:
                sections_data.append((doc_title, intro_content))

        # Process captured sections (title at odd indices, content at even indices after that)
        i = 1
        while i < len(parts):
            # parts[i] or parts[i+1] contains the section title (from capture groups)
            title = (
                (parts[i] or parts[i + 1] or "Unknown Section").strip()
                if i + 1 < len(parts)
                else (parts[i] or "Unknown Section").strip()
            )

            # Content comes after the title captures
            content_idx = i + 2
            section_content = parts[content_idx].strip() if content_idx < len(parts) else ""

            if section_content:
                sections_data.append((title, section_content))

            i += 3  # Move to next section (skip both capture groups and content)

        # Process each section
        for title, section_content in sections_data:
            if not section_content:
                continue

            # If section is small enough, keep it as one chunk (with title)
            if len(section_content) <= chunk_size:
                chunk_with_title = f"{title}\n\n{section_content}"
                chunks.append(
                    (chunk_with_title, {"source": source, "section": title, "chunk_size": len(chunk_with_title)})
                )
            else:
                # Split large sections with overlapping chunks
                paragraphs = section_content.split("\n\n")
                current_chunk_paras: List = []
                current_chunk_size = 0

                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue

                    para_size = len(para)

                    # Check if adding this paragraph exceeds chunk size
                    if current_chunk_size + para_size > chunk_size and current_chunk_paras:
                        # Save current chunk with title
                        chunk_text = "\n\n".join(current_chunk_paras)
                        chunk_with_title = f"{title}\n\n{chunk_text}"
                        chunks.append(
                            (
                                chunk_with_title,
                                {"source": source, "section": title, "chunk_size": len(chunk_with_title)},
                            )
                        )

                        # Create overlap: keep last few paragraphs based on overlap_size
                        overlap_paras: List = []
                        overlap_chars = 0

                        # Work backwards to collect paragraphs for overlap
                        for overlap_para in reversed(current_chunk_paras):
                            if overlap_chars + len(overlap_para) <= overlap_size:
                                overlap_paras.insert(0, overlap_para)
                                overlap_chars += len(overlap_para)
                            else:
                                break

                        # Start new chunk with overlap + current paragraph
                        current_chunk_paras = overlap_paras + [para]
                        current_chunk_size = sum(len(p) for p in current_chunk_paras)
                    else:
                        # Add paragraph to current chunk
                        current_chunk_paras.append(para)
                        current_chunk_size += para_size

                # Add remaining chunk (with title)
                if current_chunk_paras:
                    chunk_text = "\n\n".join(current_chunk_paras)
                    chunk_with_title = f"{title}\n\n{chunk_text}"
                    chunks.append(
                        (chunk_with_title, {"source": source, "section": title, "chunk_size": len(chunk_with_title)})
                    )

        return chunks

    def _precompute_embeddings(self):
        """
        Pre-compute embeddings for all chunks in the knowledge base.
        This significantly speeds up retrieval by avoiding on-the-fly embedding generation.
        """
        if not self.knowledge_base:
            logger.warning("No chunks to pre-compute embeddings for")
            return

        # Extract all chunk texts
        chunk_texts = [chunk[0] for chunk in self.knowledge_base]

        # Batch process embeddings (OpenAI supports up to 2048 texts per request)
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i : i + batch_size]

            try:
                response = self.client.embeddings.create(model="text-embedding-3-small", input=batch)
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Computed embeddings for chunks {i+1}-{min(i+batch_size, len(chunk_texts))}")

            except Exception as e:
                logger.error(f"Error computing embeddings for batch {i}: {e}", exc_info=True)
                # Fill with empty embeddings for failed batch
                all_embeddings.extend([[] for _ in range(len(batch))])

        # Update knowledge base to include embeddings: (text, metadata, embedding)
        self.knowledge_base = [
            (chunk[0], chunk[1], embedding) for chunk, embedding in zip(self.knowledge_base, all_embeddings)
        ]

        logger.info(f"Pre-computed embeddings for {len(all_embeddings)} chunks")

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using OpenAI's embedding model.
        Uses cache for query embeddings.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache first (for query embeddings)
        if text in self.query_cache:
            return self.query_cache[text]

        try:
            response = self.client.embeddings.create(model="text-embedding-3-small", input=text)
            embedding = response.data[0].embedding

            # Cache the query embedding
            self.query_cache[text] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Error getting embedding: {e}", exc_info=True)
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def retrieve_relevant_context(self, query: str, top_k: int = 2) -> str:
        """
        Retrieve relevant context from knowledge base based on query.
        Optimized with pre-computed embeddings for fast retrieval.

        Args:
            query: User query
            top_k: Number of top chunks to retrieve (reduced to 2 for speed)

        Returns:
            Combined relevant context as string
        """
        if not self.knowledge_base:
            logger.warning("Knowledge base is empty, loading documents")
            self.load_documents()

        if not self.knowledge_base:
            logger.warning("No documents in knowledge base")
            return ""

        # Get query embedding (only needs 1 API call)
        query_embedding = self._get_embedding(query)

        if not query_embedding:
            logger.error("Failed to get query embedding")
            return ""

        # Calculate similarity scores for all chunks using pre-computed embeddings
        scored_chunks = []

        for chunk_text, metadata, chunk_embedding in self.knowledge_base:
            if chunk_embedding:
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                scored_chunks.append((similarity, chunk_text, metadata))

        # Sort by similarity (highest first)
        scored_chunks.sort(reverse=True, key=lambda x: x[0])

        # Get top-k chunks
        top_chunks = scored_chunks[:top_k]

        if not top_chunks:
            logger.warning("No relevant chunks found")
            return ""

        # Log retrieval results
        logger.info(f"Retrieved {len(top_chunks)} relevant chunks for query")
        for i, (score, _, metadata) in enumerate(top_chunks, 1):
            logger.debug(
                f"Chunk {i}: similarity={score:.3f}, source={metadata['source']}, section={metadata['section']}"
            )

        # Combine chunks into context
        context_parts = []
        for score, chunk_text, metadata in top_chunks:
            context_parts.append(f"[Source: {metadata['source']} - {metadata['section']}]\n{chunk_text}")

        combined_context = "\n\n---\n\n".join(context_parts)

        return combined_context

    def is_loan_related_query(self, query: str) -> bool:
        """
        Determine if query is related to loans (should use RAG).

        Args:
            query: User query

        Returns:
            True if loan-related, False otherwise
        """
        loan_keywords = [
            "loan",
            "borrow",
            "financing",
            "interest",
            "rate",
            "apr",
            "payment",
            "credit",
            "eligibility",
            "document",
            "requirement",
            "apply",
            "approval",
            "auto",
            "car",
            "vehicle",
            "personal",
            "mortgage",
            "refinance",
            "down payment",
            "monthly payment",
            "term",
            "collateral",
            "cosigner",
            "prepayment",
            "default",
            "insurance",
            "gap insurance",
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in loan_keywords)


# Global RAG system instance
_rag_system = None


def initialize_rag_system(openai_client: OpenAI):
    """
    Initialize global RAG system instance.

    Args:
        openai_client: OpenAI client instance
    """
    global _rag_system

    if _rag_system is None:
        logger.info("Initializing RAG system")
        _rag_system = SimpleRAGSystem(openai_client)
        _rag_system.load_documents()
        logger.info("RAG system initialized successfully")

    return _rag_system


def get_rag_system() -> SimpleRAGSystem:
    """
    Get global RAG system instance.

    Returns:
        RAG system instance
    """
    if _rag_system is None:
        raise RuntimeError("RAG system not initialized. Call initialize_rag_system() first.")

    return _rag_system
