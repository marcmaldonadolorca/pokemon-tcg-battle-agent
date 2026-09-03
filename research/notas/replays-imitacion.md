# Replays públicos como fuente de aprendizaje por imitación (2026-08-10)

Evaluación del recurso gratuito que publica la organización a diario. **Veredicto: NO montar
behavioral cloning; SÍ usar los replays como diagnóstico, inteligencia de meta y conjunto de
validación honesto.** Todo lo de abajo está medido en esta máquina, no citado del foro.

Scripts: `research/replays/{verificar_offbyone,prueba_causal,censo,indexar,concordancia,
valida_valor,extraer,bc_piloto,corpus_valor}.py`. Datos en `data/replays/` (gitignorado).

---

## 1. Qué hay descargado y cuánto pesa

| Recurso | Ruta | Peso |
|---|---|---|
| Índice diario (`kaggle/pokemon-tcg-ai-battle-episodes-index`) | `data/replays/index/manifest.csv` | 9,7 KB |
| Dataset 2026-08-08 | `data/replays/pokemon-tcg-ai-battle-episodes-2026-08-08.zip` | 707 MiB → 21,46 GB, 4.669 JSON |
| Dataset 2026-08-09 | `data/replays/…-2026-08-09.zip` | 707 MiB → 21,47 GB, 4.668 JSON |
| Derivados propios | `idx_0809.json` 3,7 MB · `bc_0809.npz` 3,5 MB · `corpus_valor_0809.npz` 1,6 MB | ~9 MB |

El índice cubre **55 días (2026-06-16 → 2026-08-09), 273.854 episodios, 1,2 TB descomprimidos**.
Un día = ~21,5 GB. Disco al 94% (61 GB libres): **no bajar más días sin podar antes**.

Rutas de la CLI, las tres verificadas:
- `kaggle datasets download kaggle/pokemon-tcg-ai-battle-episodes-index -p X --unzip`
- `kaggle datasets download kaggle/pokemon-tcg-ai-battle-episodes-<AAAA-MM-DD> -p data/replays`
- `kaggle competitions episodes 55407312` → ids de **nuestras propias** partidas de la ladder;
  `kaggle competitions replay 91708155 -p .` → 2,9 MB de JSON con el mismo formato.
  Esto es una vía directa para depurar el agente que está jugando ahora mismo.

---

## 2. El off-by-one es REAL. Evidencia (replicada en los dos días)

Hipótesis A (desfase 0): la acción de `steps[k][p].action` responde a `steps[k][p].observation`.
Hipótesis B (desfase 1): responde a `steps[k-1][p].observation` — o sea, la acción del estado k
está en `k+1`.

**Prueba 1 — legalidad estructural** (`verificar_offbyone.py`, contrato de `motor-mecanica.md`):

| día | decisiones | desfase 0 válidas | desfase 1 válidas |
|---|---|---|---|
| 08-09 | 6.897 | **65,9997%** (1.144 índice fuera de rango, 1.121 longitud, 80 no-baraja) | **100,0000%** |
| 08-08 | 5.379 | **67,0013%** (801 fuera de rango, 914 longitud, 60 no-baraja) | **100,0000%** |

El 33-34% de violaciones del desfase 0 no son "raras": son **imposibles** (índice mayor que
`len(option)`, longitud fuera de `[minCount,maxCount]`). Un mapeo correcto no puede producirlas.

**Prueba 2 — ancla semántica de la baraja** (80 pares jugador-episodio, 40 episodios):
paso 0 con `select=None` y `action=[]` en 80/80; paso 1 con acción de 60 enteros en 80/80;
**cero** acciones de longitud 60 en cualquier otro paso. El motor pide la baraja primero y la
única carga de 60 IDs del episodio aparece un paso más tarde. Inequívoco.

**Prueba 3 — causal, `attackId`** (1.780 selects `(0,0)` con ataque disponible): se toma la opción
que cada hipótesis dice que se eligió y se compara con el `attackId` del log de ataque (type 15)
del **paso inmediatamente siguiente**.

| | desfase 0 | desfase 1 |
|---|---|---|
| coherente | 1.436/1.780 = 80,67% | **1.694/1.780 = 95,17%** |
| attackId exacto | 60 | **266** |
| attackId distinto | 8 | **0** |
| atacó y la hipótesis no lo predice | 200 | **2** |

Los 84 casos "predice ataque y no hay log" del desfase 1 son ataques cuyo log llega más tarde, no
contradicciones. **Conclusión: la acción del paso k responde a la observación del paso k−1.**
Corregido en `extraer.py` y `corpus_valor.py`; `indexar.py` lo usa para leer las barajas.

---

## 3. Cifras del material (día 08-09)

Censo sobre 150 episodios al azar + índice completo de los 4.668:

- **166,8 pasos/episodio**, 4,65 MB/episodio.
- **164,8 decisiones/episodio** con `select` no nulo; de ellas **91,0% con elección real** (>1 opción).
  → día entero: **769.411 decisiones, 700.044 con elección real**. Dos días ya bajados ≈ **1,4 M**.
- **`obs.current` presente en el 100,00%** de las decisiones → `research/valor/features.py` se aplica
  directamente, sin reconstruir nada.
- **Barajas: 9.336/9.336 recuperadas (100%)**, los 60 IDs de los dos jugadores, leyendo la acción del
  paso 1. Arquetipo clasificable con las cartas firma de `meta-recon.md`.
- **Ganador: sí**, en `ep['rewards']` (+1/−1). Solo **2 de 4.668 (0,04%)** sin resultado utilizable.
- **La mano propia del jugador que decide viene con IDs de carta** (`current.players[yo].hand`), así que
  cada opción se resuelve a su carta. Zonas medidas empíricamente: `area` 1=mazo (oculto), **2=mano**,
  **3=descarte**, **4=activo**, **5=banca**, 6=premios (boca abajo); `inPlayArea` 4=activo, 5=banca.
- Coste de parseo: **42,3 ms/episodio-proceso** → un día entero con 2 procesos en **~1,6 min**.

### El foro se equivoca: los ratings SÍ están

`manifest.csv` dentro de cada zip trae por episodio `avg_score`, `min_score`, `sum_score`. No hay
`agent_id`, pero eso es el par **no ordenado** {peor, mejor} de ratings, y la atribución a equipo se
resuelve por consistencia entre episodios (`indexar.py`): dispersión intra-equipo **22,86 pts frente a
36,94 de una asignación aleatoria**, y el rating atribuido correlaciona **r=0,514** con el winrate real
del mismo día (159 equipos con ≥20 partidas). Truco que evita el problema por completo: filtrar por
`min_score`, que ya es el peor de los dos sin ambigüedad.

**El dataset diario es la franja alta de la ladder**, no una muestra del campo:
`avg_score` mediana 1021, p75 1057, máx 1211 (08-09). El nº 100 del LB está en ~995-1000, así que
la mediana del corpus juega a nivel top-100/150. Episodios con **ambos** jugadores ≥1.050: 18,2%
(849/día); ambos ≥1.100: 5,1% (237/día).

### Qué equipos son fuertes: sí se puede

399 equipos distintos en el día, mediana 12 partidas/equipo, máx 150. Ejemplos (rating atribuido /
partidas / WR del día): Dipam Chakraborty 1098 / 150 / 69,3% · やる気元気ミワハルキ 1115 / 82 / 73,2% ·
Thai 1120 / 58 / 67,2% · M Sato 1134 / 126 / 56,3%.

### Meta de barajas al 09-ago (9.336 barajas, winrate sin espejos)

| arquetipo | share | WR |
|---|---|---|
| grimmsnarl | 31,9% | **45,1%** (n=2038) |
| «otro» (no clasificado por firmas) | 26,4% | 52,5% (n=1825) |
| alakazam | 18,0% | 50,0% (n=1371) |
| dragapult | 8,2% | **59,5%** (n=702) |
| crustle | 7,7% | 43,0% (n=675) |
| lucario | 4,3% | 56,3% (n=391) |
| garchomp | 2,0% | 53,4% (n=189) |
| starmie | 0,6% | 60,0% (n=60) |

Matchups: «otro» gana a grimmsnarl **63,0%** (n=791) y dragapult le gana **66,0%** (n=247);
grimmsnarl gana a alakazam 56,2% (n=534). **Grimmsnarl sigue siendo el más jugado y ya está en
regresión clara** (50,3% a finales de julio según Sumi → 45,1% ahora): la burbuja se comió su ventaja,
igual que pasó con Archaludon. El cubo «otro» (26% del campo, WR 52,5%) es lo que las firmas de Sumi
no cubren y es donde está el EV — merece un censo de firmas propio.

---

## 4. ¿Cuánto valdría clonar? Medido, no supuesto

### 4.1 Techo por arriba: cuánto nos separamos ya del campo

`concordancia.py` pregunta al heurístico v2 qué haría en cada estado del replay y lo compara con lo
que hizo el jugador real (con el desfase corregido):

- **42,66%** de coincidencia (n=15.612, día 08-09) — replicado: **42,58%** (n=8.901, día 08-08).
- Línea base de elegir al azar entre las opciones: 22,2%.
- Se degrada con el nivel del rival: 45,1% (rating 950-999) → 43,1% (1000-1049) → **39,8%** (1050-1099).
  Cuanto mejor el rival, más divergemos: hay señal real, no ruido.
- Por tipo de select: `(8,40)` 98,9% y `(9,43)` 97,0% (resueltos), `(1,21)` 71,3%, `(1,3)` 59,8%,
  **`(0,0)` 32,5% con n=8.892** (es el 57% de todas las decisiones), `(1,14)` 30,8%, `(1,13)` 29,9%,
  **`(1,8)` 9,4%** (n=234).

### 4.2 Techo por abajo: qué saca un clon barato

`extraer.py` + `bc_piloto.py`. Dataset: 700 episodios con ambos jugadores ≥1.030 → **98.186 decisiones
de elección única, 713.694 opciones (7,27/decisión), 44,0% de opciones resueltas a su carta**.
Modelo: puntuador por opción `MLP([estado 30, opción 39]) + sesgo por carta`, softmax sobre el bloque
de opciones, numpy puro (no hay torch en la torre y en producción hay 1,6 vCPU). Corte train/val
**por episodio** (20.037 decisiones de validación).

| | top-1 |
|---|---|
| azar | 21,96% |
| primera opción siempre | 30,62% |
| prior por tipo de opción | 38,53% |
| **heurístico v2 (sin entrenar en nada)** | **~42,7%** |
| **BC piloto** | **45,79%** (log-loss 1,4085) |

Satura en la época 5 (45,36% → 45,86% en la 15): no es falta de entrenamiento. Desglose: 73,8% con 2
opciones, 44,6% con 4-5, 29,0% con ≥13; en `(0,0)` 39,4% frente al 32,5% del heurístico.

**+3,1 puntos sobre una heurística escrita a mano en un fin de semana.** Ese es el material real.

### 4.3 La prueba que decide: el cuello de botella no son los datos, es la representación

Experimento cruzado, mismos 30 rasgos, misma arquitectura 30→32→16→1:

| función de valor | entrenada con | acierto sobre replays reales |
|---|---|---|
| `research/valor/valor.npz` | self-play del heurístico | **64,10%** (su cifra propia era 72,66%) |
| `data/replays/valor_replays.npz` | **etiquetas reales de 1.200 partidas del meta** | **65,44%** |
| base "signo de la diferencia de premios" (1 rasgo) | — | 58,66% |
| base clase mayoritaria | — | 51,81% |

Cambiar self-play por datos reales del meta top da **+1,34 puntos**. Y de paso queda medido que el
**72,66% estaba inflado en ~8,5 puntos** por la distribución fácil del self-play; la red además va
sobreconfiada en las colas (predice p<0,1 y la victoria real es 18,9%; predice p>0,9 y es 87,6%).
Por fase: 53,5% en los turnos 0-5, 73,2% en los 10-15.

Con 196.125 muestras reales, gratis y en la distribución correcta, el techo sigue en ~65%. **El límite
lo ponen los 30 rasgos, no la fuente de datos** — que es exactamente lo que dice el consenso del foro
(«la representación del estado es lo que rompe o hace el agente»). Meter BC encima de la misma
representación compra los mismos céntimos.

---

## 5. Veredicto y presupuesto

### NO montar behavioral cloning antes del 16-ago

Coste realista hasta producción: extracción **ya hecha** (~8 min/día con 2 procesos); red de política
en numpy con enmascarado de legalidad y empaquetado ~1 día de trabajo; el gate de arena es **barato**
(40 partidas en 3,6 s con 2 procesos ≈ 11 partidas/s → 4.000 partidas en ~6 min, IC95 ±1,5 pp).
O sea: el coste no es de CPU, es de **atención y riesgo**, y quedan 6 días.

Contra:

1. **El beneficio medido es +3,1 pp de acuerdo con el campo**, y no hay ninguna evidencia de que eso
   se traduzca en winrate. El experimento de valor (§4.3) muestra que con esta representación el techo
   está donde está vengan los datos de donde vengan.
2. **Clonar la mezcla no da un agente fuerte, da uno promedio.** El corpus son ~400 equipos con mediana
   1021 jugando políticas distintas; el óptimo de log-verosimilitud sobre una mezcla heterogénea es la
   política media, típicamente peor que sus mejores miembros. Filtrar a ≥1.100 deja 237 episodios/día
   (~35k decisiones), y ahí el piloto no mejora (45%-47% en todas las bandas de rating).
3. **Riesgo asimétrico**: acción ilegal = derrota instantánea. Lo que está en la ladder ahora lleva
   **0 ilegales en 1.000 partidas**. Un puntero softmax necesita enmascarado perfecto para igualar eso,
   y el fallo no se paga en puntos sino en partidas perdidas enteras.
4. **No puntúa en la rúbrica que nos importa.** Strategy = 70% consistencia entre partidas + 20% baraja
   + 10% informe. «Hemos clonado la política media del top-150» es débil en «originality of the proposed
   approach» y no ataca la consistencia. El LB de Simulation solo «se tiene en cuenta».
5. **El estado no se repite**: 188.531 contextos distintos en 197.688 decisiones (1,8% repetidos, y esos
   casi todos triviales de 2 opciones). No hay memorización posible; todo lo que aporte BC tiene que
   salir de generalizar, y generalizar es lo que limitan los 30 rasgos.

### SÍ, y ya rinde: los replays valen para otras cuatro cosas, todas baratas

1. **Conjunto de validación honesto en la distribución real** (hecho): 72,66% → **64,10%**. Cualquier
   cifra de self-play que llevemos al writeup debería ir acompañada de su número sobre replays. Esto es
   argumento directo de la rúbrica de consistencia y es material de informe de primera.
2. **Lista priorizada de reparaciones del heurístico**, ordenada por frecuencia × divergencia
   (`concordancia.py`). Lo grande: `(0,0)` con 88,9 decisiones/partida al 32,5% de acuerdo; lo flagrante:
   **`(1,8)` al 9,4%** — ahí hacemos algo que el campo top no hace casi nunca. Y hay **13 pares
   (type,context) que no están catalogados en `motor-mecanica.md`**: (1,21) (1,13) (1,16) (8,40) (1,14)
   (9,43) (1,15) (1,5) (1,17) (1,9) (7,37) (6,35) (4,33), juntos ~25% de las decisiones. Esto es señal
   accionable sin entrenar nada.
3. **Inteligencia de baraja para el 20% de Deck Score** (§3): 9.336 barajas/día con share, winrate y
   matriz de matchups propios y actualizados, más el hallazgo de que grimmsnarl ya está en regresión
   (45,1%) y de que el 26% del campo se nos escapa en el cubo «otro».
4. **Depuración del agente vivo**: `kaggle competitions episodes 55407312` + `kaggle competitions replay`
   dan nuestras partidas reales de la ladder, con la misma estructura y el mismo desfase.

### Qué queda preparado (decisión reversible en horas, no en días)

Aunque el veredicto sea NO, el extractor queda **construido y validado** porque hacía falta para medir:

- `research/replays/extraer.py` — replays → `.npz` de pares (rasgos, acción) usando
  `research/valor/features.py`, con el desfase corregido, filtro `--min-rating`, formato ragged
  (`S`, `O`, `C`, `ptr`, `y`, `ep`, `meta`). 700 episodios → 98k decisiones en ~1 min con 2 procesos.
- `research/replays/bc_piloto.py` — entrenador softmax-sobre-opciones en numpy con corte por episodio
  y líneas base honestas.
- `research/replays/corpus_valor.py` — corpus (rasgos, ¿ganó?) en el formato de
  `research/valor/entrenar.py`: 1.200 partidas → 196.125 muestras etiquetadas **sin simular nada**.

Si alguien decide reabrirlo, el camino que sí tiene sentido no es clonar la acción: es **ampliar los
rasgos** (identidad de carta, contenido de la mano, contexto de baraja) y reentrenar la función de
valor con `corpus_valor.py`, que es donde el coste marginal es casi cero y el techo del 65% está
esperando a que lo suban.

---

## 6. Cautelas de la medida

- La concordancia compara nuestro heurístico contra estados generados por **barajas ajenas**: parte de
  la divergencia es que el heurístico no entiende cartas que no juega. No es un número puro de calidad
  de política, es una cota de divergencia.
- El techo irreducible (cuánto se contradicen dos agentes distintos ante el mismo estado) **no se pudo
  medir**: los contextos repetidos son el 1,8% y todos de 2 opciones. Se deja anotado como no concluido
  en vez de dar un número que no significa lo que parece.
- Comparación §4.2 heurístico vs BC: 42,7% viene de todas las bandas de rating y 45,79% del subconjunto
  ≥1.030. En la banda comparable el heurístico está en ~40%, así que la brecha real es de +3 a +6 pp.
- Las partidas de arena duran 42 pasos con la baraja de ejemplo frente a los 166,8 de los replays: el
  throughput de 11 partidas/s es optimista para barajas del meta.
