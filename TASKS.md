# TASKS — kaggle-pokemon-tcg

Casilla marcada = evidencia, no intención.

## Control operativo

| ticket | estado | dueño | fecha límite |
|---|---|---|---|
| `PKM-000` | **cerrado** 2026-08-06 — intake y entorno | Claude | — |
| `PKM-001` | **cerrado** — el propietario hizo Join a tiempo (verificado por CLI 2026-08-10: `userHasEntered True` en ambas divisiones) | Propietario | — |
| `PKM-002` | **cerrado** 2026-08-12 — báscula construida y caracterizada (arena con ruido de suelo 0,4959 [0,4848, 0,5070] n=7.800; gauntlet de 12 arquetipos validado contra la ladder). Once hipótesis heurísticas medidas sin mejora | Claude | — |
| `PKM-003` | **cerrado** 2026-08-12 — el ISMCTS solo no rinde (0,529 y 0,487 con red de valor), pero **guiado por el clon sí**: +0,709 por sí solo y 0,859 combinado con la red grande | Claude | — |
| `PKM-004` | **cerrado sin ejecutar** 2026-08-17 — la Simulation cerro con el agente del 12-ago: puesto **2.138/6.892**, score 690,7. El candidato medido (0,7462) **no se subio**; causa raiz en `PKM-018` | Claude | vencido 2026-08-16 |
| `PKM-007` | **cerrado** 2026-08-14 — barrido de presupuesto de búsqueda: `RC` (R=32, C=5) gana **0,6350 [0,6111, 0,6582]** al agente de la ladder; 8 configuraciones medidas | Claude | — |
| `PKM-008` | **cerrado** 2026-08-17 — corpus de 30 dias validado en arena: `30d+RC` gana **0,7462 [0,7244, 0,7670]** n=1.600 al agente de la ladder (`scratchpad/cierre/d30rc_c2.json`). Llego 15 min tarde para el envio | Claude | — |
| `PKM-009` | **cerrado** 2026-08-14 — `empaquetar.py --env` y verificación de que los parámetros de búsqueda viajan dentro del paquete | Claude | — |
| `PKM-005` | **borrador escrito 2026-08-19** — `docs/writeup-strategy.md`, 1.510 palabras de 2.000, con los 11 números citados verificados uno a uno contra su fuente. **Falta: decisión del propietario sobre si se admite el fallo del envío, figuras propias (10% Report Score) y pulsar Submit** | Claude + validación | 2026-09-13 |

Límite de tres tickets en «Ahora» del workspace: este proyecto ocupa **uno**,
y por debajo del TFM.

## PKM-000 · Intake y entorno (cerrado 2026-08-06)

- [x] Reglas, calendario y criterios de evaluación verificados en la web real
      (SPA renderizada con Firefox headless) → `docs/reglas-y-calendario.md`
- [x] Descubierto el acoplamiento Simulation ↔ Strategy y el gate del 9-ago
- [x] Estado de inscripción medido por CLI en ambas competiciones
- [x] `kaggle` CLI reparado (lo había purgado una actualización del snap de VS Code)
- [x] Datos de cartas descargados y duplicados desambiguados (2.103 cartas EN)
- [x] Motor `cabt` localizado en PyPI → no depende del gate
- [x] Repo, venv y manifiesto reproducible
- [x] Partida real ejecutada de punta a punta (`research/smoke_motor.py`)
- [x] Rendimiento medido: 0,208 s/partida; 31,5 partidas/s con 16 procesos
- [x] Verificado que los hilos matan el proceso (`research/smoke_paralelo.py`)
- [x] Comprobado sin sesgo del primer jugador (104-96 en 200 partidas)
- [x] Confirmada la Search API en el binario público

## PKM-001 · Aceptar las reglas de la Simulation — **CERRADO**

- [x] Join hecho por el propietario antes del cierre del 9-ago; verificado por
      CLI el 2026-08-10 (`userHasEntered: True` en ambas divisiones)

Desbloquea el envío de agentes (5/día, 2 activos) y la descarga de
`ptcg_engine/` + `sample_submission/` (ya innecesarios para el desarrollo: la
Search API completa está en la `libcg.so` de PyPI).

## PKM-002 · Baseline medido y baraja de partida

- [ ] Parsear los CSV de cartas a una estructura consultable
- [ ] Reproducir la baraja de ejemplo del motor y medirla contra `random`
- [ ] Arnés de evaluación con intervalos de confianza (cuántas partidas hacen
      falta para distinguir dos agentes: es la pregunta que gobierna todo lo demás)
- [ ] Agentes tontos de referencia (`random`, `first`, heurístico simple) y tabla
      enfrentándolos entre sí

## PKM-003 · Agente de búsqueda

- [ ] Envolver `SearchBegin/Step/End` por ctypes (o usar `api.py` si ya hay gate)
- [ ] MCTS con determinización sobre la mano oculta del rival
- [ ] Presupuesto de cómputo ajustado a **2 vCPU** del entorno de evaluación
- [ ] Medir consistencia entre semillas y emparejamientos — es lo que puntúa el 70%

## PKM-004 · Envío a la Simulation

- [ ] `main.py` + `deck.csv` empaquetados (`tar -czvf submission.tar.gz *`, ≤197,7 MiB)
- [ ] Validación local antes de subir
- [ ] Enviar; recordar que solo los **2 últimos** envíos quedan activos

## PKM-005 · Writeup de la Strategy

- [ ] ≤2.000 palabras, con la estructura que pide el reparto 70/20/10
- [ ] Figuras y tablas propias (el 10% de Report Score se juega ahí)
- [ ] Sin imágenes de cartas con licencia problemática
- [ ] Pulsar **Submit**: un borrador guardado no se evalúa

## PKM-006 · Clon de política y búsqueda guiada (cerrado 2026-08-13)

La línea que sí escaló, después de once hipótesis heurísticas sin mejora.

- [x] Corpus de imitación desde los replays de la ladder, con el off-by-one del
      campo `selected` verificado por tres vías (2026-08-12)
- [x] Red de política que puntúa cada opción del select y elige el argmax;
      acierto top-1 **0,6178** en test frente a 0,4303 del heurístico y 0,2180 del azar
- [x] Escalado medido: la capacidad satura en H1=384 con 7 días, sin sobreajuste
      en 20 épocas, y **la curva de datos seguía subiendo**
- [x] Búsqueda guiada por la red sobre la Search API: +0,709 por sí sola, y
      **0,859 [0,843, 0,873]** combinada con la red grande (los ejes se suman en log-odds)
- [x] Negativos medidos y documentados: auto-juego por filtrado y por pesado
      (0,454 y 0,443 contra su control), filtros de calidad del corpus (valen su
      volumen, sin bonus), híbridos clon+heurística (0,486 y 0,445)
- [x] Dos bugs de medición propios cazados: `__file__` inexistente en el envío
      (tumbó el primer `submission`) y **self-play silencioso** en la arena, que
      invalidó ~20 celdas
- [x] Commiteado y pusheado al remoto propio (2026-08-13, `6eb0e17`→`37debbd`)

## PKM-007 · Presupuesto de búsqueda (cerrado 2026-08-14)

Nota: `research/notas/busqueda-presupuesto.md`. El agente de la ladder gastaba
**~1% del banco de 600 s**; el barrido midió qué compra ese margen.

- [x] `clon_busq2.py` con los siete parámetros expuestos y controlador de reloj
      (`TOPE`, `DIV`, `RESERVA`, `RESERVA_DURA`)
- [x] Ocho configuraciones medidas contra el agente de la ladder, misma red y
      misma baraja en los dos lados, asientos intercambiados (n=1.600-2.000)
- [x] **Ganan**: rollout 32 (0,5850), 5 candidatas (0,5656) y **las dos juntas
      (0,6350)** — los ejes se suman
- [x] **No compran**: 16 determinizaciones (0,5212), regla por banda sola (0,4920),
      margen 0,75 (0,4775)
- [x] **Pierden**: la regla `hueco` con tope (0,4620) y buscar siempre (0,4387)
- [x] Comportamiento del reloj caracterizado: 976 cortes y 80.236 decisiones sin
      presupuesto con `RC`, pero **0 partidas perdidas por reloj** en 3.200 asientos
- [ ] Fase 3 de validación (campo, auditoría de 500, banco reducido) — **pendiente**
- [ ] `RC` medido en `c1-grimmsnarl` — **pendiente**, todo el barrido fue en alakazam

## PKM-008 · La palanca de datos hasta el final

Nota: `research/notas/clon-datos-final.md`.

- [x] 30 días de replays descargados y **30 shards extraídos** (104.587 episodios,
      16,08 M decisiones). La primera extracción murió a los 13 shards por
      contención y quedó esperando en silencio; relanzada el 14-ago con `--procs 4`
- [x] Corpus fusionado a memmap (`data/clon/c30d`, 30 GB — no cabe en RAM)
- [x] Entrenamiento sobre 11,42 M de decisiones: val 0,6442 / test **0,6435**
- [x] **Vara común**: los dos modelos evaluados sobre el mismo test de 2,45 M
      decisiones → ladder 0,6234, nuevo **0,6435**. La mejora no es un artefacto
- [x] Curva de datos: 351 k → 11,42 M sube 0,6219 → 0,6435, **sin saturar**
- [x] Pesos versionados: `research/clon/politica_30d_h384_mejorval.npz`
- [ ] **Arena** (en curso al cierre): el top-1 mide imitación, no juego
- [ ] Capacidad revisada (H1=768, tercera capa) con 10× más datos — **sin medir**,
      corrió la tanda barata en su lugar
- [ ] Entrenamiento largo: se paró en 3 épocas y **seguía subiendo** en la última

## PKM-009 · Empaquetado con parámetros (cerrado 2026-08-14)

- [x] `empaquetar.py --env K=V` — sin él, un envío con `RC` habría salido con los
      valores por defecto sin dar error (los parámetros se leen de `os.environ` en
      tiempo de import y en el paquete no había ninguno)
- [x] Paquete de prueba construido y verificado en directorio limpio con `exec` y
      sin `__file__`: parámetros dentro, 165/324 decisiones buscadas, 0 ilegales,
      0 excepciones, 0 código de terceros
- [x] `verifica_tar.py` corregido: leía un contador inexistente y devolvía `None`
      sin quejarse; ahora cae a `ESTAD` e imprime los parámetros efectivos
- [x] Receta completa con las rutas reales de los ocho ficheros de apoyo en
      `docs/empaquetado-y-envio.md`
