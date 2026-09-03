# Heurístico v3: retirada y gusting — dos palancas medidas, dos negativos

Fecha: 2026-08-10. Código: `research/agentes/heuristico_v3.py` (el v2,
`research/agentes/heuristico.py`, no se toca: está en la ladder y en uso).
Báscula: `arena.py` (intercambio de asiento + IC de Wilson), `procs 2`.

**Veredicto en una línea: ninguna de las dos palancas mejora al v2. Las dos
quedan implementadas, verificadas y APAGADAS por defecto.**

> ## ✏️ CORRECCIÓN 2026-08-11 — el veredicto de arriba era de la BARAJA, no de las palancas
>
> **Las dos palancas de esta nota entran en el envío.** Lo que estaba mal no era
> la medida sino su alcance: **todo lo de esta nota se midió con `hops-snorlax`**
> (y un control en `iono-bellibolt`), y desde el 2026-08-10 la baraja que va en
> serio es **`mega-lucario`** (PKM-010). Re-medidas ahí, con el mismo `heuristico_v3.py`
> byte a byte y el mismo protocolo:
>
> | palanca | esta nota (hops-snorlax) | mega-lucario | n |
> |---|---|---|---|
> | `RETIRADA` | 0,476 [0,451, 0,501] | **0,5306 [0,5196, 0,5417]** | 7.800 |
> | `GUSTING` | 0,495 [0,469, 0,520] | **0,5241 [0,5130, 0,5352]** | 7.800 |
>
> No es una contradicción: es **dependencia de lista**, y las dos direcciones están
> medidas. El §3 de esta nota ya lo explicaba sin saberlo — el gusting no rendía
> porque «el v2 ya mata de un golpe con Snorlax», que es una propiedad de
> *hops-snorlax*; `mega-lucario` no remata de frente igual, así que arrastrar sí
> paga. Y la retirada perdía porque descartaba energía; en `mega-lucario` Aura Jab
> la recarga desde el descarte.
>
> **La lección de método, que vale más que las dos palancas:** un negativo medido
> con una baraja NO es un negativo de la política. Antes de enterrar una palanca
> hay que decir con qué lista se midió, y volver a medirla si la lista cambia.
> Detalle y combinación en `research/notas/agente-v5.md`.
>
> (El aviso de reactivación del §«Para reactivar cualquiera de las dos» sigue
> siendo válido, pero ya no hace falta: `research/agentes/heuristico_v5.py` las
> lleva fijadas a `True`.)

## Por qué existe este v3

`agente-heuristico.md` dejaba escritos dos recortes deliberados: la política
nunca usaba (a) la retirada (option type 12) ni (b) el gusting dirigido
(Boss's Orders 1182 y familia). Son las dos palancas tácticas grandes que
quedaban, y la hipótesis era que valían puntos. Se han cerrado las dos, cada
una tras su propia global de módulo, para poder medir el aporte AISLADO:

```python
RETIRADA = os.environ.get("V3_RETIRADA", "0") != "0"
GUSTING  = os.environ.get("V3_GUSTING",  "0") != "0"
```

Se leen en cada decisión, así que quien carga el módulo las fija por atributo
(`mod.RETIRADA = True`) o por entorno antes de importar. Con las dos apagadas
el v3 es **política idéntica al v2** (todos los caminos nuevos salen por un
`return None` antes de mirar el estado); es un drop-in seguro.

## Regla 1 — RETIRADA (option type 12)

Conservadora: todas las condiciones a la vez. La legalidad (hay banca, no se ha
retirado ya este turno, hay energía para pagar el coste) la garantiza el motor,
que solo ofrece el option 12 cuando se puede.

- **(a) atacar manda sobre huir**: si el activo ya remata al activo rival, no se
  retira.
- **(b) motivo**, uno de dos:
  - *muere*: la amenaza rival —mejor ataque del activo rival con sus energías
    **+1**, con debilidad ×2— llega a sus HP actuales. El +1 es la clave: cada
    jugador adjunta una energía por turno, así que el ataque que hoy no paga y
    mañana sí es amenaza real (`_dano_contra(..., extra=1)`).
  - *inútil persistente*: este turno no se le ofrece ningún ataque y tampoco lo
    desbloquearía una energía más.
- **(c) el relevo aguanta**: el relevo es *exactamente* el que promocionará el
  select (1,4) —misma función `_puntua_banca`, para que lo evaluado y lo
  promocionado no se separen—, tiene que poder atacar YA y no morir a esa misma
  amenaza.
- **(d) el peaje cabe**: `retreatCost` ≤ 2, o ≤ 3 si el activo regala 2 premios
  (ex/Mega ex), que es justo lo que se está salvando.
- **(e) el relevo no regala el turno**: remata al rival o pega ≥60 % de lo que
  pegaría el activo (si el activo no puede atacar, gratis).

Nunca deja la mesa indefensa: la retirada intercambia activo y banca (la banca
no se vacía, no hay derrota por «sin Pokémon en juego») y (c) exige que el que
entra pueda pelear. Entra en la fase principal en el paso 7c, con todo lo demás
ya desplegado y justo antes de atacar: el motor vuelve a preguntar (0,0) tras el
cambio y el relevo ataca en el mismo turno.

### Por qué la primera versión de la regla no servía (diagnóstico, no intuición)

Con la amenaza calculada solo con la energía YA puesta, la retirada disparó
**1 vez en 400 oportunidades** (40 partidas espejo hops-snorlax). El desglose de
los vetos dice dónde está el juego de verdad:

| Veto | Veces (de 400 options 12 ofrecidos) |
|---|---|
| (a) ya remato al activo rival | 231 |
| (b) no muero a la amenaza inmediata | 144 |
| (c) el relevo llega desarmado | 20 |
| (c) el relevo muere igual | 4 |
| **retira** | **1** |

El veto dominante no era la regla: era el estado. El rival casi nunca mata «ya»
con la energía puesta (margen típico 60-150 HP) y la banca de esta política
llega sin energía. Con la amenaza a +1 energía la palanca pasa a disparar
**27 veces en 400 partidas** en hops-snorlax y ~12 por cada 40 partidas en
iono-bellibolt: ya es medible.

El gatillo *inútil persistente* aporta 7 de esas 27 retiradas. La versión sin el
guardián «tampoco con una energía más» disparaba 24 veces más en bellibolt, pero
tirando 2 energías de un Pokémon al que le faltaba UNA para atacar: se descartó
por eso, no por gusto.

## Regla 2 — GUSTING dirigido

Clasificación **por texto**, no por lista de ids (`_RE_GUST` sobre
`trainer_effect`): `switch in 1 of your opponent.s benched (basic )?pok.mon to
the active spot`. Cubre 1182 Boss's Orders, 1088 Prime Catcher, 1124 Pokémon
Catcher (moneda), 1204 Lisia's Appeal (solo básicos, capturado por el grupo
opcional) y 1218 TR Giovanni. Queda fuera 1143 Repel, que no es dirigido.

Gates para no tirar la ranura de Supporter:

- hay banca rival **y** mi activo tiene ataque ofrecido este turno (sin remate
  detrás, arrastrar no sirve de nada);
- si ya puedo noquear al activo rival **no** se gasta la carta, salvo que el
  objetivo de banca dé más premios que él (ex escondido en la banca);
- se juega si el objetivo muere a mi ataque de este turno (KO) o si es una pieza
  que todavía no puede atacar mientras el activo rival sí (trampa de tempo); las
  cartas con moneda solo entran por KO.

Elección del objetivo (`_valor_objetivo`): KO inmediato manda, ×2 si regala 2
premios; después la pieza clave que aún no puede atacar; después el más
herido/frágil.

**La otra mitad de la palanca**: el select donde se elige el Pokémon de la banca
RIVAL. Llega como `(type 1, context 3)` — el **mismo** context que la promoción
propia tras KO — y se distingue por el `playerIndex` del option, nunca por el
context. El v2 lo resolvía puntuando la banca PROPIA con índices de la rival:
legal, pero elección ciega. Esto importa más de lo que parece en hops-snorlax:
el select llega ~2 veces por partida (798 en 400 partidas), la mayoría no de
Boss's Orders sino de Defiant Horn del 310 Hop's Dubwool, que arrastra al
evolucionar. Va bajo la palanca GUSTING porque es su otra mitad.

## Medición (arena.py, procs 2, baraja hops-snorlax = la del envío 55407312)

Cada variante contra el **v2** con la misma baraja en los dos lados: aísla
piloto, no baraja.

| Palanca | n | Tasa vs v2 | IC95 |
|---|---|---|---|
| solo RETIRADA | 300 | 0,473 | [0,418, 0,530] |
| solo RETIRADA | 1.200 | 0,477 | [0,449, 0,505] |
| **solo RETIRADA (pool 1.500)** | 1.500 | **0,476** | **[0,451, 0,501]** |
| solo GUSTING | 300 | 0,510 | [0,454, 0,566] |
| solo GUSTING | 1.200 | 0,491 | [0,463, 0,519] |
| **solo GUSTING (pool 1.500)** | 1.500 | **0,495** | **[0,469, 0,520]** |
| v3 COMPLETO | 300 | 0,460 | [0,404, 0,517] |
| v3 COMPLETO | 1.200 | 0,501 | [0,473, 0,529] |
| v3 COMPLETO (verificación) | 400 | 0,517 | [0,469, 0,566] |
| **v3 COMPLETO (pool 1.900)** | 1.900 | **0,498** | **[0,475, 0,520]** |
| solo RETIRADA, iono-bellibolt | 1.200 | 0,483 | [0,455, 0,512] |
| v3 con las DOS apagadas (no-regresión) | 600 | 0,508 | [0,468, 0,548] |

- Las n=300 que pedía el guion no distinguen nada (±5,6 pts). Como la partida
  cuesta 0,17 s, se subió a 1.200 para separar «nulo» de «efecto pequeño»: con
  la n grande el IC excluye ganancias mayores de ~3 pts en las tres.
- **Retirada**: el estimador puntual queda por debajo de 0,5 en las **tres**
  corridas independientes (0,473 / 0,477 en hops, 0,483 en bellibolt). No es
  significativo, pero no hay ni rastro de ganancia y sí un sesgo consistente al
  daño: retirarse descarta energía y cede el ataque del turno.
- **Gusting**: 0,495 con 1.500 partidas y 149 activaciones por cada 400 — la
  palanca engancha de sobra, y aun así no mueve la aguja. Coste real: gastar la
  ranura de Supporter que el v2 usa para robar.
- La corrida en **iono-bellibolt** es el control de «¿será que la palanca no
  dispara en esta baraja?»: allí la retirada dispara ~12 veces por 40 partidas
  (vs ~1 en hops) y sigue sin mejorar. El negativo no es por falta de muestra de
  la palanca.

## Verificación de legalidad y coste (400 partidas, v3 COMPLETO, hops-snorlax)

| Prueba | Resultado |
|---|---|
| Estatus propios | **400× DONE — 0 INVALID / ERROR / TIMEOUT** |
| Estatus rival | 400× DONE |
| `FALLBACKS` (4 contadores) | **todos a 0** |
| `CASOS_RAROS` | **set() vacío** |
| Activaciones | retirada 27 (7 por «inútil») · gusting 149 (141 por KO) · objetivo de banca rival 798 |
| Decisiones | 22.294 (55,7/partida) |
| Tiempo/decisión | **media 0,029 ms**, máx 30,2 ms (carga del catálogo), 8 por encima de 1 ms |

Presupuesto del motor: 1 s/decisión. Margen ×34.000 sobre la media. Sin cambio
de orden respecto al v2 (0,083 ms).

## Qué se lleva el proyecto

1. **Las dos palancas quedan apagadas por defecto.** El envío sigue siendo el v2
   en cuanto a política; el v3 con `RETIRADA=GUSTING=0` es un drop-in idéntico y
   verificado, no una regresión.
2. **Un negativo medido cierra dos ideas caras.** «Boss's Orders es una palanca
   grande» es cierto en el TCG humano y falso para *esta* política: el v2 ya
   mata de un golpe con Snorlax (140 base + 30 Band + 30 Extra Helpings + 30
   Postwick), así que el gusting solo entra cuando NO puede rematar de frente, y
   ahí el premio que gana lo paga con la carta de robo.
3. **Dónde está el techo de verdad**: el diagnóstico de la retirada lo enseña sin
   ambigüedad — 20 de 400 vetos por «el relevo llega desarmado» y 288 de 542 en
   bellibolt. La banca de esta política se llena de básicos sin energía. La
   siguiente palanca no es táctica, es de **desarrollo de banca** (a quién se le
   pone la energía y en qué orden), no otra carta.
4. Para reactivar cualquiera de las dos: `V3_RETIRADA=1` / `V3_GUSTING=1` en el
   entorno, o el atributo del módulo. La medición está aquí para no repetirla.

## Reproducir

```bash
# palanca aislada (wrappers de un solo uso en el scratchpad fijan palanca+baraja)
.venv/bin/python arena.py --a <wrapper_v3>.py --b <wrapper_v2>.py --n 1200 --procs 2
# legalidad + tiempos + contadores de uso
.venv/bin/python <scratchpad>/verif_v3.py --n 400 --procs 2 --ret 1 --gus 1 \
    --deck hops-snorlax --rival v2
```

Contadores nuevos a nivel módulo, junto a `FALLBACKS`/`CASOS_RAROS`:
`USOS = {retirada, retirada_inutil, gusting, gusting_ko, objetivo_rival}`.
