# InfoTracker: contabilidad de información y determinizaciones para la Search API

Fecha: 2026-08-07. Código: `research/agentes/tracker.py`.
Verificación: `research/test_tracker.py` (210 partidas, 19.456 updates, **0 discrepancias**).

## Qué es

La Search API (`search_wrapper.search_begin`) exige que el llamante aporte la información
oculta como multiconjuntos exactos en tamaño. `InfoTracker` lleva esa contabilidad
consumiendo cada obs y `sample()` produce los 6 arrays.

## API

```python
from agentes.tracker import InfoTracker, MirrorModel, MetaModel

tr = InfoTracker(mi_deck)            # lista de 60 IDs; ValueError si no son 60
tr.update(obs)                       # llamar con CADA obs (también la del paso 0)
det = tr.sample(rng, modelo)         # rng = random.Random; modelo = callable
res = search_wrapper.search_begin(obs, **det)   # manual_coin se pasa aparte
```

- `sample -> dict` con `your_deck, your_prize, opp_deck, opp_prize, opp_hand,
  opp_active`, tamaños EXACTOS a `deckCount`/premios/`handCount` reales.
- `modelo(cartas_vistas: Counter, n: int) -> n IDs` que completan a 60 la lista
  rival (`cartas_vistas` = todas sus copias físicas ya identificadas, por serial).
  - `MirrorModel(lista60)`: el rival juega esa lista (baseline defendible: mi lista).
    Si lo visto no cabe (rival real distinto) recorta de lo más repetido / rellena.
  - `MetaModel(lista60)`: stub idéntico para listas de arquetipo (`research/decks/meta/*.csv`);
    pendiente elegir arquetipo por verosimilitud.
- Estado útil: `tr.pool` (mi mazo∪premios, exacto), `tr.mazo` (mi mazo exacto o None),
  `tr.rival_mano` (serial→id conocidos en su mano), `tr.rival_serial_id` (todas sus
  copias identificadas), `tr.avisos` (discrepancias, lista de strings, debe quedar
  vacía), `tr.calibraciones` (Counter: total/pool_ok/con_prevision/exactas),
  `tr.mano_decaida`, conteos `deck_n/premios_n/rival_*`.

## Diseño

- **Mi pool es sin estado**: se recalcula de `current` en cada update
  (`lista − visibles − limbo`); los logs solo sostienen dos conocimientos que
  `current` no da: el **mazo exacto** (tras revelarlo un select (1,7)) y lo
  aprendido del **rival** (mano conocida, copias identificadas).
- **Calibración gratis**: todo select (1,7) trae en `select["deck"]` el contenido
  real de mi mazo → se verifica (aviso si difiere) y se resincroniza SIEMPRE.
  Con el mazo exacto, mis premios son exactos: `pool − mazo`.

## Reglas de logs deducidas (evidencia: censo de 210 partidas en test_tracker.py)

| Evento | Regla | Evidencia |
|---|---|---|
| type 4 propio (cardId,serial) | robo: mazo −= carta | 13.517 casos, 1.474/1.474 calibraciones exactas |
| type 6 propio from/to área 1 | mazo −=/+= carta (búsqueda 1→2, mill 1→3, reveladas 1→12 y 12→1, devolver 3→1, al banco 1→5) | ídem |
| type 6 propio to 4/5 | **colocada en setup va BOCA ABAJO**: `current` muestra `null` en mi propio active/bench pero mi log da id → va a "limbo" conocido, fuera del pool | sin esto, pool descuadraba +1 en turno 0 (selects (1,2)/(8,38)) |
| type 10 (trainer jugado) | la carta queda EN RESOLUCIÓN (área 9): **no aparece en NINGUNA lista de `current`** hasta llegar al descarte (6,9,3) | suma de zonas da 59/60 durante el (1,7) de 1092 |
| type 11/12 rival | energía/evolución salen de su mano **sin type 6** → pop de mano conocida | sin el pop, serials rancios en mano |
| type 6 rival to 2 | veo lo que gana su mano: búsquedas (1→2), premios NO (ver abajo), reveladas (12→2) | 901+33 casos |
| type 6 rival 2→1 | mulligan: mano revelada entera | 1.932 casos |
| type 7 rival from 2 | carta NO identificada sale de su mano (p. ej. devolver al mazo 7,2,1): cualquier serial conocido pudo irse → crédito de incertidumbre **ACUMULATIVO** (el exceso aflora turnos después); al clampear se olvida FIFO sin aviso | 2.199 casos; 12 decaimientos en 19k updates |
| type 7 rival 6→2 | sus premios cogidos son OCULTOS (no aprendo la carta); los míos sí: (6,6,2) propio con cardId | 485 vs 459 casos |
| área 12 | zona de cartas reveladas del mazo (1→12, 12→1, 12→2); del rival viaja como type 7 salvo 12→2 | 520/486/34 casos |
| (7,1,6) propio | reparto inicial de premios (única salida oculta de mi mazo; ocurre con mazo aún desconocido) | 2.520 casos, `mazo_perdido` jamás disparó |

Boca abajo rival: `null` en su `active`/`bench` (`rival_bocabajo_n`); solo en setup
(463 updates de setup con 1, ninguno en partida). `sample` lo saca en `opp_active`
(máx 1; >1 avisa y descarta — SearchBegin no lo admite).

## Resultado de la verificación (test_tracker.py, 140 espejo + 70 asimétricas garchomp)

- 210/210 partidas DONE; ambos lados trackeados (420 trackers·partida).
- Calibraciones (1,7): **1.854/1.854 pool_ok; 1.474/1.474 exactas** cuando había
  previsión de mazo de una búsqueda anterior (0 discrepancias).
- Invariantes por update (pool == deckCount+premios; rival vis+mano+mazo+premios+
  bocaabajo+limbo == 60): 19.456 updates, 0 avisos.
- `sample()`+`search_begin`: **12.742 begins, 0 errores, 0 mismatch del select raíz**,
  0 tamaños malos — incluye fase con MirrorModel EQUIVOCADO (rival jugaba garchomp):
  el motor acepta cualquier determinización consistente en tamaños.
- Coste: ~0,28 s/partida con tracker+begin por decisión MAIN (despreciable frente
  al presupuesto; el tracker en sí es O(cartas) por update).

## Limitaciones conocidas

- `opp_active` con >1 carta rival boca abajo (setup con banca sin voltear) no es
  representable; búsqueda en turno 0 sigue sin probar (ya era «pendiente» de
  search-api.md).
- La mano conocida del rival decae (FIFO) cuando él mueve mano→oculto sin
  identificar; es pérdida de información real, no error (12/19.456 updates).
- `MetaModel` no elige arquetipo: se construye ya con la lista.
