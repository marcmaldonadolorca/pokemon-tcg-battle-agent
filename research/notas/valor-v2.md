# Función de valor v2 — rasgos tácticos sobre el catálogo del motor

Fecha: 2026-08-10. Piezas: `research/valor/features_v2.py`, `entrenar_v2.py`,
`corpus_v2.npz`, `valor_v2.npz`. **La v1 no se ha tocado** (`features.py`,
`valor.npz`, `entrenar.py` intactos: los usa la batería de arena en curso).

Titular: **v1 0,7238 → v2 0,7539** de acierto en la MISMA partición honesta
(base trivial 0,5419). Δ pareado por partida **+0,0276 ± 0,0042 (z = +6,6)**,
log-loss 0,5132 → 0,4886. Con capacidad igualada la ventaja sigue siendo
**+0,0189 (z = +4,5)**: son los rasgos, no los pesos. El grupo que más aporta no
es el que se esperaba: es `tablero`, no `combate`.

Aviso sobre el 72,66% de la v1: ese número salía de `corpus.npz` con el corte por
tramos de `entrenar.py`, que tiene fuga (abajo, §5). No es comparable con nada de
aquí. La cifra honesta de la v1 es 0,7238.

---

## 1. Convenciones del motor, verificadas (no supuestas)

Probe propio sobre `AllCard`/`AllAttack` de `libcg.so` con partida iniciada
(1.267 cartas, 1.556 ataques, 1.056 Pokémon) y sobre un `obs["current"]` real:

- **Un solo espacio de tipos.** `energyType` ∈ 0..9 (0 = incolora, 9 = dragón),
  `weakness` ∈ 1..8 o `None` (35 cartas sin debilidad), `resistance` ∈ {1, 6} o
  `None` (836 sin resistencia). Los tres viven en el mismo espacio, así que
  comparar `weakness == energyType` del atacante es correcto. Como `weakness`
  nunca vale 0, un atacante incoloro **nunca** cobra bonus de debilidad — que es
  la regla real.
- **Coste de ataque** = lista `energies`; el valor 0 aparece 1.464 veces = requisito
  INCOLORO (lo paga cualquier energía), 1..8 exigen ese tipo concreto.
- **`ex` y `megaEx` son bools y son mutuamente excluyentes** (121 ex, 30 megaEx,
  0 con las dos). De ahí premios = 3 / 2 / 1.
- `retreatCost` ∈ 0..4. `pkm["energies"]` ya viene resuelto a lista de ints (tipos),
  no a cartas.
- `current` tiene los flags `retreated`, `energyAttached`, `stadiumPlayed`;
  `stadium` es una **lista de carta** (vacía si no hay), y la carta lleva
  `playerIndex`, que es lo que permite distinguir estadio propio de rival.
- `players[j]["prize"]` es una lista de `null`: solo se ve la **longitud** = premios
  que le quedan por coger a j. Nada más — y es todo lo que usan los rasgos.

**Lo único que sigue siendo supuesto**: que un KO de megaEx concede 3 premios y uno
de ex concede 2. No lo he re-medido contra logs en esta tanda. Afecta a 151 de 1.056
Pokémon y, si estuviera mal, degradaría a un rasgo de «carta gorda sí/no», que es
casi toda la señal de todos modos.

## 2. Legalidad de los rasgos

Todo sale de información **pública**: activo y banca de los dos lados con su HP y
sus energías, longitud de los montones de premios, descarte, estadio, flags del
turno — más el catálogo estático del motor. Cero mano rival, cero contenido de
premios, cero mazo. Los rasgos son legales tal cual en el envío.

Y siguen siendo **deck-agnósticos**: no entra ninguna identidad de carta como
rasgo, solo propiedades derivadas (daño, coste, premios, retirada). Una baraja que
la red no vio entrenando se describe con los mismos números.

## 3. Los 32 rasgos nuevos (v2 = 30 de la v1 + 32)

Invariante duro: `features_v2.extrae(cur)[:30]` **es** `features.extrae(cur)` —
se llama a la v1, no se reimplementa. Por eso la comparación v1/v2 sobre el mismo
corpus es exacta.

**Combate (11)** — la aritmética de «quién tumba a quién antes»:

| Rasgo | Por qué |
|---|---|
| `mata_ya` | Mi activo noquea al suyo ESTE turno con un ataque pagable: el evento que más mueve la partida. Se anula si estoy dormido o paralizado. |
| `me_mata_ya` | El simétrico: su activo me noquea. Distingue «voy ganando» de «voy ganando y me muero». |
| `dmg_yo` / `dmg_rival` | Daño del mejor ataque **pagable ahora**, con debilidad (×2) y resistencia (−30) aplicadas. |
| `dmg_pot_yo` / `dmg_pot_rival` | Daño del mejor ataque aunque no esté pagado: el techo de la amenaza. |
| `debil_favor` / `debil_contra` | Emparejamiento de tipos explícito; duplica el daño y decide muchos cambios de activo. |
| `turnos_yo` / `turnos_rival` | Turnos para tumbar al rival al ritmo actual (tope 6). Convierte HP y daño en la magnitud que importa. |
| `gano_carrera` | 1 / 0,5 / 0 según `turnos_yo` < = > `turnos_rival`. La carrera resumida en un número. |

**Energía (3)** — el recurso que limita todo lo anterior:

| Rasgo | Por qué |
|---|---|
| `falta_ene_yo` | Energías que faltan para mi mejor ataque: mide cuántos turnos de preparación quedan. |
| `falta_ene_rival` | Lo mismo del rival = cuánto margen tengo antes de que empiece a pegar de verdad. |
| `mato_con_una_mas` | Con UNA energía más mataría. Es exactamente la señal que premia adjuntar aquí y no en la banca. |

**Premios (7)** — la matemática que de verdad termina las partidas:

| Rasgo | Por qué |
|---|---|
| `prz_act_yo` / `prz_act_rival` | Premios que concede cada activo si cae (1/2/3). Perder un ex vale el doble que perder un básico: la v1 no lo sabía. |
| `prz_banca_yo` / `prz_banca_rival` | Exposición media de la banca: cuánto regalo cuando me rompan el tablero. |
| `intercambio_prz` | Diferencia (suyos − míos): ¿el intercambio de golpes me sale a favor? |
| `gano_si_mato` | Matar ahora agota mis premios = victoria inmediata. Estado terminal, no gradiente. |
| `pierdo_si_me_matan` | El simétrico. Solo se dan en el 2,3% de las decisiones, pero ahí valen la partida entera. |

**Tablero (11)** — recursos posicionales; el grupo que más aporta:

| Rasgo | Por qué |
|---|---|
| `retirada_yo` / `retirada_rival` | Coste de retirada = movilidad. Un activo caro queda anclado y es un pasivo. |
| `puedo_retirar` | Tengo energías, banca y no he retirado aún: la opción existe de verdad. |
| `estadio_mio` / `estadio_rival` | La v1 solo sabía «hay estadio»; de quién es cambia el signo del efecto. |
| `tools_tot_yo` / `tools_tot_rival` | Tools en TODO el tablero (la v1 solo miraba el activo). |
| `banca_lista_yo` / `banca_lista_rival` | Fracción de la banca que ya podría atacar si sube: mide si tengo relevo o me quedo vendido tras un KO. |
| `banca_dmg_yo` / `banca_dmg_rival` | Mejor daño potencial esperando en banca = la amenaza del turno siguiente. |

## 4. Corpus: por qué hubo que regenerar

**No se pudo reutilizar `corpus.npz`.** Guarda solo la matriz de 30 rasgos ya
extraídos, no los estados `obs["current"]` de los que salieron; los rasgos nuevos
necesitan el estado crudo (ids de carta, energías, banca), que nunca se guardó.
Recalcular era imposible por construcción, no por pereza.

Además `corpus.npz` **no tiene `g`** (id de partida), así que ni siquiera permite el
corte honesto — motivo independiente para rehacerlo.

`corpus_v2.npz`: 9.000 partidas → **822.726 muestras × 62 rasgos**, balance 0,542,
con `g`. Self-play heurístico v2 contra sí mismo sorteando 2 de las 15 listas del
catálogo por partida. (Generado en la tanda anterior con
`generar.py --rasgos features_v2`; en esta sesión se reutilizó tal cual y se
verificó columna a columna: **los 32 rasgos nuevos están vivos**, ninguno constante,
`estadio_mio` dispara el 23,9% y `puedo_retirar` el 54,0%.)

## 5. Protocolo y resultado

Corte **por partida** con `g` explícito, tres particiones 70/15/15
(6.300 / 1.350 / 1.350 partidas). La época se elige por pérdida en VALIDACIÓN y
todo lo reportado sale de TEST. 3 semillas por configuración, se queda la mejor por
val (nunca por test). Misma red que la v1 (dim→32→16→1, Adam, 40 épocas).

| | acierto (test) | log-loss | mejora sobre base |
|---|---|---|---|
| base trivial | 0,5419 | — | — |
| **v1 (30 rasgos)** | **0,7238 ± 0,0054** | 0,5132 | +0,1819 |
| **v2 (62 rasgos)** | **0,7539 ± 0,0057** | 0,4886 | +0,2120 |

Comparación **pareada por partida** (la unidad correcta: las ~90 muestras de una
partida comparten resultado y no son 90 observaciones):

- Δacierto v2 − v1 = **+0,0276 ± 0,0042 (z = +6,6)**
- Δlog-loss v1 − v2 = **+0,0314 ± 0,0053 (z = +6,0)**
- v2 acierta más en el 56,8% de las partidas de test, igual en el 7,0%.

**La fuga del protocolo viejo, medida** (`--fuga`): con el corte por tramos de
`entrenar.py`, la v1 sobre este mismo corpus da 0,7289 frente a 0,7238 con corte
por partida real. **La trampa valía +0,0051 de acierto.** Causa: cada partida
aporta sus dos perspectivas con etiquetas opuestas, el corte ingenuo las ve como
dos tramos distintos y manda uno a train y otro a validación — y son casi
espejo.

### 5b. Control de capacidad: ¿son los rasgos o son los parámetros?

La v2 tiene el doble de entradas, así que también más pesos. Para separar las dos
cosas se repitió todo con la red al doble de ancho (dim→64→32→1):

| red | v1 (30) | v2 (62) | Δ pareado v2−v1 |
|---|---|---|---|
| 32→16 | 0,7238 | **0,7539** | +0,0276 ± 0,0042 (z +6,6) |
| 64→32 | 0,7301 | 0,7536 | +0,0189 ± 0,0042 (z +4,5) |

Dos conclusiones, las dos útiles:

1. **Duplicar la capacidad de la v1 recupera +0,0063 de los +0,0276.** El resto
   (+0,0189, z = +4,5, con capacidad igualada) es de los rasgos, no de los pesos.
   La mejora no es «una red más grande».
2. **La v2 está saturada en 32→16** (0,7539 vs 0,7536: nada). Ensancharla no da
   nada y sí cuesta inferencia. Se queda en 32→16, que además es lo que cabe en el
   presupuesto de ~1,6 vCPU. Los pesos publicados son los de 32→16.

## 6. Ablación

Dos direcciones, porque una sola engaña. Los Δ son **pareados por partida**
(mismo test, misma partición); ojo, el `acc` de la tabla está ponderado por
MUESTRA y el Δ por PARTIDA, así que pueden discrepar en el tercer decimal — manda
el Δ, que es el que trae error estándar y el que se corresponde con «consistencia
entre partidas».

**(a) v2 completa MENOS un grupo** — referencia v2 = 0,7539. Si Δ < 0, el grupo aporta:

| quito | acierto | Δacierto (z) | Δlog-loss |
|---|---|---|---|
| − tablero | 0,7438 | **−0,0112 (z −3,5)** | −0,0037 |
| − premios | 0,7517 | **−0,0062 (z −2,1)** | −0,0012 |
| − energía | 0,7539 | **−0,0060 (z −2,0)** | −0,0020 |
| − combate | 0,7531 | −0,0039 (z −1,2) | −0,0043 |

**(b) v1 MÁS un solo grupo** — referencia v1 = 0,7238. Cuánto aporta por sí solo:

| añado | acierto | Δacierto (z) | Δlog-loss |
|---|---|---|---|
| + tablero | 0,7464 | **+0,0199 (z +4,9)** | +0,0257 |
| + combate | 0,7335 | +0,0025 (z +0,7) | +0,0103 |
| + energía | 0,7260 | +0,0019 (z +0,7) | +0,0099 |
| + premios | 0,7269 | +0,0018 (z +0,6) | +0,0074 |

**Lectura honesta:**

1. **`tablero` es el grupo que manda, y no era la hipótesis.** Solo él ya recupera
   +0,0199 de los +0,0276 totales (72% de la mejora), y quitarlo de la v2 es lo que
   más duele. Es el único grupo con z alto en las dos direcciones. Interpretación:
   `banca_lista`, `banca_dmg` y `retirada` describen si el jugador **tiene tablero
   montado**, que es un predictor de resultado mucho más estable que el intercambio
   concreto del turno en curso.
2. **`combate`, `energía` y `premios` son redundantes entre sí pero no sobran.**
   Por separado casi no mueven el acierto (z ≈ 0,6–0,7), pero los tres mejoran el
   log-loss de forma clara (+0,007 a +0,010) y **quitar cualquiera de ellos de la
   v2 completa sí duele** (z −1,2 a −2,1). Miden la misma cosa desde tres ángulos:
   quién gana el intercambio. Se quedan porque calibran la probabilidad, que es
   justo lo que necesita la búsqueda, aunque no cambien tanto el signo.
3. `combate` es el más flojo de los cuatro en acierto y el mejor en log-loss al
   añadirlo solo. Es el candidato a recortar si el coste apretara.

## 7. Coste

Extracción de rasgos, medida en la torre (1 partida, 74 estados, 6 repeticiones,
catálogo ya memoizado):

| | µs/estado | estados/s |
|---|---|---|
| v1 | 9,4 | 106.000 |
| v2 | 43,5 | 23.000 |

**v2 cuesta 4,6× más** (34 µs de margen). No es gratis: la evaluación vive en la
ruta caliente de la búsqueda con ~1,6 vCPU, así que a igualdad de tiempo la v2
permite ~4,6× menos evaluaciones. Referencia: el heurístico decide en 86 µs. La
red en sí (62→32→16→1, 16 KiB) es despreciable frente a la extracción.

## 8. Veredicto

- **La v2 mejora a la v1 de forma clara y con el protocolo estricto**: +0,0276 de
  acierto (z = +6,6) y −0,0314 de log-loss sobre la misma partición, y +0,0189
  (z = +4,5) con la capacidad de la red igualada. Se adopta como función de valor
  de referencia. Pesos en `research/valor/valor_v2.npz` (62→32→16→1, 16 KiB).
- La v1 sigue intacta y en uso; nada de esto toca `valor.npz`, `features.py`,
  `entrenar.py` ni `mcts.py` (md5 comprobados).
- **La v2 no está cableada a nada todavía.** `valor.py` busca literalmente
  `valor.npz` y sirve a una red de 30 entradas; usar la v2 exige o un parámetro de
  ruta o un `valor_v2.py` hermano, y que quien llame use `features_v2.extrae`. Es
  una decisión de integración, no de investigación, y queda para el orquestador.
- **Lo que esto NO demuestra**: que el agente juegue mejor. El resultado previo es
  que el ISMCTS con la v1 empata al heurístico; una función de valor +2,8 puntos
  mejor es condición necesaria, no suficiente. La prueba real es una tanda de
  `arena.py` con MCTS+valor_v2 contra el heurístico, y ese gate queda fuera de esta
  nota (mcts.py estaba en uso).
- Antes de meterla en el envío hay que decidir el intercambio coste/precisión: 4,6×
  en extracción es mucho con 1,6 vCPU. Si hay que recortar, el orden por la
  ablación es: fuera `combate` primero, nunca `tablero`.
