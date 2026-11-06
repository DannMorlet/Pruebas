# Propuestas RECIBIDAS de Gemini #6 y Copilot #7

Actualizado: 2026-10-29. Se conservan exactamente siete IAs en el orden acordado.

**Ya no están pendientes los documentos de personalidad.** El usuario envió:

- Gemini Manual para IA de Empires 2 de .pdf (2 páginas)
- Copilot_Strategic_Core_v7_AOE.pdf (12 páginas)
- Perfil Nutella #5 por mensaje de conversación.

Sus requisitos y advertencias de compilación se consolidaron en [AOE2_PERFILES_NUTELLA_GEMINI_COPILOT.md](AOE2_PERFILES_NUTELLA_GEMINI_COPILOT.md) y en [aoe2/agents.json](../aoe2/agents.json).

**Lo que SÍ está pendiente:**
- Convertir el fragmento económico de Gemini a reglas .per y .ai válidas dentro de la base de IA HD.
- Implementar las 10 funciones de Copilot como un sistema táctico medible, no como diez procesos externos.
- Convertir los cinco subagentes lógicos de Nutella en operaciones válidas del juego.
- Reconciliar todos los goals/constantes e includes con Promisory original.
- Verificar las tres IAs en partidas reales, con fallback económico y cero trucos predeterminados.
- Recuperar mediciones de VRAM/FPS si se activa un modelo externo.

**Recordatorio de subagentes GPU:** Tyran #3 y Mazapan #4 deben probar un ÚNICO modelo SmolLM2-360M-Instruct cargado en GPU, dos personas y memorias separadas. No es una partición física en modelos de 200 MB. Comprobar consumo real; no cargar ni descargar modelos sin decisión expresa del usuario.

Prototipo sin juego: [aoe2/strategy_profiles.py](../aoe2/strategy_profiles.py); diseñado para devolver prioridades simbólicas, no mandar órdenes a Age of Empires.
