# Morlet · Age of Empires II DE · Arquitectura de las siete IAs

Estado: documento de preparación 2026-10-29. No equivale a una integración jugable terminada ni a pruebas reales de GPU, NPU o FPS. Este repositorio es público: no publicar originales de terceros, historiales, rutas privadas, partidas, claves ni datos personales.

## Exactamente siete identidades (orden obligatorio)

| N.º | IA | Archivo final | Procedencia | Procesamiento |
|---:|---|---|---|---|
| 1 | Matick | Matick.per | Agua_de_Morlet.per | LM Studio con modelo del usuario en RTX 5060; puente de juego |
| 2 | Nemesis | Nemesis.per | Nemesis.per | OpenVINO y NPU Intel, experimental |
| 3 | Tyran | Tyran.per | Agua_de_Mazapan.per | Modelo pequeño en GPU, subagente A |
| 4 | Mazapan | Mazapan.per | Capuchino_de-Mazapan.per | Modelo pequeño en GPU, subagente B |
| 5 | Nutella | Nutella.per | AI (HD version).per | Reglas autónomas + conocimiento táctico |
| 6 | Gemini | Gemini.per | AI (HD version).per | Propuesta Gemini recibida: Tesorero/Explorador, economía por edad, flancos |
| 7 | Copilot | Copilot.per | AI (HD version).per | Propuesta Copilot recibida: comandante adaptativo y nueve especialistas |

Aegis, Promisory, Apex y los archivos de HD son dependencias o antecedentes, NO jugadores adicionales. Los siete necesitan sus archivos .ai emparejados y los módulos .per compatibles que carguen.

## Tyran y Mazapan: IA en GPU con presupuesto mínimo

Petición: dos agentes de aproximadamente 200 MB cada uno o un único modelo de aproximadamente 400 MB compartido.

Opción A: dos copias independientes de SmolLM2-135M-Instruct GGUF Q8_0; cada GGUF pesa aproximadamente 145 MB en disco. No garantiza 145 o 200 MB reales de VRAM/RAM durante la ejecución. Fuente: https://huggingface.co/tensorblock/SmolLM2-135M-Instruct-GGUF

Opción B PREFERIDA para ensayar: un solo SmolLM2-360M-Instruct GGUF Q8_0, aproximadamente 386 MB en disco, que recibe dos contextos/personalidades diferenciadas. Alternativa Q4_K_M aproximadamente 271 MB. Dos agentes lógicos comparten los pesos de un modelo completo; NO se puede dividir ese modelo en dos medios modelos que funcionen cada uno por separado. Fuente: https://huggingface.co/tensorblock/SmolLM2-360M-Instruct-GGUF

Cada agente conserva memoria y política por separado; turnos encolados, temperatura y formato de salida definidos, tokens de contexto limitados y velocidad medida en el PC. No asumir que un modelo de 135M/360M entiende tácticas complejas: darle solo el estado RESUMIDO visible y pedirle escoger entre acciones validadas por código. El motor .per debe seguir desarrollando economía, entrenando y defendiendo cuando falle el modelo. No cargar automáticamente más modelos durante una partida ni consumir VRAM constantemente sin solicitud.

Protocolo propuesto: observar estado legítimo → resumir en datos compactos → consultar Tyran/Mazapan por la API local de LM Studio → aceptar solo una decisión de una lista blanca (explorar, producir, defender, atacar, reparar, fortificar, comerciar o hablar) → comprobar unidades propias, recursos y precondiciones → ejecutar mediante puente solo si el usuario habilitó partida local con agente externo. No usar el mouse ni teclado del usuario.

LM Studio: https://lmstudio.ai/docs/developer/openai-compat
Bridge de AoE2Control: https://aoe2control.github.io/agent-bridge/

El puente de AoE2Control es de un tercero que utiliza componentes dentro del proceso del juego, con riesgos y compatibilidad que habrá que inspeccionar. Solo partidas individuales autorizadas. Desactivar modo omnisciente y mantener la IA .per nativa activa. Para evitar competir por las mismas unidades, coordinar mediante goals del jugador cuando estén disponibles. No instalar el puente ni cambiar antivirus sin autorización.

## Lo que queremos que hagan todas

1. Arranque fiable: producir aldeanos, recolectar, construir, avanzar de edad, explorar, atacar y defender. La falta de un modelo externo NUNCA paraliza el .per.
2. Supervivencia desde un solo aldeano cuando sea viable: economía de emergencia, casa/TC si hay recursos y acceso, preservar aldeanos, reconstruir y luego militarizar. Sin prometer victorias imposibles.
3. Defensa creativa: murallas, puertas, protección de recursos y rutas, aldeanos disponibles (objetivo 1 a 10) para construir, sin comprometer toda la economía.
4. Reconocimiento y contrajuego: explorar sin omnisciencia, cambiar composición según fuerzas visibles, defender con profundidad, ataques por flancos, retiradas calculadas, recuperación de rutas comerciales.
5. Onagros y bosque solo cuando tecnología, unidad, línea de visión y juego lo permitan; no disparar peligrosamente a aliados.
6. Unidades atascadas: determinarlo con evidencia de movimiento/órdenes durante varios ciclos, intentar desbloqueo y limitar reintentos. No atribuir capacidades de detección que el .per no tenga; requerirá interfaz de estado si no existe.
7. Chat: objetivo 500 frases ORIGINALES por IA, estilo único, bromas y frases como XD o nomms, alagos, desafíos y solicitudes, límites antispam, conversación externa solo con puente. Esas 3500 frases NO están implementadas todavía.
8. Recursos de ayuda incluso entre enemigos: si el juego admite tributo y hay mercado y reservas, transferir recursos propios tras una petición, con presupuesto y sin quedarse sin supervivencia. No generar recursos.
9. Pequeños bonos por edad solicitados: 50 Oscura, 100 Feudal, 200 Castillos, 500 Imperial, tipo aleatorio. No son juego limpio; incluir únicamente en modo opcional AYUDAS con cooldown muy largo y tope finito por edad y partida, DESACTIVADO en modo justo predeterminado.
10. Inspiración militar histórica: abastecimiento, reconocimiento, maniobra, protección del flanco, defensa en profundidad, señuelos y retirada racional, traducidos a decisiones posibles en AoE2DE. No copiar capítulos completos de obras protegidas.

## Cerebros y personalidades

- Matick (#1): LLM cargado por el usuario en LM Studio, creativo y conversador. Arquitectura y manual preliminar en la rama del PR #2: https://github.com/DannMorlet/Pruebas/pull/2
- Nemesis (#2): aprendiz NPU con OpenVINO, inicializado de forma opcional y sin fallback silencioso. El anterior selector elegía aperturas rush/flush/boom y no producía tácticas en vivo. Mantenerlo como experimento medible.
- Tyran (#3): subagente GPU centrado en decisiones militares y presión controlada; personalidad definitiva adaptable al usuario.
- Mazapan (#4): subagente GPU centrado en adaptación, supervivencia y economía creativa; personalidad definitiva adaptable al usuario.
- Nutella (#5): IA táctica autónoma .per, con fortificación, resistencia y sorpresa.
- Gemini (#6): Ver documento de perfiles recibido de Gemini; no fingir que conocemos su propuesta.
- Copilot (#7): Ver documento de perfiles recibido de Copilot; no fingir que conocemos su propuesta ni que usa el servicio comercial.

## Trabajo de Codex en la PC

- Confirmar código y dependencias Promisory de los archivos .per aportados, respaldar y verificar las siete IAs base primero. No publicar automáticamente la base HD de terceros.
- Probar una IA sin controlador externo, luego una IA con bridge en modo simulación, luego Matick y después los dos agentes GPU.
- Medir VRAM real al compartir modelo, caché de contexto, latencia por decisión, RAM residente de LM Studio y FPS durante el juego. Modelos de 200 MB en disco NO garantizan procesos de 200 MB.
- Conservar NPU opcional para Nemesis y comparar con lógica .per. Sin reiniciar ni cambiar los drivers ni Python global.
- Incorporar los requisitos ya recibidos de Gemini y Copilot distinguiendo ideas PDF de código ejecutable y verificar por etapas.
- Construir y probar chat, intercambio de recursos, murallas, rescate de aldeanos y defensa por iteraciones pequeñas, con fallback.
- Rechazar comandos ajenos al jugador, acceso omnisciente, ejecución de código de modelo y operaciones que usen los controles reales del usuario.
- No declarar ninguna función jugable hasta probarla dentro de AoE2 DE. Tests unitarios fuera del juego no son suficiente.

Fuentes: https://lmstudio.ai/docs/developer/openai-compat ; https://aoe2control.github.io/agent-bridge/ ; https://huggingface.co/tensorblock/SmolLM2-135M-Instruct-GGUF ; https://huggingface.co/tensorblock/SmolLM2-360M-Instruct-GGUF .

## Diseños Nutella, Gemini y Copilot RECIBIDOS (2026-10-29)

Ya se recibieron los perfiles: Nutella por mensaje del usuario, Gemini mediante PDF de 2 páginas y Copilot mediante PDF de 12 páginas. Los hallazgos, sus parámetros, subagentes y advertencias de que el PDF es pseudocódigo se guardaron en [AOE2_PERFILES_NUTELLA_GEMINI_COPILOT.md](AOE2_PERFILES_NUTELLA_GEMINI_COPILOT.md). Se añadieron perfiles estructurados en `aoe2/agents.json` y un planificador de propuestas para los tres en `aoe2/strategy_profiles.py` con tests por ejecutar en Windows. No confundir la propuesta con código .per ya funcional.

**Recordatorio inequívoco:** la prueba preferida para Tyran (#3) y Mazapan (#4) usa UN SmolLM2-360M-Instruct cargado en GPU y DOS identidades lógicas con memoria y contexto separados, no dos medios modelos de 200 MB. Se puede optar por dos SmolLM2-135M si la calidad/rendimiento medidos lo justifican.
