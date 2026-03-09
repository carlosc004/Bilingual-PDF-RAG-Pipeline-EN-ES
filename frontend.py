import streamlit as st
import requests
import os
import shutil

# Configuración de la interfaz
st.set_page_config(
    page_title="RAG Asistente Técnico WMF 1500 S",
    page_icon="☕",
    layout="centered"
)


st.markdown("""
    <style>
    .stChatFloatingInputContainer { bottom: 20px; }
    .stChatMessage { border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Panel de Control")
    
    # 1. Selección de Idioma
    idioma_selec = st.selectbox(
        "Idioma de respuesta:",
        ["Español", "English"],
        index=0
    )
    idioma_code = "ES" if idioma_selec == "Español" else "EN"
    
    st.divider()
    
    # 2. Botón de búsqueda de imágenes
    # Al hacer clic, busca imágenes relevantes para la última pregunta
    if st.button("Buscar imágenes"):
        # Obtener la última pregunta del usuario
        ultima_pregunta = None
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "user":
                ultima_pregunta = msg["content"]
                break
        
        if ultima_pregunta:
            with st.spinner("Buscando imágenes relevantes..."):
                try:
                    payload = {"pregunta": ultima_pregunta, "idioma": idioma_code}
                    response = requests.post(
                        "http://127.0.0.1:8001/search_images", 
                        json=payload, 
                        timeout=180 
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        imagenes = data.get("imagenes", [])
                        descripciones = data.get("descripciones", [])
                        aviso = data.get("aviso", "")
                        
                        if imagenes:
                            st.session_state["ultimas_imagenes"] = imagenes
                            st.session_state["ultimas_descripciones"] = descripciones
                            st.session_state["ultimas_aviso"] = aviso
                            st.rerun()
                        else:
                            st.info("No se encontraron imágenes relevantes")
                    else:
                        st.error("Error al buscar imágenes")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Mostrar imágenes si existen
    if st.session_state.get("ultimas_imagenes"):
        with st.container(border=True):
            # Mostrar aviso si existe
            aviso = st.session_state.get("ultimas_aviso", "")
            if aviso:
                st.caption(f"⚠️ {aviso}")
            else:
                st.caption("📷 Imágenes sugeridas:")
            imgs = st.session_state["ultimas_imagenes"]
            pags = st.session_state.get("ultimas_paginas", [])
            
            # Navegador de imágenes
            if "img_idx" not in st.session_state:
                st.session_state["img_idx"] = 0
            
            idx = st.session_state["img_idx"]
            total = len(imgs)
            
            if total > 0 and os.path.exists(imgs[idx]):
                st.image(imgs[idx], width='stretch')
                if idx < len(pags):
                    st.caption(f"Página {pags[idx]}")
                
                # Navegación
                col_prev, col_next = st.columns(2)
                with col_prev:
                    if st.button("⬅️ Anterior", key="prev_img"):
                        st.session_state["img_idx"] = (idx - 1) % total
                        st.rerun()
                with col_next:
                    if st.button("Siguiente ➡️", key="next_img"):
                        st.session_state["img_idx"] = (idx + 1) % total
                        st.rerun()
    
    st.divider()
    
    # 3. Limpiar Chat
    if st.button("🗑️ Borrar Conversación"):
        st.session_state.messages = []
        # Limpiar también las imágenes guardadas y los archivos
        for key in ["ultimas_imagenes", "ultimas_descripciones", "ultimas_paginas", "ultimas_aviso", "img_idx"]:
            if key in st.session_state:
                del st.session_state[key]
        # Eliminar archivos temporales
        temp_dir = "temp_visuals"
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)
            except:
                pass
        st.rerun()

st.title("Asistente WMF 1500 S")
st.info("Consulta dudas técnicas sobre operación, limpieza o errores de la máquina.")

# --- RENDERIZADO DEL HISTORIAL ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- ÁREA DE ENTRADA (INPUT) ---
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Añadir mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta del Asistente
    with st.chat_message("assistant"):
        with st.spinner("Pensando... (puede tardar un poco):"):
            try:
                # Llamada al Backend en el puerto 8001
                payload = {"pregunta": prompt, "idioma": idioma_code}
                response = requests.post("http://127.0.0.1:8001/chat", json=payload, timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    txt = data["respuesta"]
                    imgs = data.get("imagenes", [])

                    st.markdown(txt)
                    
                    # Guardar en el historial
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": txt,
                        "imagenes": imgs 
                    })
                else:
                    st.error("El servidor respondió con un error.")
            except Exception as e:
                st.error(f"Error de conexión con el backend: {e}")