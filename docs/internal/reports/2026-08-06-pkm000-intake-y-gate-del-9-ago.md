# PKM-000 · Intake del Pokémon TCG y el gate que estaba mal fechado

Fecha: 2026-08-06 · Ticket: `PKM-000` (cerrado) · Sin commits (falta autorización)

## Resumen

Se pidió preparar la competición de Pokémon para arrancar la investigación
cuando el propietario avise. Está preparada: proyecto creado, reglas
verificadas, motor de batalla corriendo y medido en la torre, entorno
reproducible. Se puede empezar a trabajar en cuanto él lo diga.

Por el camino apareció **un error de fecha en el plan que teníamos** y no es
menor: el gate no es el 6 de septiembre, es **el 9 de agosto**, dentro de tres
días.

## El hallazgo

Arrastrábamos que había que hacer *Join* en la Strategy antes del 6-sep. Al
leer las páginas reales resultó que:

1. **Ese Join ya estaba hecho.** La CLI da `userHasEntered: True` para
   `pokemon-tcg-ai-battle-challenge-strategy`.
2. **La Strategy no se puede competir sola.** Su propia página lo dice:
   «Participation in the Simulation Category […] **is required** to enter this
   Strategy Category competition», y sus reglas oficiales añaden que para optar
   a premio hay que competir «as part of the **same Team registered in the
   Simulation division**».
3. **La Simulation cierra inscripciones el 9-ago** y envíos el 16-ago. En ella
   **no** estamos inscritos (`userHasEntered: False`, y `competitions download`
   devuelve 403).

El plan decía «intake la semana del 7-sep, entre entrega del TFM y defensa».
Para esa fecha la Simulation llevaría un mes cerrada y los 240.000 USD de la
Strategy estarían fuera de alcance sin remedio.

## Qué se preparó

Proyecto `~/work/active/kaggle-pokemon-tcg` con la estructura de casa, git local
en `main` **sin commit inicial** (falta autorización), venv de Python 3.12 y
`requirements.txt`.

**El motor no depende del gate.** El entorno de batalla `cabt` viaja dentro de
`kaggle-environments` en PyPI, con `libcg.so` compilada para x86-64. Es decir:
se puede desarrollar y entrenar hoy sin haber aceptado nada. El gate bloquea
entrar y enviar, no trabajar. Esto es lo que permitió cerrar la preparación
entera sin esperar a nadie.

## Lo medido en la torre

| qué | resultado |
|---|---|
| partida completa, un proceso | 0,208 s (200 partidas en 41,6 s) |
| 8 procesos | 27,1 partidas/s |
| 16 procesos | 31,5 partidas/s (~113.000/hora) |
| sesgo del primer jugador | ninguno: 104-96 en 200 partidas `random` vs `random` |
| hilos | **matan el proceso** |

Lo de los hilos merece detalle porque habría costado caro descubrirlo a mitad de
un experimento: `Battle.battle_ptr` es estado global del módulo, así que cuatro
hilos jugando a la vez corrompen memoria dentro del `.so`. Salió primero como
`std::length_error` desde el C++ y luego como SIGSEGV limpio. No es capturable
con `try/except`: se lleva el proceso entero. Todo paralelismo va con
`multiprocessing`, y el punto de trabajo son 8 procesos (a 16 solo se gana 16%).

También se confirmó que `libcg.so` exporta `SearchBegin`, `SearchStep`,
`SearchEnd` y `SearchRelease`, así que **MCTS con determinización sobre la mano
oculta del rival es viable** sin nada de lo bloqueado por el 403.

## Efecto colateral: la CLI de Kaggle estaba rota

`kaggle` no existía: su enlace apuntaba a
`~/snap/code/250/.local/share/pipx/venvs/kaggle`, y esa revisión del snap de VS
Code ya se purgó (ahora van por la 252 y 254). Es el mismo patrón que ya nos
mordió con `uv` y el JRE de Momentum. Reinstalado con `XDG_DATA_HOME` forzado a
`~/.local/share`, que sobrevive a las actualizaciones.

Queda un caso igual sin arreglar y no lo he tocado por estar fuera de alcance:
los binarios de **esptool** (proyecto Marauder) siguen colgando de la revisión
252, que morirá en la próxima actualización del snap.

## Dónde está el dinero, para cuando arranque la investigación

El 70% de la nota es «Model Score», y sus criterios premian **consistencia entre
partidas repetidas** y **no depender de estados iniciales o emparejamientos
favorables**. Las reglas dicen literalmente que un puesto alto en el leaderboard
«no garantiza» buen resultado y que equipos de la zona media «pueden igualmente
lograr puntuaciones altas» con análisis profundo y buen informe.

Con 6.400 equipos en la Simulation, pelear por el top es mal negocio. El ratio
está en un agente estable, medido con rigor, y un informe que demuestre por qué
lo es. Es la tesis que ya se validó en `kaggle-rogii`, donde la solución propia y
más simple batió en el leaderboard privado al pipeline público que dominaba el
escaparate.

## Lo que necesita decisión suya

1. **`PKM-001`, antes del 2026-08-09:** aceptar las reglas de
   <https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/rules>. Un clic.
   Aceptar **no obliga a enviar nada**; no aceptar cierra la puerta del todo.
2. **`PKM-D02`, después:** cuánto esfuerzo dedicar, con el baseline delante. El
   TFM manda hasta el 21-sep y el envío del agente (16-ago) cae justo después
   del corte (~15-ago).
