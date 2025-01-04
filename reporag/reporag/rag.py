import logging
from typing import List, Dict, Any, Optional, Tuple
import shutil
import os
import hashlib
import pickle
import re
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str

class RepoRAGSplitter:
    """Custom text splitter for repository content."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        # Regex patterns for different content types
        self.patterns = {
            'function': r'(?:def|class)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\):',
            'markdown_section': r'^#{1,6}\s+.+$',
            'code_block': r'```[\s\S]*?```',
            'file_header': r'File:\s+([^\n]+)',
            'import_statement': r'^(?:from|import)\s+\w+',
        }

    def split_content(self, content: str) -> List[Document]:
        """Split content based on content type and semantic boundaries."""
        chunks = []

        # First, try to identify the content type
        content_type = self._identify_content_type(content)

        # Split based on content type
        if content_type == "code":
            raw_chunks = self._split_code(content)
        elif content_type == "markdown":
            raw_chunks = self._split_markdown(content)
        else:
            raw_chunks = self._split_generic(content)

        # Process each chunk and convert to Document
        for chunk in raw_chunks:
            processed_chunk = self._process_chunk(chunk, content_type)
            # Convert dict to Document
            doc = Document(
                page_content=processed_chunk["page_content"],
                metadata=processed_chunk["metadata"]
            )
            chunks.append(doc)

        return chunks

    def _identify_content_type(self, content: str) -> str:
        """Identify the type of content."""
        if re.search(self.patterns['import_statement'], content) or '.py' in content[:100]:
            return "code"
        elif content.startswith('# ') or '```' in content:
            return "markdown"
        return "text"

    def _split_code(self, content: str) -> List[str]:
        """Split code content preserving function/class boundaries."""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        in_function = False

        for i, line in enumerate(lines):
            # Check for function/class definition
            if re.match(self.patterns['function'], line):
                if current_chunk and (not in_function or current_size >= self.chunk_size):
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                in_function = True

            current_chunk.append(line)
            current_size += len(line)

            # Check if we should split
            if not in_function and current_size >= self.chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            # Check if function ends
            if in_function and line.strip() == "" and i < len(lines) - 1:
                if not lines[i + 1].startswith(' '):
                    in_function = False

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _split_markdown(self, content: str) -> List[str]:
        """Split markdown content preserving section boundaries."""
        chunks = []
        current_chunk = []
        current_size = 0

        for line in content.split('\n'):
            # Check for new section
            if re.match(self.patterns['markdown_section'], line):
                if current_chunk and current_size >= self.chunk_size:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

            current_chunk.append(line)
            current_size += len(line)

            # Split if chunk is too large
            if current_size >= self.chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _split_generic(self, content: str) -> List[str]:
        """Split generic content using sentence boundaries."""
        sentences = sent_tokenize(content)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            current_size += len(sentence)

            if current_size >= self.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _process_chunk(self, chunk: str, content_type: str) -> Dict[str, Any]:
        """Process chunk and add metadata with proper type handling."""
        # Extract file path if present
        file_path = None
        file_match = re.search(self.patterns['file_header'], chunk)
        if file_match:
            file_path = file_match.group(1)

        # Ensure all metadata values are valid types (str, int, float, or bool)
        metadata = {
            "content_type": content_type or "unknown",
            "file_path": file_path or "unknown",
            "language": self._detect_language(chunk),
            "size": len(chunk),
            "tokens": len(word_tokenize(chunk))
        }

        # Filter out any None values and ensure proper types
        filtered_metadata = {}
        for key, value in metadata.items():
            if value is not None:
                # Convert to appropriate type if needed
                if isinstance(value, (str, int, float, bool)):
                    filtered_metadata[key] = value
                else:
                    # Convert other types to string
                    filtered_metadata[key] = str(value)

        return {
            "page_content": chunk,
            "metadata": filtered_metadata
        }

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text content."""
        # Lowercase
        text = text.lower()

        # Tokenize
        words = word_tokenize(text)

        # Remove stop words and lemmatize
        words = [self.lemmatizer.lemmatize(word) for word in words if word not in self.stop_words]

        return ' '.join(words)

    def _detect_language(self, content: str) -> str:
        """Detect programming language from content."""
        if '.py' in content or 'def ' in content:
            return 'python'
        elif '.js' in content or 'function ' in content:
            return 'javascript'
        elif '.java' in content or 'class ' in content:
            return 'java'
        return 'unknown'

class RepoRAG:
    """RAG system optimized for repository content."""

    def __init__(
        self,
        groq_api_key: str,
        model_name: str = "mixtral-8x7b-32768",
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        k_retrieval: int = 4,
        cache_dir: str = "./cache"
    ):
        self.setup_logging()
        self.initialize_components(
            groq_api_key, model_name, embedding_model,
            chunk_size, chunk_overlap, k_retrieval, cache_dir
        )

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def initialize_components(
        self,
        groq_api_key: str,
        model_name: str,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
        k_retrieval: int,
        cache_dir: str
    ):
        """Initialize RAG components."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k_retrieval = k_retrieval
        self.cache_dir = cache_dir
        self.chat_history = []

        # Initialize custom splitter
        self.splitter = RepoRAGSplitter(chunk_size, chunk_overlap)

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize LLM
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model_name=model_name
        )

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

        # Initialize prompt templates
        self._initialize_prompts()

    def _initialize_prompts(self):
        """Initialize different prompt templates for different types of queries."""
        self.prompts = {
            "code": """You are a code analysis assistant. Focus on:
                1. Code structure and patterns
                2. Implementation details
                3. Best practices and potential improvements
                4. Dependencies and requirements

                Current context:
                {context}

                Question: {question}
                """,

            "documentation": """You are a documentation specialist. Focus on:
                1. Project overview and purpose
                2. Installation and setup
                3. Usage instructions
                4. API documentation

                Current context:
                {context}

                Question: {question}
                """,

            "general": """You are a repository analysis assistant. Focus on:
                1. Repository structure and organization
                2. Code and documentation quality
                3. Implementation patterns
                4. Project requirements

                Current context:
                {context}

                Question: {question}
                """
        }

    def _filter_documents_metadata(self, documents: List[Document]) -> List[Document]:
        """Filter document metadata to ensure compatibility with Chroma."""
        filtered_documents = []
        for doc in documents:
            if doc.metadata:
                # Create new filtered metadata dictionary
                filtered_metadata = {}
                for key, value in doc.metadata.items():
                    if value is not None and isinstance(value, (str, int, float, bool)):
                        filtered_metadata[key] = value
                    elif value is not None:
                        # Convert other types to string
                        filtered_metadata[key] = str(value)

                # Create new document with filtered metadata
                filtered_doc = Document(
                    page_content=doc.page_content,
                    metadata=filtered_metadata
                )
                filtered_documents.append(filtered_doc)
            else:
                # If no metadata, add empty dict
                filtered_doc = Document(
                    page_content=doc.page_content,
                    metadata={}
                )
                filtered_documents.append(filtered_doc)

        return filtered_documents

    def ingest_content(self, content: str) -> None:
        """Ingest repository content with specialized processing."""
        try:
            # Clear existing vector store
            self.clear_vector_store()

            # Process content with custom splitter
            documents = self.splitter.split_content(content)

            # Filter metadata before creating vector store
            filtered_documents = self._filter_documents_metadata(documents)

            # Create vector store with filtered documents
            self.vector_store = Chroma.from_documents(
                documents=filtered_documents,
                embedding=self.embeddings,
                persist_directory="./repo_chroma_db"
            )

            # Initialize retrieval chain
            self._initialize_qa_chain()

            self.logger.info("Content ingestion completed successfully")

        except Exception as e:
            self.logger.error(f"Error during content ingestion: {str(e)}")
            raise

    def _initialize_qa_chain(self):
        """Initialize the QA chain with custom prompts and retrieval settings."""
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": self.k_retrieval,
                    "filter": None
                }
            ),
            return_source_documents=True,
            verbose=False
        )

    def query(
        self,
        question: str,
        context_filter: Optional[Dict] = None,
        query_type: str = "general"
    ) -> Dict[str, Any]:
        """Query the RAG system with custom filtering and response generation."""
        if not self.vector_store:
            raise ValueError("No content ingested. Call ingest_content first.")

        try:
            # Generate cache key
            cache_key = self._generate_cache_key(question, context_filter, query_type)

            # Check cache
            cached_response = self._check_cache(cache_key)
            if cached_response:
                return cached_response

            # Update retriever filter
            self._update_retriever_filter(query_type, context_filter)

            # Get appropriate prompt
            prompt = self.prompts.get(query_type, self.prompts["general"])

            # Execute query
            response = self.qa_chain({
                "question": question,
                "chat_history": self.get_chat_history()
            })

            # Process and structure response
            processed_response = self._process_response(response, query_type)

            # Update chat history
            self._update_chat_history(question, processed_response["answer"])

            # Cache response
            self._cache_response(cache_key, processed_response)

            return processed_response

        except Exception as e:
            self.logger.error(f"Error in query: {str(e)}")
            raise

    def _process_response(self, response: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """Process and structure the response based on query type."""
        # Format the answer for terminal readability
        formatted_answer = self._format_for_terminal(response["answer"])

        processed_response = {
            "answer": formatted_answer,
            "sources": [],
            "metadata": {
                "query_type": query_type,
                "timestamp": RepoRAG._get_timestamp()
            }
        }

        # Extract and format source information
        for doc in response.get("source_documents", []):
            source_info = {
                "content": doc.page_content[:200] + "...",  # Truncate for brevity
                "metadata": doc.metadata
            }
            processed_response["sources"].append(source_info)

        # Create a formatted string representation
        processed_response["formatted_output"] = self._create_formatted_output(processed_response)

        return processed_response

    def _format_for_terminal(self, text: str) -> str:
        """Format text for better terminal readability."""
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Format code blocks
        text = re.sub(
            r'```(\w+)?\n(.*?)\n```',
            lambda m: f"\n{'=' * 40}\n{m.group(2)}\n{'=' * 40}\n",
            text,
            flags=re.DOTALL
        )

        # Format inline code
        text = re.sub(
            r'`([^`]+)`',
            lambda m: f"[{m.group(1)}]",
            text
        )

        return text

    def _create_formatted_output(self, processed_response: Dict[str, Any]) -> str:
        """Create a formatted string representation of the response."""
        sections = []

        # Add answer section
        sections.append("### Answer\n")
        sections.append(processed_response["answer"])

        # Add sources section if available
        if processed_response["sources"]:
            sections.append("\n### Sources\n")
            for idx, source in enumerate(processed_response["sources"], 1):
                source_text = f"\n{idx}. **File:** {source['metadata'].get('file_path', 'unknown')}"
                if 'language' in source['metadata']:
                    source_text += f"\n   **Language:** {source['metadata']['language']}"
                source_text += f"\n   **Preview:** {source['content']}"
                sections.append(source_text)

        # Add metadata section
        sections.append("\n### Metadata\n")
        sections.append(f"**Query Type:** {processed_response['metadata']['query_type']}")
        sections.append(f"**Timestamp:** {processed_response['metadata']['timestamp']}")

        return "\n".join(sections)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def _generate_cache_key(
        self,
        question: str,
        context_filter: Optional[Dict],
        query_type: str
    ) -> str:
        """Generate cache key including context filter and query type."""
        key_content = f"{question}-{str(context_filter)}-{query_type}"
        return hashlib.md5(key_content.encode('utf-8')).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if response is cached."""
        cache_path = os.path.join(self.cache_dir, cache_key)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None

    def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache response."""
        cache_path = os.path.join(self.cache_dir, cache_key)
        with open(cache_path, 'wb') as f:
            pickle.dump(response, f)

    def _update_retriever_filter(self, query_type: str, custom_filter: Optional[Dict] = None):
        """Update retriever's filter based on query type and custom filter."""
        base_filter = {}

        # Add query type-specific filters
        if query_type == "code":
            base_filter["content_type"] = "code"
        elif query_type == "documentation":
            base_filter["content_type"] = "markdown"

        # Merge with custom filter if provided
        if custom_filter:
            base_filter.update(custom_filter)

        # Update retriever
        if base_filter:
            self.qa_chain.retriever.search_kwargs["filter"] = base_filter
        else:
            self.qa_chain.retriever.search_kwargs["filter"] = None

    def get_chat_history(self) -> List[Tuple[str, str]]:
        """Get formatted chat history."""
        return [(self.chat_history[i].content, self.chat_history[i + 1].content)
                for i in range(0, len(self.chat_history), 2)]

    def _update_chat_history(self, question: str, answer: str) -> None:
        """Update chat history."""
        self.chat_history.append(HumanMessage(content=question))
        self.chat_history.append(AIMessage(content=answer))

    def clear_memory(self) -> None:
        """Clear chat history."""
        self.chat_history = []
        self.logger.info("Chat history cleared")

    def clear_vector_store(self) -> None:
        """Clear the vector store."""
        if hasattr(self, 'vector_store'):
            self.logger.info("Clearing vector store")
            shutil.rmtree('./repo_chroma_db', ignore_errors=True)
            self.vector_store = None

    def clear_cache(self) -> None:
        """Clear the cache directory."""
        self.logger.info("Clearing cache directory")
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        stats = {
            "total_documents": 0,
            "total_tokens": 0,
            "content_types": {},
            "languages": {},
            "cache_size": 0,
            "chat_history_length": len(self.chat_history) // 2
        }

        # Get vector store stats if available
        if self.vector_store:
            collection = self.vector_store._collection
            docs = collection.get()
            stats["total_documents"] = len(docs["ids"])

            # Analyze metadata
            for metadata in docs["metadatas"]:
                # Count content types
                content_type = metadata.get("content_type", "unknown")
                stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1

                # Count languages
                language = metadata.get("language", "unknown")
                stats["languages"][language] = stats["languages"].get(language, 0) + 1

                # Count tokens
                stats["total_tokens"] += metadata.get("tokens", 0)

        # Get cache size
        cache_size = 0
        for root, _, files in os.walk(self.cache_dir):
            for file in files:
                cache_size += os.path.getsize(os.path.join(root, file))
        stats["cache_size"] = cache_size

        return stats

    def optimize(self) -> None:
        """Optimize the RAG system for better performance."""
        if not self.vector_store:
            return

        try:
            self.logger.info("Starting RAG system optimization")

            # Get current stats
            before_stats = self.get_stats()

            # Optimize vector store
            collection = self.vector_store._collection
            collection.persist()

            # Clear unnecessary cache entries
            self._clean_cache()

            # Get stats after optimization
            after_stats = self.get_stats()

            # Log optimization results
            self.logger.info(f"Optimization completed. Cache size reduced from "
                           f"{before_stats['cache_size']} to {after_stats['cache_size']} bytes")

        except Exception as e:
            self.logger.error(f"Error during optimization: {str(e)}")
            raise

    def _clean_cache(self) -> None:
        """Clean old or invalid cache entries."""
        try:
            # Get all cache files
            cache_files = os.listdir(self.cache_dir)

            # Remove files older than 7 days
            from datetime import datetime, timedelta
            max_age = timedelta(days=7)
            now = datetime.now()

            for cache_file in cache_files:
                cache_path = os.path.join(self.cache_dir, cache_file)
                file_modified = datetime.fromtimestamp(os.path.getmtime(cache_path))

                if now - file_modified > max_age:
                    os.remove(cache_path)

        except Exception as e:
            self.logger.error(f"Error cleaning cache: {str(e)}")
            raise

    def export_config(self) -> Dict[str, Any]:
        """Export current configuration."""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "k_retrieval": self.k_retrieval,
            "cache_dir": self.cache_dir,
            "stats": self.get_stats()
        }

    @classmethod
    def from_config(cls, config: Dict[str, Any], groq_api_key: str) -> 'RepoRAG':
        """Create a RepoRAG instance from configuration."""
        instance = cls(
            groq_api_key=groq_api_key,
            chunk_size=config.get("chunk_size", 1000),
            chunk_overlap=config.get("chunk_overlap", 200),
            k_retrieval=config.get("k_retrieval", 4),
            cache_dir=config.get("cache_dir", "./cache")
        )
        return instance

# Helper functions for external use
def create_repo_rag(groq_api_key: str, **kwargs) -> RepoRAG:
    """Create a new RepoRAG instance with given configuration."""
    return RepoRAG(groq_api_key=groq_api_key, **kwargs)

def load_repo_rag(config_path: str, groq_api_key: str) -> RepoRAG:
    """Load a RepoRAG instance from a configuration file."""
    with open(config_path, 'r') as f:
        config = pickle.load(f)
    return RepoRAG.from_config(config, groq_api_key)