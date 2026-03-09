import os
from langchain_chroma import Chroma
from functions import obtener_embeddings


class RAGEngine:
    def __init__(self, db_dir="db", k=10):
        self.k = k
        self.embeddings = obtener_embeddings()
        
        # Verificar existencia ANTES de crear la conexión
        if not os.path.exists(db_dir):
            print(f"[ERROR] La base de datos en {db_dir} no existe.")
        
        self.vector_db = Chroma(persist_directory=db_dir, embedding_function=self.embeddings)

    def buscar_contexto(self, query_en, k=None):
        k = k if k is not None else self.k
        results = self.vector_db.similarity_search(query_en, k=k)
        
        if not results:
            return "", []

        contexto_acumulado = "CONTEXT EXTRACTED FROM MANUAL:\n"
        for d in results:
            page_num = d.metadata.get('page', 0) + 1
            contexto_acumulado += f"\n[Page {page_num}]: {d.page_content}\n"
                    
        return contexto_acumulado, results
