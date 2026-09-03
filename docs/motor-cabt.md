# El motor `cabt` — lo verificado en la torre

Fecha de la medición: 2026-08-06. Todo lo de aquí está ejecutado, no leído.

## El motor no depende del gate de Kaggle

El entorno `cabt` viaja **dentro de `kaggle-environments` en PyPI**:

```
kaggle_environments/envs/cabt/
├── cabt.json          # especificación del entorno
├── cabt.py            # interpreter, renderer, agentes `random` y `first`
├── cg/
│   ├── libcg.so       # motor C++ compilado, x86-64  ← el que usa la torre
│   ├── libcg-arm64.so, libcg.dylib, cg.dll
│   ├── game.py        # battle_start / battle_select / battle_finish
│   └── sim.py         # binding ctypes
└── visualizer/default/dist/index.html   # visor HTML de partidas
```

Esto significa que **se puede desarrollar y entrenar sin haber aceptado las
reglas de la Simulation**. El gate solo bloquea entrar y enviar, no trabajar.

La competición cita `kaggle-environments 1.14.10`, versión que **no existe en
PyPI** (salta de 1.14.9 a 1.14.11). Se ha instalado la actual, **1.32.4**, cuyos
ficheros de `cabt` están fechados el 2026-08-04. Si aparecen discrepancias con el
entorno de evaluación, este es el primer sitio donde mirar.

## Rendimiento medido

Prueba: `research/smoke_motor.py`, agentes `random` contra `random`.

Partida suelta, un proceso: **0,208 s** (200 partidas en 41,6 s), con 14 pasos
de mínimo, 77 de mediana y 241 de máximo.

Escalado real con `multiprocessing`, 400 partidas repartidas en lotes por
proceso (la torre tiene 16 cores):

| procesos | partidas/s | factor |
|---|---|---|
| 1 | 5,0 | 1,0× |
| 8 | **27,1** | 5,4× |
| 16 | **31,5** | 6,3× |

Satura hacia los 8 procesos: pasar de 8 a 16 solo añade un 16%. El punto de
trabajo sensato son **8 procesos**, dejando la máquina utilizable.

A 31,5 partidas/s, 100.000 partidas son **~53 minutos** de reloj. La evaluación
estadística de una baraja o una política no es el cuello de botella; el cuello
será la calidad de la política.

**Ojo con el entorno de evaluación:** allí solo hay **2 vCPU**. Lo que se
entrene en la torre con 16 cores tiene que decidir en 2 al competir.

## Sin sesgo del primer jugador

Las 5 primeras partidas dieron 5-0 para P0, lo que apuntaba a ventaja del que
empieza o a semilla fija. Con 200 partidas: **104-96**, dentro del ruido (±14 a
1σ). No hay sesgo estructural y la aleatoriedad del motor es real.

## Interfaz del agente

Un agente es una función `obs -> list[int]`:

- Si `obs["select"] is None`, se está en la fase de selección de baraja: hay que
  devolver **la lista de 60 IDs de carta**. Un tamaño distinto de 60 marca el
  estado como `INVALID` y se pierde la partida.
- Si no, `obs["select"]["option"]` son las opciones **legales** (el motor nunca
  ofrece una ilegal) y hay que devolver `maxCount` índices.

`obs` trae además `logs` (eventos pasados), `current` (estado del tablero) y
`search_begin_input`.

`current` contiene `players` (cada uno con `active`, `bench` de hasta 5, `hand`
—solo la propia; de la rival únicamente el recuento—, `prize` con las boca abajo
como `None`, `deckCount`, `discard`, y los flags de estado `poisoned`, `burned`,
`asleep`, `paralyzed`, `confused`), `stadium`, y la información de turno.

## La Search API existe y está en el binario

`libcg.so` exporta `SearchBegin`, `SearchStep`, `SearchEnd`, `SearchRelease` y
`AllAttack`, verificado con `hasattr` sobre el handle de ctypes. Permite explorar
transiciones de estado sin jugarlas de verdad, que es lo que hace falta para
**MCTS o búsqueda con determinización** sobre la mano oculta del rival.

Matiz: el envoltorio Python de esas funciones (`api.py`) **no viaja en el paquete
de PyPI** — vive en el `ptcg_engine/` de la competición Simulation, que hoy da
403. Hay dos salidas y ninguna bloquea: bajarlo cuando se acepten las reglas, o
llamar a las funciones C directamente por ctypes como ya hace `sim.py`.

`AllCardData` no aparece con ese nombre exacto entre los símbolos; los metadatos
de carta están de todos modos en los CSV de `data/raw/`.

## Ejecutar una partida con baraja propia

```python
from kaggle_environments import make

with open("deck.csv") as f:
    deck = [int(l) for l in f if l.strip()]

env = make("cabt", configuration={"decks": [deck, deck]})
env.run([mi_agente, "random"])
open("result.html", "w").write(env.render(mode="html"))
```

El visor HTML sirve para inspeccionar partidas a mano — útil para las figuras que
pide el 10% de Report Score.

## Con hilos el motor mata el proceso — verificado

`Battle.battle_ptr` es un atributo **de clase**, no de instancia, y `sim.py`
llama a `lib.GameInitialize()` al importar: el estado de la partida es global.

Lanzar partidas en un `ThreadPoolExecutor` de 4 hilos **no da una excepción de
Python: revienta el proceso entero**. Primero apareció como

```text
terminate called after throwing an instance of 'std::length_error'
  what():  basic_string::_M_create
```

y en la repetición aislada, directamente **SIGSEGV** (`returncode -11`, sin
stderr). Es corrupción de memoria dentro del `.so`, no algo capturable con
`try/except`.

**Consecuencia operativa:** paralelizar solo con `multiprocessing`, un `env` por
partida, y nunca con hilos. Está comprobado en `research/smoke_paralelo.py`, que
aísla la prueba de hilos en un subproceso justamente porque se lleva por delante
a quien la ejecuta.
