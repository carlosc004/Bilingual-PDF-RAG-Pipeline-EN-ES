import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from rag_engine import RAGEngine
from functions import consultar_llm, llamar_servidor_traduccion, extraer_imagenes_de_pagina, describir_imagen_simple, evaluar_relevancia_con_llm
from indexador import ejecutar_indexacion
import cache_rag

# --- CONFIGURACIÓN INICIAL ---
PATH_PDF = "Documento.pdf"
DB_DIR = "db"

app = FastAPI(title="RAG Backend API")

# --- INICIALIZACIÓN DEL SISTEMA ---
if not os.path.exists(DB_DIR):
    print(f"\n[SISTEMA] Base de datos no encontrada en '{DB_DIR}'.")
    print(f"[SISTEMA] Iniciando indexación de {PATH_PDF} (esto puede tardar un momento)...")
    ejecutar_indexacion(PATH_PDF, DB_DIR)
    print("[SISTEMA] Indexación completada con éxito.\n")

# Cargamos el motor RAG una sola vez al inicio
rag = RAGEngine(DB_DIR)

# --- MODELOS DE DATOS ---
class ChatRequest(BaseModel):
    pregunta: str
    idioma: str  # Recibe "ES" o "EN" desde el Frontend

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "message": "Servidor WMF 1500 S listo"}

@app.post("/clear_cache")
def clear_cache():
    """Limpia el caché de imágenes y contexto."""
    cache_rag.limpiar_cache()
    return {"status": "cache_cleared"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Proceso:
    1. Traducir pregunta al inglés (solo para buscar en RAG)
    2. Buscar en RAG (contexto siempre en inglés)
    3. Consultar LLM con pregunta y contexto en inglés
    4. El LLM responde en español (forzado por el prompt)
    """
    pregunta = request.pregunta
    idioma = request.idioma
    pregunta_en = pregunta
    
    # 1. TRADUCIR PREGUNTA AL INGLÉS (solo para buscar)
    if idioma == "ES":
        print(f"[BACKEND] Traduciendo pregunta al inglés: {pregunta}")
        res_to_en = llamar_servidor_traduccion("to_en", pregunta)
        if res_to_en:
            pregunta_en = res_to_en["translated_text"]
    
    # 2. BÚSQUEDA EN EL MANUAL (RAG) - contexto siempre en inglés
    print(f"[BACKEND] Buscando en manual: {pregunta_en}")
    contexto_en, docs_originales = rag.buscar_contexto(pregunta_en)
    
    print(f"[DEBUG] Contexto encontrado: {len(contexto_en)} caracteres")
    
    if not contexto_en:
        return {
            "respuesta": "No he encontrado información relevante en el manual para esa consulta.",
            "imagenes": []
        }

    # 3. CONSULTA AL LLM
    respuesta = consultar_llm(pregunta_en, contexto_en, idioma_destino=idioma)
    
    print(f"[DEBUG] Respuesta del LLM: {respuesta[:200] if respuesta else 'VACÍA/NONE'}...")

    if not respuesta:
        respuesta = "No tengo una respuesta disponible."
    
    # 4. GUARDAR EN CACHÉ (solo pregunta, respuesta y páginas)
    paginas_detectadas = sorted(list(set([d.metadata.get('page', 0) for d in docs_originales])))
    
    cache_rag.actualizar_cache(
        pregunta_en=pregunta_en,
        respuesta=respuesta,
        paginas_contexto=paginas_detectadas
    )
    
    return {
        "respuesta": respuesta,
        "imagenes": [],
        "pregunta_original": pregunta_en
    }


@app.post("/search_images")
async def search_images_endpoint(request: ChatRequest):
    """
    Busca imágenes relevantes para la pregunta usando BLIP y LLM.
    Usa caché si está disponible para evitar cálculos redundantes.
    """
    print(f"[BACKEND] Buscando imágenes para: {request.pregunta}")
    
    # 1. Verificar si hay caché válido (pregunta + páginas)
    cache = cache_rag.obtener_cache()
    usar_cache = cache_rag.hay_cache_valido()
    
    if usar_cache:
        print(f"[BACKEND] Usando páginas en caché: {cache['paginas_contexto']}")
        pregunta_en = cache["pregunta_en"]
        respuesta = cache["respuesta"]
        paginas_detectadas = cache["paginas_contexto"]
    else:
        # 1. Traducir pregunta
        pregunta_en = request.pregunta
        if request.idioma == "ES":
            res_to_en = llamar_servidor_traduccion("to_en", request.pregunta)
            if res_to_en:
                pregunta_en = res_to_en["translated_text"]
        
        # 2. Buscar en RAG para obtener páginas relevantes
        contexto_en, docs_originales = rag.buscar_contexto(pregunta_en)
        
        if not contexto_en:
            return {"imagenes": [], "mensaje": "No se encontró contexto relevante"}
        
        paginas_detectadas = sorted(list(set([d.metadata.get('page', 0) for d in docs_originales])))
        respuesta = None
    
    # 3. Extraer imágenes de las páginas (siempre hacerlo aquí, bajo demanda)
    rutas_imagenes = []
    for p in paginas_detectadas:
        img_paths = extraer_imagenes_de_pagina(PATH_PDF, p)
        rutas_imagenes.extend(img_paths)
    
    print(f"[BACKEND] Imágenes extraídas: {len(rutas_imagenes)}")
    
    if not rutas_imagenes:
        return {"imagenes": [], "mensaje": "No hay imágenes en las páginas del contexto"}
    
    # 4. Describir imágenes con BLIP (bajo demanda)
    descripciones = []
    for img_path in rutas_imagenes:
        try:
            desc = describir_imagen_simple(img_path)
            descripciones.append({
                "imagen": img_path,
                "descripcion": desc
            })
        except Exception as e:
            print(f"[WARN] Error describiendo imagen {img_path}: {e}")
    
    if not descripciones:
        return {"imagenes": [], "mensaje": "No se pudieron extraer descripciones"}
    
    # Filtrar imágenes que son solo texto
    descripciones_filtradas = [d for d in descripciones if not d['descripcion'].lower().strip().startswith('a table')]
    descripciones = descripciones_filtradas
    
    if not descripciones:
        return {"imagenes": [], "mensaje": "Todas las imágenes eran solo texto"}
    
    # 5. Usar LLM para determinar relevancia (pasando pregunta + descripciones + respuesta)
    print(f"[BACKEND] Evaluando relevancia con LLM...")
    relevantes, aviso = evaluar_relevancia_con_llm(pregunta_en, descripciones, respuesta)
    
    if len(relevantes) < 3 and len(rutas_imagenes) > 0:
        relevantes = rutas_imagenes[:5]
        aviso = "(Mostrando imágenes del manual - no se pudo determinar relevancia precisa)"
    
    print(f"[BACKEND] Imágenes mostradas: {len(relevantes)}")
    
    return {
        "imagenes": relevantes,
        "todas_las_imagenes": rutas_imagenes,
        "descripciones": [d["descripcion"] for d in descripciones],
        "aviso": aviso
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
