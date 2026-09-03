# Lucario v2: variantes de lista medidas contra la de la ladder (2026-08-11)

Qué se probó: llevar a la lista de Mega Lucario los hallazgos de deckbuilding de
`estrategia-arquetipos.md §7` y `estrategia-deckbuilding.md`. Seis variantes, cada una con
**un** cambio conceptual para poder atribuir el efecto.

**Veredicto corto: ninguna mejora la lista que está en la ladder. Dos empeoran de forma
significativa.** La lista actual está en un óptimo local para el piloto `heuristico.py`, y el
consenso del papel apunta en la dirección contraria a lo que mide este motor.

- Listas: `research/decks/propios/lucario-v2b-*.csv` (las 6 pasan `battle_start`, errorPlayer −1)
- Báscula 1 (duelo directo): `arena` vía `gauntlet.mide`, mismo piloto los dos lados, n=400
- Báscula 2 (la buena, ver `gauntlet.md`): gauntlet núcleo c1..c8, n=200, cobertura 89,6%
- Piloto en los dos lados: `research/agentes/heuristico.py` (sin tocar)

---

## 1. Auditoría de `mega-lucario.csv` (la que está en la ladder, μ 464,8)

60 exactas · ≤4 copias por id · 8 básicos · 1 ACE SPEC (Master Ball 1125) · legal.

| magnitud | nuestra lista | campo (medido) | canon | lectura |
|---|---|---|---|---|
| Pokémon / Trainer / Energía | **12 / 29 / 19** | — | — | 19 energías es el doble de la mediana del papel (9) |
| básicos | **8** | 10 (c1, c7) | — | |
| **mulligan** (hipergeométrica) | **0,3464** | 0,2586 | — | empírico en `lab-barajas.md`: 0,359, coincide |
| Pokémon de 2 premios | **8 de 12 = 66,7%** | 16,7% (c1) · 23,5% (c7) | 27,9% | 4 Mega Lucario ex + 4 Regirock ex, **cero atacantes de 1 premio** |
| **estadios** | **0** | 4 (c1) · 0 (c7) | 2,53 | no llevamos, y por tanto no podemos tirar el suyo |
| **supporters de robo** | **10** | 4 (c1) · 8 (c7) | 4–9 | el desvío más grande de la lista |
| **Pokémon Tool** | **0** | 0–1 | — | **el hueco de herramienta está vacío**: cualquier Tool que entre se pega seguro |
| objetivos de Poké Pad | 4 | 15 (c1) · 12 (c7) | 12,5 | irrelevante: no llevamos Poké Pad |

Composición: 4× Riolu 677 · 4× Mega Lucario ex 678 · 4× Regirock ex 447 · 4× Fighting Gong
1142 · 4× Ultra Ball 1121 · 4× Cheren 1224 · 4× Urbain 1236 · 2× Switch 1123 · 2× Night
Stretcher 1097 · 2× Premium Power Pro 1141 · 2× Tarragon 1238 · 2× Lillie's Determination
1227 · 2× Boss's Orders 1182 · 1× Master Ball 1125 · 19× {F} básica 6.

Los cinco desvíos frente al papel que señala §7.1 se confirman todos. **Y los cinco resultan
ser irrelevantes o beneficiosos en este motor** (§3).

## 2. Las variantes

Todas parten de `mega-lucario.csv` y solo cambian lo indicado. `mega-lucario.csv` no se tocó.

| lista | cambio | concepto que prueba |
|---|---|---|
| `lucario-v2b-belt` | 1125 Master Ball → **1158 Maximum Belt** | el ACE SPEC de 3 de las 5 listas de papel; +50 permanente contra el Activo ex (Mega Brave 270+50 = **320**, OHKO exacto a Grimmsnarl ex y Dragapult ex) |
| `lucario-v2b-balloon` | −2 Urbain 1236, **+2 Air Balloon 1174** | retirada de Mega Lucario ex de 2 → **0**, pagando con el exceso de robo |
| `lucario-v2b-ratios` | −2 Cheren, −2 Urbain, **+2 Gravity Mountain 1252**, +2 Premium Power Pro (→4) | corregir los desvíos medidos: robo 10→6, estadios 0→2, PPP al 4 del papel |
| `lucario-v2b-energia` | **−6 energía (19→13)**, +2 PPP (→4), +2 Mega Signal 1145, +2 Night Stretcher (→4) | la mediana del papel es 9 energías; §7.1 llama a 19 «~7 cartas muertas» |
| `lucario-v2b-basicos` | −2 Urbain, **+2 Terrakion 607** | cuerpos básicos de 1 premio en los huecos de robo: mulligan 0,346→0,259, banca más grande |
| `lucario-v2b-basicos4` | −2 Urbain, −2 Cheren, +2 Terrakion 607, **+2 Ting-Lu 41** | lo mismo, al doble: básicos 12, mulligan **0,191**, 2 premios 8/16 |

## 3. Resultados

**Duelo directo contra `mega-lucario.csv`** (WR de la variante; empate = IC95 cubre 0,500):

| variante | n | WR | IC95 | 1.º / 2.º | veredicto |
|---|---|---|---|---|---|
| `balloon` | 400 | 0,515 | [0,466 – 0,564] | 0,610 / 0,420 | empate |
| `ratios` | 400 | 0,512 | [0,464 – 0,561] | 0,595 / 0,430 | empate |
| **`belt`** | **1600** | **0,488** | **[0,464 – 0,513]** | 0,557 / 0,419 | **empate** (a n=400 dio 0,477, era ruido) |
| `basicos` | 400 | 0,472 | [0,424 – 0,521] | 0,540 / 0,405 | empate |
| **`basicos4`** | 400 | **0,425** | **[0,377 – 0,474]** | 0,540 / 0,310 | **PIERDE** |
| **`energia`** | 400 | **0,410** | **[0,363 – 0,459]** | 0,415 / 0,405 | **PIERDE** |

**Gauntlet del campo real** (núcleo c1..c8, n=200 por emparejamiento, 1.600 partidas por fila):

| lista | POND | IC95 | peor emparejamiento |
|---|---|---|---|
| `lucario-v2b-basicos` | 0,771 | [0,749 – 0,792] | **0,315** vs c5-kangaskhan-crustle |
| **`mega-lucario` (ladder)** | **0,767** | [0,749 – 0,786] | 0,278 vs c5-kangaskhan-crustle |
| `lucario-v2b-balloon` | 0,767 | [0,746 – 0,789] | 0,290 vs c5-kangaskhan-crustle |
| `lucario-v2b-belt` | 0,749 | [0,727 – 0,772] | 0,280 vs c5-kangaskhan-crustle |
| `lucario-v2b-ratios` | 0,743 | [0,720 – 0,767] | 0,260 vs c5-kangaskhan-crustle |

Las cuatro diferencias son **muy inferiores a la resolución medida de la báscula (0,10 de
POND**, `gauntlet.md` §4[D]): no son un orden, son un empate. Ninguna variante toca los dos
agujeros de la lista (c5-kangaskhan-crustle y c6-ogerpon, 11,8% del campo juntos), que es
donde de verdad hay POND que ganar.

## 4. Evidencia de uso: ¿se juegan las cartas nuevas?

Sonda `scratchpad/sonda.py`: instrumenta el piloto y cuenta, por id, cuántas veces el motor
**ofrece** la carta y cuántas el piloto la **elige**. 60 partidas contra `c1-grimmsnarl`.

| carta | ofrecida | elegida | tasa | conclusión |
|---|---|---|---|---|
| **Maximum Belt 1158** (Tool) | 130 | **25** | 0,19 | **SÍ se pega.** ~0,42 usos/partida con 1 sola copia |
| **Air Balloon 1174** (Tool) | 306 | **58** | 0,19 | **se pega ~1 vez/partida…** |
| **retirada (option type 12)** | **975** | **0** | **0,00** | **…y no sirve para nada: el piloto NUNCA retira** |

El paso 4 de `_fase_principal` pega cualquier Pokémon Tool, y al Activo primero — que es
exactamente donde Maximum Belt hace su trabajo. Como la lista actual lleva **0 Tools**, no hay
competencia por el hueco: la carta llega. **Maximum Belt no falla por pilotaje; llega, se pega
y aun así el efecto no se ve en el marcador.**

Air Balloon es el caso opuesto y es el hallazgo más limpio de esta tanda: la línea 22 de
`heuristico.py` declara el recorte «nunca retirada (option 12)», y la sonda lo confirma con
**0 usos en 975 oportunidades ofrecidas**. Air Balloon es una carta **inerte** bajo este
piloto: se adjunta, ocupa el hueco de herramienta y no hace nada. Es el mismo patrón que las
2 Boss's Orders y que Pokégear en `lab-barajas.md §4bis`: **hueco de PILOTO, no de carta.**

> Corolario accionable: Air Balloon **no puede entrar** hasta que el piloto sepa retirar.
> Si alguna vez se implementa la retirada, esta lista es la primera que hay que volver a medir.

Efecto lateral que sí mide algo: `balloon` cambia 2 Urbain (robar 3) por 2 cartas inertes y
**no pierde nada** (h2h 0,515; POND 0,767, idéntico). Es la prueba directa de que al menos 2
de nuestros 10 supporters de robo no valen nada — el desvío de robo era real. Lo que no
existe es una carta del pool que ocupe mejor ese hueco: se probaron cuatro (Gravity Mountain,
PPP, Terrakion, Ting-Lu) y ninguna sube el marcador.

## 5. Lo que este motor dice y el papel no

Los dos resultados negativos son los informativos, porque contradicen el consenso de §7.1:

1. **Bajar de 19 a 13 energías pierde: 0,410 [0,363 – 0,459].** El papel llama a las 19
   «~7 cartas muertas» y su mediana es 9. En este motor no lo son, y encaja con el hallazgo de
   `estrategia-principios.md`: **el discriminante entre ganador y perdedor es la energía en
   juego** (turno 5: 3,17 frente a 1,91). Con `Aura Jab` y `Regi Charge` reciclando del
   descarte, cada energía extra es combustible, no lastre. **19 energías es correcto aquí.**
2. **Meter atacantes de 1 premio a costa del robo pierde: `basicos4` 0,425 [0,377 – 0,474]**
   pese a bajar el mulligan de 0,346 a **0,191** y los Pokémon de 2 premios de 8/12 a 8/16.
   La tesis central del papel («no regales premios, ataca con cuerpos de 1 premio») **no se
   paga** con este piloto, que es un atacante greedy sin plan de premios: cuerpos que no matan
   nada solo diluyen la baraja. `basicos` (la mitad de dosis) empata.
3. El consenso del ACE SPEC (Maximum Belt en 3 de 5 listas) **empata a 1.600 partidas**:
   0,488 [0,464 – 0,513]. Con 1 sola copia en 60 cartas, un +50 condicional no mueve el
   marcador aunque la carta llegue.

Todo esto es material directo para el 20% de Deck Score: se puede escribir que las
desviaciones de la lista frente al campo se detectaron, se corrigieron una a una y se
**midieron**, y que tres de ellas resultaron ser correctas para este motor por razones que el
papel no ve (el motor premia energía en juego y banca grande, no economía de premios).

## 6. Veredicto y qué queda

- **No se cambia la lista de la ladder.** Ninguna variante gana; dos pierden. Sigue
  `research/decks/propios/mega-lucario.csv`.
- `lucario-v2b-basicos` es la única con algo a favor: **mejor peor-emparejamiento** (0,315 vs
  0,278 en c5) y POND nominalmente mayor (0,771 vs 0,767). Ambas diferencias están dentro del
  ruido y muy por debajo de la resolución de 0,10. Es una candidata para volver a medir con n
  alto, no un cambio que hacer hoy.
- **Dónde está el POND que falta, y no es en estas cartas**: c5-kangaskhan-crustle (0,278) y
  c6-ogerpon (0,335) valen el 11,8% del campo. Ninguno es débil a {F}. Ese es el problema de
  lista sin resolver.
- **Air Balloon queda bloqueada** hasta que el piloto retire.

### Nota sobre ficheros

En `research/decks/propios/` había ya nueve ficheros `lucario-v2-*.csv` (marcas de tiempo del
2026-08-11 entre 02:23 y 10:22) que ninguna nota ni documento referencia. **No los he tocado
ni medido**, y por eso mis listas usan el prefijo `lucario-v2b-`. Los contenidos de
`lucario-v2-belt.csv` y `lucario-v2-balloon.csv` coinciden exactamente con los de
`lucario-v2b-belt.csv` y `lucario-v2b-balloon.csv`. Conviene decidir si se consolidan o se
borran.
