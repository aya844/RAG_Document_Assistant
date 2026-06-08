# RAG Document Assistant

A prototype document-grounded question-answering system that enables users to upload PDF/TXT documents and receive answers grounded in the uploaded content, with explicit citations or refusal on unsupported queries.

## Overview

**RAG Document Assistant** combines hybrid retrieval (dense + sparse), cross-encoder reranking, and a controlled LangGraph agent workflow to deliver reliable, interpretable answers from document collections. The system prioritizes local operation, privacy, and minimal architectural complexity.

### Key Features

- **Document Upload**: Support for PDF and TXT formats with automatic parsing and indexing
- **Hybrid Retrieval**: Combined dense (semantic) and sparse (lexical) search with RRF fusion
- **Cross-Encoder Reranking**: Precise relevance scoring with `ms-marco-MiniLM-L-6-v2`
- **Threshold-Based Refusal**: Explicit refusal on low-confidence queries to prevent hallucination
- **Document Filtering**: Query-time filtering to search specific document subsets
- **Parent-Child Chunking**: Dual-level indexing for precise search + coherent context
- **Local-Only Models**: All LLM and embedding inference via Ollama (no external APIs)
- **Grounded Responses**: Citations include filename, page number, rerank score, and excerpt

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js / TypeScript)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           FastAPI Backend (Python)                   │   │
│  │                                                      │   │
│  │  Upload Endpoint         Chat Endpoint               │   │
│  │  ↓                        ↓                          │   │
│  │  Parse → Chunk →         LangGraph Agent             │   │
│  │  Embed → Store           ├─ Classify Intent          │   │
│  │                          ├─ Retrieve Tool            │   │
│  │  ┌────────────────────┐  ├─ Summarize Tool           │   │
│  │  │  Storage Layer     │  └─ Generate Answer          │   │
│  │  │                    │                              │   │
│  │  │  Qdrant            │  Retrieval Pipeline:         │   │
│  │  │  (child vectors)   │  1. Dense (Qdrant)           │   │
│  │  │                    │  2. Sparse (BM25)            │   │
│  │  │  SQLite            │  3. RRF Fusion (k=60)        │   │
│  │  │  (parent chunks)   │  4. Cross-Encoder Rerank     │   │
│  │  │                    │  5. Fetch Parents            │   │
│  │  │  BM25 Index        │  6. Return Top-5             │   │
│  │  │  (disk-persisted)  │                              │   │
│  │  └────────────────────┘                              │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Technology |
|-----------|------|-----------|
| **Ingestion** | Parse, chunk, embed, store documents | FastAPI, Ollama |
| **Dense Retrieval** | Semantic search via embeddings | Qdrant, nomic-embed-text |
| **Sparse Retrieval** | Lexical search via BM25 | rank-bm25 |
| **Fusion** | Combine dense + sparse results | RRF (k=60) |
| **Reranking** | Precision scoring of candidates | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| **Agent** | Orchestrate workflow & tools | LangGraph |
| **Answer Generation** | LLM-based response synthesis | Ollama (qwen2.5:7b) |
| **Frontend** | User interface & real-time chat | Next.js, TypeScript |

---

## Technical Stack

### Backend
- **Framework**: FastAPI 0.115.5
- **Runtime**: Python 3.10+
- **Agent Orchestration**: LangGraph 0.2.53
- **Vector Database**: Qdrant 1.12.1
- **SQL Database**: SQLite (aiosqlite 0.20.0)
- **Document Parsing**: PyMuPDF 1.24.13, pypdf 5.1.0
- **Retrieval**:
  - Dense: Ollama + nomic-embed-text
  - Sparse: rank-bm25 0.2.2
  - Reranker: sentence-transformers 3.3.1 (cross-encoder/ms-marco-MiniLM-L-6-v2)
- **LLM**: Ollama + qwen2.5:7b-instruct (configurable)

### Frontend
- **Framework**: Next.js 14+
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Fetch API

### Infrastructure (Local)
- **Ollama**: Local inference engine for embeddings and LLM
- **Qdrant**: Local vector database (Docker or standalone)

---

## Project Structure

```
RAG_document_Assistant/
├── Backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration & settings
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── agent/
│   │   │   ├── graph.py         # LangGraph workflow
│   │   │   ├── tools.py         # Tool implementations
│   │   │   └── prompts.py       # LLM prompts
│   │   ├── api/
│   │   │   ├── documents.py     # Upload endpoint
│   │   │   ├── chat.py          # Chat endpoint
│   │   │   └── retrieval.py     # Retrieval endpoints
│   │   ├── ingestion/
│   │   │   ├── parser.py        # Document parsing
│   │   │   ├── chunker.py       # Parent-child chunking
│   │   │   └── embedder.py      # Embedding generation
│   │   ├── retrieval/
│   │   │   ├── pipeline.py      # Main retrieval pipeline
│   │   │   ├── dense.py         # Qdrant search
│   │   │   ├── sparse.py        # BM25 search
│   │   │   ├── fusion.py        # RRF fusion
│   │   │   └── reranker.py      # Cross-encoder reranking
│   │   └── storage/
│   │       └── database.py      # SQLite operations
│   └── data/
│       ├── rag.db              # SQLite database
│       ├── bm25_index.pkl      # Persisted BM25 index
│       └── uploads/            # Uploaded document files
├── Frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Main page
│   │   │   ├── globals.css
│   │   │   └── api/
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── CitationBadge.tsx
│   │   ├── lib/
│   │   │   └── api.ts           # API client
│   │   └── types/
│   │       └── index.ts         # TypeScript types
├── docker-compose.yml           # Docker setup (Qdrant)
└── README.md                   # This file
```

---

## Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Ollama** installed and running locally
  - Download: [ollama.ai](https://ollama.ai)
  - Run: `ollama serve`
- **Qdrant** running locally
  - Option 1: Docker: `docker run -p 6333:6333 qdrant/qdrant`
  - Option 2: Standalone: [qdrant.tech](https://qdrant.tech)
- **Git** for cloning the repository

---

## Installation & Setup

### 1. Backend Setup

```bash
cd Backend
pip install -r requirements.txt
```


### 2. Frontend Setup

```bash
cd Frontend
npm install
```

### 3. Start Ollama & Qdrant

In separate terminals:

```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Qdrant
docker run -p 6333:6333 qdrant/qdrant
# OR standalone Qdrant if installed
```

### 4. Start Backend Server

```bash
cd Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs` (Swagger UI)

### 5. Start Frontend Development Server

```bash
cd Frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

---

## Usage

### 1. Upload a Document

1. Open the frontend at `http://localhost:3000`
2. Click **"Upload Document"**
3. Select a PDF or TXT file
4. System will:
   - Parse the document
   - Create parent-child chunks
   - Generate embeddings (via Ollama)
   - Store in Qdrant, SQLite, and BM25 index
   - Return upload confirmation

### 2. Ask a Question

1. Type a question in the chat input
2. Optionally select specific documents to filter search
3. Press Enter or click Send
4. System will:
   - Classify intent (retrieve vs. summarize)
   - Execute hybrid retrieval (dense + sparse + RRF + rerank)
   - Check grounding threshold (default: 0.25)
   - Generate answer with citations OR return refusal

### 3. Example Queries

- **Retrieval**: "What is the main topic of this document?"
- **Summarization**: "Summarize the document"
- **Filtered**: Select document(s) in sidebar, then ask a question

---

## Retrieval Pipeline Details

### Dense Retrieval (Qdrant)
- Embeds query with nomic-embed-text (via Ollama)
- Searches Qdrant for top-15 semantically similar child chunks
- Returns chunks with cosine similarity scores

### Sparse Retrieval (BM25)
- Tokenizes query on whitespace
- Matches against BM25-indexed child chunks
- Returns top-15 matches by BM25 score
- Index is persisted to disk and updated on each document upload

### Reciprocal Rank Fusion (RRF)
- Combines dense and sparse rankings using formula: `score(d) = Σ 1/(k + rank(d))`
- Dampening constant: k=60 (standard)
- Documents appearing in both lists receive contributions from both rankers

### Cross-Encoder Reranking
- Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` from sentence-transformers
- Evaluates query-chunk pairs jointly
- Returns top-5 reranked results

### Threshold-Based Refusal
- If top rerank score < 0.25 (configurable), system refuses without LLM call
- Prevents hallucination and saves compute on low-confidence queries

---

## Configuration

Edit `Backend/app/config.py` or `.env` to customize:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `child_chunk_size` | 300 | Words per child chunk |
| `child_chunk_overlap` | 50 | Word overlap between children |
| `parent_chunk_size` | 1200 | Words per parent chunk |
| `retrieval_top_k` | 15 | Top-K for dense and sparse retrieval |
| `rerank_top_n` | 5 | Top-N after reranking |
| `grounding_score_threshold` | 0.25 | Min rerank score for grounding |
| `embed_model` | nomic-embed-text | Ollama embedding model |
| `llm_model` | qwen2.5:7b-instruct | Ollama LLM model |

---

## Performance Considerations

- **Embedding Generation**: ~0.5–2s per document (depends on size and GPU availability)
- **Query Latency**: ~2–5s (dense + sparse + fusion + reranking)
- **Storage**: ~100MB for BM25 index per 1000 child chunks

---

## Limitations of the Prototype

This is a **prototype** designed for evaluation and iterative development. For production deployment, consider:
- Migrating SQLite to PostgreSQL for concurrent access
- Adding query caching and result streaming
- Implementing user authentication and multi-tenancy
- Replacing Ollama with cloud inference for reliability
- Adding structured logging and monitoring

---

## License

This project is provided as-is for educational and research purposes.

---

**Created by**: Eya Bargouth  


