# Política greedy sobre la función de valor (1 ply, sin MCTS) — NEGATIVO GRANDE

Fecha: 2026-08-10. Código: `research/agentes/greedy_valor.py`.
Báscula: `arena.py` (y un clon suyo con recogida de `ESTAD`/`TIEMPOS` del módulo,
`medir.py`, en el scratchpad de la sesión). Pesos: `research/valor/valor_v2.npz`
(62→32→16→1, el de 0,7539 de acierto). `mcts.py` y `heuristico.py` intactos.

## Titular

**La hipótesis se rechaza, y por goleada.** El greedy de 1 ply sobre la red v2
gana **0,160 [0,127; 0,199] (n=400)** al heurístico y **0,280 [0,232; 0,333]
(n=300)** a `first` — el heurístico saca 0,620 a `first`. No es que no mejore:
**es casi tan malo como jugar al azar** (random saca 0,062 al heurístico) y
pierde contra la política más tonta que existe.

Y el mecanismo está medido: **no es un fallo de fontanería, ni ruido, ni
perspectiva**. La red es un buen PREDICTOR del ganador y un pésimo CRÍTICO de
acciones. Elegir por argmax de valor a 1 ply es una forma sistemática de elegir
mal, y **el daño es proporcional a cuánto se le hace caso** (curva dosis-respuesta
abajo).

## Arquitectura de lo construido

`agent(obs) -> list[int]` con `DECK = heuristico.DECK`. Por decisión no trivial:

1. Candidatas de la raíz con `_candidatas` (copiada de `mcts.py`, la heurística
   SIEMPRE en el índice 0, cap 24, todas pasan `_es_legal`).
2. K determinizaciones del `InfoTracker` (`sample` + `search_begin`, 0,13 ms). Por
   cada una, **un `search_step` por candidata desde el MISMO searchId raíz** (el
   re-step desde un sid es determinista: es la misma expansión de hijos que hace
   `mcts._itera`). Eso son K begins y K·n steps por decisión, nada más.
3. El estado hijo se evalúa con `features_v2.extrae` + la red, **en lote**
   (`np.stack` de todas las candidatas vivas de esa determinización).
   Perspectiva: copia superficial de `current` con `yourIndex = me` cuando tras la
   acción le toca al rival (igual que `mcts._evalua`). Terminal → 1/0/0,5.
4. Media por acción sobre las determinizaciones → argmax.
5. Triviales sin evaluar; guarda de `rival_bocabajo_n == 0`; `search_end()` en
   `finally`; `_T10` del heurístico salvado y restaurado; toda acción devuelta pasa
   `_es_legal` con `_fallback`; cualquier excepción → heurístico.
6. Reloj: `presupuesto = min(TOPE, (remainingOverageTime − 40) / max(rest, 20))`,
   degrada a heurístico por debajo de 0,02 s (el greedy es barato, el umbral de
   0,15 de mcts sobraba).

Config por entorno: `GREEDY_K` (4), `GREEDY_TOPE` (1,0 s), `GREEDY_CAP` (24),
`GREEDY_MARGEN` (0), `GREEDY_SIGNO` (1 / −1 test de orientación), `GREEDY_MODO`
(`todo` | `fase` | `turno` | `cartas`), `GREEDY_RASGOS` (`v2` | `v1`),
`GREEDY_PESOS`.

**Cuál es cuál en `research/valor/`** (había que comprobarlo): `valor.npz` = v1,
30 entradas; **`valor_v2.npz` = v2, 62 entradas, el bueno**; `valor_g.npz` = otra
red de 30 entradas (corpus `corpus_g.npz`), no documentada en las notas y no usada
aquí. `valor.py` carga literalmente `valor.npz`, así que **no sirve para la v2**:
`greedy_valor.py` lleva su propio cargador de 10 líneas (mismo forward, ReLU-ReLU-
sigmoide) y no toca `valor.py`.

## Resultados (todos con `--procs 3`, torre compartida)

### 1. La medida principal

| enfrentamiento | n | tasa | IC95 | referencia |
|---|---|---|---|---|
| greedy (K=4) vs **heurístico** | 400 | **0,160** | [0,127; 0,199] | 0,500 = empate |
| greedy (K=4) vs **first** | 300 | **0,280** | [0,232; 0,333] | heurístico 0,620 |

Por asiento (vs heurístico): 0,215 yendo primero / 0,105 yendo segundo.

### 2. Coste y seguridad

| | media | p50 | p95 | máx |
|---|---|---|---|---|
| s/decisión vs heurístico (n=400) | 2,46 ms | 2,10 ms | 5,60 ms | 64,2 ms |
| s/decisión vs first (n=300) | 3,06 ms | 2,50 ms | 7,85 ms | 72,2 ms |

Total de reloj por partida: **0,047 s** (presupuesto: 600 s). Primera llamada
(imports incluidos) 27 ms. **0 acciones ilegales en las 700 partidas** de las dos
tandas (7.293 + 7.502 decisiones), **0 errores de `search_step`** en 339.696 steps,
**0 determinizaciones fallidas**, 0 trackers rotos. La fontanería está sana; lo que
está roto es la idea.

### 3. Barrido de determinizaciones — NO es ruido

vs heurístico, n=200 cada uno:

| K | tasa | IC95 | ms/decisión |
|---|---|---|---|
| 1 | 0,180 | [0,133; 0,239] | 1,12 |
| 3 | 0,155 | [0,111; 0,212] | 2,14 |
| 8 | 0,160 | [0,116; 0,217] | 4,57 |

**Plano.** Más muestreo de la información oculta no arregla nada: el error es
sesgo, no varianza. (Lo mismo en modo `turno`: K=1 → 0,225 [0,173; 0,288],
K=8 → 0,185 [0,137; 0,245].)

### 4. Curva dosis-respuesta: cuanto menos se le hace caso, mejor

`GREEDY_MARGEN` = ventaja mínima que debe sacar una acción a la del heurístico
para desviarse de ella. n=200, K=4:

| margen | % decisiones que desvía | tasa vs heurístico | IC95 |
|---|---|---|---|
| 0,00 | 49% | 0,160 (n=400) | [0,127; 0,199] |
| 0,05 | 21% | 0,290 | [0,232; 0,356] |
| 0,15 | 6,5% | 0,380 | [0,316; 0,449] |
| 0,30 | 1,6% | 0,430 | [0,363; 0,499] |
| ∞ (= heurístico) | 0% | 0,500 | — |

Monótona y sin cruzar el 0,5 en ningún punto: **cada gramo de política de red
cuesta victorias**, incluso el 1,6% de desviaciones más «confiadas» (IC superior
0,499). No hay una dosis buena.

### 5. Intentos de reparación (los tres, medidos)

| variante | qué cambia | n | tasa | IC95 |
|---|---|---|---|---|
| `fase` | en la fase principal solo compara candidatas de la misma clase que la heurística (finalizadoras {atacar, terminar} vs desarrollo) | 100 | 0,140 | [0,085; 0,221] |
| `turno` | tras la acción, **completa el turno con el heurístico** y evalúa en la frontera de fase (todas las candidatas comparables) | 100 | 0,230 | [0,158; 0,322] |
| `cartas` | como `turno` pero SOLO en selects de elegir cartas (type 1), el resto lo decide el heurístico | **400** | **0,480** | **[0,431; 0,529]** |

`turno` es la reparación conceptualmente correcta (evita comparar «mi turno sigue»
con «turno del rival») y sube de 0,16 a 0,23: **arregla un tercio del agujero y
sigue perdiendo 3 a 1**. `cartas` es el único que no pierde — y no gana:
**empate limpio**, la red no aporta ni en el nicho donde el heurístico es más
pobre. Coste de `cartas`: 2,06 ms de media, p50 0,09 ms (solo actúa en el 12% de
las decisiones).

## Diagnóstico: por qué falla (con evidencia, no con hipótesis)

Protocolo del diagnóstico: se juega con el HEURÍSTICO (trayectoria sana, la partida
no se desmorona) y en cada decisión se calcula la matriz K×candidatas de valores.
25 partidas, 503 decisiones, `diag.py`/`diag2.py` del scratchpad.

**Lo que se descarta primero, medido:**

1. **No es la perspectiva ni el signo.** Con `GREEDY_SIGNO=-1` (argmin) la tasa
   cae a **0,000 [0,000; 0,037] (n=100)** frente al 0,09-0,16 del argmax: el orden
   es el correcto, solo que ambos extremos son malos. La red distingue mejor de
   peor, pero su «mejor» no es el mejor movimiento.
2. **No es que los índices signifiquen otra cosa.** El `select` raíz de la búsqueda
   se comparó con el `select` real como JSON canónico: **4.008 comparaciones,
   0 mismatches**. El índice que devuelvo es el que probé.
3. **No es ruido de determinización.** Dispersión ENTRE acciones (señal) 0,0604 vs
   dispersión de una misma acción ENTRE determinizaciones (ruido) 0,0174 →
   **señal/ruido 3,47**; el argmax con 4 dets coincide con el de otras 4 dets
   independientes el **89,6%** de las veces. La preferencia es estable y
   reproducible: se equivoca siempre igual. Concuerda con el barrido de K plano.
4. **La red SÍ predice, en la trayectoria buena.** Media del valor de la mejor
   acción por partida: **0,796 en las 16 ganadas vs 0,500 en las 9 perdidas**.
   Como predictor funciona; el problema es usarla como criterio de acción.

**Lo que sí pasa:**

5. **El greedy se desvía del heurístico en el 42,7% de las decisiones** y en cada
   desvío «ve» una ventaja media de **+0,105** de probabilidad de ganar que no
   existe. Concentración: en la fase principal (select (0,0)) coincide con el
   heurístico solo el 48,5% de las veces; en (9,41) y (4,30) coincide el 100%.
6. **Quema el turno.** Censo de tipos de opción elegidos (503 decisiones): donde
   hay ataque disponible, el heurístico ataca en 61/207 y el greedy atacaría en
   **100/207** — pero atacar cierra el turno, así que ataca ANTES de banquear,
   evolucionar y adjuntar energía. Y **termina el turno (option 14) en 36/315
   decisiones frente a 6/315 del heurístico**: seis veces más. Las transiciones
   más frecuentes son «heurístico juega carta → greedy TERMINA» (33 casos) y
   «heurístico ataca → greedy TERMINA» (16).
7. **La causa raíz, en los pesos.** Sensibilidad de la red v2 a un cambio unitario
   REAL de cada rasgo (20.000 estados del corpus, `p(ganar)` medio):

   | cambio de UNA acción | Δp(ganar) |
   |---|---|
   | quitar 30 HP al activo rival | **−0,0002** |
   | adjuntar un tool propio | **−0,055** |
   | coger un premio (−1 premio propio) | +0,013 |
   | +1 energía en mi activo | +0,006 |
   | +1 Pokémon en mi banca | +0,009 |
   | −1 carta de mi mano | −0,002 |

   Y el ranking global por |Δp| ante +0,5 σ lo encabezan rasgos que **ninguna
   acción mía mueve causalmente**: `dif_premios` +0,046, `descarte_rival` +0,040,
   `mazo_rival` +0,039, `dmg_pot_yo` **−0,039** (¡tener más daño potencial le
   parece malo!), `mazo_yo` −0,035, `descarte_yo` −0,033.

   Traducido: **hacer daño al rival vale cero para la red**, adjuntar un tool le
   parece un error, y las señales que dominan su predicción son correlatos del
   avance de la partida (descartes, tamaño de mazos) cuyo signo, leído como
   criterio de acción, es anti-causal. Una red entrenada para predecir el ganador
   aprende «cómo se ve un ganador», no «qué acción acerca a ganar»; a 1 ply el
   argmax explota exactamente esas correlaciones.

## Veredicto y qué significa para el proyecto

- **Cerrado. La política greedy sobre la función de valor no se envía.** Es el
  tercer negativo medido de la línea de búsqueda: ISMCTS 0,529, ISMCTS+valor
  0,487, greedy 0,160. `heuristico.py` (v2) sigue siendo el piloto.
- **La conclusión que sí es valiosa, y es de writeup**: el 0,7539 de acierto de la
  función de valor **no se traduce en juego**, y ahora se sabe por qué con números
  — la derivada que importa (¿esta acción mejora mi posición?) es ~0 o de signo
  contrario en los rasgos que la red pondera. Esto explica también, a posteriori,
  por qué la red no aportó nada como evaluación de hojas del MCTS: no era el árbol,
  era que el crítico no discrimina entre acciones del mismo turno. La suposición de
  partida («el problema es el árbol, no la evaluación») queda **refutada**.
- **Si alguien quiere reabrir esta línea**, lo que hay que cambiar es la etiqueta,
  no el buscador: entrenar con VENTAJA/diferencia de valor entre estados sucesivos
  (o directamente clonar acciones de los replays, que ya están descargados y con el
  off-by-one resuelto), no la probabilidad de ganar de un estado suelto. Con el
  calendario a 6 días de la fecha de envío, eso es una apuesta grande y no es esta.
- Lo que sí queda utilizable de aquí: la fontanería 1-ply (`_completa_turno`, el
  cargador de la v2, el lote de evaluación, el diagnóstico señal/ruido) y el
  hallazgo de que `cartas` empata a 0,480 [0,431; 0,529] sin coste de reloj —
  suelo sólido si algún día hay un crítico que sí discrimine.
