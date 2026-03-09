import os
from transformers import MarianTokenizer, AutoModelForSeq2SeqLM, logging

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
logging.set_verbosity_error()

# Cargar el modelo de ES->EN (para traducir preguntas al inglés)
print("Cargando modelo de traducción ES->EN...")
tk_en = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-es-en")
md_en = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-es-en")
print("Modelo ES->EN cargado.")

def _traducir(texto, tk, md):
    inputs = tk(texto, return_tensors="pt", padding=True)
    out = md.generate(**inputs, max_new_tokens=512)
    return tk.decode(out[0], skip_special_tokens=True)

def traducir_a_ingles(texto):
    return _traducir(texto, tk_en, md_en), {}
