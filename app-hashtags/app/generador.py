# Plantillas y listas para copy y hashtags por red (sin IA).
import random

REDES = ["instagram", "tiktok", "pinterest", "youtube"]

COPY_PLANTILLAS = [
    "¿Ya probaste {tema}? Te cuento por qué me encanta.",
    "Todo lo que necesitas saber sobre {tema} en un post.",
    "Si buscas {tema}, esto te va a interesar.",
    "Mi recomendación de hoy: {tema}.",
    "{tema} — tips que aplico siempre.",
    "No te pierdas esto sobre {tema}.",
    "Hilo sobre {tema}. Guarda y comparte.",
]

HASHTAGS_BASE = {
    "instagram": [
        "marketing", "emprendimiento", "negocios", "tips", "contenido", "creadores",
        "socialmedia", "community", "growth", "ventas", "ecommerce", "dropshipping",
        "colombia", "latam", "emprendedores", "digital", "redes", "inspiracion",
    ],
    "tiktok": [
        "fyp", "viral", "parati", "tips", "emprendimiento", "negocios", "marketing",
        "contenido", "creadores", "colombia", "latam", "aprende", "tutorial",
    ],
    "pinterest": [
        "ideas", "inspiracion", "tips", "marketing", "negocios", "emprendimiento",
        "diy", "diseno", "contenido", "creadores", "pinterestmarketing",
    ],
    "youtube": [
        "tutorial", "tips", "emprendimiento", "marketing", "negocios", "como",
        "aprende", "contenido", "creadores", "colombia", "latam",
    ],
}


def generar(tema: str, red: str) -> tuple[str, str]:
    tema = (tema or "").strip() or "mi contenido"
    red = (red or "instagram").lower()
    if red not in REDES:
        red = "instagram"
    copy = random.choice(COPY_PLANTILLAS).format(tema=tema)
    base = HASHTAGS_BASE.get(red, HASHTAGS_BASE["instagram"])
    tema_palabras = [p.strip().lower().replace(" ", "") for p in tema.replace(",", " ").split() if len(p.strip()) > 2][:4]
    combined = list(set(tema_palabras + base))[:16]
    random.shuffle(combined)
    hashtags = " #".join([""] + combined[:12]).strip()
    return copy, hashtags
