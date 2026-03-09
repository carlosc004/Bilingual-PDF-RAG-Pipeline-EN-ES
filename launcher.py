import subprocess
import time
import sys
import requests
import shutil
import os

def limpiar_temp():
    """Limpia la carpeta de imágenes temporales al iniciar."""
    temp_dir = "temp_visuals"
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            print(f"[LIMPIEZA] Carpeta {temp_dir} eliminada")
        except Exception as e:
            print(f"[WARN] No se pudo eliminar {temp_dir}: {e}")
    os.makedirs(temp_dir, exist_ok=True)

def esperar_servicio(puerto, max_intentos=20):
    """Espera a que un servicio esté disponible."""
    for i in range(max_intentos):
        try:
            requests.get(f"http://127.0.0.1:{puerto}/", timeout=5)
            return True
        except:
            time.sleep(2)
    return False

def iniciar_sistema():
    print("Iniciando el sistema...")
    
    # Limpiar carpetas temporales
    limpiar_temp()
    
    # 1. Iniciar el Servidor de Traducción
    print("1/3 Lanzando Servidor de Traducción (Puerto 8000)...")
    traductor = subprocess.Popen([sys.executable, "server_translation.py"])
    
    # 2. Iniciar el Backend (API)
    print("2/3 Lanzando Backend API (Puerto 8001)...")
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "main_api:app", "--port", "8001"])

    # Esperar a que los servicios estén listos
    print("Esperando a que los servicios estén disponibles...")
    if not esperar_servicio(8000):
        print("[WARN] El servicio de traducción puede no estar listo")
    if not esperar_servicio(8001):
        print("[WARN] El backend puede no estar listo")

    # 3. Iniciar el Frontend (Streamlit)
    print("3/3 Lanzando Interfaz de Usuario...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend.py"])
    except KeyboardInterrupt:
        print("\nCerrando servicios...")
        traductor.terminate()
        backend.terminate()

if __name__ == "__main__":
    iniciar_sistema()