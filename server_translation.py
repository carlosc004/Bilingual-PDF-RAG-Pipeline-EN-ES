from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uvicorn
import translator 
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

app = FastAPI(title="Servidor de Traducción + Visión WMF")

vision_model = None
vision_processor = None
device = "cuda" if torch.cuda.is_available() else "cpu"

@app.get("/")
def root():
    return {"status": "online", "service": "translation+vision"}

def cargar_vision():
    global vision_model, vision_processor
    if vision_model is None:
        print("[SERVIDOR] Cargando modelo de visión BLIP ...")
        vision_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        vision_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
        print("[SERVIDOR] Modelo BLIP Large listo.")

class TranslationRequest(BaseModel):
    text: str
    tokens: Optional[dict] = None

class ImageDescriptionRequest(BaseModel):
    image_path: str
    pregunta: str

@app.post("/translate/to_en")
def to_en(req: TranslationRequest):
    print(f"[SERVIDOR] Recibido para traducción EN: {req.text[:50] if req.text else 'VACÍO'}...")
    en_text, tokens = translator.traducir_a_ingles(req.text)
    return {"translated_text": en_text, "tokens": tokens}

@app.post("/vision/describe")
async def describe_image(req: ImageDescriptionRequest):
    """Describe una imagen y calcula relevancia con la pregunta."""
    cargar_vision()
    
    # Cargar imagen desde archivo
    image = Image.open(req.image_path).convert('RGB')
    
    # BLIP describe la imagen naturalmente, sin contexto forzado
    inputs = vision_processor(image, return_tensors="pt").to(device)
    out = vision_model.generate(**inputs, max_new_tokens=200)
    descripcion = vision_processor.decode(out[0], skip_special_tokens=True)
    
    return {
        "description": descripcion.strip(),
        "image_path": req.image_path
    }

@app.post("/vision/describe_batch")
async def describe_batch(req: ImageDescriptionRequest):
    """
    Describe múltiples imágenes y retorna relevancia.
    Espera una lista de rutas de imágenes.
    """
    cargar_vision()
    
    image_paths = req.image_path.split("|")  # Separar por pipe
    pregunta = req.pregunta
    resultados = []
    
    for img_path in image_paths:
        if not img_path.strip():
            continue
            
        try:
            image = Image.open(img_path.strip()).convert('RGB')
            
            # BLIP describe la imagen naturalmente
            inputs = vision_processor(image, return_tensors="pt").to(device)
            out = vision_model.generate(**inputs, max_new_tokens=100)
            descripcion = vision_processor.decode(out[0], skip_special_tokens=True)
            
            resultados.append({
                "image_path": img_path.strip(),
                "description": descripcion.strip()
            })
        except Exception as e:
            resultados.append({
                "image_path": img_path.strip(),
                "description": f"Error: {str(e)}"
            })
    
    return {"results": resultados}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
