import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from functions import obtener_embeddings

def ejecutar_indexacion(path_pdf, db_dir):
    # 1. Comprobación de existencia
    if os.path.exists(db_dir):
        print(f"[INDEXADOR] La base de datos en {db_dir} ya existe. Saltando indexación.")
        return 
    
    # 2. Si no existe, procedemos con la creación
    print(f"[INDEXADOR] Base de datos no encontrada. Iniciando creación en {db_dir}...")
    
    print(f"[INDEXADOR] Cargando PDF: {path_pdf}...")
    loader = PyPDFLoader(path_pdf)
    paginas = loader.load()
    
    # Configurar el splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=200,
        add_start_index=True 
    )

    # Dividir manteniendo la metadata
    docs_finales = text_splitter.split_documents(paginas)

    # VALIDACIÓN
    if docs_finales:
        test_page = docs_finales[0].metadata.get('page')
        print(f"[INDEXADOR] Test de metadata: Fragmento 1 corresponde a Pág {test_page + 1}")
    
    print(f"[INDEXADOR] Indexando {len(docs_finales)} fragmentos en Chroma...")

    embeddings = obtener_embeddings() 
    Chroma.from_documents(
        documents=docs_finales,
        embedding=embeddings,
        persist_directory=db_dir
    )
    
    print("[INDEXADOR] ¡Completado! Base de datos creada y lista.")