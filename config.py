"""Configuration for Cloud Migration Agent with LangChain + RAG"""

import os
from typing import Optional

from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

# Bedrock Configuration
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v1")

# RAG Configuration
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 100
RAG_K_RESULTS = 4

# Vector Store Configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss")  # Can be: faiss, weaviate, chromadb, opensearch


class BedrockLLMConfig:
    """Bedrock LLM Configuration"""

    def __init__(self, region: str = BEDROCK_REGION, model_id: str = BEDROCK_MODEL_ID):
        self.region = region
        self.model_id = model_id
        self.llm = ChatBedrock(
            model_id=model_id,
            region_name=region,
            model_kwargs={
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9
            }
        )

    def get_llm(self):
        return self.llm


class EmbeddingConfig:
    """Bedrock Embeddings Configuration"""

    def __init__(self, region: str = BEDROCK_REGION, model_id: str = EMBEDDING_MODEL_ID):
        self.region = region
        self.model_id = model_id
        self.embeddings = BedrockEmbeddings(
            model_id=model_id,
            region_name=region
        )

    def get_embeddings(self):
        return self.embeddings


class VectorStoreConfig:
    """Vector Store Configuration (supports multiple backends)"""

    def __init__(
        self,
        vector_db_type: str = VECTOR_DB_TYPE,
        embeddings = None,
        documents: Optional[list] = None
    ):
        self.vector_db_type = vector_db_type
        self.embeddings = embeddings
        self.documents = documents or []
        self.vector_store = None

    def create_vector_store(self):
        """Create vector store based on configured type"""

        if not self.documents or not self.embeddings:
            return None

        if self.vector_db_type == "faiss":
            self.vector_store = FAISS.from_documents(
                documents=self.documents,
                embedding=self.embeddings
            )
        elif self.vector_db_type == "weaviate":
            # Weaviate would require client setup
            print("[Config] Weaviate support requires additional setup")
        elif self.vector_db_type == "chromadb":
            # ChromaDB would be initialized here
            print("[Config] ChromaDB support requires additional setup")
        elif self.vector_db_type == "opensearch":
            # OpenSearch requires connection details
            print("[Config] OpenSearch support requires connection details")

        return self.vector_store

    def get_vector_store(self):
        return self.vector_store


class RAGConfig:
    """RAG (Retrieval-Augmented Generation) Configuration"""

    def __init__(
        self,
        llm_config: Optional[BedrockLLMConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
        vector_store_config: Optional[VectorStoreConfig] = None
    ):
        self.llm_config = llm_config or BedrockLLMConfig()
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.vector_store_config = vector_store_config

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP
        )

    def create_rag_chain(self, documents: list):
        """Create RAG chain for question answering"""

        # Split documents
        splits = self.text_splitter.split_documents(documents)

        # Create vector store
        vs_config = VectorStoreConfig(
            vector_db_type=VECTOR_DB_TYPE,
            embeddings=self.embedding_config.get_embeddings(),
            documents=splits
        )
        vector_store = vs_config.create_vector_store()

        if not vector_store:
            return None

        # Create RAG chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=self.llm_config.get_llm(),
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_kwargs={"k": RAG_K_RESULTS}
            )
        )

        return rag_chain

    def get_llm(self):
        return self.llm_config.get_llm()

    def get_embeddings(self):
        return self.embedding_config.get_embeddings()


class AgentMemoryConfig:
    """Memory configuration for agents (conversation history)"""

    def __init__(self):
        self.chat_history: dict = {}

    def get_history(self, agent_id: str) -> list:
        return self.chat_history.get(agent_id, [])

    def add_message(self, agent_id: str, role: str, content: str):
        if agent_id not in self.chat_history:
            self.chat_history[agent_id] = []

        self.chat_history[agent_id].append({
            "role": role,
            "content": content
        })

    def clear_history(self, agent_id: str):
        self.chat_history[agent_id] = []


# Global configuration instances
bedrock_llm_config = BedrockLLMConfig()
embedding_config = EmbeddingConfig()
rag_config = RAGConfig(
    llm_config=bedrock_llm_config,
    embedding_config=embedding_config
)
agent_memory_config = AgentMemoryConfig()


def get_configured_llm():
    """Get globally configured LLM"""
    return bedrock_llm_config.get_llm()


def get_configured_embeddings():
    """Get globally configured embeddings"""
    return embedding_config.get_embeddings()


def get_rag_chain(documents: list):
    """Get configured RAG chain"""
    return rag_config.create_rag_chain(documents)
