# Presupuesto de tiempo real por decisión (cabt / kaggle-environments 1.32.4)

Fecha: 2026-08-06. Script de verificación: `research/test_presupuesto_tiempo.py` (3 tests, todos pasan).

## Semántica exacta (con citas fichero:línea del paquete instalado)

Config de cabt (`envs/cabt/cabt.json`): `episodeSteps=10000000`, `actTimeout=0`, `runTimeout=2000`,
`observation.remainingOverageTime=600`.

- **`actTimeout=0` = CERO tiempo gratis por paso.** El descuento del banco es
  `overage_time_consumed = max(0, duration - actTimeout)` (`core.py:631-632`), con `actTimeout=0`
  ⇒ **cada segundo de pared de cada decisión sale del banco de 600 s**. No hay tiempo de gracia por paso
  (el `+1` de `agent.py:89` es solo margen de red del HTTP del orquestador, no tiempo utilizable).
- **`remainingOverageTime=600` es POR AGENTE** (`schemas.json:105`, `"shared": false`): cada lado tiene su
  banco propio de 600 s por episodio. Lo decrementa el orquestador tras cada step con la `duration` medida
  con `perf_counter` alrededor de la llamada al agente (`agent.py:191-207` mide; `core.py:629-632` descuenta).
  **Es tiempo de pared, no de CPU** (GC, I/O, carga de módulos… todo cuenta).
- **La `obs.remainingOverageTime` que ve el agente es el banco ANTES de la decisión actual** (el descuento
  se aplica después del step). Verificado en local (Test A).
- **Agotamiento ⇒ TIMEOUT ⇒ derrota inmediata.** Chequeo post-hoc en `agent.py:220-222`: si
  `duration - actTimeout > remainingOverageTime` la acción se sustituye por `DeadlineExceeded`;
  `core.py:279-281` marca status `TIMEOUT`; el intérprete de cabt da la partida al rival
  (`envs/cabt/cabt.py:148-160`: rival `DONE` con reward `1`) y `core.py:636-637` deja el reward del
  agotado en `None`. Consecuencia: **una sola decisión más larga que el banco restante pierde la partida
  en el acto**, aunque el banco fuera positivo al empezarla.
- **No hay interrupción del cómputo en local**: la llamada al agente NO se aborta a mitad; el chequeo es
  a posteriori (verificado: sleep de 5 s con banco de 3 s se completa entero y LUEGO llega el TIMEOUT).
  En producción el orquestador llama a cada agente por HTTP (`UrlAgent`) con
  `timeout = remainingOverageTime + actTimeout + 1` (`agent.py:89`): un agente colgado se corta ahí y
  recibe `DeadlineExceeded` (`agent.py:102-104`). Además el propio contenedor del agente aplica el mismo
  chequeo post-hoc (`main.py:109-135` → `Agent.act`).
- **`runTimeout=2000` limita el episodio ENTERO en segundos de pared**: bucle de `env.run` en
  `core.py:326-332`, incluye a los dos agentes + motor + intérprete; al excederse lanza
  `DeadlineExceeded` del episodio (error de episodio, no derrota de un agente concreto). Con bancos de
  600+600 s y motor ~ms/decisión **nunca es el límite activo** (1200 s máx de agentes ≪ 2000 s).
  Verificado en local con `runTimeout=1` (Test C).
- **Solo paga el que mueve**: cabt alterna turnos — un agente `ACTIVE`, el otro `INACTIVE`
  (`envs/cabt/cabt.py:181-182`); al `INACTIVE` ni se le llama ni consume banco (`core.py:175-176, 629`).
  **Excepción: el paso 0 (elección de mazo) tiene a los DOS `ACTIVE` a la vez** (`cabt.py:111-120`) y en
  producción se les llama en paralelo (Pool, `core.py:740-743`) — en la validación self-play (mismo pod,
  2 vCPU) ese paso solapa CPU de los dos lados.
- **La carga del módulo/modelo del agente cuenta en la PRIMERA decisión**: `build_agent` difiere el
  `exec` del fichero hasta la primera llamada (`agent.py:146-154`), que ya está dentro del cronómetro.
  El `agentTimeout` que menciona el README de GitHub ya no existe en 1.32.4 (0 apariciones en el código).
- La decisión del mazo (paso 0) también consume banco.

## Verificación empírica (local, torre; `debug=True`)

- **Test A** (decremento por agente): agente A0 con sleep 0,10 s y A1 con 0,03 s; A0 consumió 2,00 s en
  21 decisiones, A1 0,57 s en 20 — decremento ≈ duración propia, bancos independientes, monótono.
- **Test B** (agotamiento): banco reducido a 3 s, decisión de 5 s → el sleep se completa (sin preempción
  local), status `['TIMEOUT','DONE']`, rewards `[None, 1]`. Episodio muere ahí (5,01 s).
- **Test C** (`runTimeout`): con `runTimeout=1` y agentes de 0,3 s, `DeadlineExceeded` a los 1,2 s de pared.
- **Local vs producción**: el descuento, el TIMEOUT post-hoc y `runTimeout` son código común y están
  verificados en local. Lo NO verificable en local: el corte duro por HTTP (`agent.py:89-104`) y el
  paralelismo real del paso 0 (Pool con `UrlAgent`) — eso lo afirma el código del camino de producción,
  no lo he ejecutado.

## Presupuesto por decisión (2 vCPU, banco 600 s/lado/partida)

Reservas fijas recomendadas: ~10 s primera llamada (imports/carga; medir con el agente final) +
margen de seguridad 30 s (5%). Utilizable ≈ **560 s**.

| Decisiones propias/partida | s/decisión (media segura) |
|---|---|
| 60 | ~9,3 |
| 150 | ~3,7 |
| 300 (planificación conservadora) | **~1,8** |

- **Regla operativa: presupuesto medio seguro ≈ 1,5 s/decisión** (aguanta 300 decisiones + carga + margen
  con holgura). Con partidas típicas más cortas sobrará banco — no pasa nada, no se acumula entre partidas
  (el banco es por episodio).
- **Picos puntuales**: sí caben (p. ej. 5-10 s en turnos críticos tempranos) siempre que un controlador
  dinámico lo compense: `presupuesto_mov = (obs.remainingOverageTime - reserva) / movimientos_restantes_estimados`,
  y **tope duro por decisión = obs.remainingOverageTime - reserva** (superarlo = derrota instantánea).
  Ojo: `obs.remainingOverageTime` no incluye la decisión en curso — automedirse con `perf_counter`.
- **CPU compartida en la validación** (agente contra sí mismo, mismo pod de 2 vCPU): los bancos son
  independientes por lado, pero el reloj es de pared y la CPU es común. Como los turnos alternan, en la
  práctica solo computa un lado a la vez salvo el paso 0 (mazo), que solapa. Recomendación: ≤2 hilos de
  búsqueda propios, no asumir 2 vCPU enteras para ti, y que la elección de mazo sea barata (precomputada).
- El motor es despreciable en el balance: partida completa random en 0,208 s (ya medido en serie).
