# Bilingual-PDF-RAG-Pipeline-EN-ES

> This repository features a RAG framework optimized for English PDF documents. It supports seamless bilingual interaction, allowing users to query and receive answers in either English or Spanish.
>
> Note: Includes an experimental multimodal module for query-based image extraction (Work in Progress).
>
> **Note**: This project works with **any PDF in ENGLISH** named `Documento.pdf`.

## 🚀 Features

- **Intelligent Chatbot**: Ask technical questions about any topic in the manual
- **Semantic Search**: Uses embeddings to find relevant content
- **Multilingual Support**: Responds in Spanish or English based on user preference
- **Automatic Image Extraction**: Shows relevant technical images from the document
- **User-Friendly Web Interface**: Modern interface built with Streamlit

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Streamlit)                      │
│                         http://localhost:8501                    │
└──────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                       │
│                       http://localhost:8001                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  RAG Engine │  │  Cache RAG  │  │  LLM (Groq - Llama)     │ │
│  │  (Chroma)   │  │             │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
 ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
 │   Translation   │ │     Vision      │ │    PDF Index    │
 │   Server        │ │    (BLIP)       │ │    (on-demand)  │
 │   :8000         │ │                 │ │                 │
 │  Helsinki-NLP   │ │                 │ │                 │
 └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Components

| Component | Port | Description |
|------------|--------|-------------|
| Streamlit Frontend | 8501 | Web user interface |
| Backend API | 8001 | Main logic and coordination |
| Translation Server | 8000 | ES↔EN translation + Computer Vision |

## 📋 Requirements

### Required Software

- **Python 3.10+**
- **Groq API Key** (free at [groq.com](https://groq.com))

### Main Dependencies

```
fastapi
streamlit
langchain
langchain-chroma
langchain-huggingface
chromadb
sentence-transformers
transformers
torch
pymupdf
pillow
requests
language_tool_python
uvicorn
```

See [`requirements.txt`](requirements.txt) for the complete list.

## ⚡ Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd RAG
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key**
   
   Create `api.key` file with your Groq key:
   ```
   gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

5. **Place the manual**
   
   Place any PDF in **ENGLISH** named `Documento.pdf` in the project root. The system will automatically index its content.

## 🎯 Usage

### Quick Start

Run the launcher that starts all services automatically:

```bash
python launcher.py
```

This will open:
1. Translation server (port 8000)
2. Backend API (port 8001)
3. Web interface (port 8501)

### Manual Start (optional)

If you prefer to start services separately:

```bash
# Terminal 1: Translation server + vision
python server_translation.py

# Terminal 2: Backend API
uvicorn main_api:app --port 8001

# Terminal 3: Frontend
streamlit run frontend.py
```

## 💬 Using the Assistant

1. Open browser at `http://localhost:8501`
2. Select response language (Spanish/English)
3. Write your technical question, for example:
   - "¿Cómo limpio el grupo de café?"
   - "What does error E12 mean?"
   - "¿Cada cuánto debo hacer mantenimiento preventivo?"
4. The assistant will respond citing the manual pages
5. Click "Buscar imágenes" to see relevant technical diagrams

## 🔧 Configuration

### Change the PDF Manual

Edit [`main_api.py`](main_api.py:11) to specify another file:

```python
PATH_PDF = "tu_manual.pdf"
```

### LLM Models

The system uses Groq with Llama models. You can modify the models in [`functions.py`](functions.py:89):

```python
modelos = [
    ("llama-3.3-70b-versatile", "mejor calidad"),
    ("llama-3.1-8b-instant", "fallback rápido")
]
```

### Embeddings

By default it uses `sentence-transformers/all-MiniLM-L6-v2`. You can change it in [`functions.py`](functions.py:10).

## 📁 Project Structure

```
RAG/
├── launcher.py              # Automatic startup of all services
├── main_api.py              # Main FastAPI backend
├── frontend.py              # Streamlit interface
├── functions.py             # Core functions (LLM, embeddings, images)
├── rag_engine.py            # RAG search engine
├── indexador.py             # PDF to Chroma indexer
├── cache_rag.py             # Cache system
├── server_translation.py    # Translation + vision server
├── translator.py            # Translation model
├── api.key                  # Groq API key (not included)
├── requirements.txt         # Python dependencies
├── Documento.pdf           # Your PDF in ENGLISH
├── db/                      # Vector database (Chroma)
└── temp_visuals/           # Temporary images
```

## 🐛 Troubleshooting

### Error: "Manual not found"
- Make sure `Documento.pdf` exists in the project root
- The system will automatically index it the first time

### Connection error with Groq
- Verify that `api.key` contains a valid API key
- Check your quota in the Groq dashboard

### Images not displaying
- Make sure the PDF has embedded images
- Verify that the translation server is running on port 8000

### Insufficient memory
- Reduce the number of chunks in [`indexador.py`](indexador.py:22): `chunk_size=300`

## 📄 License

This project is for educational and demonstration purposes.

## 🙏 Credits

- **Translation models**: [Helsinki-NLP/opus-mt-es-en](https://huggingface.co/Helsinki-NLP/opus-mt-es-en)
- **Vision model**: [Salesforce/blip-image-captioning-base](https://huggingface.co/Salesforce/blip-image-captioning-base)
- **Embeddings**: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- **LLM**: [Groq Llama](https://groq.com)
