"""
Sistema de caché para optimizar el flujo RAG.
Almacena: pregunta, respuesta LLM, y páginas del contexto.
Las imágenes se describen bajo demanda en /search_images.
"""

# Caché global para almacenar datos de la sesión actual
_cache = {
    "pregunta_en": None,           # Pregunta traducida al inglés
    "respuesta": None,             # Respuesta generada por el LLM
    "paginas_contexto": [],         # Páginas donde se encontró contexto
    "timestamp": None              # Para validar antigüedad
}

def actualizar_cache(pregunta_en, respuesta, paginas_contexto):
    """Actualiza el caché con los datos de la consulta actual."""
    import time
    _cache["pregunta_en"] = pregunta_en
    _cache["respuesta"] = respuesta
    _cache["paginas_contexto"] = paginas_contexto
    _cache["timestamp"] = time.time()
    print(f"[CACHE] Caché actualizado: pregunta='{pregunta_en[:30]}...', páginas={paginas_contexto}")

def obtener_cache():
    """Retorna el caché actual."""
    return _cache

def limpiar_cache():
    """Limpia el caché."""
    global _cache
    _cache = {
        "pregunta_en": None,
        "respuesta": None,
        "paginas_contexto": [],
        "timestamp": None
    }
    print("[CACHE] Caché limpiado")

def hay_cache_valido():
    """Verifica si hay caché válido (no vacío)."""
    return _cache["pregunta_en"] is not None and _cache["respuesta"] is not None

def obtener_paginas_cache():
    """Retorna las páginas en caché."""
    return _cache.get("paginas_contexto", [])
