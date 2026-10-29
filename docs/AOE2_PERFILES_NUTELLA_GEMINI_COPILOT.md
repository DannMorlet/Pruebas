# Diseños recibidos · Nutella #5, Gemini #6, Copilot #7

Fecha: 2026-10-29. Se registran solo **resúmenes y requisitos derivados** de la conversación y de los dos PDF aportados por el usuario; **no se publican sus PDF ni se presupone que los ejemplos INI/YAML sean código .per jugable**.

## ALINEACIÓN INALTERABLE: solo 7

1. Matick → Matick.per → Agua_de_Morlet.per → LM Studio / GPU RTX.
2. Nemesis → Nemesis.per → Nemesis.per → Intel NPU experimental.
3. Tyran → Tyran.per → Agua_de_Mazapan.per → SmolLM2-360M compartido en GPU, personalidad A.
4. Mazapan → Mazapan.per → Capuchino_de-Mazapan.per → el MISMO SmolLM2-360M compartido en GPU, personalidad B.
5. Nutella → Nutella.per → AI (HD version).per → guerra de desgaste.
6. Gemini → Gemini.per → AI (HD version).per → operaciones económicas/tácticas coordinadas.
7. Copilot → Copilot.per → AI (HD version).per → general adaptativo y analítico.

**RECORDATORIO DEL USUARIO (pendiente de prueba):** cuando se retome Tyran y Mazapan, recordar probar **UN SmolLM2-360M-Instruct** (opción Q8_0 ~386 MB de archivo o Q4_K_M ~271 MB), compartiendo pesos cargados en GPU y separando contexto/persona/memoria para ambas IAs. Los pesos no se parten en 2 fragmentos independientes de 200 MB. Verificar VRAM real, KV-cache, fiabilidad y FPS. El usuario desea que se le recuerde esta decisión.

## 5. NUTELLA — La estratega del desgaste

**Material de origen:** descripción original escrita por el usuario en el chat. Frase central de la personalidad: «No necesito destruirte hoy. Necesito que cometas errores mañana.»

**Perfil principal expresado por el usuario:**
- agresividad = 65
- economía = 85
- molestia = 100
- paciencia = 95
- caos = 90

**Otro bloque INI de intención (NO sintaxis nativa .per):** AnnoyEnemy=100; DirectConquest=40; Harassment=100; Expansion=95; Economy=90; SneakyBases=100; VillagerRaids=100; NeverFightFair=95. Hay dos valores económicos (85 y 90) en distintas secciones; conservar ambos como preferencias de origen, sin simular que no hay discrepancia. Para el primer perfil de prueba: usar 85 como preferencia primaria y 90 como objetivo situacional en expansiones de alto rendimiento.

### Sus cinco subagentes lógicos — NO cinco modelos cargados

1. **Untador:** expansión gradual, puestos avanzados, asegurar recursos abandonados, múltiples bases.
2. **Hormiga:** hostigar aldeanos aislados, reliquias, exploradores y rutas de comercio; evitar sacrificios gratuitos.
3. **Chocolate Negro:** operaciones de desgaste; intercambiar presión militar por pérdida económica rival.
4. **Avellana:** explotar debilidades reveladas por reconocimiento (oro expuesto, trabajadores lejanos, huecos de muralla).
5. **Empalagador Supremo:** recuperación y dispersión de la economía tras perder base, proteger aldeanos supervivientes y construir otro ejército.

### Reglas tácticas a implementar tras validar motor

- Explorar legalmente; elegir blancos económicos visibles; raid corto y retirada segura.
- En paz, distribuir aldeanos para expansión segura; establecer defensas y puestos de producción.
- Preferir desgaste de unidades/economía frente a exterminio frontal si está en desventaja.
- Recuperarse desde una base secundaria o un solo aldeano cuando la situación y recursos lo permitan.
- Rivalidades de chat de broma con Copilot (analiza mucho), Gemini (obligarlo a reaccionar), Matick/Gemma 4 (desgastarlo) y Morlet (impredecible). Mantener tono divertido, sin toxicidad ni spam.
- **NeverFightFair=95 significa tácticas sorprendentes, no hacks, omnisciencia ni recursos regalados**. Modo fair-play por defecto.

## 6. GEMINI — Tactical Operations Manual (2 páginas aportadas)

**Material de origen:** PDF «Gemini Manual para IA de Empires 2 de .pdf» páginas 1–2.

- Filosofía: macromanagement eficiente + exploración inteligente + picos de poder sincronizados; coordinación conceptual con Copilot y el modelo de **Matick/Gemma 4** cargado en LM Studio. NO introducir una octava IA llamada Gemma.
- **Tesorero (Macroeconomía):** balance dinámico de aldeanos y de recogida de recursos para subir de edad sin colapsar.
- **Explorador (Scout & Visión):** reconocer recursos/reliquias y evitar bajas suicidas bajo torres rivales.
- **Pesos PDF:** aggression_level = 78/100, economic_efficiency = 92/100, flank_support_weight = 88/100, retreat_threshold_hp = 30 %.

### Distribución de aldeanos por edad — copia fiel de porcentajes del PDF

| Edad | Comida | Madera | Oro | Piedra | Contexto |
|---|---:|---:|---:|---:|---|
| Oscura | 55 % | 35 % | 10 % | 0 % | Recolección, subida ágil, scouting |
| Feudal | 45 % | 40 % | 15 % | 0 % | Defensa, murallas, arqueros |
| Castillos | 40 % | 35 % | 20 % | 5 % | Monjes, castillos, preparación asedio |
| Imperial | 35 % | 35 % | 20 % | 10 % | Trabuquetes y composición élite |

**Advertencias de compilación del ejemplo PDF, página 2:**
- El ejemplo es un **fragmento conceptual**, no una IA completa.
- Las directivas \`#load-if-defined EDAD-OSCURA\`, etc. requieren macros definidas por el loader real; comprobar sintaxis y definición en AoE2 DE.
- Las instrucciones \`(goal estrategia-actual N)\` aparecen tras \`=>\` como si fueran acciones, pero \`goal\` no equivale a una asignación; traducir a \`set-goal\` con ID legal y sin colisiones tras verificar la tabla existente.
- Bloques \`(true)\` sin controles pueden disparar repetidamente; añadir comparación de edad y control del estado de ejecución, o condiciones apropiadas.
- Un porcentaje no entrena aldeanos, no manda unidades a construir ni combate por sí mismo; fusionar con la IA HD completa y sus dependencias compatibles. No sobrescribir el original por un fragmento.
- Los pesos 78, 92, 88 y 30 % son **objetivos de diseño**; el motor .per no los interpreta automáticamente como propiedades.

### Comportamiento esperado

Mantener producción de aldeanos y rotar porcentajes por edad, explorar sin pérdidas innecesarias, pedir apoyo de flanco a Copilot cuando comparta equipo, retirarse de enfrentamientos desfavorables y lanzar picos de fuerza cuando tenga producción/militares listos. Solo información permitida por el juego.

## 7. COPILOT — Strategic Core v7.0 (12 páginas aportadas)

**Material de origen:** PDF «Copilot_Strategic_Core_v7_AOE.pdf» páginas 1–12.

Filosofía del PDF: **«La información gana batallas. La economía gana guerras. La adaptación gana campeonatos.»**

### Metas

- Supervivencia, economía continua, exploración, tecnología y dominio militar.
- Estrategia según civilización, mapa, aliados y enemigos; perfiles para arqueros, caballería, infantería, asedio, naval y economía.
- Analizar expansión, ejércitos, tecnologías, oportunidades y vulnerabilidades únicamente con estado observado.
- Producir aldeanos de manera continua, redistribuir recursos, expandir y escoger contracomposiciones.
- Evaluar riesgos de escenarios futuros y balance de control económico/militar/territorial.

### Diez funciones / subagentes lógicos descritos (NO diez LLM adicionales)

1. Comandante Supremo (orquestador)
2. Economista
3. Explorador
4. Ingeniero
5. General Militar
6. Defensor
7. Analista del enemigo
8. Logística
9. Predictivo
10. Cazador de oportunidades

En la página 12 se listan 9 entradas bajo \`subagents\`, más \`commander: supreme\` = **10 funciones en total**. No confundir con 10 procesos ni 10 agentes externos independientes.

### Pesos de personalidad (página 12)

Adaptive=100; Economy=95; Technology=100; Military=90; Exploration=90; Risk=45; Expansion=85.

### Límites del material

- Páginas 2–11, tituladas «Módulo Avanzado 1–10», **repiten casi literalmente la misma frase** sobre análisis de recursos/rutas/tecnología/composiciones. No aportan diez algoritmos ni bloques de reglas distintos; los roles detallados son **especificación a implementar**.
- La página 12 usa \`Copilot.per [Personality]\` y \`Copilot.ia\` con YAML; es **pseudocódigo de diseño**, no el formato ejecutable para el motor de AoE2 DE. El archivo emparejado necesario se llamará **Copilot.ai**, no \`.ia\`.
- No es evidencia de integración con Microsoft/GitHub Copilot de pago. Solo define la personalidad de la IA personal.

### Traducción táctica para la versión experimental

1. Si hay amenaza cercana y riesgo elevado, priorizar defensa y evacuación.
2. Si hay aldeanos ociosos, colas vacías o déficit de recursos, corregir macroeconomía.
3. Si falta información, explorar sin sacrificar el scout.
4. Si se detecta debilidad visible y se dispone de contracomposición, atacar con límite de riesgo.
5. Si es viable avanzar de edad, investigar; si el mapa cambia, reconsiderar prioridades.
6. Si hay aliados, coordinar logística, producción complementaria y apoyo, no compartir información oculta.

## Requisitos comunes a las siete

- Jugables sin LLM y sin puentes: economía, viviendas, aldeanos, edad, ejército, ataque y defensa básicos en sus \`.per\`.
- No regalar recursos en el modo por defecto fair-play; ayudas pequeñas por edad, si se implementan, deberán ser un modo opcional identificado como no competitivo.
- Chat con personalidad y límites de frecuencia. Objetivo heredado: 500 frases por IA; todavía **NO están creadas 3,500 frases ni un sistema completo de chat**.
- Las capacidades de LM Studio y NPU deben estar en servicios separados y opcionales, con simulación y permisos antes de controlar partidas.
- Antes de afirmar funcionamiento: validar paréntesis, \`#load-if\`, IDs de goals, includes \`Promisory\`, soporte de engine/edades y partidas reales en AoE2 DE, sin modificar originales.

## Próximas tareas

1. Traducir la especificación de Gemini a porcentajes por edad **dentro de la base HD completa**, sin reglas infinitas ni comandos inventados.
2. Crear planificador de acciones de Copilot con datos observados y contraunidades compatibles con civilización.
3. Crear política Nutella para múltiples bases, raids económicos, recuperación y desgaste.
4. Priorizar que los tres produzcan aldeanos y edificios en una partida real antes de añadir 500 frases cada uno.
5. Medir y probar después Tyran y Mazapan con **SmolLM2-360M compartido**. Esta es una decisión de trabajo a recordar en futuras sesiones.

**Nota de publicación:** este documento resume entradas del usuario. No se copian ni incluyen los PDF originales en el repositorio público.
