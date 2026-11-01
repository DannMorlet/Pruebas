# 🍓 Fresita Studio — IA en español (Windows x64)

Espacio de desarrollo independiente para **Fresita Studio**, creador, editor, entrenador y laboratorio de modelos de inteligencia artificial.

> Estado: **rama de desarrollo**. No confundir este andamiaje con una versión terminada ni con los paquetes locales Fresita 0.1/0.2.

## Objetivo

Interfaz en español mexicano para:
- Crear modelos Transformer desde cero con arquitectura configurable y recuento verificable de parámetros.
- Entrenar con SFT, LoRA, QLoRA, DPO, destilación profesor-alumno y otras técnicas respaldadas por motores compatibles.
- Preparar datasets JSONL/JSON/CSV, preferencias y conjuntos de evaluación.
- Inspeccionar modelos safetensors; editar vocabulario, capas y adaptadores **mediante copias**, sin sobrescribir el original.
- Exportar modelos y adaptadores en formatos que realmente soporte su arquitectura.
- Registrar hardware, estimar RAM/VRAM y administrar experimentos reproducibles.
- Probar Qwen, Gemma, Phi y Nemotron; objetivo experimental Matick v1: cuatro estudiantes ~600M.
- Explorar la red Matick de 1,000 agentes independientes de ~2.4M parámetros, con pruebas de desempeño por etapa.

## Equipo de referencia

Windows 11 x64; NVIDIA RTX 5060 8 GB; Intel Core Ultra 5 225F; 32 GB RAM. El objetivo es trabajar dentro de ~7.6 GB VRAM utilizable, con entrenamientos pequeños, descarga de activaciones y configuraciones ajustables.

## Principios

1. **Operaciones reales:** nunca fingir entrenamiento, destilación, reducción de parámetros ni exportaciones.
2. **Modularidad:** GUI ligera; motores PyTorch/Unsloth/Transformers en entornos de entrenamiento separados.
3. **Reproducibilidad:** guardar parámetros, semillas, rutas, resultados y errores por experimento.
4. **Seguridad:** no ejecutar scripts arbitrarios de repositorios ni modelos sin consentimiento; nunca subir pesos, datasets personales, contraseñas o tokens.
5. **Español de México** como idioma de la interfaz, con documentación técnica en inglés cuando resulte útil.

## Organización

- `src/` código de aplicación.
- `tests/` pruebas.
- `docs/` arquitectura, compatibilidad, plan.
- `experiments/` recetas de ejemplo, **sin checkpoints grandes**.

### Referencias técnicas

- [Unsloth](https://github.com/unslothai/unsloth) — entrenamiento optimizado; código ajeno no se copia indiscriminadamente.
- [Transformers](https://github.com/huggingface/transformers)
- [TRL](https://github.com/huggingface/trl)
- [PEFT](https://github.com/huggingface/peft)
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)

## Estado de entrega GitHub

Este repositorio no incluye aún el Fresita.exe autónomo ni el código completo del paquete local ya preparado. Los archivos subidos a esta rama son el comienzo documentado del desarrollo. Para obtener .exe independiente usaremos compilación Windows x64 en CI después de sincronizar el programa y pasar sus pruebas.

Proyecto alojado temporalmente en `DannMorlet/Pruebas`, rama `feature/fresita-studio`. Cuando exista acceso de creación de repositorios se moverá sin alterar Manguito ni Matick.
