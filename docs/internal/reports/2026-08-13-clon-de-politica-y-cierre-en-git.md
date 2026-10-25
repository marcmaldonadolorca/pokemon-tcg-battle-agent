# Del heurístico al clon de política: μ 368,9 → 709,0, y cierre en Git

Fecha: 2026-08-13 · Tickets: `PKM-002`, `PKM-003`, `PKM-006` (cerrados), `PKM-004` (en curso)

## Resumen

El agente pasó de **368,9 a 709,0 de rating** en la ladder de la Simulation. La
mejora no vino de afinar la heurística —once hipótesis midieron empate o peor—
sino de **cambiar de arquitectura**: una red de política entrenada por imitación
sobre los replays de los equipos mejor valorados, con búsqueda guiada por ella.

El repositorio queda commiteado y pusheado a un remoto en disco propio.

## La progresión, y qué la produjo

| envío | μ | qué cambió |
|---|---|---|
| heurístico v2 + hops-snorlax | 368,9 | punto de partida |
| heurístico v2 + mega-lucario | 447,1 | **la baraja** (mismo piloto, md5 idéntico) |
| clon 2 días H96 + alakazam / grimmsnarl | 523,0 / 563,7 | **el piloto**: red en vez de reglas |
| **busq-d7h384 + alakazam / grimmsnarl** | **675,3 / 709,0** | **más datos + búsqueda guiada** |

Referencias del campo: μ₀ de partida 600; puesto ~2554 ≈ 682; ~799 ≈ 813; ~100 ≈ 995.

## Lo que no funcionó (y por qué importa)

Once hipótesis heurísticas sin una sola mejora confirmada: ISMCTS solo (0,529),
ISMCTS con red de valor (0,487), greedy sobre la red de valor (0,160), retirada
(0,476), gusting (0,495), banca (0,509 con n=6.000), secuenciación (**0,4797**,
peor de forma significativa), descartes (0,484), variantes de baraja (todas
empate o peor) e híbridos clon+heurística (0,486 y 0,445). Y después, ya con el
clon: auto-juego por filtrado de ganador y por pesado, ambos **perdiendo contra
su propio control** (0,454 y 0,443), y filtros de calidad del corpus que valen
exactamente su volumen, sin bonus.

Dos diagnósticos que explican el patrón:

- **La red de valor predice pero no decide.** Acierta el 0,7539 prediciendo el
  ganador desde un estado y rinde 0,160 como política, porque quitarle 30 HP al
  Pokémon rival le mueve la valoración −0,0002. Aprendió cómo se ve un ganador,
  no qué acción acerca a ganar.
- **El acuerdo con los expertos no predice ganar** (r = −0,028 sobre 1.000
  jugador-episodios). Imitar la secuenciación de los mejores, medida sobre
  161.644 decisiones, empeoró el juego.

## Dos bugs de medición propios

- **`__file__` no existe** en el `main.py` del envío: Kaggle lo ejecuta con
  `exec`, no lo importa. Tumbó el primer envío. La validación local usaba
  `import` —donde sí existe— y daba verde sobre un paquete roto.
- **Self-play silencioso**: `clon.py` resolvía la ruta de sus pesos al importarse
  y `arena.py` carga los dos agentes en el mismo proceso. El segundo heredaba los
  pesos del primero, y la medida daba 0,50 pasara lo que pasara. Invalidó ~20
  celdas, que hubo que repetir.

Los dos comparten forma: una verificación que parecía funcionar y no medía lo que
creía medir.

## El hallazgo metodológico (`PKM-012`)

**La báscula de barajas se invierte según el piloto.** Con el heurístico flojo,
`mega-lucario` daba POND 0,758 y `c1-grimmsnarl` 0,413; con el clon, 0,362 y
0,558 — intervalos disjuntos, orden del revés. La primera elección de baraja se
hizo con el instrumento equivocado, y ahora está medido en vez de intuido.

## Estado en Git

Cuatro commits (`6eb0e17` → `37debbd`) en `main`, pusheados al remoto propio
`/mnt/backup/git/kaggle-pokemon-tcg.git`, siguiendo el patrón de `kaggle-rogii` y
`momentum`. Escaneo de secretos previo, sin hallazgos.

Fuera de Git por tamaño o licencia: `data/` (datos de la competición, con
obligación de borrado al terminar), `scratchpad/`, los corpus `.npz`
regenerables, y `research/terceros/` (notebooks públicos de Kaggle, que se leen
pero no se redistribuyen desde aquí). Los pesos de los modelos sí se versionan:
3,3 MB en total.

## Lo que queda

- **`PKM-004`, antes del 2026-08-16 23:59 UTC**: cerrar la tanda de recta final
  (más días de replays, presupuesto de búsqueda) y subir el candidato definitivo.
  Si nada bate los 709,0 actuales, mantener lo que está es la decisión correcta.
- **`PKM-005`, 13-sep**: el writeup, que es lo que reparte los premios.
- **Del propietario**: si prefiere jugar la lista propia `mia-crustle-tijeras` en
  un slot. Compra concepto propio para el 20% de Deck Score —construida alrededor
  de que Crustle previene todo el daño de Pokémon ex y el 84,5% del campo ataca
  con un ex, verificado en el motor— y cuesta bajar el peor emparejamiento de
  0,547 a 0,287, que es justo lo que puntúa el 70%.
