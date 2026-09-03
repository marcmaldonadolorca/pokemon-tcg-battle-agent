# Los selects donde jugábamos al azar — qué son, cuáles nos tocan, y qué midió la báscula

Fecha: 2026-08-11. Motiva esta nota `research/notas/diagnostico-expertos.md` §1: hay
**11.071 decisiones (7,3% del total)** repartidas en cinco clases de select donde el
acuerdo del heurístico v2 con los expertos es **igual al suelo aleatorio**. La más cara
es `(1,8)`, con 2.064 casos, **10,8% de acuerdo contra un 10,7% de azar**.

Piezas: `research/replays/censo_selects_azar.py` (evidencia, 600 episodios de la ladder),
`research/replays/acuerdo_descartes.py` (dirección), `research/agentes/heuristico_descartes.py`
(la regla), `research/probe_descartes.py` (legalidad y frecuencia real), `arena.py` (el gate).

**Resumen de la tanda, por delante:**

| resultado | medida |
|---|---|
| ❌ Regla de descarte `(1,8)` | 0,484 IC95 [0,463, 0,505] sobre 2.100 partidas → **no entra** |
| ✅ Regla de búsqueda `(1,7)` *(el extra)* | **0,538 IC95 [0,520, 0,556]** sobre 3.000 partidas frescas → **pasa**, pero **solo con mega-lucario** (hops-snorlax: 0,500 [0,475, 0,525]) |
| ❌ Regla de promoción tras KO *(el otro extra, §8)* | confirmatoria 0,488 IC95 [0,463, 0,513] sobre 1.500 → **no entra** |
| 🔁 Reordena el backlog | **8.244 de las 11.071** decisiones «aleatorias» del diagnóstico **no son nuestras** |
| 🧭 Corrige el mapa | `(1,3)` y `(1,4)` estaban **intercambiados** en `motor-mecanica.md` y en el diagnóstico; y `area == 5` tiene un tercer inquilino, `(1,21)` (§8.1) |

La ironía útil de la tanda: el contexto con la brecha más escandalosa contra el experto
(`(1,8)`, 10,8% vs 10,7% de azar) tenía techo **cero**, y el que ganó fue el que nadie
había señalado como aleatorio — `(1,7)`, que ya acordaba un 50,4%. Otra confirmación de
que el acuerdo con el experto no localiza dónde está el dinero.

---

## 1. Qué es cada contexto, con evidencia

El campo `select.effect` (`{id, playerIndex, serial}`) identifica la carta que abre el
select. Cruzándolo con `current.yourIndex` se sabe además **quién decide**: PROPIO =
lo provoca el jugador que responde; RIVAL = lo provoca el otro y a mí me toca sufrirlo.

Censo sobre 600 episodios (300 por zip, `data/replays/censo_selects_azar.pkl`):

| (t,c) | carta que lo provoca | dueño | n | % |
|---|---|---|---|---|
| **(1,8)** | **Ultra Ball** (1121) | PROPIO | 585 | 52,1% |
| (1,8) | Xerosic's Machinations (1197) | **RIVAL** | 265 | 23,6% |
| (1,8) | Lunatone (675) | PROPIO | 123 | 11,0% |
| (1,8) | Hand Trimmer (1087) | RIVAL 6,0% / PROPIO 3,0% | 101 | 9,0% |
| (1,8) | N's Zoroark ex (293) 2,6%, Morty's Conviction (1187) 1,1%, Secret Box (1092) 0,1% | PROPIO | 42 | 3,8% |
| (1,13) | **Munkidori** (112) | PROPIO | 1.852 | **100%** |
| (1,16) | **Munkidori** (112) | PROPIO | 1.852 | **100%** |
| (1,14) | **Dragapult ex** (121) | PROPIO | 1.620 | **100%** |
| (1,17) | **Wally's Compassion** (1229) | PROPIO | 267 | 99,6% |
| (1,3) | *sin `effect`* — cambio forzado sobre mi banca (**no** es la promoción tras KO: eso es `(1,4)`, §8.1) | — | 1.163 | 58,7% |
| (1,3) | Boss's Orders (1182) | PROPIO | 621 | 31,3% |
| (1,3) | Abra 3,1%, Switch 3,1%, Hariyama 1,5%, Prime Catcher 0,6%… | PROPIO | 198 | 10,0% |

**`(1,8)` = descarte de coste de la mano**, y la nota `motor-mecanica.md` estaba mal:
decía «elegir 3 de la mano (efecto 1092)». Ese 1092 es Secret Box, **1 de 1.123
apariciones (0,1%)** — un artefacto de haber sondeado solo con la baraja de ejemplo del
motor. La confirmación textual es directa: Ultra Ball dice *«You can use this card only
if you discard 2 other cards from your hand»* y las formas observadas son
`min == max` siempre, `area = 2` (mano), con **N variable**:

| N (min=max) | n | quién |
|---|---|---|
| 2 | 637 | Ultra Ball |
| 1 | 206 | Lunatone, Hand Trimmer |
| 3 | 43 | Secret Box, Xerosic |
| 4 / 5 / 6 | 41 / 43 / 37 | Xerosic's Machinations (baja la mano a 3 → N depende de cuántas cartas tenga la víctima) |

Un agente que asumiera `N = 3` (lo que sugería la nota vieja) se rompería en el 96% de
los casos. `motor-mecanica.md` queda corregida con esta tabla y con el criterio general:
**`context` no identifica una mecánica, identifica el hueco de una carta**; lo robusto es
despachar por `(area de option[0], minCount==maxCount, effect.id, effect.playerIndex == yourIndex)`.

Los otros cuatro contextos quedan identificados y son de **carta única**:
`(1,13)` y `(1,16)` son las dos mitades del Adrena-Brain de Munkidori (origen `area 4` y
destino `area 4/5` de los contadores de daño); `(1,14)` es el reparto de daño de
Dragapult ex sobre la banca rival (`area 5`); `(1,17)` es el objetivo de
Wally's Compassion (`area 4/5`).

Hallazgo colateral sobre `(1,3)`: **son dos decisiones opuestas bajo el mismo
(type, context) y la misma forma** (`min=max=1`, `area=5`). Con `effect is None` (58,7%)
es un cambio forzado sobre MI banca → quiero el mejor. Con `effect` no nulo
(41,3%, de los cuales Boss's Orders 75,8% = 621/819 — de ahí el «75%» del diagnóstico,
que es sobre los que tienen efecto, no sobre el total) es *«arrastro a un Pokémon de la
banca del RIVAL»* → quiero el peor suyo. El v2 aplica la misma función a las dos ramas.

---

## 2. Cuáles nos tocan de verdad

Cruzando las cartas provocadoras con nuestras barajas (`research/decks/propios/`) y con
el campo (`research/decks/campo/`). La clave es que **`(1,13)`, `(1,14)`, `(1,16)` y
`(1,17)` son 100% PROPIO**: si la carta no está en TU lista, no ves nunca ese select,
aunque el rival la juegue.

| contexto | carta | ¿en mega-lucario / hops-snorlax? | ¿nos afecta? |
|---|---|---|---|
| (1,13)+(1,16) | Munkidori | **NO** (está en c1, c4, x4, x5 del campo) | **NO**: 100% PROPIO. 6.094 decisiones del diagnóstico que **no son nuestras** |
| (1,14) | Dragapult ex | **NO** (c4, x5) | **NO**: 100% PROPIO. 2.772 decisiones ajenas |
| (1,17) | Wally's Compassion | **NO** (c3, c7, x7) | **NO**: 99,6% PROPIO |
| **(1,8)** | **Ultra Ball ×4** | **SÍ, en las dos** | **SÍ, y es el grueso** |
| (1,8) | Xerosic's Machinations | NO, pero **RIVAL** | sí, cuando el rival la lleva (c2, c5, x3, x4: 4 de 15 barajas de campo) |
| (1,8) | Hand Trimmer | NO, pero RIVAL 6% | marginal (c3: 1 de 15) |
| (1,8) | Lunatone, N's Zoroark, Morty's | NO, y PROPIO | **NO** |

**Conclusión de priorización: de las 11.071 decisiones «aleatorias» del diagnóstico, la
única clase que nos toca es `(1,8)`, y dentro de ella lo que importa es nuestro propio
Ultra Ball.** Los 8.244 casos de Munkidori/Dragapult/Wally son ruido ajeno: gastar
esfuerzo ahí sería trabajar para el rival. Esto reordena el diagnóstico, que los contaba
como si fueran deuda nuestra.

Y en NUESTRAS partidas `(1,8)` pesa **mucho más** que en la media de la ladder, porque
llevamos el máximo de Ultra Ball. Medido con `probe_descartes.py --legalidad 400`
(mega-lucario en los dos lados, 400 partidas):

- **1,44 selects `(1,8)` por partida y jugador**, = **4,31% de todas nuestras decisiones**
  (en la muestra de ladder era el 1,4%). Es decir, tres veces más frecuente que la media.

---

## 3. La regla implementada

`research/agentes/heuristico_descartes.py` = copia exacta de `heuristico.py` (que NO se
toca: pilota los dos envíos vivos) con un único cambio de política, la rama de coste de
`_elige_cartas` (`area == 2` con `effect`). Interruptor: `HD_DESCARTES=0` → v2 exacto.

**El defecto de v2**: reutiliza `_util`, que es una utilidad para **buscar** en el mazo
(Pokémon 3,0 + daño/1000 + hp/10000; energía 2,5 si falta, 1,0 si no; supporter de robo
2,0; «search» 1,5; **todo lo demás 0,5**) y la invierte para decidir qué se sacrifica.
Consecuencias medidas en los replays: descartamos Pokémon el **3,0%** de las veces
cuando el experto lo hace el **22,2%** (y la disponibilidad es 21,8%), y en cambio
tiramos Boss's Orders el 80,2% (experto 43,5%), Night Stretcher el 87,0% (experto 26,6%)
y Enhanced Hammer el 97,4% (experto 73,0%). Además el empate entre las muchas cartas de
0,5 lo rompe el índice de la mano, que es arbitrario: **de ahí el acuerdo al nivel del azar**.

**La utilidad nueva** (`_utils_descarte`) puntúa *cuánto duele tirar cada carta*:

| valor | carta |
|---|---|
| 9,0 | pieza de evolución cuya base ya está en juego (jugable YA) |
| 6,5 / 4,0 | evolución con su base en la mano / evolución huérfana |
| 6,0 / 2,5 | básico jugable con hueco en banca / con la banca llena |
| 4,0 | energía que le falta a un atacante propio para su mejor ataque |
| 3,2 / 2,0 | buscador con el setup a medias / con el setup hecho |
| 2,6 / 2,0 / 1,8-1,4 | supporter de robo / tool / estadio |
| 1,0 | energía sobrante |
| **0,2** | **carta que nuestra propia política no puede jugar nunca** |
| **0,15** | **energía básica sobrante habiendo reciclador en mesa** |

Dos piezas merecen justificación porque son específicas y se verificaron:

1. **«Carta muerta» (0,2)**: `_jugable_por_politica` pregunta si `_fase_principal` tiene
   alguna rama capaz de devolver esa carta. Los items solo salen por el paso 5
   (`"search" in trainer_effect`) y los supporters por el paso 6 (`"draw"`/`"search"`).
   Verificado carta a carta sobre nuestras listas: en **mega-lucario son 10 de 60**
   cartas que el agente **no puede jugar jamás** — Switch ×2, Night Stretcher ×2,
   Premium Power Pro ×2, Boss's Orders ×2, Tarragon ×2. En hops-snorlax son 6
   (Switch ×2, Night Stretcher ×2, Boss's Orders ×2). Tirarlas es gratis.
2. **Reciclador (0,15)**: se detecta en tiempo real buscando un Pokémon propio (en juego
   o en mano) cuyo texto de ataque/habilidad contenga `discard pile` + `attach` + `energy`.
   En mega-lucario existe y es el motor de la baraja: **Mega Lucario ex — Aura Jab**
   («Attach up to 3 Basic {F} Energy cards **from your discard pile** to your Benched
   Pokémon») y **Regirock ex — Regi Charge** («Attach up to 2 Basic {F} Energy cards
   **from your discard pile** to this Pokémon»). Con uno de ellos en juego, descartar una
   {F} básica no la pierde: **la carga**. Comprobado que la rama no está muerta: el
   catálogo del motor (`AllAttack` de `libcg.so`) sí trae el campo `text` (verificado en
   partida real: atk 982 y 628). En hops-snorlax no hay reciclador y la energía se queda
   en 1,0, como debe.

### Lo que la evidencia NO respaldó (y está en el código de todos modos)

Honestidad sobre dos supuestos que el censo contradice:

- **Duplicados**: el código multiplica la 2ª/3ª copia por 0,45/0,25 (0,7/0,5 en Pokémon).
  Los expertos **no hacen eso**: la tasa de descarte es plana con el número de copias en
  mano — 44,7% con 1 copia, 45,3% con 2, 49,6% con 3, 44,6% con 4. «Tirar duplicados»
  era una intuición nuestra, no un patrón del campo.
- **Proteger Pokémon**: el experto descarta Pokémon exactamente a la par de su
  disponibilidad (22,2% descartados / 21,8% disponibles), o sea que no los protege. La
  regla nueva los sigue poniendo en la banda alta (6,0–9,0). Es una desviación
  deliberada respecto al experto, pero **el experto no es el objetivo** (r = −0,028).

---

## 4. Medición — el gate

Legalidad primero (`probe_descartes.py --legalidad 400`, mega-lucario en ambos lados):

| métrica | resultado |
|---|---|
| partidas | 400 |
| estados DONE / INVALID | **800 / 0** |
| `FALLBACKS` (excepción, ilegal, select desconocido, fase sin acción) | **0 / 0 / 0 / 0** |
| `CASOS_RAROS` | ninguno |

**CERO ilegales en 400 partidas.** Requisito cumplido.

### Dirección (acuerdo con el experto, `acuerdo_descartes.py`, 1.000 episodios)

Comparado **por conjunto de cartas**, no por índice (elegir la otra copia de la misma
carta no es un desacuerdo):

| agente | acuerdo exacto (n=2.263) | cartas acertadas (n=6.430) |
|---|---|---|
| v2 | 25,6% | 50,0% |
| descartes | **25,4%** | **50,2%** |

Es decir: **la regla nueva no se parece más al experto**. (Con una muestra pequeña de 120
episodios parecía +3,1 pp; se evaporó al ampliar a 1.000. Buen recordatorio de por qué el
gate es la báscula y no una corazonada sobre 200 casos.) Ojo con interpretarlo: el corpus
son barajas ajenas, y la regla es deliberadamente específica de la nuestra (cartas
muertas, reciclador), así que este número mide poco de lo que la regla intenta hacer.

### El gate: arena, mega-lucario en los dos lados, `heuristico_descartes` vs `heuristico`

| n | tasa A | IC95 | veredicto |
|---|---|---|---|
| 600 | 0,500 | [0,460, 0,540] | sin diferencia significativa |
| 1500 | 0,477 | [0,452, 0,503] | sin diferencia significativa |
| **agregado 2.100** | **0,484** | **[0,463, 0,505]** | **no supera el gate** |

(Se amplió a n=1500 porque el n=600 cayó exactamente en 0,500, dentro de la banda de
reevaluación. El agregado suma las dos tiradas, independientes y con la misma configuración.)

---

## 5. Veredicto: NEGATIVO. La regla no entra.

El gate es IC95 con el límite inferior por encima de 0,5. Aquí el límite inferior es
**0,463** sobre 2.100 partidas, y la estimación puntual está por **debajo** de 0,5. La
regla de descarte queda **medida y descartada**; `heuristico_descartes.py` se conserva
como control reproducible (`HD_DESCARTES=0/1`), no como candidata a envío.
`heuristico.py` (v2) sigue intacto y pilotando los dos envíos vivos.

Es el **sexto** precedente de mejora «obvia» que mide empate o peor, junto a ISMCTS
(0,529), ISMCTS+red de valor (0,487), retirada (0,476), gusting (0,495) y greedy sobre la
red de valor (0,160). El patrón se repite: dirección plausible, evidencia de brecha
grande contra el experto, y cero efecto en la báscula.

### Por qué no ganó — la explicación es del tamaño del hueco, no del signo

No es que la regla elija mal: es que **en mega-lucario no había casi nada que ganar**.
`_util` de v2 puntúa con 0,5 todo lo que no es Pokémon / energía / robo / buscador, y
resulta que en esta baraja **ese cajón de 0,5 coincide casi exactamente con las 10 cartas
que nuestra política no puede jugar nunca** (Switch, Night Stretcher, Premium Power Pro,
Boss's Orders, Tarragon). O sea: v2 ya estaba tirando basura, por accidente. La regla
nueva tira la otra cosa gratis de la baraja (energía {F} sobrante habiendo reciclador).
Dos formas distintas de pagar un coste con algo que no duele → mismo resultado.

Corolario para no repetir el error: **una brecha grande de acuerdo con el experto no
implica headroom**. En `(1,8)` el acuerdo era 10,8% contra 10,7% de azar, la brecha más
escandalosa del diagnóstico, y el techo real era ~0. El acuerdo mide *«elijo lo mismo»*;
lo que importa es *«cuánto cuesta elegir distinto»*, y con 19 energías y 10 cartas
muertas en una mano de 7, ese coste es casi cero. Esto probablemente aplique también a
`(1,13)`/`(1,14)`/`(1,16)`, que además ni siquiera son nuestros (§2).

### Lo que sí queda como valor permanente

1. `motor-mecanica.md` corregida: `(1,8)` no es «elegir 3 de la mano», y `N` es variable
   (2 en Ultra Ball, hasta 6 en Xerosic). Un agente futuro que asumiera N=3 se rompería.
2. **8.244 de las 11.071 decisiones «aleatorias» del diagnóstico no son nuestras**
   (Munkidori, Dragapult ex, Wally's Compassion son 100% PROPIO y no están en nuestras
   listas). El diagnóstico las contaba como deuda propia; no lo son. Ese backlog se cierra.
3. `(1,3)` mezcla dos decisiones de signo opuesto bajo la misma forma, distinguibles por
   `effect is None`. Explotado en §8 — y **medido negativo**. Ojo con la etiqueta:
   esos 3.691 casos NO son la promoción tras KO (que es `(1,4)`, 4.391 casos).
4. `probe_descartes.py`: legalidad + frecuencia real de un contexto en NUESTRAS partidas,
   reutilizable con `--agente`. Fue lo que reveló que `(1,8)` pesa 4,31% con mega-lucario
   frente al 1,4% de la media de la ladder — priorizar por la ladder habría mentido.

---

## 6. Extra medido aparte: `(1,7)` búsqueda en mazo

Mismo método sobre el otro contexto flojo, que es **mucho más grande**: 23.509 decisiones
(**15,6% del total**) con 50,4% de acuerdo. `research/agentes/heuristico_busqueda.py`
(interruptor `HB_BUSQUEDA=0` → v2 exacto) suma **jugabilidad** a `_util` al elegir qué
sacar del mazo: +2,0 si el Pokémon se puede poner YA (básico con hueco, o evolución cuya
base está en juego) y −1,5 si no; +2,0 a la energía solo si aún no adjunté este turno y
alguien la necesita; −1,5 al trainer que nuestra política no puede jugar; −0,8 si ya
tengo una copia en la mano. El defecto que corrige: v2 saca **siempre Mega Lucario ex**
aunque no haya ningún Riolu en juego que evolucionar — una carta muerta en la mano.

| medida | resultado |
|---|---|
| legalidad (400 partidas) | **800 DONE / 0 INVALID**, 0 fallbacks, 0 casos raros |
| arena n=600 (exploratoria) | 0,540 IC95 [0,5000, 0,5795] |
| arena n=1500 (confirmatoria) | 0,515 IC95 **[0,4900, 0,5406]** |
| agregado 2.100 | 0,5224 IC95 [0,5010, 0,5437] |
| **arena n=3000 (decisoria, muestra fresca)** | **0,538 IC95 [0,520, 0,556] → PASA** |

**Cuidado con el agregado.** Cruza el 0,5 por 0,001, pero está contaminado por parada
opcional: la tirada de 1.500 se lanzó *porque* la de 600 salió bien, así que sumarlas
infla el resultado. La tirada limpia — la confirmatoria de 1.500 por sí sola — **no pasa
el gate** (límite inferior 0,4900). Por eso se tiró una tercera muestra, fresca e
independiente, con la regla de decisión fijada de antemano: IC95 con límite inferior
> 0,5 sobre esas 3.000 partidas y nada más.

Aun así, `(1,7)` es la pista con diferencia más prometedora que deja esta tanda, y por
razones de tamaño: son **15,6% de las decisiones** (3,6× el peso de `(1,8)`), y el defecto
que corrige es concreto y comprobable — v2 saca del mazo la carta con mejores estadísticas
sin mirar si se puede jugar, y en mega-lucario eso significa acumular Mega Lucario ex en
la mano sin Riolu que evolucionar.

---

## 7. `(1,7)` PASA EL GATE — primera mejora medida que entra

Muestra fresca e independiente de **3.000 partidas**, con la regla de decisión fijada
antes de tirarla:

```
heuristico_busqueda vs heuristico (v2), mega-lucario en ambos lados, 3.000 partidas
tasa de victoria : 0,538   IC95 [0,520, 0,556]
  yendo primero  : 0,633      yendo segundo : 0,443
VEREDICTO        : A es mejor (significativo al 95%)
```

**Límite inferior 0,520 > 0,5: pasa.** Y pasa con margen, no rozando. Las tres tiradas
juntas (5.100 partidas) dan 0,5316 IC95 [0,5179, 0,5452], consistente con la decisoria.

Es **+3,8 pp de winrate** contra el piloto de los dos envíos vivos, y rompe la racha de
cinco (ahora seis, con los descartes) candidatas que medían empate o peor. Conviene
subrayar de dónde sale: **no** de parecerse más al experto, sino de dejar de meterse
cartas muertas en la mano.

### La ganancia es de mega-lucario, no de la política — comprobado

Repetido con **hops-snorlax**, la otra baraja viva, 1.500 partidas:

```
heuristico_busqueda vs v2, hops-snorlax en ambos lados, 1.500 partidas
tasa de victoria : 0,500   IC95 [0,475, 0,525]     VEREDICTO: sin diferencia
```

| baraja | n | tasa | IC95 | veredicto |
|---|---|---|---|---|
| **mega-lucario** | 3.000 | **0,538** | [0,520, 0,556] | **gana** |
| hops-snorlax | 1.500 | 0,500 | [0,475, 0,525] | neutro |

Exactamente **cero** en la segunda baraja, y tiene una explicación mecánica limpia: el
grueso de la regla es el término de jugabilidad de evolución (+2,0 si la base está en
juego, −1,5 si no). mega-lucario vive de la línea **Riolu → Mega Lucario ex**, así que
sacar del mazo un Mega Lucario ex sin Riolu en mesa es una carta muerta y corregirlo vale
puntos. hops-snorlax es casi toda básicos (Hop's Snorlax es básico y es el atacante
principal): ahí no hay nada que corregir, y la regla se queda en el sitio.

Traducción práctica: **no es una mejora de política general, es una mejora de
mega-lucario**. Como no hace daño en hops-snorlax y mega-lucario es la baraja que va en
serio (rating 558,3 contra 409,0 — la baraja vale +149 puntos con el mismo piloto), sigue
siendo neta positiva. Pero hay que llamarla por su nombre, porque el mecanismo predice
que **cualquier baraja de campo sin línea de evolución la verá plana**.

### Pendiente antes de tocar el envío — esto **no** es una recomendación de subir nada

1. Pasarla por el **gauntlet ponderado de campo** (`research/gauntlet.py`), no solo el
   espejo. El espejo mide contra una copia de uno mismo, que es el rival más blando
   posible frente a un cambio de política; y las barajas del campo con evolución
   (grimmsnarl, alakazam, dipplin, dragapult) son justo donde la regla debería lucir.
2. El sesgo de asiento del espejo es enorme (0,633 primero / 0,443 segundo con
   mega-lucario). `arena.py` lo cancela repartiendo asientos, pero conviene tenerlo
   presente al leer cualquier winrate de esta baraja.
3. La decisión de subir es del propietario. Los dos envíos vivos siguen pilotados por
   `heuristico.py` v2 sin tocar.

---

## 8. Extra medido aparte: la promoción del activo — y una corrección del mapa

El diagnóstico señalaba `(1,3)` «promoción del activo tras KO» (3.691 casos, 59,9% de
acuerdo) como pista viva. Se ha ejecutado, y ha dejado dos cosas: **una corrección de
identificación que vale más que la regla**, y **un negativo medido**.

Piezas: `research/replays/promocion_expertos.py` (dirección), `research/replays/corpus_promocion.py`
(corpus compacto, 800 episodios), `scratchpad/barre_promocion.py` (barrido de criterios),
`research/agentes/heuristico_promocion.py` (la regla, interruptor `HP_PROMOCION=0` → v2
exacto), `research/probe_promocion.py` (legalidad y frecuencia real), `arena.py` (el gate).

### 8.1 `(1,3)` y `(1,4)` estaban intercambiados — y `area == 5` tiene un tercer inquilino

Al medir la frecuencia real en NUESTRAS partidas salió **cero** `(1,3)` en 400 partidas.
No era un fallo del contador: es que la promoción tras KO **no es `(1,3)`**. El
discriminante no es el `effect` sino **el estado de mi activo**:

| (t,c) | `players[me].active` | dueño de las opciones | n | qué es de verdad |
|---|---|---|---|---|
| **(1,4)** | **vacío** (100%) | propia (100%) | 3.554 | **promoción tras KO** |
| (1,3) | ocupado (100%) | propia | 1.982 | cambio forzado de MI activo |
| (1,3) | ocupado (100%) | **del rival** | 953 | arrastre (Boss's Orders) |

Ni un solo `(1,4)` con activo vivo, ni un solo `(1,3)` con activo vacío, sobre 6.489
casos con ≥2 opciones. El cruce que lo cierra: el acuerdo de v2 medido por rama sobre
este corpus reproduce las filas del diagnóstico casi al decimal — **55,1% en `(1,4)`**
contra el 55,5% que el diagnóstico atribuía a «nuevo activo al retirar», y **60,2% en
`(1,3)`** (juntando sus dos mitades) contra el 59,9% que atribuía a «nuevo activo tras
KO». O sea que el diagnóstico también las tenía cruzadas, y **la promoción tras KO es la
fila de 4.391 casos, no la de 3.691**.

Y hay un tercero que ninguna nota tenía: **`(1,21)`**, objetivo en banca de un efecto de
carta. Con mega-lucario es el destino de la energía de **Aura Jab**, y sale **1,36 veces
por partida**, más que la propia promoción tras KO (1,22). Los tres caen en el mismo
`area == 5` de `_elige_cartas`, así que v2 los trata a los tres con la misma función.
`motor-mecanica.md` queda corregida (✏️ 2026-08-11b).

Consecuencia de método, otra vez la misma: **`context` no es una mecánica**. Aquí lo
robusto es despachar por `players[me].active == []` y por el `playerIndex` de las
opciones, que son estado, no numeración de huecos de carta.

### 8.2 Qué nos toca de verdad

Con mega-lucario, medido con `probe_promocion.py --legalidad 400`:

| clase de select `area == 5` | por partida | % de nuestras decisiones |
|---|---|---|
| `(1,4)` promoción tras KO | 1,22 | ~3,5% |
| `(1,21)` objetivo de Aura Jab | 1,46 | ~4,2% |
| `(1,3)` arrastre de la banca rival | **0,00** | 0% |

El arrastre es **cero** y por una razón estructural ya conocida: nuestra política no
puede jugar Boss's Orders (`_jugable_por_politica` solo saca supporters con «draw» o
«search»). Llevamos 2 copias en las dos barajas y son carta muerta. Así que el arreglo
del arrastre entra por corrección, no por ganancia — pero es un **bug real**: v2 resuelve
esos índices contra su PROPIA banca ignorando `option.playerIndex`, o sea que lee otro
Pokémon. Acuerdo con el experto 34,0%; corregido, 49,4%.

### 8.3 La regla implementada

`heuristico_promocion.py` = copia de `heuristico.py` con `_promociona`, que solo actúa en
dos casos identificados por estado (activo vacío, u opciones del rival) y devuelve `None`
en el resto — deliberadamente, para **no** tocar el objetivo de Aura Jab y que la medida
sea atribuible.

El defecto de v2: puntúa `10×energías + daño/10 + hp/100`. Las energías sueltas no son
lo mismo que poder atacar. La variable que mejor explica al experto es **`falta`**: las
energías que le faltan al Pokémon para su ataque más barato, con emparejamiento de tipo
(0 = puede atacar ya). Criterio nuevo: `-200×falta + maxHp/10 + hp/100 + daño/1000`, es
decir *el que antes pueda atacar; a igualdad, el más duro, porque va a comer el golpe*.

Barrido sobre 6.489 casos reales (`scratchpad/barre_promocion.py`):

| rama | n | v2 | binario «puede atacar» | **`falta` (elegido)** |
|---|---|---|---|---|
| `(1,4)` tras KO | 3.554 | 55,1% | 56,0% | **62,3%** |
| `(1,3)` propia | 1.982 | 72,8% | 75,8% | **76,6%** |
| `(1,3)` ajena | 953 | 34,0% | — | **49,4%** (criterio «el ex») |

Nota de honestidad sobre el arrastre: el criterio que sonaba bien —*arrastra al que no
puede contestar*— midió **39,9%**, peor que simplemente quedarse con el ex (49,4%).

### 8.4 Medición — el gate

Legalidad (`probe_promocion.py --legalidad 400`, mega-lucario en ambos lados):
**800 DONE / 0 INVALID**, fallbacks `0/0/0/0`, `CASOS_RAROS` ninguno. **Cero ilegales en
400 partidas.**

| n | tasa A | IC95 | veredicto |
|---|---|---|---|
| 600 (exploratoria) | 0,513 | [0,473, 0,553] | sin diferencia |
| **1.500 (confirmatoria, regla fijada de antemano)** | **0,488** | **[0,463, 0,513]** | **no pasa** |
| agregado 2.100 *(informativo, contaminado por parada opcional)* | 0,495 | [0,474, 0,517] | — |

**Veredicto: NEGATIVO.** La confirmatoria queda por debajo de 0,5 y su límite inferior
es 0,463. `heuristico_promocion.py` se conserva como control reproducible
(`HP_PROMOCION=0/1`), no como candidata a envío. `heuristico.py` (v2) intacto.

Es el **séptimo** precedente de mejora «obvia» que mide empate o peor: ISMCTS (0,529),
ISMCTS+red de valor (0,487), retirada (0,476), gusting (0,495), greedy sobre la red de
valor (0,160), descartes (0,484) y ahora promoción (0,488). Frente a un solo positivo,
`(1,7)` (0,538).

### 8.5 Por qué no ganó, y qué queda

El patrón de `(1,8)` se repite con un matiz. Allí no había headroom porque casi todo lo
descartable era gratis. Aquí sí hay brecha de acuerdo (+7,2 pp en la rama que nos toca) y
la frecuencia es decente (1,22/partida), pero el espejo mega-lucario contra mega-lucario
es un banco de pruebas pobre para esta decisión concreta: **la banca es casi siempre
homogénea** — Regirock ex y Mega Lucario ex, ambos de coste bajo en {F} y ambos duros —
así que «el que antes puede atacar» y «el que más energías tiene» coinciden a menudo, y
cuando no coinciden la diferencia es de un turno de carga en una baraja que recarga desde
el descarte con Aura Jab. El mecanismo predice que esta regla debería lucir más en
barajas con banca heterogénea (básicos frágiles junto a atacantes caros), y el espejo no
tiene ninguna.

Lo que queda vivo de esta tanda, por orden de tamaño:

1. **`(1,21)`, el objetivo de Aura Jab: 1,46 selects por partida, más que la promoción**,
   y hoy lo decide una función pensada para «elegir nuevo activo». Nadie lo ha mirado
   nunca porque no aparecía en ninguna tabla. Es el candidato más gordo que deja esto.
2. El arreglo del `playerIndex` en el arrastre es correcto y está medido en acuerdo, pero
   **no se puede cobrar** hasta que la política sepa jugar Boss's Orders — que es otro
   hueco: 2 copias de carta muerta en las dos barajas.
3. Pasar `(1,7)` (la única que pasó el gate) por el **gauntlet de campo** antes de tocar
   el envío, tal como dice §7.
