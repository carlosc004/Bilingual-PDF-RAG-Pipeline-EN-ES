# Bilingual-PDF-RAG-Pipeline-EN-ES

> This repository features a RAG framework optimized for English PDF documents. It supports seamless bilingual interaction, allowing users to query and receive answers in either English or Spanish.
>
> Note: Includes an experimental multimodal module for query-based image extraction (Work in Progress).
>
> **Nota**: Este proyecto funciona con **cualquier PDF en INGLÉS** con el nombre `Documento.pdf`.

Un asistente virtual inteligente para consultar manuales técnicos. Utiliza tecnologías de IA avanzadas para responder preguntas en español o inglés, mostrando información relevante del documento y automáticamente extraer imágenes relacionadas.

## 🚀 Características

- **Chatbot Inteligente**: Consulta dudas técnicas sobre cualquier tema del manual
- **Búsqueda Semántica**: Utiliza embeddings para encontrar contenido relevante
- **Soporte Multidioma**: Responde en español o inglés según preferencia del usuario
- **Extracción Automática de Imágenes**: Muestra imágenes técnicas relevantes del documento
- **Interfaz Web Amigable**: Interfaz moderna construida con Streamlit

## 🏗️ Arquitectura del Sistema

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

### Componentes

| Componente | Puerto | Descripción |
|------------|--------|-------------|
| Frontend Streamlit | 8501 | Interfaz de usuario web |
| Backend API | 8001 | Lógica principal y coordinación |
| Translation Server | 8000 | Traducción ES↔EN + Visión por computadora |

## 📋 Requisitos

### Software Necesario

- **Python 3.10+**
- **API Key de Groq** (gratuita en [groq.com](https://groq.com))

### Dependencias Principales

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

Ver [`requirements.txt`](requirements.txt) para la lista completa.

## ⚡ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repo-url>
   cd RAG
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar API Key**
   
   Crear archivo `api.key` con tu clave de Groq:
   ```
   gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

5. **Colocar el manual**
   
   Coloca cualquier PDF en **INGLÉS** llamado `Documento.pdf` en la raíz del proyecto. El sistema indexará su contenido automáticamente.

## 🎯 Uso

### Inicio Rápido

Ejecuta el launcher que inicia todos los servicios automáticamente:

```bash
python launcher.py
```

Esto abrirá:
1. Servidor de traducción (puerto 8000)
2. Backend API (puerto 8001)
3. Interfaz web (puerto 8501)

### Inicio Manual (opcional)

Si prefieres iniciar los servicios por separado:

```bash
# Terminal 1: Servidor de traducción + visión
python server_translation.py

# Terminal 2: Backend API
uvicorn main_api:app --port 8001

# Terminal 3: Frontend
streamlit run frontend.py
```

## 💬 Uso del Asistente

1. Abre el navegador en `http://localhost:8501`
2. Selecciona el idioma de respuesta (Español/Inglés)
3. Escribe tu pregunta sobre el documento
4. El asistente responderá citando las páginas relevantes
5. Haz clic en "Buscar imágenes" para ver imágenes técnicas relacionadas

## 🔧 Configuración

### Cambiar el Documento PDF

Edita [`main_api.py`](main_api.py:11) para especificar otro archivo:

```python
PATH_PDF = "tu_documento.pdf"
```

### Modelos LLM

El sistema usa Groq con modelos Llama. Puedes modificar los modelos en [`functions.py`](functions.py:89):

```python
modelos = [
    ("llama-3.3-70b-versatile", "mejor calidad"),
    ("llama-3.1-8b-instant", "fallback rápido")
]
```

### Embeddings

Por defecto usa `sentence-transformers/all-MiniLM-L6-v2`. Puedes cambiarlo en [`functions.py`](functions.py:10).

## 📁 Estructura del Proyecto

```
RAG/
├── launcher.py              # Inicio automático de todos los servicios
├── main_api.py              # Backend FastAPI principal
├── frontend.py              # Interfaz Streamlit
├── functions.py             # Funciones core (LLM, embeddings, imágenes)
├── rag_engine.py            # Motor de búsqueda RAG
├── indexador.py             # Indexador de PDF a Chroma
├── cache_rag.py             # Sistema de caché
├── server_translation.py    # Servidor de traducción + visión
├── translator.py            # Modelo de traducción
├── api.key                  # API key de Groq (no incluido)
├── requirements.txt         # Dependencias Python
├── Documento.pdf           # Tu PDF en INGLÉS
├── db/                      # Base de datos vectorial (Chroma)
└── temp_visuals/           # Imágenes temporales
```

## 🐛 Solución de Problemas

### Error: "No se encontró el documento"
- Asegúrate de que `Documento.pdf` existe en la raíz del proyecto
- El sistema lo indexará automáticamente la primera vez

### Error de conexión con Groq
- Verifica que `api.key` contiene una API key válida
- Comprueba tu cuota en el dashboard de Groq

### Las imágenes no se muestran
- Asegúrate de que el PDF tiene imágenes embebidas
- Verifica que el servidor de traducción está corriendo en puerto 8000

### Memoria insuficiente
- Reduce el número de fragmentos en [`indexador.py`](indexador.py:22): `chunk_size=300`

## 📄 Licencia

Este proyecto es para uso educativo y de demostración.

## 🙏 Créditos

- **Modelos de traducción**: [Helsinki-NLP/opus-mt-es-en](https://huggingface.co/Helsinki-NLP/opus-mt-es-en)
- **Modelo de visión**: [Salesforce/blip-image-captioning-base](https://huggingface.co/Salesforce/blip-image-captioning-base)
- **Embeddings**: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- **LLM**: [Groq Llama](https://groq.com)
