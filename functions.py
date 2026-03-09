import re, os, sys
from langchain_huggingface import HuggingFaceEmbeddings 
import language_tool_python
import fitz 
import shutil
import requests

def obtener_embeddings():
    """Centraliza la configuración del modelo de embeddings."""
    return HuggingFaceEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")


def corregir_texto(texto):
    """
    Función única de limpieza:
    1. Elimina palabras repetidas (ej: 'el el').
    2. Corrige ortografía (ej: 'riefgos' -> 'riesgos').
    """
    if not texto: return ""
    
    # Paso A: Limpieza de duplicados (regex básica)
    texto = re.sub(r'(?i)\b(\w+)(?:\s+\1\b)+', r'\1', texto).strip()
    
    # Paso B: Corrección gramatical profunda
    try:
        tool = language_tool_python.LanguageTool('es')
        matches = tool.check(texto)
        texto = language_tool_python.utils.correct(texto, matches)
    except Exception:
        pass # Si falla el corrector, devolvemos al menos el texto limpio del Paso A
        
    return texto

def consultar_llm(pregunta, contexto, idioma_destino="ES"):
    """
    Consulta al LLM de Groq con fallback automático.
    Intenta primero con modelo pequeño (más rápido, mayor límite),
    si falla por rate limit, usa el modelo grande.
    
    Args:
        pregunta: Pregunta en el idioma del usuario
        contexto: Contexto (ya traducido si es necesario)
        idioma_destino: "ES" para español, "EN" para inglés
    """
    with open("api.key", "r") as f: api_key = f.read().strip()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Definir instrucciones según el idioma
    if idioma_destino == "ES":
        sistema = (
            "Eres el mejor ingeniero de soporte técnico para la máquina de café WMF 1500 S. "
            "INSTRUCCIONES DE FORMATO - SIEMPRE SIGUE ESTAS REGLAS:\n"
            "- Al dar pasos o instrucciones, usa listas numeradas: 1., 2., 3.\n"
            "- Al listar elementos, usa puntos: - elemento\n"
            "- NUNCA escribas los pasos como un párrafo\n"
            "- Usa saltos de línea entre elementos\n"
            "- SIEMPRE incluye el número de página del contexto [Página X] en tu respuesta cuando esté disponible\n"
            "INSTRUCCIONES:\n"
            "1. Usa ÚNICAMENTE el contexto proporcionado.\n"
            "2. SIEMPRE cita el número de página en tu respuesta usando el formato [Página X] (ej: 'Según la Página 5...').\n"
            "3. Si el contexto no contiene la respuesta, di que no lo sabes. No inventes números de página.\n"
            "4. Nunca menciones 'te mostraré una imagen'.\n"
            "5. Mantén las respuestas concisas y técnicas.\n"
            "6. Responde SIEMPRE en ESPAÑOL.\n"
        )
        prompt_pregunta = f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"
    else:
        sistema = (
            "You are the best technical support engineer for the WMF 1500 S coffee machine. "
            "IMPORTANT FORMATTING - ALWAYS FOLLOW THESE RULES:\n"
            "- When giving steps or instructions, use numbered lists: 1., 2., 3.\n"
            "- When listing items, use bullet points: - item\n"
            "- NEVER write steps as a paragraph\n"
            "- Use line breaks between items\n"
            "- ALWAYS include the page number from the context [Page X] in your answer when available\n"
            "INSTRUCTIONS:\n"
            "1. Use ONLY the provided context.\n"
            "2. ALWAYS cite the page number in your answer using [Page X] format (e.g., 'According to Page 5...').\n"
            "3. If the context does not contain the answer, say you don't know. Do not invent page numbers.\n"
            "4. Never mention 'I will show you an image'.\n"
            "5. Keep answers concise and technical.\n"
            "6. Respond ALWAYS in ENGLISH.\n"
        )
        prompt_pregunta = f"Context:\n{contexto}\n\nQuestion: {pregunta}"

    # Lista de modelos a intentar (orden: mejor calidad primero)
    modelos = [
        ("llama-3.3-70b-versatile", "mejor calidad"),
        ("llama-3.1-8b-instant", "fallback rápido")
    ]
    
    print(f"[DEBUG LLM] Enviando pregunta: {pregunta}")
    print(f"[DEBUG LLM] Contexto length: {len(contexto)} chars")
    print(f"[DEBUG LLM] Idioma de respuesta: {idioma_destino}")
    
    for modelo, tipo in modelos:
        print(f"[DEBUG LLM] Intentando modelo: {modelo} ({tipo})")
        
        data = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": prompt_pregunta}
            ],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            status = response.status_code
            print(f"[DEBUG LLM] Response status: {status} (type: {type(status)})")
            
            if status == 200:
                res = response.json()
                contenido = res['choices'][0]['message']['content']
                print(f"[DEBUG LLM] Éxito con modelo {modelo}")
                return contenido
            
            # Rate limit o error - intentar siguiente modelo
            print(f"[WARN LLM] Estado {status} con {modelo}, intentando siguiente...")
            print(f"[DEBUG LLM] Respuesta: {response.text[:200]}")
            continue
            
        except Exception as e:
            print(f"[ERROR LLM] Excepción con {modelo}: {e}")
            continue
    
    print("[ERROR LLM] Todos los modelos fallaron")
    return None
    
def llamar_servidor_traduccion(ruta, texto, tokens=None):
    url = f"http://127.0.0.1:8000/translate/{ruta}"
    try:
        # Debug: mostrar qué se está enviando
        print(f"[DEBUG] Traduciendo texto: {texto[:100] if texto else 'VACÍO'}...")
        print(f"[DEBUG] Tokens: {tokens}")
        
        # Solo incluir tokens si existe y no está vacío
        if tokens:
            payload = {"text": texto, "tokens": tokens}
        else:
            payload = {"text": texto}
            
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Translation server returned {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception calling translation server: {e}")
        return None

def extraer_imagenes_de_pagina(path_pdf, nro_pagina):
    """
    Extrae imágenes de una página del PDF.
    
    Basado en análisis del PDF real:
    - Imágenes embebidas típicas: 200-220px ancho (logos WMF)
    - Drawings relevantes: diagramas vectoriales individuales o compuestos
    """
    TEMP_IMG_DIR = "temp_visuals"
    if not os.path.exists(TEMP_IMG_DIR): os.makedirs(TEMP_IMG_DIR)
    doc = fitz.open(path_pdf)
    page = doc[nro_pagina]
    img_paths = []
    
    # ===== MÉTODO 1: Extraer imágenes EMBEBIDAS (logos, fotos) =====
    # Umbrales optimizados según análisis del PDF:
    # - Imágenes útiles: 100-600px (las pequeñas son iconos decorativos)
    img_list = page.get_images(full=True)
    for img_idx, img in enumerate(img_list):
        xref = img[0]
        base_img = doc.extract_image(xref)
        
        width = base_img.get("width", 0)
        height = base_img.get("height", 0)
        
        # Filtrar: logos típicos 100-600px (descartar iconos tiny)
        if 100 < width < 600 and 100 < height < 600:
            img_ext = base_img.get("ext", "png")
            fname = os.path.join(TEMP_IMG_DIR, f"img_p{nro_pagina+1}_{img_idx}.{img_ext}")
            with open(fname, "wb") as f:
                f.write(base_img["image"])
            img_paths.append(fname)
    
    # ===== MÉTODO 2: Detectar construcciones vectoriales (individuales o compuestas) =====
    if not img_paths:
        drawings = page.get_drawings()
        
        if drawings:
            # Obtener todos los rectángulos de drawings
            rects = [d["rect"] for d in drawings]
            
            # Buscar dibujos individuales grandes (diagramas bien definidos)
            for i, rect in enumerate(rects):
                # Diagramas típicos: 60-500px ancho, 25-200px alto
                if 60 < rect.width < 500 and 25 < rect.height < 200:
                    pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(1.5, 1.5))
                    if not pix.is_unicolor:
                        fname = os.path.join(TEMP_IMG_DIR, f"vec_p{nro_pagina+1}_{len(img_paths)}.png")
                        pix.save(fname)
                        img_paths.append(fname)
                        break  # Uno por página
            
            # Si no encontramos individuales grandes, buscar grupos de drawings cercanos
            # (construcciones vectoriales compuestas = varios dibujos pequeños juntos)
            if not img_paths and len(drawings) >= 3:
                # Encontrar el bounding box de todos los drawings
                min_x = min(r.x0 for r in rects)
                min_y = min(r.y0 for r in rects)
                max_x = max(r.x1 for r in rects)
                max_y = max(r.y1 for r in rects)
                
                ancho_total = max_x - min_x
                alto_total = max_y - min_y
                
                # Si el grupo total forma una región interesante (no es solo texto disperso)
                if 50 < ancho_total < 500 and 30 < alto_total < 300:
                    # Verificar que no sea solo líneas de texto
                    rect_grupo = fitz.Rect(min_x, min_y, max_x, max_y)
                    pix = page.get_pixmap(clip=rect_grupo, matrix=fitz.Matrix(1.5, 1.5))
                    if not pix.is_unicolor:
                        fname = os.path.join(TEMP_IMG_DIR, f"vec_comp_p{nro_pagina+1}.png")
                        pix.save(fname)
                        img_paths.append(fname)
    
    # ===== MÉTODO 3: Región inteligente como último recurso =====
    if not img_paths:
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Probar regiones típicas donde están los diagramas (lado derecho o centro)
        regions = [
            fitz.Rect(page_width * 0.5, page_height * 0.2, page_width * 0.95, page_height * 0.7),  # Derecha centro
            fitz.Rect(page_width * 0.3, page_height * 0.2, page_width * 0.8, page_height * 0.7),  # Centro
            fitz.Rect(0, page_height * 0.15, page_width * 0.45, page_height * 0.6),  # Izquierda
        ]
        
        for i, rect in enumerate(regions):
            pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(1.5, 1.5))
            if not pix.is_unicolor:
                fname = os.path.join(TEMP_IMG_DIR, f"ref_p{nro_pagina+1}_{i}.png")
                pix.save(fname)
                img_paths.append(fname)
                break
    
    doc.close()
    return img_paths

def abrir_recurso_visual(path):
    if sys.platform == "win32": os.startfile(path)
    elif sys.platform == "darwin": os.system(f"open '{path}'")
    else: os.system(f"xdg-open '{path}'")

def limpiar_temporales():
    TEMP_IMG_DIR = "temp_visuals"
    if os.path.exists(TEMP_IMG_DIR):
        try: shutil.rmtree(TEMP_IMG_DIR)
        except: pass

def describir_imagenes_y_filtrar(rutas_imagenes, pregunta, threshold=0.3):
    """
    Describe imágenes con BLIP y filtra por relevancia.
    Retorna solo las imágenes relevantes.
    """
    if not rutas_imagenes:
        return [], []
    
    try:
        # Llamar al servicio de visión
        url = "http://127.0.0.1:8000/vision/describe_batch"
        payload = {
            "image_path": "|".join(rutas_imagenes),
            "pregunta": pregunta
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"[WARN] Error en describe_batch: {response.status_code}")
            return rutas_imagenes, []  # Devolver todas si falla
        
        resultados = response.json().get("results", [])
        
        # Calcular relevancia: comparar descripción con pregunta
        pregunta_words = set(pregunta.lower().split())
        imagenes_relevantes = []
        descripciones = []
        
        for item in resultados:
            desc = item.get("description", "").lower()
            desc_words = set(desc.split())
            
            # Similitud: palabras en común entre pregunta y descripción
            common = pregunta_words & desc_words
            relevancia = len(common) / max(len(pregunta_words), 1)
            
            # Solo mostrar si hay suficientes palabras en común
            if relevancia >= threshold or len(common) >= 2:
                imagenes_relevantes.append(item["image_path"])
                descripciones.append(desc)
                print(f"[VISION] Relevante ({relevancia:.2f}, palabras: {common}): {desc[:60]}...")
        
        # Si no hay relevantes, devolver la primera
        if not imagenes_relevantes and rutas_imagenes:
            imagenes_relevantes = [rutas_imagenes[0]]
            descripciones = ["(Sin descripción de relevancia)"]
        
        return imagenes_relevantes, descripciones
        
    except Exception as e:
        print(f"[ERROR] describrir_imagenes_y_filtrar: {e}")
        return rutas_imagenes, []


def describir_imagen_simple(ruta_imagen):
    """Describe una imagen usando el servicio de visión."""
    try:
        url = "http://127.0.0.1:8000/vision/describe"
        payload = {"image_path": ruta_imagen, "pregunta": ""}
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("description", "")
        return ""
    except Exception as e:
        print(f"[ERROR] describir_imagen_simple: {e}")
        return ""


def evaluar_relevancia_con_llm(pregunta, descripciones, respuesta=None):
    """
    Usa el LLM para evaluar qué imágenes son relevantes.
    Recibe también la respuesta del LLM para mejor contextualización.
    """
    if not descripciones:
        return [], "No hay imágenes disponibles"
    
    lista_desc = "\n".join([
        f"- Imagen {i+1}: {d['descripcion']}" 
        for i, d in enumerate(descripciones)
    ])
    
    # Añadir la respuesta del LLM al prompt si está disponible
    respuesta_info = ""
    if respuesta:
        respuesta_info = f"""
And this is the answer already provided to the user:
{respuesta}
"""
    
    prompt = f"""
Given the user's question: "{pregunta}"
{respuesta_info}
And the following image descriptions from the manual:
{lista_desc}

Rate each image from 0-10 based on how RELEVANT it is to answering the user's question or expanding on the answer provided.
0 = completely irrelevant, 10 = highly relevant.

Respond with ONLY the ratings in this exact format:
Imagen 1: 8
Imagen 2: 3
Imagen 5: 10

Rate ALL images, even if irrelevant.
"""
    
    resultado = consultar_llm(prompt, "", idioma_destino="EN")
    print(f"[LLM Relevancia] {resultado}")
    
    try:
        ratings = {}
        matches = re.findall(r'(?:Imagen\s*)?(\d+)\s*:\s*(\d+)', resultado)
        for img_num, score in matches:
            idx = int(img_num) - 1
            if 0 <= idx < len(descripciones):
                ratings[idx] = int(score)
        
        if not ratings:
            return [d["imagen"] for d in descripciones[:3]], "(Imágenes sugeridas - no se pudo evaluar relevancia)"
        
        sorted_images = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
        top_images = [descripciones[idx]["imagen"] for idx, score in sorted_images[:5]]
        
        avg_score = sum(score for _, score in sorted_images[:5]) / len(sorted_images[:5]) if sorted_images else 0
        if avg_score < 5:
            aviso = f"(Estas imágenes pueden no ser muy relevantes - puntuación media: {avg_score:.1f}/10)"
        else:
            aviso = f"(Imágenes sugeridas - relevancia media: {avg_score:.1f}/10)"
        
        return top_images, aviso
        
    except Exception as e:
        print(f"[ERROR] evaluando relevancia: {e}")
        return [d["imagen"] for d in descripciones[:3]], "(Imágenes sugeridas)"