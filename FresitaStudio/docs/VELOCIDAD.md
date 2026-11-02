# Benchmark de latencia y tokens por segundo (experimental)

Fresita puede medir un modelo local compatible con OpenAI usando el script
fresita_speed.py. El panel gráfico integra esta medición en la pestaña **Evaluar IA**.

Ejemplo con Python 3.12 desde FresitaStudio:

    py -3.12 fresita_speed.py casos.jsonl --modelo modelo-cargado

El archivo casos.jsonl tiene las claves pregunta, referencia y categoria,
igual que el benchmark de calidad existente. Solo se envía pregunta al
servidor 127.0.0.1. No se envía referencia.

Se guardan predicciones privadas para posterior evaluación y un reporte
numérico independiente bajo Documents/Fresita Studio/experiments/velocidad.
El reporte no contiene prompts, referencias ni respuestas. Si el servidor
no reporta usage.completion_tokens, Fresita muestra N/D en lugar de
inventar tokens por segundo.

La tasa calculada es tokens de salida / duración total de solicitudes.
Incluye latencia HTTP y prefill; no representa velocidad pura de
decodificación. El benchmark también muestrea la VRAM global de la GPU 0 (si existe nvidia-smi) y la RAM global de Windows mediante GlobalMemoryStatusEx. Informa línea base, pico observado, último valor y delta pico-base, todos en MiB. **Estos números NO son memoria atribuible al modelo**, porque incluyen otros procesos y pueden omitir picos entre muestras. Si el hardware o la API no permiten medir, muestra N/D; nunca inventa valores. El muestreo comienza y termina con el benchmark y no permanece activo después.
El servidor debe estar iniciado manualmente. No se ejecuta código
Python generado por el modelo. Las pruebas CI usan un requester falso.


## VRAM por proceso (opcional)

En **Evaluar IA** puedes introducir el PID de Windows del servidor local que
ejecuta el modelo. Deja el campo vacío si no conoces el PID. También está
disponible en la línea de comandos:

    py -3.12 fresita_speed.py casos.jsonl --modelo modelo-cargado --pid-servidor 12345

Fresita consulta `nvidia-smi --id=0 --query-compute-apps=pid,used_gpu_memory`
para identificar una única fila del PID indicado en GPU 0. No suma procesos
distintos, no atribuye la VRAM global al modelo y no interpreta `N/A` como
cero. Si Windows WDDM, el controlador o el servidor no permiten identificar
la memoria del proceso, informa **N/D**. La cifra por PID, cuando existe,
incluye todas las asignaciones del proceso (no sólo los pesos del modelo).
Un PID incorrecto o un servidor que usa varios procesos puede dar N/D o
una medición incompleta. No se envían datos a internet y el muestreo sólo
ocurre mientras se ejecuta el benchmark. **Esta función aún requiere
validación física en RTX 5060 / Windows 11.**


## RAM física por proceso (opcional)

Con el mismo PID introducido para VRAM, Fresita consulta en Windows 11 la
API de sólo lectura GetProcessMemoryInfo y registra WorkingSetSize
en MiB: línea base, pico observado, última muestra y diferencia pico-base.
El working set es la RAM física residente del proceso completo y puede
incluir páginas compartidas. No es memoria privada ni memoria exclusiva del
modelo; tampoco suma automáticamente procesos hijos del servidor.

Si no se proporciona PID, no se realiza consulta por proceso. Si el PID es
incorrecto, el proceso termina o Windows deniega acceso, se registra N/D,
no cero. El muestreo termina con el benchmark, no lee contenidos de memoria,
no instala controladores y no requiere paquetes adicionales. Las pruebas CI
comprueban la API sobre el propio proceso de pruebas de Windows; todavía
falta contrastar el valor con el servidor real y la RTX 5060.


## Detectar el PID automáticamente (Windows 11)

En **Evaluar IA**, pulsa **Detectar PID del servidor local**. Fresita consulta
`netstat -ano -p tcp` en segundo plano y busca exclusivamente un proceso en
estado de escucha (`LISTENING` o `ESCUCHANDO`) sobre el puerto exacto de
`http://127.0.0.1:PUERTO/v1`. Sólo considera direcciones locales IPv4
`127.0.0.1` y `0.0.0.0`; si hay varios PIDs diferentes, un error o ningún
listener, indica **N/D** y deja el PID manual sin cambios. No mata ni inicia
procesos, no consulta redes externas y no atribuye la memoria al modelo.

**Limitación:** el PID del listener puede ser el de un proxy o servidor
intermediario, no el del proceso que aloja los pesos de la IA. Verifica el PID
antes de confiar en RAM/VRAM por proceso; Windows WDDM puede seguir mostrando
N/D. Esta detección tiene pruebas de parsing en CI, pero aún falta comprobar
su comportamiento con un servidor real y la RTX 5060.


## Posibles procesos secundarios (informativo, Windows)

Al pulsar **Detectar PID y posibles procesos secundarios**, Fresita identifica el
PID del listener local y obtiene una instantánea de los pares PID/PPID mediante
la API de Windows Toolhelp. Muestra hasta 32 **posibles descendientes** en tres
niveles. No ejecuta comandos de esos procesos ni lee argumentos, rutas, pesos,
datasets o memoria. No requiere paquetes adicionales.

**Importante:** la relación padre-hijo no demuestra que un proceso cargue la
IA. Un PID puede reutilizarse, el árbol puede cambiar después de la instantánea
y un motor puede no ser descendiente del servidor HTTP. Los secundarios
**no se suman** a las mediciones de RAM/VRAM por PID. El PID que se registra en
el benchmark sigue siendo el listener seleccionado. Si la instantánea falla
o excede los límites, se muestra N/D en vez de una lista parcial. La
detección se ejecuta en segundo plano, sin sondeo permanente.

Las pruebas unitarias cubren jerarquías, ciclos, duplicados, profundidad y
límites; en CI Windows se consulta una instantánea real y se comprueba que
incluya el propio proceso de pruebas. Sigue pendiente contrastar el árbol
con un servidor real y RTX 5060 física.


## Instantánea de RAM por PID de posibles secundarios

Al pulsar **Detectar PID y posibles procesos secundarios**, Fresita consulta una
vez el working set del listener y hasta 32 candidatos descendientes. La barra
de estado muestra valores individuales o **N/D** si Windows deniega el acceso.
No suma memoria ni afirma qué proceso aloja la IA. El PID puede reutilizarse,
el parentesco puede cambiar y el working set incluye páginas compartidas.
No hay muestreo continuo ni acceso a pesos o datasets.

CI verifica la lógica con mediciones simuladas; falta validación con servidor
real en Windows 11 y RTX 5060.
