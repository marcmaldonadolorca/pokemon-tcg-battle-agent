# La palanca de DATOS hasta el final: 30 días de replays, la curva y el techo

Fecha: 2026-08-13. Encargo: llevar la curva de datos del clon hasta donde dé, con
el corte de la Simulation a tres días (2026-08-16 23:59 UTC).

Punto de partida (`clon-escalado.md`): con 7 días / 10.413 episodios la curva de
aprendizaje **seguía subiendo** (+0,6 pp en la última duplicación) y H1=384
saturaba *con esos 7 días*. La pregunta abierta era doble: dónde satura la curva
de datos, y si con 3-6× más datos la capacidad vuelve a comprar.

**Resumen: la palanca de datos era real y sigue sin agotarse.** El corpus pasa de
7 a **30 días** (11,42 M de decisiones de entrenamiento frente a 1,10 M) y el
acierto top-1 sube de **0,6234 a 0,6435 medido con la misma vara** — el test del
corpus grande, 2.446.334 decisiones, aplicado a los dos modelos con `evalua3.py`.
La curva no ha saturado y el modelo nuevo **ni siquiera está convergido**: se
entrenó con 3 épocas por falta de tiempo y seguía subiendo en la última.

| | resultado |
|---|---|
| Descargas | 30 días de replays (2026-07-13 → 08-11), ~21 GB de zips |
| Extracción | **30 shards**, 104.587 episodios, 16.078.039 decisiones (`--min-rating 1030`) |
| Corpus fusionado | `data/clon/c30d`, **30 GB** memmapeable (no cabe en RAM: la torre tiene 30 GB compartidos con el escritorio) |
| Train / test | 11.420.139 decisiones (74.291 episodios) / 2.446.334 |
| Suelos del test | azar 0,2258 · heurístico 0,4358 |
| **Modelo de la ladder** (7 días) | top-1 **0,6234** · log-loss 1,1149 |
| **Modelo nuevo** (30 días, H1=384, 3 épocas) | top-1 **0,6435** · log-loss 1,0361 |
| Pesos | `research/clon/politica_30d_h384_mejorval.npz` (0,57 MB) |

---

## 1. El corpus: 30 días

La extracción se hizo shard a shard (`extraer2.py`, uno por día) para poder
fusionar después sin volver a tocar los zips. Los días de julio son
sistemáticamente más grandes que los de agosto (hasta 4.894 episodios/día frente a
~1.400), lo que importa porque el corpus no está equilibrado por fecha y el meta
cambió por el camino.

**Interrupción a registrar:** la primera extracción murió el 2026-08-13 a las 20:23
en el shard del 07-29, con 13 de 30 días hechos, mientras competía por la máquina
con el barrido de reloj (15 procesos) y un entrenamiento. Como `etapa2.sh` espera
la línea `FIN-EXTRACCION` que nunca llegó, la fusión y el entrenamiento grande no
llegaron a arrancar: quedaron esperando en silencio. Se relanzó el 2026-08-14 a las
09:37 con `--procs 4` y terminó a las 10:23 sin incidencias.

## 2. Piezas nuevas

(sin cambios respecto al plan; ver la tabla de arriba en esta misma nota)

## 3. Curva de datos

Fracciones del corpus de 30 días, todas con H1=384 y evaluadas sobre el mismo test:

| fracción | episodios | decisiones de train | val | test |
|---|---|---|---|---|
| 3,125% | ~2.300 | 351.113 | 0,6232 | 0,6219 |
| 6,25% | ~4.600 | 711.479 | 0,6302 | 0,6291 |
| 12,5% | ~9.300 | 1.425.890 | 0,6314 | 0,6308 |
| **100%** | **74.291** | **11.420.139** | **0,6442** | **0,6435** |

De 1,43 M a 11,42 M de decisiones —ocho veces más dato— el test gana +1,27 pp. La
pendiente se aplana pero **no se anula**, y el punto de 100% está limitado por
épocas, no por datos: con 3 épocas hizo 0,6389 → 0,6419 → 0,6442, subiendo hasta la
última. Un entrenamiento largo sobre este mismo corpus es margen que queda sin
cobrar.

Referencia útil para el writeup: el suelo heurístico sobre este test es 0,4358 y el
azar 0,2258. El modelo nuevo acierta la jugada del experto **el 64,35% de las
veces** eligiendo entre 7,2 opciones de media.

## 4. Capacidad revisada

**Sin medir.** El plan incluía reprobar H1=768 y una tercera capa ahora que hay 10×
más datos (con 7 días saturaban en H1=384), pero esa parte del barrido —
`cfg_curva.txt`— no llegó a correr: la tanda que se ejecutó fue la barata
(`cfg_barato.txt`), tres fracciones y nada de capacidad. Queda como hipótesis
abierta, no como negativo.

## 5. Arena

En curso al cierre de esta nota (2.000 partidas por baraja, `clon_busq.py` en los
dos lados para aislar la red). El top-1 mide imitación, no juego, y este proyecto
ya tiene un caso documentado de que **el acuerdo con los expertos no predice
ganar** (r = −0,028 sobre 1.000 jugador-episodios, `diagnostico-expertos.md`). Sin
el número de la arena, +2 pp de top-1 no autorizan ningún envío.

## 6. Gauntlet

Pendiente de la arena.

## 7. Coste y reproducción

| etapa | coste |
|---|---|
| Descarga de 23 días de replays | ~16 GB, 8 min |
| Extracción de 30 shards | ~47 min con `--procs 4` (la torre libre) |
| Fusión a memmap | incluida en `etapa2.sh`, ~12 min |
| Entrenamiento 100% × 3 épocas | 4.653 s (2.779 + 1.138 + 736) |
| Curva (3 fracciones, 2 en paralelo) | ~70 min |

Reproducción: `scratchpad/datos/descargar.sh` → `extraer_bucle.sh` →
`etapa2.sh` (espera, funde y entrena) → `etapa3.sh <pesos> <tag>` para la arena.
