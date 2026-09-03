# Catálogo de errores: qué separa a un jugador malo de uno bueno

Fecha: 2026-08-10; **segunda pasada 2026-08-11 (verificación empírica)**. Tema: los fallos
típicos del jugador flojo, contrastados **uno a uno** contra lo que hace nuestra política
greedy (`research/agentes/heuristico.py`, v2, el piloto de los envíos vivos) y contra el pool
real de 1.267 cartas (`research/cards_clean.csv`).

> **Qué cambió en la segunda pasada.** La primera versión estimaba valores a ojo y dejaba tres
> preguntas abiertas. La pasada del 11-ago las midió sobre el corpus real de la ladder
> (`data/replays/pokemon-tcg-ai-battle-episodes-2026-08-08.zip`, 4.669 episodios) y sobre el
> pool. Resultado: **dos verificaciones cerradas, dos entradas corregidas (E10 y E13 decían
> algo falso), cinco errores nuevos (E16–E20) y, el hallazgo grande, que el agente
> físicamente no puede jugar el 73% de los Items y el 41% de los Supporters del pool**
> (E16). Todo lo medido va marcado `MEDIDO` con su n; lo que sigue siendo juicio, no.

**Por qué existe esta nota**: cuatro palancas algorítmicas seguidas han dado empate — ISMCTS
0,529 · ISMCTS+valor 0,487 · retirada 0,476 · gusting 0,495 (`agente-heuristico-v3.md`,
`agente-mcts.md`). La hipótesis de trabajo pasa a ser que no falta búsqueda, falta
**conocimiento de juego**. Esta nota es el inventario de ese conocimiento en forma de
errores detectables.

## Cómo leer esto

Cada entrada lleva: **(a)** el error tal y como lo enuncia la literatura competitiva,
**(b)** el razonamiento del jugador, **(c)** si NUESTRO agente lo comete y por qué línea de
código, **(d)** la condición detectable en un log de partida, **(e)** valor estimado.

Etiquetas de alcance:
- `PRINCIPIO` — regla general del juego, aplica al simulador tal cual.
- `FORMATO` — depende del formato/pool concreto; verificado contra nuestras 1.267 cartas.
- `NO-APLICA` — cierto en papel/torneo, falso o irrelevante aquí (se explica por qué).

Los valores estimados son **juicio, no medida**. Escala: ALTO ≈ >3 pts de winrate esperados
contra el gauntlet, MEDIO ≈ 1-3 pts, BAJO ≈ <1 pt. Todo lo marcado ALTO/MEDIO debería pasar
por `arena.py` antes de creérselo, igual que se hizo con retirada y gusting.

## Aviso sobre el campo

El censo que circula en los briefings (Mega Lucario ~42%, Alakazam ~17%, aggro tipo ejemplo
~17%, Cynthia's Garchomp ~8%) **está desfasado**: era ruido de 12 replays. El censo bueno son
18.674 barajas de la ladder (`baraja-vs-campo.md`, 2026-08-10): Grimmsnarl 31,2% · Alakazam
18,2% · Lopunny/Froslass 12,8% · Dragapult 8,2% · Kangaskhan/Crustle 6,9% · Ogerpon 5,0% ·
**Mega Lucario 4,0%** · Dipplin 3,5%. La baraja de ejemplo del motor: 0 de 18.674. Las
prioridades de abajo usan el censo bueno.

Dato medido para esta nota: **8 de 8 barajas del gauntlet llevan gusting** (Boss's Orders ×2-4;
c7 además 2 Hariyama). O sea, cualquier Pokémon que pongamos en banca es alcanzable por el
100% del campo. Eso sube el precio de todos los errores de banca de esta lista.

---

# PARTE 1 — Catálogo de errores

Ordenado por valor esperado **para nosotros**, no por importancia en el juego humano.

---

## E1. Atacar con el mayor daño disponible en vez del ataque que prepara el turno siguiente

`PRINCIPIO` + `FORMATO`. **Valor: ALTO en 4 de nuestras 9 barajas, NULO en la que está viva.**

**(a) El error.** Elegir siempre el ataque de más daño de la carta, ignorando que el ataque
grande suele llevar lastre (bloqueo del turno siguiente, descarte de energía propia,
autodaño) y que el ataque pequeño suele ser el motor del mazo.

**(b) Razonamiento del jugador.** El daño no es el objetivo; los premios lo son. Si el
ataque barato ya mata, el ataque caro no compra nada y sí paga: «forcing a knockout to take
an additional turn can often be a boost to a deck in need of the improved prize trade»
(<https://www.justinbasil.com/guide/damage>). Y si el ataque barato además acelera energía,
está comprando el turno siguiente: «if you see a knockout coming next round, start attaching
Energy to the next attacker now» (<https://levelsptcg.com/pokemon-tcg-turns/>).

**(c) Nuestro agente lo comete por construcción.** `heuristico.py`, paso 8 de
`_fase_principal`:

```python
kills = [(i, o) for i, o in ataques if obj and eficaz(o) >= (obj.get("hp") or 1)]
elegidos = kills or list(ataques)
return [max(elegidos, key=lambda t: eficaz(t[1]))[0]]
```

`max(...)` **entre los que matan**: overkill garantizado. Y si nadie mata, otra vez el de más
daño. No lee el texto del ataque: ni lastre, ni aceleración, ni efectos.

Medido sobre el pool: **64 de las 436 cartas con ≥2 ataques** tienen el ataque de más daño
con lastre y una alternativa sin él. En NUESTRAS listas y en el gauntlet:

| Baraja | Trampa concreta |
|---|---|
| `mega-lucario.csv`, `c7-lucario-campo.csv` | **Mega Lucario ex 678**: greedy usa Mega Brave (270, {F}{F}, «can't use Mega Brave next turn») en vez de **Aura Jab (130, {F}, adjunta hasta 3 {F} del descarte a la BANCA)**. Aura Jab *es* el motor de energía del arquetipo A1. |
| `ns-zekrom.csv` | **N's Zekrom 906**: greedy usa Rampaging Thunder (250) → «During your next turn, this Pokémon can't use **attacks**». Bloqueo total. Como el v2 nunca retira, el turno siguiente es un turno en blanco. Shred (70, 3E) queda sin usar. |
| `abomasnow-plus.csv` | **Kyogre 721**: greedy estima Riptide («20×») en 20×3=60 y elige Swirling Waves (130) que **descarta 2 energías propias**; se desarma solo. |

Matiz honesto: en Mega Lucario el propio lastre fuerza la alternancia (bloqueado Mega Brave,
el turno siguiente solo hay Aura Jab). El fallo no es «nunca acelera», es «**nunca elige
cuándo** acelerar»: acelera solo los turnos en que no le queda otra, y nunca justo antes del
turno en que hará falta.

Y el caso donde el error vale cero: **`hops-snorlax`** (la lista del envío 55407312) monta
Hop's Snorlax 304 con un único ataque, Dynamic Press. No hay elección → E1 no puede
manifestarse en el envío actual. **Esto importa para no engañarse con la medida**: arreglar
E1 no moverá la ladder de hoy; lo que desbloquea es la evaluación honesta de otras barajas.

**(d) Detección en log.** En cada select `(0,0)` con opciones `type 13`: calcular daño
efectivo de todas las opciones ofrecidas. Marcar cuando **≥2 opciones alcanzan los HP del
activo rival** y la elegida tiene en su texto `can't use` / `discard N Energy from this
Pokémon` / `does N damage to itself` y otra no. Métrica: `overkill_ratio = overkills /
turnos con KO disponible`. Segunda métrica sin necesidad de KO: `usos_del_ataque_lastre /
usos totales` por carta.

**(e) Valor.** ALTO (>3 pts) en mega-lucario, ns-zekrom, okidogi, abomasnow; **0 en
hops-snorlax**. Coste: ~15 líneas (penalizar en `eficaz` los ataques con lastre y desempatar
los KO por coste ascendente). Es la mejora de mejor relación valor/riesgo del catálogo.

---

## E2. Los ataques de daño 0 son invisibles: el agente no ve los ataques de preparación

`FORMATO`. **Valor: ALTO en 3 barajas — y contamina el ranking del laboratorio.**

**(a) El error.** Tratar «ataque» como sinónimo de «daño». Muchos ataques hacen 0 y su
función es buscar energía, acelerar o buscar Supporter.

**(b) Razonamiento del jugador.** Un ataque de setup gasta el turno pero compra dos turnos de
daño doble. Es la versión-ataque del principio de secuenciación: acciones que dan recursos
antes que acciones que comprometen.

**(c) Nuestro agente.** `_dmg()` devuelve 0 para esos ataques, así que `max(..., key=eficaz)`
solo los elige **cuando son la única opción legal**. Cartas afectadas en nuestras listas:

- `okidogi.csv` — **Okidogi ex 138 · Poisonous Musculature** [●, daño 0]: busca 2 {D} del
  mazo, se las adjunta y **se autoenvenena**. Chain-Crazed hace 130 y **130 más si está
  envenenado** (260, o 300 con Binding Mochi). Si el Okidogi llega con 3 energías puestas
  (Janine's Secret Art acelera), el greedy va directo a Chain-Crazed **a 130: la mitad del
  daño del arquetipo**, para siempre, porque nunca se envenena.
- `okidogi.csv`, `tr-mewtwo.csv` — **Team Rocket's Murkrow 463 · Deceit** [●, daño 0]: busca
  un Supporter. Invisible.
- `mega-lucario.csv` — **Regirock ex 447 · Regi Charge** [●, daño 0]: adjunta 2 {F} del
  descarte a sí mismo. Las 4 Regirock de A1 están ahí exactamente para eso. Invisible.
- `c5-kangaskhan-crustle.csv` (rival) — **Dwebble · Ascension**: busca su evolución.

**(c-bis) La consecuencia grave.** `lab-barajas.md` ya documentó este mismo patrón un nivel
más arriba: «El heurístico actual IGNORA el type 10 → toda baraja cuyo motor es una habilidad
juega sin su motor en las medidas». Se arregló para habilidades (v2). **La misma clase de
sesgo sigue viva para los ataques**: el ranking de barajas se midió con un piloto que no sabe
usar el motor de okidogi, ni el de regirock, ni el de TR-Murkrow. Cualquier decisión de
selección de baraja tomada con ese ranking está contaminada — y Deck Score es el 20% del
premio.

**(d) Detección.** Contar selects `(0,0)` donde se ofrece una opción `type 13` cuyo ataque
tiene `damage == 0` y texto con `attach`/`search your deck`, y la elegida es otra. Cruzar con
«¿el Pokémon propio tenía energía suficiente para su ataque caro?». Métrica:
`setup_attacks_ofrecidos / setup_attacks_usados`.

**(e) Valor.** ALTO para okidogi (duplica el daño del arquetipo) y mega-lucario. Coste:
clasificar el texto del ataque igual que ya se hace con las habilidades en
`_habilidad_activable` — el patrón ya está escrito en el mismo fichero.

---

## E3. No contar los premios: no ver la línea letal

`PRINCIPIO`. **Valor: MEDIO-ALTO, coste ridículo.**

**(a) El error.** Atacar «al que se pueda» sin mirar el marcador. El jugador de torneo hace
*prize mapping*: planifica la secuencia de KOs desde el principio, «rather than making
reactive decisions», y usa reglas del tipo «always count opponent's prizes left — if 2
remain, prioritize 1-prize snipes to force bad trades»
(<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-mapping-guide-2026>).
SixPrizes lo cataloga como misplay *de desarrollo*: «Ignoring Prize dynamics — not respecting
the 6-Prize race structure» (<https://sixprizes.com/2012/12/13/and-ill-pass-a/>).

**(b) Razonamiento.** La partida no se gana matando; se gana con el sexto premio. Con 2
premios restantes, un KO a un ex gana la partida y un KO a un básico no. Con 1 premio, gana
cualquier KO — incluido uno en la banca rival, que exige gustear.

**(c) Nuestro agente: ciego total.** `grep -c prize research/agentes/heuristico.py` → **0**.
La política **no lee el marcador en ningún punto**. El dato está en la observación y es
gratis: `len(obs["current"]["players"][i]["prize"])` = premios que le quedan por robar a `i`
(el contenido es `null`, la longitud no; `motor-mecanica.md` §4).

**(d) Detección.** Por cada turno propio: `mios = len(cur["players"][me]["prize"])`. Marcar
`LETAL_PERDIDA` si existía una combinación de KOs alcanzable este turno (activo rival, o de
banca vía gust) cuyo valor en premios ≥ `mios` y no se ejecutó. Marcar también
`REGALO_LETAL`: terminamos el turno con el rival a `k` premios y le dejamos en mesa un
objetivo que se los da todos.

**(e) Valor.** MEDIO-ALTO. Ojo a la honestidad: el greedy ya prefiere el KO cuando puede, así
que la ganancia **no** está en «rematar el activo», está en dos sitios concretos:
1. **Gusting solo para letal.** El v3 midió el gusting general en 0,495 (neutro) con una
   puerta que decía «si ya puedo matar de frente, no gasto la carta». Nunca se probó la
   versión estrecha: *gustear cuando y solo cuando eso cierra la partida este turno*. Es un
   disparador raro y de valor máximo — exactamente el perfil que una medida agregada de
   0,495 esconde.
2. **Elegir el ataque por premios, no por daño**: con 2 premios restantes, matar al ex de la
   banca en vez de al básico de delante.
Coste: ~20 líneas. Es la mejora más barata de la lista.

> **Ampliado 2026-08-11 → ver E20.** La ceguera al marcador no solo cuesta la línea letal:
> **desactiva una familia entera de cartas del pool** cuyo texto está condicionado a los
> premios (Briar, Counter Gain, Rosa's Encouragement, Lacey, Legacy Energy, Kingambit…),
> incluida **Lillie's Determination 1227, que la baraja de ejemplo lleva ×4**. Eso mueve parte
> del valor de E3 desde la ladder hacia Deck Score (20% del premio).

---

## E4. Adjuntar la energía al Pokémon equivocado (y demasiado pronto)

`PRINCIPIO`. **Valor: ALTO — es el cuello de botella ya diagnosticado.**

**(a) El error.** Poner la energía del turno en el atacante activo por defecto. La
literatura lo enuncia de dos formas complementarias:
- «Attaching Energy to the Wrong Pokemon Too Early — early-game Pokemon get knocked out
  quickly, causing invested energy to be lost»
  (<https://pixel-hub.co.uk/blogs/news/12-beginner-mistakes-in-pokemon-tcg>).
- «Energy attachments should typically occur near the end of your turn, not early.
  Attaching energy prematurely can lock you into a suboptimal strategy»
  (<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-advanced-sequencing-guide-grandmaster-playbook>);
  «Attaching Energy is one of the most significant and irreversible commitments»
  (<https://tcgprotectors.com/blogs/pokemon-deck-guides/pokemon-tcg-intermediate-strategy-guide>).
- Y la versión positiva: «build your main attacker safely on the bench so that when the
  active Pokémon goes down, they're ready to respond immediately instead of scrambling».

**(b) Razonamiento.** La energía adjunta a un Pokémon que muere el turno siguiente se va al
descarte con él. Una energía por turno es el regulador de tempo del juego entero: enterrar
una es perder un turno de desarrollo.

**(c) Nuestro agente.** Paso 3 de `_fase_principal`, criterio de orden:

```python
i = min(cands, key=lambda t: (0 if t[2] > 0 else 1,          # le falta energía
                              0 if t[1].get("inPlayArea") == 4 else 1,  # el ACTIVO primero
                              -t[3], t[2]))[0]
```

El activo tiene prioridad explícita sobre la banca, **sin mirar si el activo muere este
turno**. Y `faltan` se calcula contra el ataque **más caro** (`max(...)` de costes), no
contra el que se va a usar.

Esto ya está medido como el cuello de botella real del proyecto, aunque no se etiquetó como
error de juego. `agente-heuristico-v3.md`: de 400 oportunidades de retirada, 20 vetos por «el
relevo llega desarmado»; en iono-bellibolt, **288 de 542**. Conclusión textual de esa nota:
«La banca de esta política se llena de básicos sin energía. La siguiente palanca no es
táctica, es de **desarrollo de banca**». Esta entrada es el nombre que le da la literatura y
E1/E2 son la mitad de la causa (el motor de aceleración nunca se enciende).

**(d) Detección.** Dos métricas sobre el log:
- `energia_enterrada` = energías adjuntas (log type 11) a un Pokémon que es noqueado en el
  turno siguiente del rival ÷ total de energías adjuntas. En un jugador bueno debería ser
  baja salvo cuando la inversión ya rentó.
- `banca_armada` = fracción de turnos en los que existe en banca al menos un Pokémon capaz de
  atacar YA si fuera promovido. La retirada del v3 medía justo esto de refilón; se puede
  contar sin activar la retirada.
- Señal de secuenciación: posición de la adjunción dentro de la cadena `(0,0)` del turno.

**(e) Valor.** ALTO. Regla candidata mínima y barata: *si el activo muere a la mejor amenaza
rival con una energía más, la energía del turno va al mejor candidato de banca que pueda
atacar tras la promoción*. Es el reverso exacto del cálculo `_dano_contra(..., extra=1)` que
ya está escrito y verificado en `heuristico_v3.py` — se reutiliza la función, se cambia el
consumidor.

---

## E5. Secuenciación: buscar antes de robar, y comprometer antes de mirar

`PRINCIPIO`. **Valor: MEDIO.**

**(a) El error.** Orden equivocado dentro del turno. El error canónico citado en todas
partes: «Playing Ultra Ball before Professor's Research, then discarding the searched card»
(<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-advanced-sequencing-guide-grandmaster-playbook>).
Los tres principios que lo generan: **maximizar información**, **minimizar compromiso**,
**negar información al rival**. La versión de la guía intermedia: «Golden Rule: gain as much
information as possible before you commit to an action. Draw Before Search».

**Matiz — las fuentes no coinciden y el matiz es el que hay que llevarse.**
<https://levelsptcg.com/pokemon-tcg-turns/> recomienda «play Items first ... fire them off
early» porque los Items no tienen límite por turno. La reconciliación honesta: lo invariante
no es «Items antes» ni «Supporter antes», es **el orden por reversibilidad** — primero lo que
da información sin comprometer nada (habilidades de robo, Supporter de robo llano), luego lo
que compromete poco (Items de búsqueda, ya sabiendo qué falta), y al final lo irreversible
(energía, ataque). Y hay una excepción dura: ante un Supporter que **baraja o descarta la
mano** (Iono, Judge, Lillie's Determination 1227, Team Rocket's Ariana 1216), primero se
juega la mano y después se refresca.

**(c) Nuestro agente.** El orden fijo de `_fase_principal` es:
`1 bancar → 2 evolucionar → 2b habilidad de robo → 3 ENERGÍA → 3b habilidad de aceleración →
4 tool → 5 item de búsqueda → 6 Supporter de robo → 7 estadio → 8 atacar → 9 fin`.

Dos violaciones directas:
- **La energía (3) va antes que la búsqueda (5) y el robo (6)**: se compromete el recurso más
  irreversible del turno antes de ver las cartas que iban a decidir dónde ponerlo. Es
  literalmente el error «attach energy early, locking yourself into one strategy».
- **La búsqueda (5) va antes del Supporter de robo (6)**: es el «Ultra Ball antes de
  Professor's Research» del manual, con nombre y apellidos.

Lo que sí hace bien: activar habilidades de robo (2b) antes de gastar recursos, y condicionar
el Supporter de robo a mano corta (≤4 cartas no-energía), que es la puerta correcta para
Lillie's Determination.

Tercer defecto, más sutil: el paso 5 recorre `por_tipo.get(7)` y devuelve **el primer** item
con «search» en el texto, no el mejor. Ultra Ball 1121 (descarta 2) se juega igual que Poffin
1086 (gratis), sin mirar si hay algo que descartar sin dolor ni si hace falta el objetivo.

**(d) Detección.** Reconstruir la cadena `(0,0)` de cada turno (las acciones del turno llegan
como selects encadenados) y comprobar el orden de: log 11 (energía), log 10 (trainer), tipo
de trainer. Marcar `SEQ_ENERGIA_PRONTO` si hay un log 11 antes del primer Supporter de robo
del turno; `SEQ_BUSQUEDA_ANTES_ROBO` si un Item de búsqueda precede a un Supporter de robo en
el mismo turno; `SEQ_REFRESCO_CON_MANO_LLENA` si se juega un Supporter que baraja la mano
teniendo ≥2 cartas jugables sin jugar.

**(e) Valor.** MEDIO. Reordenar `_fase_principal` (mover el bloque 3 detrás del 6) es un
cambio de 4 líneas y **cero riesgo de ilegalidad**, porque el motor vuelve a ofrecer el
option de energía en la siguiente iteración de la cadena mientras `energyAttached` sea falso.
Es la primera prueba que yo lanzaría: barata, aislable y con literatura sólida detrás.

---

## E6. Bajar todos los básicos posibles a la banca

`PRINCIPIO` + `FORMATO`. **Valor: depende de la baraja — ALTO con ex, BAJO/NEGATIVO con
single-prize.**

**(a) El error.** Llenar la banca porque se puede. «Do not bench a multi-prize Pokémon unless
you absolutely have to or plan to use it that turn, as **every Pokémon you bench is a
potential part of your opponent's prize map**» (<https://www.justinbasil.com/guide/main-attacker>).
«Avoid benching Pokémon unnecessarily, as it gives opponents targeting information and
potential prize opportunities»; «Benching multi-prize Pokémon unnecessarily, telegraphing
your plans» (guía de secuenciación, URL arriba). Y desde el lado del atacante: «Damaged
Pokémon and otherwise vulnerable Pokémon are prime targets for gusting»
(<https://www.justinbasil.com/guide/gusting>).

**(b) Razonamiento.** Cada cuerpo en banca es (i) premios regalados si lo arrastran y matan,
(ii) información sobre tu plan, (iii) un objetivo que hace *rentable* el Boss's Orders del
rival. El contrapeso es real: quedarse sin Pokémon en juego **es derrota inmediata** (motor
verificado, `reason 3` en `motor-mecanica.md` §5) y sin banca no hay relevo tras un KO.

**(c) Nuestro agente.** Paso 1: `if len(bench) < 4: baja el mejor básico`. Rellena a 4
siempre, lo antes posible, y escoge por `_util` — que puntúa **más alto al que más pega**, o
sea, tiende a bancar justo el atacante caro que no querías enseñar.

**(c-bis) El matiz que hay que llevar al writeup.** «Banca menos» **no** es una regla
universal, y aplicarla a ciegas nos empeoraría:
- `hops-snorlax` (la lista viva) es **single-prize entera**: cada cuerpo en banca cuesta 1
  premio, el rival necesita 6 KOs, y bancar rápido es correcto. Aquí E6 casi no existe.
- `mega-lucario` regala **3 premios por Mega ex** (regla del papel; ver §Pendientes): bancar
  cuatro Mega Lucario es entregar la partida al primer Boss's Orders.
La regla correcta es **de responsabilidad en premios, no de conteo**: banca todo lo que sea
single-prize; baja el multi-premio solo el turno que lo vas a usar o cuando ya no queda
alternativa.

**(d) Detección.** `premios_en_banca` = suma del valor en premios de los Pokémon de banca en
cada turno. `gust_castigado` = veces que el rival juega un gusting (log 10 con cardId en el
conjunto gust) y el objetivo arrastrado muere ese mismo turno; desglosado por «¿estaba ese
Pokémon en banca por necesidad o de relleno?» (proxy: `energies == 0` y `appearThisTurn`).
Contra este campo la señal es fuerte: **8/8 barajas del gauntlet llevan gust** (2-4 copias).

**(e) Valor.** ALTO en las listas con ex/Mega ex, BAJO en hops-snorlax. Riesgo si se aplica
mal: derrota por mesa vacía. Puerta obligatoria: nunca bajar de 2 Pokémon en juego.

---

## E7. Quemar recursos clave demasiado pronto

`PRINCIPIO`. **Valor: MEDIO.**

**(a) El error.** Gastar la carta que gana la partida por gastarla. «Wasting Resources Too
Early: using powerful cards immediately without considering long-term impact»
(<https://pixel-hub.co.uk/blogs/news/12-beginner-mistakes-in-pokemon-tcg>). «Don't
over-extend early: avoid playing every card available in your opening turns. Holding
resources protects against opponent disruption supporters»; «Boss's Orders is often held as
a late-game resource to secure game-winning plays»
(<https://tcgprotectors.com/blogs/pokemon-beginners-guide/pokemon-tcg-resource-management-master-guide-2026>).
SixPrizes lo lista como misplay de desarrollo: «Unnecessary card play — playing cards like N
without strategic benefit».

**(b) Razonamiento.** Hay una sola ranura de Supporter por turno y un solo ACE SPEC por
baraja (verificado en el motor: `29 ACE SPEC` en el pool, máx. 1). Gastar Boss's Orders para
arrastrar algo que no vas a matar convierte una carta que cierra partidas en un cambio de
activo gratis para el rival.

**(c) Nuestro agente.** Dos comportamientos:
- El v2 **no gustea nunca**, así que no quema Boss's Orders... porque no la usa jamás. El
  problema no es quemarla pronto, es que la carta es papel muerto y encima ocupa ranuras.
- Sí quema los Items de búsqueda: paso 5 juega el primer Item con «search» que aparezca,
  siempre, sin objetivo definido y sin mirar el coste de descarte.

**(d) Detección.** `gust_sin_remate` = gusts jugados sin KO al objetivo ese turno.
`busqueda_sin_objetivo` = Items de búsqueda jugados en turnos donde el resultado no cambia el
plan (proxy: la carta buscada no se juega ni ese turno ni el siguiente).
`ace_spec_temprano` = turno en que se juega el ACE SPEC.

**(e) Valor.** MEDIO. Interacción importante con E3: la versión **estrecha** del gusting
(solo para letal) resuelve a la vez E3 y E7 y evita el resultado neutro medido en el v3.

---

## E8. Jugar el estadio en mal momento

`PRINCIPIO`. **Valor: BAJO-MEDIO.**

**(a) El error.** Bajar el estadio en cuanto se tiene. Un estadio solo puede jugarse uno por
turno, y el único modo real de quitar el del rival es sustituirlo: eso genera «stadium wars»
donde el que baja primero le regala al otro un intercambio gratis
(<https://bulbapedia.bulbagarden.net/wiki/Stadium_card_(TCG)>,
<https://en.wikibooks.org/wiki/Pok%C3%A9mon_Trading_Card_Game/Stadium_Cards>).

**(b) Razonamiento.** Un estadio propio en mesa sin efecto útil ese turno es munición para
que el rival la sustituya sin coste. Y guardarlo es la única respuesta al estadio del rival.

**(c) Nuestro agente.** Paso 7: `for i, o in por_tipo.get(7): if clase(cid) == 4: return [i]`
— juega **cualquier estadio, siempre, sin condición**. Ni mira `cur["stadium"]` (si el suyo
propio ya está en mesa) ni si el efecto le sirve este turno. `heuristico.py` menciona
`stadium` una sola vez en todo el fichero, y es para leer el efecto del estadio ya en juego
(paso 7b, Levincia).

**(d) Detección.** `estadio_autobump` = jugar un estadio mientras `cur["stadium"]` ya contiene
uno **nuestro** con efecto activo. `estadio_sin_ganancia` = jugar estadio en un turno en que
su efecto no se usa (para Levincia 1254: no había {L} en descarte; para Postwick 1255: no
había Hop's atacando). `estadio_perdido` = el rival lo sustituye en su turno siguiente.

**(e) Valor.** BAJO-MEDIO. Puerta trivial: no jugar estadio propio si el estadio en mesa ya
es nuestro y su efecto sigue vivo; y priorizar jugarlo el turno en que el efecto se consume.

---

## E9. Poner la herramienta en el Pokémon equivocado

`PRINCIPIO`. **Valor: BAJO-MEDIO.**

**(a) El error.** Adjuntar la Tool al activo por defecto. Las Tools son de un solo uso
efectivo: se van al descarte con el Pokémon.

**(b) Razonamiento.** Poner Hero's Cape / Choice Band en el que muere este turno es tirar la
carta. Las Tools defensivas van al que va a **aguantar**; las ofensivas al que va a **matar**,
y solo el turno en que lo hace.

**(c) Nuestro agente.** Paso 4: `min(cands, key=lambda t: 0 if inPlayArea == 4 else 1)` — al
activo, siempre, en cuanto la tiene. Nunca lee `pkm["tools"]` (grep: 0 apariciones), así que
tampoco razona sobre si ya lleva una.

**(d) Detección.** `tool_enterrada` = Tools adjuntadas a un Pokémon noqueado en el turno
siguiente ÷ Tools jugadas. `tool_sin_efecto` = Tool ofensiva (+daño) adjuntada en un turno en
el que ese Pokémon no ataca.

**(e) Valor.** BAJO-MEDIO en general; **MEDIO en hops-snorlax**, donde Hop's Choice Band 1171
(coste −{C} y +30) es lo que convierte Dynamic Press en 200 y decide si Snorlax puede atacar
ya. Ahí la Tool es tempo, no adorno.

---

## E10. Evolucionar por evolucionar

`PRINCIPIO` + `FORMATO`. **Valor: MEDIO.**

**(a) El error.** Evolucionar siempre que se puede. Evolucionar a un ex/Mega ex **sube la
responsabilidad en premios** de 1 a 2-3 y a menudo no cambia el resultado del turno.
«A single-prize Pokémon capable of consistently dealing 160 damage ... is superior to a
two-prize Pokémon of the equivalent evolution stage that also does 160»
(<https://www.justinbasil.com/guide/main-attacker>); el trade favorable es el que gana
partidas: «a player who consistently makes favorable prize trades will almost always win the
game, even if they Knock Out fewer Pokémon overall»
(<https://tcgprotectors.com/blogs/pokemon-deck-guides/pokemon-tcg-intermediate-strategy-guide>).

**(b) Razonamiento.** Un Riolu de 80 HP que va a morir igual, muerto, cuesta 1 premio; el
Mega Lucario de 340 HP que va a morir igual cuesta 3. Si evolucionar no evita el KO, no
evoluciones: deja que se lleven el premio barato y evoluciona sobre un cuerpo fresco.

**(c) Nuestro agente.** Paso 2: evoluciona siempre que hay opción, activo primero, escogiendo
por `_util` (que premia daño y HP → premia justo al ex). Sin mirar premios ni si el activo
muere igual.

Caso especial que además desperdicia una carta buena: **Hop's Dubwool 310** tiene *Defiant
Horn* — «when you play this Pokémon from your hand to evolve 1 of your Pokémon, you may
switch in 1 of your opponent's Benched Pokémon». O sea, **un gust gratis que no gasta la
ranura de Supporter**, disparado por el momento en que decides evolucionar. El v3 midió que
ese select llega ~2 veces por partida (798 en 400 partidas) y que el v2 **elige el objetivo a
ciegas** puntuando la banca rival con la función de la banca propia. Evolucionar Dubwool «por
orden de lista» tira el timing y el objetivo de un gust gratis.

**(d) Detección.** `evolucion_esteril` = evoluciones (log 12) tras las cuales el Pokémon es
noqueado en el turno siguiente **y** el daño acumulado ya superaba los HP de la preevolución
(es decir: iba a morir igual). `prima_de_premios` = variación del valor en premios de nuestra
mesa por turno. `gust_gratis_desperdiciado` = evoluciones de Dubwool en turnos sin remate al
objetivo arrastrado.

**(e) Valor.** MEDIO. Contraindicación real: retrasar evoluciones cuesta tempo.

> ⚠️ **Corregido 2026-08-11.** La primera versión decía «en un motor **sin Rare Candy** la
> línea es lenta». **Falso**: Rare Candy existe en el pool (`card_id 1079`, Item — «choose 1 of
> your Basic Pokémon in play. If you have a Stage 2 card in your hand that evolves from that
> Pokémon, put it onto that Basic Pokémon»), y el campo la juega: `alakazam-v10` lleva 3 y
> `grimmsnarl-dtc` lleva 3. Lo que pasa es que **nuestro agente no puede jugarla** porque su
> texto no contiene la palabra `search` (ver E16). El motor tiene el salto a Stage 2; el
> piloto, no.

La regla que sí vale es la estrecha: *no evoluciones a multi-premio un Pokémon que muere igual
este turno*. Y la aritmética de premios que la sostiene ya está **verificada** (E10 usaba
números del papel; ahora están medidos: ver «Verificaciones cerradas»).

---

## E11. Matar el objetivo que da premios pero deja al rival con mejor tablero

`PRINCIPIO`. **Valor: MEDIO (bajo en el v2, porque no puede elegir objetivo).**

**(a) El error.** Ir siempre a por el atacante gordo. La guía de prize mapping lo enseña con
un ejemplo explícito: en vez de atacar al Charizard ex activo, usar el gust para sacar el
Bidoof de banca y matar **el soporte**, negando el setup — «a high efficiency alternative to
immediate KOs»
(<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-mapping-guide-2026>).

**(b) Razonamiento.** Los premios que ganas hoy valen menos que los turnos que le quitas. Un
motor de robo o de aceleración en banca (Dudunsparce, Kilowattrel, Zoroark ex) noqueado deja
al rival sin recursos durante toda la partida; el ex noqueado se sustituye por otro ex.

**(c) Nuestro agente.** En el motor, el objetivo del ataque es el activo rival: la única
elección real de objetivo es **el gust**, que en el v2 está apagado y en el v3 puntúa por
`_valor_objetivo` (KO inmediato manda, ×2 si da 2 premios; luego pieza que aún no puede
atacar; luego el más herido). Le falta la categoría «motor de robo/aceleración», que es la
que la literatura pone primero.

**(d) Detección.** Al elegir objetivo en banca rival, clasificar la carta por su
`ability_text`: `draw`/`attach ... energy`/`search` ⇒ pieza de motor. Métrica:
`motores_rivales_vivos_al_final`.

**(e) Valor.** MEDIO, y solo se cobra si se reactiva el gusting. Buen candidato para
combinarlo con el gusting-solo-para-letal de E3 (dos disparadores estrechos, no uno ancho).

---

## E12. Ignorar el mazo: deck-out y contar cartas

`PRINCIPIO`. **Valor: BAJO en general, ALTO en partidas largas.**

**(a) El error.** Robar y buscar sin mirar cuánto mazo queda. En este motor, quedarse sin
mazo al robar **pierde la partida** (`reason 2`, verificado: pasivo vs pasivo terminó en
deck-out en el turno ~93, `motor-mecanica.md` §5).

**(c) Nuestro agente.** Lee `deckCount` **solo** para vetar habilidades de robo con mazo ≤6
(`_habilidad_activable`). No lo mira para el Supporter de robo, ni para buscar, ni para
decidir si la partida se está yendo a deck-out.

**(d) Detección.** `deckCount` propio al final de cada turno; marcar la partida si baja de 5
antes del turno 25, y contar las derrotas por `reason 2` en el log 23.

**(e) Valor.** BAJO por defecto, pero conviene medirlo: si nuestro ratio de derrotas por
deck-out es no trivial en la ladder, la prioridad cambia sola. Es un contador de 3 líneas
sobre los replays de `kaggle competitions episodes 55407312`.

---

## E13. La elección de primero/segundo está hardcodeada

`FORMATO` — **pendiente de verificar contra el motor. Valor: MEDIO-ALTO si se confirma.**

**(a) El contexto.** En el TCG moderno el que va primero **no puede atacar en su primer
turno**; el que va segundo sí. La opinión de la comunidad competitiva en formatos recientes
es que ir segundo suele ser mejor: «going second is almost always better ... the second
player wins the energy race since most of the best attacks require at least two energies»
(<https://community.pokemon.com/en-us/discussion/13427/going-first-is-simply-worse-than-going-second>).
Regla oficial de referencia:
<https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/mew_rulebook_en.pdf>.

**(b) Nuestro agente.** Select `(9,41)`: elige **primero, siempre**.

```python
if t == 9:  # primero/segundo: primero (option con type 1)
```

Y ese select lo recibe **siempre el jugador 0 del env**, o sea ~50% de las partidas de
ladder: la palanca solo actúa en la mitad de los emparejamientos, pero es gratis.

**(c) Evidencia propia, débil pero consistente.** En los dos replays completos que hay
descomprimidos en `data/replays/muestras/` (91366414, 91369023) **no aparece ningún log de
ataque (type 15) en el turno 1**, y en ambos el primer ataque de la partida es del jugador
segundo en el turno 2. Dos partidas no demuestran la regla: hay que contarlo sobre el corpus.

**(d) Detección / probe.** Sobre los replays ya descargados: contar logs `type 15` con
`turn == 1`. Si son **0 sobre miles de episodios**, la regla «el primero no ataca» está
implementada y la decisión es real. Segundo probe, ya con partidas: winrate condicionado a
`current["firstPlayer"] == yourIndex`, que se puede sacar del corpus de la ladder sin jugar
nada.

**(e) Valor — REVISADO 2026-08-11 con datos. Ya no es «cambiar a segundo».**

`MEDIDO` sobre el corpus de la ladder (`pokemon-tcg-ai-battle-episodes-2026-08-08.zip`):

| Medida | Resultado | n |
|---|---|---|
| Ataques (log 15) en `turn == 1` | **0** — el primer ataque de toda partida es siempre en el turno 2 (298 ataques ahí) | 120 episodios |
| Elección de p0 → `firstPlayer` | **99,2% elige PRIMERO** (495 de 499) | 499 partidas decididas |
| Gana quien fue primero | **53,5%**, IC95 ±4,4 pts | 499 |
| Turno final mediano / p90 | 13 / 19 | 499 |

Tres conclusiones, y las tres cambian la entrada:

1. **La regla existe**: el que va primero no ataca en su turno 1. Confirmado, no inferido.
2. **Ir primero NO es peor aquí.** El estimador puntual favorece al primero (53,5%). Como el
   emparejamiento de la ladder es aleatorio, la población de agentes es la misma en los dos
   asientos y la única asimetría del asiento 0 es que **elige**; como elige «primero» el 99,2%
   de las veces, «gana el asiento 0» ≈ «gana el que va primero». No es significativo al 95%
   (el IC cruza 0,5), pero **no hay ninguna evidencia a favor de cambiar a segundo**, y la
   hardcodeada actual es la opción que juega todo el mundo.
3. **`NO-APLICA` la literatura que citaba la versión anterior.** El «going second is almost
   always better» que circula es mayoritariamente de **Pokémon TCG Pocket**, que es otro juego:
   tiene *energy zone* que genera energía sola, y ahí el que va segundo gana el desarrollo de
   energía (<https://www.cbr.com/pokemon-tcg-pocket-always-go-second/>,
   <https://game8.co/games/Pokemon-TCG-Pocket/archives/483043>). Nuestro simulador es de
   adjunción manual desde la mano: el argumento no se traslada. El hilo del foro que citaba la
   v1 (<https://community.pokemon.com/en-us/discussion/13427/going-first-is-simply-worse-than-going-second>)
   es opinión de comunidad, no medida, y va contra nuestros propios datos.

**El corpus no puede decidirlo y hay que decirlo así**: con 4 partidas en las que alguien
eligió segundo, el observacional está **saturado** — no hay variación que explotar. La única
vía es un A/B propio en `arena.py` (1 línea, mismo agente contra sí mismo forzando el otro
lado). **Valor rebajado a BAJO-MEDIO y prioridad rebajada**: ya no es «la prueba con mejor
relación coste/información»; es una comprobación de higiene por si la ladder entera está
equivocada a la vez, lo cual es posible pero no es donde está el dinero.

---

## E14. Promover mal tras un KO

`PRINCIPIO`. **Valor: BAJO-MEDIO.**

**(a) El error.** SixPrizes lo lista entre los misplays técnicos: «Promoting wrong Pokémon
after knockouts» (<https://sixprizes.com/2012/12/13/and-ill-pass-a/>).

**(c) Nuestro agente.** `_elige_cartas`, `area == 5`: puntúa
`10*len(energies) + mejor_ataque/10 + hp/100` → **el más cargado**. No mira si el promovido
muere al ataque que ya tiene enfrente, ni cuántos premios regala. Con una lista de Megas eso
es promocionar 3 premios a la boca del lobo.

**(d) Detección.** `promocion_suicida` = promovidos noqueados en el turno rival inmediato
**existiendo** en banca una alternativa que sobrevivía a la misma amenaza (se calcula con
`_dano_contra`, ya escrita en el v3).

**(e) Valor.** BAJO-MEDIO. Es el mismo cálculo de amenaza que ya está implementado y
verificado; reutilizarlo aquí es casi gratis.

---

## E16. El agente solo sabe jugar cartas que digan «draw» o «search»: el resto de la baraja es papel

`FORMATO` — **hallazgo nuevo 2026-08-11. Valor: ALTO. Es el error más grande del catálogo y no
es táctico, es estructural.**

**(a) El error.** No es un error que aparezca en ninguna lista de misplays humanos, porque
ningún humano lo comete: es el equivalente a **no leer la mitad de tus cartas**. SixPrizes lo
roza al describir al jugador flojo: «inexperienced players play the game on **autopilot**, and
when their primary strategy cannot be found, they give up at the lack of any other strategy»
(<https://sixprizes.com/2014/10/02/deft-decisions/>). Nuestro agente no es que se rinda: es
que la otra estrategia le es literalmente invisible.

**(b) De dónde sale.** Los dos filtros de `_fase_principal` están escritos por texto:

```python
# paso 5) item de búsqueda
if cid is not None and clase(cid) == 1 and "search" in textos.get(cid, ""):
# paso 6) supporter de robo/búsqueda
if "draw" in txt or "search" in txt:
```

Si la carta no dice literalmente `search` (Item) o `draw`/`search` (Supporter), **nunca se
juega**. No hay rama que la alcance.

**(c) Cuánto pool se pierde.** `MEDIDO` sobre `research/cards_clean.csv` (1.267 cartas):

| Tipo | Jugables por el agente | Muertas | % muerto |
|---|---|---|---|
| Item | 21 / 77 | 56 | **73%** |
| Supporter | 36 / 61 | 25 | **41%** |

Y no son cartas marginales: lo que cae fuera es **el juego entero que no es robar**.

- **Gusting / posicionamiento**: Boss's Orders 1182, Prime Catcher 1088, Pokémon Catcher 1124,
  Lisia's Appeal 1204, Repel 1143, TR Giovanni 1218. Esto explica por qué «el v2 no gustea
  nunca» (E7): no es una decisión de diseño, es que la carta no tiene rama.
- **Movilidad**: Switch 1123, Scramble Switch 1107, Scoop Up Cyclone 1093, Kieran 1191.
  Nuestras listas llevan 2-4 Switch cada una: papel.
- **Evolución rápida**: **Rare Candy 1079** (corrige E10).
- **Recursión**: Night Stretcher 1097, Energy Retrieval 1118, Max Rod 1110, Miracle Headset
  1109, Super Rod-likes. Presente en **todas** nuestras barajas.
- **Aceleración de energía**: N's PP Up 1113, Wondrous Patch 1146, Reboot Pod 1089, Waitress
  1235, Tarragon 1238, Rosa's Encouragement 1240.
- **Buff de daño**: Black Belt's Training 1211 (**+40 al ataque de este turno**), Premium Power
  Pro 1141 (+30 a {F}). En `mega-lucario` hay 2 Premium Power Pro sin usar.
- **Disrupción**: Xerosic's Machinations 1197, Eri 1186, Enhanced Hammer 1081, Crushing Hammer
  1120, Ruffian 1209, Tool Scrapper 1137, Megaton Blower 1104, Hand Trimmer 1087.
- **Curación**: Potion, Super Potion, Cook 1212, Fennel 1222, Jacinthe 1241, Poké Vital A 1096.
- **Y robo que no dice «draw»**: Explorer's Guidance 1185 («put 2 of them into your hand»),
  Drayton 1202, Grimsley's Move 1230, Pokégear 3.0 1122, Dusk Ball 1102, Roto-Stick 1077. Son
  cartas de **robo/búsqueda puras** que el filtro de texto no reconoce. Este subgrupo es un
  bug, no una simplificación.

**(d) Cuánto perdemos en NUESTRAS barajas.** `MEDIDO` — cartas Item/Supporter que el agente
nunca jugará, por lista de 60:

| Baraja | Trainers | Muertos | Las principales |
|---|---|---|---|
| `ns-zekrom` | 30 | **15** | N's PP Up ×4, Night Stretcher ×3, N's Plan ×2, Boss's Orders ×2, Switch ×2 |
| `okidogi` | 33 | **12** | Pokégear 3.0 ×4, Night Stretcher ×4, Boss's Orders ×2, Switch ×2 |
| `mega-lucario` | 29 | **10** | Switch ×2, Night Stretcher ×2, Premium Power Pro ×2, Tarragon ×2, Boss's Orders ×2 |
| `mega-kangaskhan` | 33 | **10** | Switch ×4, Boss's Orders ×2, Night Stretcher ×2, Pokégear ×2 |
| `ethans-hooh` | 32 | **9** | Switch ×3, Boss's Orders ×2, Night Stretcher ×2, Pokégear ×2 |
| `iono-bellibolt` | 27 | 8 | Boss's Orders ×2, Switch ×2, Night Stretcher ×2, Energy Retrieval ×2 |
| `tr-mewtwo` | 31 | 8 | Boss's Orders ×2, Switch ×2, Night Stretcher ×2, Pokégear ×2 |
| **`hops-snorlax` (envío vivo)** | 25 | **6** | Boss's Orders ×2, Switch ×2, Night Stretcher ×2 |
| `abomasnow-plus` | 17 | 2 | Night Stretcher ×2 |

**El envío que está jugando la ladder ahora mismo lleva 6 cartas de 60 (10%) que nunca
saldrán de la mano.** A efectos prácticos juega con una baraja de 54 cartas y con 6 cartas de
lastre que además atascan la mano y empeoran cada robo.

**(e) Y contamina la báscula.** `arena.py` enfrenta dos módulos con `agent()`; el gauntlet se
pilota con el mismo heurístico. Las barajas rivales pierden lo mismo o más:

| Baraja del gauntlet | Trainers | Muertos |
|---|---|---|
| `great-tusk-v10` | 38 | **23** (Pokégear ×4, Switch ×4, Xerosic ×4, Explorer's Guidance ×4, Boss's ×4) |
| `alakazam-v10` | 34 | **17** (Rare Candy ×3, Enhanced Hammer ×3, Night Stretcher ×3, Boss's ×3, Xerosic ×3) |
| `lucario-sample` | 28 | 12 · `grimmsnarl-dtc` 28 | 11 · `garchomp-sample` 28 | 10 |

Consecuencia dura: **`alakazam-v10` juega sin sus 3 Rare Candy**, o sea sin su línea de Stage 2
a velocidad real. Alakazam es el 18,2% del campo bueno (`baraja-vs-campo.md`). Los winrates
del gauntlet están medidos contra rivales tullidos de la misma enfermedad que nosotros, y
**el sesgo no es simétrico**: castiga más a la baraja con más trainers no-buscadores. Esto es
la misma clase de error que `lab-barajas.md` documentó con las habilidades (type 10) y que E2
documenta con los ataques de daño 0. Es la tercera vez que aparece el mismo patrón.

**(f) Detección en log.** Trivial y no necesita partidas nuevas: por cada partida, contar
cartas Item/Supporter que estuvieron en la mano ≥1 turno y **jamás** aparecen en un log 10
(trainer jugado). Métrica: `cartas_inertes_por_partida` y `turnos_con_carta_inerte_en_mano`.
Se puede calcular ahora mismo sobre nuestros propios episodios de ladder.

**(g) Valor.** **ALTO, y probablemente el techo real del proyecto.** No es una heurística más
fina: es acceso a mecánicas que hoy no existen para el agente (gustear, cambiar, revivir,
acelerar, subir daño). Coste: cada familia es una rama corta en `_fase_principal` con su
puerta de utilidad, pero son varias y algunas abren selects nuevos (Switch → (1,4);
Boss's Orders → elegir de la banca rival). **Orden sensato por valor/riesgo**: (1) arreglar
el filtro de robo/búsqueda para que reconozca «into your hand» y «look at the top N»
—es corregir un bug y no abre selects nuevos—; (2) Switch/movilidad; (3) gusting con puerta
estrecha (E3/N5); (4) buffs de daño; (5) el resto.

---

## E17. Empezar la partida con el atacante gordo de activo

`PRINCIPIO`. **Valor: MEDIO-ALTO en listas con ex/Mega ex, nulo en single-prize.**

**(a) El error.** Elegir como activo inicial el Pokémon que más pega. En el setup se coloca el
activo **boca abajo** y sin información del rival; el activo inicial es el que va a comer el
primer ataque de la partida, normalmente sin energía y sin poder responder.

**(b) Razonamiento del jugador.** El activo inicial debe ser **desechable**: un básico de 1
premio, idealmente uno que haga *setup* (buscar básicos, robar). El atacante real se monta en
la banca y entra cuando está armado. La versión de la literatura: el papel del *pivot* es
«take the Active Spot after one of our Pokémon is knocked out», y empezar con un multi-premio
se describe como una **desventaja** que hay que evitar al construir
(<https://www.justinbasil.com/guide/crafting-your-deck>); y en general «every Pokémon you bench
is a potential part of your opponent's prize map»
(<https://www.justinbasil.com/guide/main-attacker>) — el activo, más todavía.

**(c) Nuestro agente lo comete por construcción.** El select `(1,1)` (activo inicial de mano,
min1/max1) cae en `_elige_cartas` sin `effect`, área 2 → rama `area in (1,2,3,6)` →
`puntuados[:1]`, ordenado por `_util`, que para Pokémon es:

```python
return 3.0 + _mejor_ataque(cid, cards, atks) / 1000 + (c.get("hp") or 0) / 10000
```

O sea: **empieza siempre con el básico de más daño**, y como desempate el de más HP. Y el
select `(1,2)` (banca inicial, min0/max2) usa la misma función: baja de entrada los **dos
siguientes mejores**. En `mega-lucario` eso significa abrir enseñando la línea entera; con
premios verificados (Mega ex = 3), un Boss's Orders rival en el turno 2-3 sobre esa mesa es
media partida.

**(d) Detección en log.** `activo_inicial_caro` = valor en premios del Pokémon en `active[0]`
en la primera observación con mesa montada (1 / 2 / 3). `apertura_expuesta` = suma de premios
de activo + banca al terminar el setup. Y el contrafactual barato: ¿había en la mano inicial
un básico de 1 premio con habilidad de robo/búsqueda que no se eligió?

**(e) Valor.** MEDIO-ALTO en `mega-lucario`, `mega-kangaskhan`, `okidogi`, `tr-mewtwo`;
**nulo en `hops-snorlax`**, que es single-prize entera y donde da igual quién abra. Coste:
~10 líneas (una `_util_apertura` que invierta el criterio: menos premios primero, habilidad de
setup después, daño en último lugar). Riesgo: bajo. **Es la mejora más barata que sí toca a
las barajas con ex.**

---

## E18. Pagar los costes con la carta equivocada

`PRINCIPIO` + `FORMATO`. **Valor: BAJO-MEDIO, coste casi cero.**

**(a) El error.** Cuando un efecto te obliga a descartar energía adjunta o cartas de la mano
como coste, tirar la mejor. El jugador bueno paga con lo más barato que satisfaga el coste.

**(b) Nuestro agente.** Dos ramas ciegas en `_politica`:

```python
if t == 4:  # descartar energía adjunta como coste, encadenado: la primera
    return [0]
if t == 2:  # ...coste forzoso → las primeras minCount
    k = min(sel["minCount"], len(sel["option"])); return list(range(k))
```

**Siempre la primera de la lista.** El pool tiene **12 energías especiales** y varias valen
mucho más que una básica: **Legacy Energy 12** («that player takes **1 fewer Prize card**»,
una vez por partida — es una carta de intercambio de premios, justo lo que decide E10/N2/N6),
**Neo Upper Energy 10** (2 energías de cualquier tipo en un Stage 2), **Prism Energy 16**,
**Boomerang Energy 9** (vuelve sola si la descarta un ataque propio), **Mist Energy 11** y
**Rock Fighting Energy 20** (previenen efectos de ataques). Descartar una de esas por índice 0
para pagar un coste que aceptaba una {C} básica es tirar la carta.

Mismo problema en `t == 5` y en el descarte de mano: `_elige_cartas` sí ordena por `_util`
para el coste de mano (`list(reversed(puntuados))[:k]`, correcto), pero `_util` valora las
energías con un binario grosero (2,5 si falta energía, 1,0 si no) y **no distingue básica de
especial**: todas las energías empatan.

**(d) Detección.** `coste_caro` = descartes de energía especial (`card_id` en 9..20) o de carta
con `_util` alta ejecutados como coste cuando existía en las opciones una alternativa de menor
valor. Métrica directa: `especiales_descartadas_como_coste / especiales_jugadas`.

**(e) Valor.** BAJO-MEDIO hoy (nuestras listas llevan pocas especiales), pero es **~6 líneas**
y el mismo arreglo protege a `_util` de tratar todas las energías igual. Sube a MEDIO si el
laboratorio de barajas mete Legacy Energy, que es tecnología de premios pura.

---

## E19. No contar el daño entre turnos (veneno y quemadura)

`PRINCIPIO`, pero **`NO-APLICA-EN-LA-PRÁCTICA` en el campo actual. Valor: BAJO — y esa es la
conclusión útil, porque impide gastar tiempo aquí.**

**(a) El error.** Elegir el ataque sin contar el daño que va a caer solo entre turnos. Es el
ejemplo de manual: «If your opponent has a Pokémon with 220 HP and your main attack deals 200
damage, by poisoning them first, the 10 damage from poison after your turn and the 10 damage
after their turn will put them at 220 total damage, **guaranteeing a knockout before you even
start your next turn**» (<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-special-conditions-guide>).
La quemadura pone 2 contadores entre turnos en vez de 1
(<https://www.thegamer.com/pokemon-tcg-every-status-effect-guide/>,
<https://dotesports.com/guides/news/special-conditions-in-the-pokemon-trading-card-game-explained>).
Es exactamente el razonamiento de rangos de N3, con la aritmética desplazada.

**(b) Nuestro agente.** `grep` de `poisoned|burned|asleep|paralyzed|confused` en
`heuristico.py` → **0**. La observación los expone a nivel jugador
(`players[j]["poisoned"]`, etc., verificado en el corpus) y no se leen.

**(c) Pero el campo no lo usa.** `MEDIDO` sobre **200 partidas** de la ladder: los cinco flags
(`poisoned`, `burned`, `asleep`, `paralyzed`, `confused`) están en **False en todas las
observaciones de todas las partidas**. Cero. En el pool hay material —28 ataques envenenan,
25 paralizan, 20 confunden, 17 queman, 13 duermen— pero **el campo no juega ninguno**.

**(d) Las dos lecturas, y hay que quedarse con las dos.**
- *Defensiva*: no hace falta programar la aritmética de estados para la ladder de hoy.
  Prioridad BAJA. **Esto ahorra una tarde.**
- *Ofensiva y para Deck Score*: es un eje del juego que **nadie está explotando** en un campo
  de 4.669 episodios. Okidogi ex 138 (E2) ya se autoenvenena para duplicar su daño, así que la
  baraja que tenemos toca este eje sin querer. Si el laboratorio busca un ángulo diferenciado
  que un jurado de The Pokémon Company reconozca, «somos los únicos que usamos condiciones
  especiales» es una frase de writeup con datos detrás. Riesgo honesto: rutas del motor que
  nadie ha pisado son rutas donde nadie ha encontrado los bugs.

**(e) Detección.** `estado_ignorado` = turnos en los que el activo rival estaba envenenado o
quemado y elegimos un ataque cuyo daño ≥ HP rival, existiendo otro más barato que dejaba al
rival por debajo del daño entre turnos. Y `estado_propio_ignorado` = turnos en que nuestro
activo envenenado no se retira ni ataca antes de morir por el contador.

---

## E20. La ceguera al marcador desactiva una familia entera de cartas

`FORMATO` — **extensión medida de E3. Valor: ALTO para Deck Score (20% del premio).**

E3 dice que el agente no lee los premios (`grep -c prize` → 0). La segunda pasada mide qué
cuesta eso **en cartas concretas del pool**: hay una familia entera cuyo texto está
condicionado al marcador, y para un agente ciego al marcador **todas son inútiles o
imposibles de evaluar**.

| Carta | Tipo | Condición de premios |
|---|---|---|
| **Briar 1201** | Supporter | «only if your opponent has **exactly 2** Prize cards remaining» — carta de cierre |
| **Acerola's Mischief 1228** | Supporter | «only if your opponent has **2 or fewer**» |
| **Rosa's Encouragement 1240** | Supporter | «only if you have **more** Prize cards remaining than your opponent» — adjunta 2 energías del descarte |
| **Counter Gain 1168** | Tool | si vas **por detrás** en premios, los ataques cuestan {C} menos |
| **Lacey 1199** | Supporter | roba 4, u **8 si el rival tiene ≤3 premios** |
| **Emcee's Hype 1214** | Supporter | roba 2, +2 más si el rival tiene ≤3 |
| **Lillie's Determination 1227** | Supporter | roba 6, u **8 si tienes exactamente 6 premios** (está en la baraja de ejemplo, ×4) |
| **Legacy Energy 12** | Energía especial | el rival toma **1 premio menos** al noquearla (una vez por partida) |
| **Lillie's Pearl 1172** | Tool | 1 premio menos sobre un Lillie's Pokémon |
| **Kingambit 901** | Stage 2 | **+30 de daño por cada premio que el rival ya se llevó** |
| **Bloodmoon Ursaluna ex 44** | Básico | su ataque cuesta {C} menos por cada premio que el rival tomó |
| **Hydreigon ex 618** | Stage 2 | **1 premio extra** al noquear un básico rival |
| **Shedinja 748** / **Mega Gengar ex 772** / **Munkidori ex 139** | Pokémon | denegación de premios contra ex |

Dos consecuencias separadas, y conviene no mezclarlas:

1. **Táctica** (E3): sin marcador no hay línea letal ni gusting-para-letal. Ya estaba dicho.
2. **De construcción** (nuevo, y es lo que puntúa Deck Score): el laboratorio de barajas **no
   puede evaluar ninguna de estas cartas**, porque el piloto que mide no sabe leer su
   condición. Cualquier lista que las llevara puntuaría mal por culpa del piloto, no de la
   lista. Es E16 otra vez, un nivel más arriba: el sesgo del piloto decide qué barajas
   «funcionan».

**Nota de honestidad para el writeup**: la pregunta pendiente n.º 3 de la v1 («¿existe un
equivalente de Counter Catcher?») queda **respondida**: sí existe la mecánica de «vas
perdiendo en premios → descuento», encarnada en **Counter Gain 1168** (Tool) y
**Rosa's Encouragement 1240** (Supporter), pero **no** hay un gusting condicionado a ir
perdiendo. El gusting confirmado sigue siendo el incondicional (Boss's Orders 1182, Prime
Catcher 1088, Pokémon Catcher 1124, Lisia's Appeal 1204, TR Giovanni 1218).

---

## E15 (cierre de la Parte 1). Los que NO aplican a nuestro simulador

> Va al final aunque lleve el número 15: es la tabla de descartes de toda la Parte 1. Los
> errores nuevos de la segunda pasada (E16–E20) se numeraron por orden de hallazgo y quedan
> antes de esta tabla, no después de E14.

Documentarlos evita perder tiempo y da material para el writeup (demuestra que se contrastó
el simulador con el juego de papel).

| Error clásico | Por qué NO aplica |
|---|---|
| «No lleves el reloj / juega rápido, hay límite de tiempo» | En cabt no hay reloj de torneo: `actTimeout 0`, `runTimeout 2000`, 600 s de `remainingOverageTime` acumulados y ~0,03 ms por decisión en nuestro agente. El presupuesto es ×34.000. |
| «Baraja bien / corta el mazo / errores de manipulación física» | El motor baraja. |
| Errores de deck-building tipo «lleva 8-12 Supporters» | Aplica al laboratorio de barajas, no al piloto. Vive en `lab-barajas.md`. |
| «Cuenta las cartas premiadas para saber qué te falta» | **Los premios propios están ocultos también para nosotros** (`prize: [null,…]`, `motor-mecanica.md` §4). Solo se puede inferir por eliminación contando mazo+mano+descarte+mesa. Posible, pero caro; no es prioridad. |
| «Lee el lenguaje corporal / gestión del tilt» | Sin rival humano. |
| «Cuidado con las reglas de moneda a mano» | El motor tiene `manual_coin` en la Search API pero los ataques con moneda se resuelven solos. Sí aplica la consecuencia: **100 cartas del pool llevan `flip a coin`** → varianza, mala compañera del 70% de Model Score que premia consistencia. |
| «Guarda el Counter Catcher para cuando vayas perdiendo en premios» | No he verificado que exista un equivalente de Counter Catcher en el pool; el gusting confirmado es Boss's Orders 1182, Prime Catcher 1088, Pokémon Catcher 1124, Lisia's Appeal 1204, TR Giovanni 1218. **Comprobar antes de citarlo en el writeup.** |

---

# PARTE 2 — Jugadas «de nivel» que una greedy nunca hará

Lo contrario del catálogo: lo que hace el jugador bueno y que ninguna heurística de daño
máximo puede producir. Estas son las que dan puntos de Model Score, porque son las que un
jurado de The Pokémon Company reconoce al leerlas.

---

## N1. Atacar con el ataque pequeño para armar la banca

**Qué es.** Usar Aura Jab (130) en vez de Mega Brave (270) el turno en que 130 basta o el
turno en que la banca necesita las 3 energías. Es E1 leído del derecho.

**Por qué un buen jugador lo hace.** «The winning turn usually starts a turn (or two)
earlier» (<https://levelsptcg.com/pokemon-tcg-turns/>). El daño que no gasta se convierte en
el atacante de repuesto que evita el turno muerto tras el próximo KO.

**Condición detectable.** `usó_ataque_setup = 1` cuando: había un ataque de más daño
disponible, el ataque elegido acelera o busca, y (i) el elegido igualmente noqueaba, o (ii)
ningún ataque noqueaba y la banca tenía Pokémon sin energía suficiente.

**Valor.** ALTO en mega-lucario/okidogi/ns-zekrom. Es la contrapartida exacta de E1+E2+E4:
las tres se arreglan con la misma función de evaluación de ataque.

---

## N2. No evolucionar para no regalar premios

**Qué es.** Dejar al Riolu de 80 HP morir como Riolu (1 premio) en vez de evolucionarlo a
Mega Lucario ex (3 premios) para que muera igual.

**Por qué.** Prize trade: «use lower-value Pokémon to defeat higher-value opponents ...
gaining a 2-to-1 prize advantage»
(<https://tcgprotectors.com/blogs/pokemon-deck-guides/pokemon-tcg-intermediate-strategy-guide>).

**Condición detectable.** Turnos con evolución disponible a multi-premio en un Pokémon cuyo
daño acumulado + mejor amenaza rival ≥ HP de la evolución, y no se evolucionó.

**Valor.** MEDIO. Muy vistosa en el writeup: es exactamente el tipo de decisión «contraria al
instinto» que separa niveles.

---

## N3. Atacar sin matar para dejar al rival en rango

**Qué es.** Elegir el ataque que deja al rival justo por debajo de lo que remata el turno
siguiente, en vez del que hace más daño y no cambia nada. Y su gemela defensiva: elegir el
ataque que **no** mata cuando matar te expone.

**Por qué.** El daño desperdiciado por encima de los HP no existe; lo que existe son los
rangos. La literatura de damage control es toda sobre umbrales: cartas de +10/+30 y de −20
que «make the difference between a 1- and a 2-hit knockout»
(<https://www.justinbasil.com/guide/damage>).

**Condición detectable.** Para cada ataque ofrecido, calcular `hp_restante_rival` tras el
golpe y compararlo con el daño que ese mismo Pokémon podrá hacer el turno siguiente
(energías + 1). Marcar `RANGO_PREPARADO` si el elegido deja `hp_restante ≤ daño_siguiente` y
`RANGO_PERDIDO` si otro ataque lo lograba y el elegido no.

**Valor.** MEDIO-ALTO en las barajas que no matan de un golpe (todas contra Megas de 300+ HP).
Barato: es aritmética sobre datos que ya se leen.

---

## N4. Sacrificar un Pokémon a propósito

**Qué es.** Dejar morir delante un cuerpo barato (single-prize, sin energía) mientras el
atacante real se carga en banca. En este juego no hay forma de «pasar»: el sacrificio es la
manera de comprar un turno.

**Por qué.** Cambias 1 premio por un turno de desarrollo, y el que muere no llevaba nada
invertido. Confirmación de regla: cualquier KO, incluso autoinfligido, da premio al rival
(<https://compendium.pokegym.net/category/7-gameplay/knock-outs-and-prizes/>) — luego el
sacrificio hay que elegirlo, no sufrirlo.

**Condición detectable.** `sacrificio_deliberado` = turnos en que el activo va a morir, hay
retirada legal y **no** se retira, y la energía del turno va a la banca. Hoy nuestro agente
produce esto por accidente (nunca retira), no por decisión: la diferencia es si la energía
fue a la banca o al muerto.

**Valor.** MEDIO. Nota importante: el v3 midió la retirada en 0,476 (peor que no retirarse).
Eso **no** dice que sacrificar sea malo; dice que *huir* es malo. El sacrificio bien hecho es
justamente no retirarse — pero invirtiendo en la banca mientras tanto (E4).

---

## N5. Cerrar la ruta de escape antes de gustear

**Qué es.** Arrastrar a la posición activa al Pokémon que **no puede volver**: `retreatCost >
energías adjuntas` y sin Switch a la vista. El rival pierde el turno entero o retrocede
descartando energía.

**Por qué.** «If the Pokémon doesn't have enough attached? You're stuck»
(<https://levelsptcg.com/pokemon-tcg-retreat/>). Arrastrar algo con coste de retirada 0-1 es
regalarle un cambio gratis; arrastrar algo con coste 3-4 y la banca sin energía es un turno
robado. Nuestro pool tiene mucho material así: Hop's Snorlax 304 retirada **4**, Mega
Abomasnow 723 retirada 4, Mega Kangaskhan 756 retirada 3, Okidogi ex 138 retirada 3.

**Condición detectable.** En cada gust propio, registrar `retreatCost(objetivo) −
len(energies(objetivo))` y si el rival consiguió salir en su turno. Métrica: `gust_atrapa` =
fracción de gusts tras los cuales el objetivo sigue activo al empezar nuestro turno
siguiente.

**Valor.** MEDIO. **Es la puerta que le faltaba al gusting del v3**: allí el criterio era «KO
inmediato, o pieza que aún no puede atacar». Añadir «o pieza que no puede retirarse» es una
tercera categoría, más barata de comprobar y con efecto de tempo garantizado. Merece una
corrida propia antes de dar el gusting por muerto.

---

## N6. Forzar el séptimo premio

**Qué es.** Ordenar los intercambios para que el rival necesite **más KOs de los que le caben
en 6 premios**: pelear con single-prize y matar multi-premio.

**Por qué.** Es la definición del prize trade favorable; la guía lo llama literalmente
«forcing the 7th prize ... you make them take more KOs than they need to win»
(<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-mapping-guide-2026>).

**Condición detectable.** Al final de cada partida: `KOs_recibidos` vs `premios_cedidos`
(si son iguales, todo lo nuestro era single-prize) y `premios_ganados / KOs_hechos` (cuanto
más alto, mejor trade). Es la métrica de una línea que resume si la baraja + piloto están
ganando la carrera o solo matando.

**Valor.** Es un **criterio de evaluación**, no una jugada: sirve para elegir baraja
(hops-snorlax y ns-zekrom están construidas justo sobre esto) y como frase del writeup. Alto
valor narrativo, cero coste.

---

## N7. Comprometer lo irreversible al final del turno

**Qué es.** Robar → habilidades → buscar → **energía** → atacar. Nunca al revés.
«Minimize commitment until necessary ... energy attachments should typically occur near the
end of your turn» (guía de secuenciación).

**Condición detectable.** Es E5 con el signo cambiado: posición relativa del log 11 dentro de
la cadena de acciones del turno.

**Valor.** MEDIO y es el **cambio más barato del documento**: mover un bloque de código.

---

## N8. Dejar hueco en la banca a propósito

**Qué es.** No llenar la banca a 4 «porque se puede», y en particular no bajar el multi-premio
hasta el turno en que se usa. Es E6 del derecho.

**Condición detectable.** `premios_expuestos_en_banca` por turno, cruzado con si el rival ya
ha jugado gusts. Umbral candidato: no exponer en banca más premios de los que el rival puede
cobrar para ganar.

**Valor.** ALTO en listas con ex, y **negativo si se aplica a hops-snorlax**: siempre
condicionar a la responsabilidad en premios, nunca al conteo de cuerpos.

---

## N9. Elegir el turno (primero/segundo) como decisión, no como constante

Ver E13. Es la única decisión del juego que se toma **antes** de ver una sola carta, y hoy es
una constante en el código.

---

## N10. Abrir con el cuerpo barato y guardar el atacante en la mano

**Qué es.** Lo contrario de E17. En el setup, poner de activo el básico de 1 premio (mejor si
hace *setup*: busca básicos o roba) y **no** bajar el ex/Mega ex hasta el turno en que se usa.
El atacante entra desde la mano cuando la banca está armada, no antes.

**Por qué un buen jugador lo hace.** El activo inicial come el primer ataque de la partida sin
energía y sin respuesta; lo que se enseña en el setup entra en el *prize map* del rival desde
el turno 1 (<https://www.justinbasil.com/guide/main-attacker>), y con el dato ya verificado de
que un Mega ex vale **3 premios**, abrir con uno es poner medio marcador en la mesa antes de
jugar una carta.

**Condición detectable.** `apertura_barata` = 1 si el valor en premios del activo inicial es 1
**y** existía en la mano inicial otro básico de más daño que no se eligió (o sea: la elección
fue deliberada, no forzada).

**Valor.** MEDIO-ALTO en las listas con ex; nulo en `hops-snorlax`. Se implementa a la vez que
E17 con la misma función.

---

## N11. Invertir la energía donde vaya a sobrevivir

**Qué es.** La versión positiva de E4, y **la jugada de nivel con más respaldo empírico de toda
la nota**. No es «no adjuntar»: es adjuntar al cuerpo que seguirá vivo el turno que viene.

**Por qué.** `MEDIDO` sobre 695 lados de partida de la ladder (350 ganadores, 345 perdedores),
métrica `energía_enterrada` = energías que murieron adjuntas a su Pokémon ÷ energías totales
invertidas:

| | Energía enterrada |
|---|---|
| **Ganadores** | **0,448** |
| **Perdedores** | **0,718** |
| Diferencia | −0,269 (ee 0,018) → **z = −14,6** |

El perdedor típico entierra **7 de cada 10 energías que adjunta**; el ganador, menos de la
mitad. Es la correlación más fuerte que se ha medido en este proyecto, muy por encima de
cualquiera de las cuatro palancas algorítmicas que dieron empate.

**Aviso de causalidad, obligatorio.** Está confundido: perder implica que te maten cosas, así
que parte del efecto es consecuencia y no causa. **No se puede leer como «bajar la métrica 0,27
da +X% de winrate».** Lo que sí sostiene: (i) la dirección y la magnitud coinciden con lo que
predice la teoría (E4), (ii) es una métrica **observable, barata y directamente optimizable**
que hoy nadie mira, y (iii) el ranking de valor de la v1 puso E4 en ALTO por juicio y el dato
no lo contradice. Sirve como **función objetivo intermedia** para A/B rápidos: si un cambio
baja la energía enterrada sin bajar el winrate, va en la dirección buena.

**Condición detectable.** Ya implementada para esta nota: seguir `serial` → máximo de energías
visto, y sumar las de los serials que desaparecen de `active`+`bench`. ~25 líneas sobre
episodios ya descargados, sin jugar ni una partida.

**Valor.** ALTO. Es la que yo mediría primero, porque **da señal sin necesidad de ganar
partidas**: se puede iterar contra la métrica y validar con `arena.py` solo al final.

---

## N12. Vaciar la mano antes de refrescarla

**Qué es.** Cuando vas a jugar un Supporter que **baraja o descarta la mano** (Lillie's
Determination 1227, Iono, Judge, Lacey 1199, TR Ariana 1216), jugar primero todo lo que ibas a
jugar igualmente —items, energía, evoluciones— y refrescar al final. Es el caso donde la regla
«roba antes de buscar» de E5 se **invierte**, y por eso va aparte.

**Por qué.** El refresco convierte la mano en cartas nuevas; cada carta jugable que sigue en la
mano cuando lo juegas es una carta que has barajado gratis. Es el mismo principio de
minimizar compromiso, aplicado a un efecto que destruye información en vez de crearla.

**Condición detectable.** `refresco_con_mano_llena` = jugadas de un Supporter con «shuffle your
hand into your deck» o «discard your hand» habiendo en la mano ≥2 cartas que eran jugables ese
turno y no se jugaron. Se calcula cruzando el log 10 con las opciones ofrecidas en los
selects `(0,0)` anteriores del mismo turno.

**Valor.** MEDIO en `hops-snorlax` y en la baraja de ejemplo (4× Lillie's Determination). Se
implementa dentro del reorden de E5/N7 y no cuesta nada extra: es la excepción a la regla que
se está tocando de todas formas.

---

# PARTE 2-bis — Lo que midió la segunda pasada

Tres bloques: verificaciones cerradas, precios medidos y una advertencia.

## Verificaciones cerradas (eran los pendientes de la v1)

**1. Premios por KO — CERRADO.** `MEDIDO` sobre 250 episodios, quedándose solo con los KO
limpios (exactamente **un** Pokémon salió de juego entre dos observaciones, para no mezclar
KOs simultáneos ni evoluciones):

| Regla de la carta | n | Premios robados |
|---|---|---|
| normal (single-prize) | 497 | **1** en 465 (93,6%) |
| `Pokémon ex` | 125 | **2** en 123 (98,4%) |
| `Mega Pokémon ex` | 29 | **3** en **29/29 (100%)** |

**Mega ex = 3 premios, confirmado en el motor.** Toda la aritmética de E6, E10, E17, N2, N6 y
N8 se sostiene. El ruido de las filas «normal» con 2-3 premios es KOs múltiples en la misma
ventana de observación, no una excepción de regla.

**2. ¿El primero no ataca en el turno 1? — CERRADO: sí.** 0 logs de ataque (type 15) en
`turn == 1` sobre 120 episodios; el primer ataque de toda partida cae en el turno 2 (298
ocurrencias). La regla del papel está implementada. Pero ver E13: **eso no implica que
convenga ir segundo**, y de hecho el 99,2% de la ladder elige ir primero y el asiento que
elige gana el 53,5%.

**3. ¿Existe un Counter Catcher? — RESPONDIDO: la mecánica sí, la carta no.** Ver E20:
Counter Gain 1168 y Rosa's Encouragement 1240 dan la ventaja condicionada a ir perdiendo en
premios, pero **no hay gusting condicionado**. N6 es táctica *y* narrativa, pero no hay una
carta que la ejecute sola.

## Precios medidos (sustituyen a estimaciones de la v1)

| Métrica | Ganadores | Perdedores | Señal | Qué prioriza |
|---|---|---|---|---|
| Energía enterrada | 0,448 | 0,718 | **z = −14,6** | E4 / N11 — la palanca mejor respaldada |
| Premios expuestos en banca (media/obs) | **4,33** | 3,74 | z = +5,6 | **contradice** la versión ingenua de E6/N8 |
| Cuerpos en banca (media/obs) | **3,45** | 3,07 | — | idem |
| Duración de partida | mediana 13 turnos, p90 19 | | | el deck-out (E12) es marginal |

## La advertencia: el dato contradice a E6/N8 y hay que decirlo

La v1 marcó E6 («bajar todos los básicos posibles») como ALTO con ex y propuso «banca por
premios, no por cuerpos» como acción n.º 6. **El campo dice lo contrario**: los que ganan
tienen la banca **más llena** (3,45 vs 3,07 cuerpos) y exponen **más** premios (4,33 vs 3,74),
con z = +5,6.

Lectura honesta de por qué, sin barrer nada debajo de la alfombra:

- **Está confundido, casi con seguridad.** Banca llena es sobre todo un síntoma de haber
  montado la mesa; el que pierde muchas veces es el que se atascó y no pudo bancar nada. El
  dato mide «desarrollarse es bueno», que ya lo sabíamos.
- **Pero cambia la decisión igualmente.** No tenemos ninguna evidencia de que reducir la banca
  ayude, y sí una correlación fuerte en contra. Implementar «banca menos» a ciegas es
  arriesgarse a empeorar por la vía conocida: menos desarrollo, más turnos muertos tras un KO,
  y en el límite derrota por mesa vacía (`reason 3`).
- **Lo que sobrevive de E6 es la versión estrecha y solo esa**: *no bajar un multi-premio
  hasta el turno en que se usa*. Eso no reduce cuerpos en banca —se sustituye el ex por un
  single-prize— y por tanto no choca con el dato. Todo lo demás de E6/N8 queda **en
  suspenso hasta un A/B propio**.

Esto es material de writeup: el 70% de Model Score premia solidez y consistencia, y
«medimos nuestra propia recomendación, salió al revés y la retiramos» es exactamente la clase
de razonamiento que un jurado con jugadores de verdad sabe distinguir de una lista de tópicos
copiada de una guía.

---

# PARTE 3 — Qué hacer con esto

## Prioridad — REORDENADA 2026-08-11 con lo medido

Cambios respecto a la tabla de la v1: entra E16 en el n.º 1 (era invisible), E13 baja del n.º 2
al final (los datos lo desinflan), E6/N8 pasa a **congelado** (los datos lo contradicen), y
entran E17 y N11.

| # | Acción | Coste | Valor | ¿Toca al envío vivo (`hops-snorlax`)? |
|---|---|---|---|---|
| **1** | **Arreglar el filtro de trainers jugables** para que reconozca robo/búsqueda que no dice «draw»/«search» (Explorer's Guidance, Drayton, Pokégear, Dusk Ball, Grimsley's Move, Waitress) — E16, subgrupo bug | ~5 líneas | ALTO | Sí |
| **2** | **Medir sobre nuestros episodios** `energía_enterrada` y `cartas_inertes` — el detector, no la política (N11/E16) | ~40 líneas, 0 partidas | ALTO (da señal sin ganar) | Sí |
| **3** | **Rama de movilidad**: jugar Switch y afines, con puerta (E16) | ~15 líneas + select (1,4) | ALTO | Sí (2 Switch muertos) |
| 4 | **Energía a la banca cuando el activo muere igual** (E4/N4/N11) | ~15 líneas, reusa `_dano_contra` | ALTO | Sí |
| 5 | **Reordenar la fase principal**: energía después del robo y la búsqueda, con la excepción del refresco de mano (E5/N7/N12) | 4-8 líneas | MEDIO | Sí |
| 6 | **Contar premios** + gusting estrecho solo-para-letal (E3/E7/N5) | ~20 líneas + rama de gusting | MEDIO-ALTO | Sí |
| 7 | **Apertura barata**: activo inicial y banca de setup por premios, no por daño (E17/N10) | ~10 líneas | MEDIO-ALTO con ex / nulo aquí | No |
| 8 | **Elegir ataque con criterio**: penalizar lastre, desempatar KOs por coste, ver los ataques de daño 0 (E1/E2/N1/N3) | ~30 líneas | ALTO en 4 barajas | **No** (Snorlax tiene un solo ataque) |
| 9 | Tool y estadio con puerta de utilidad (E8/E9) | ~12 líneas | BAJO-MEDIO | Sí (Hop's Choice Band) |
| 10 | Coste pagado con la carta barata; `_util` distingue energía especial (E18) | ~6 líneas | BAJO-MEDIO | Sí |
| 11 | Promoción tras KO con cálculo de amenaza (E14) | reusa `_dano_contra` | BAJO-MEDIO | Sí |
| — | A/B primero/segundo (E13) | 1 línea | BAJO-MEDIO | Sí |
| ❄️ | **Banca por premios / banca menos (E6/N8)** | — | **CONGELADO**: el campo mide lo contrario (z = +5,6). Solo sobrevive «no bajar el multi-premio hasta usarlo» | No |
| ❄️ | Aritmética de veneno/quemadura (E19) | — | **CONGELADO**: 0 estados en 200 partidas del campo | No |

Lectura estratégica, revisada: la v1 decía que el reparto era «táctica que mueve la ladder» vs
«medida que destapa el laboratorio». Con lo medido el reparto real es otro:

- **1, 2 y 3 son de acceso**: hoy el agente no puede tocar mecánicas enteras. Antes de afinar
  una heurística, hay que darle las cartas.
- **4, 5 y 6 son las tácticas** que sí pueden mover la ladder de hoy.
- **7 y 8 no tocan `hops-snorlax`**: su valor es desbloquear la evaluación honesta de las
  demás barajas, que es Deck Score (20%), no ladder.
- **Los dos ❄️ son ahorro**: dos tardes que la v1 habría gastado y los datos dicen que no.

## El detector (propuesta, no escrito)

Un `research/replays/detector_errores.py` que recorra episodios (formato ya conocido,
**con la corrección de desfase 1**: la acción del paso *k* responde a la observación del
paso *k−1*, `replays-imitacion.md` §2) y emita un contador por partida con las condiciones de
arriba. Dos usos:

1. **Sobre nuestros propios episodios de ladder** (`kaggle competitions episodes 55407312` →
   `kaggle competitions replay <id>`): dice qué errores comete el agente que está jugando
   ahora mismo, con frecuencias reales. Convierte esta nota en una lista ordenada por datos y
   no por juicio.
2. **Sobre el campo** (los 9.337 episodios ya descargados): mide qué errores cometen los
   rivales. Los que el campo comete mucho son los que hay que castigar; los que no comete
   nadie son los que hay que dejar de arreglar.

Coste estimado: una tarde. Es la pieza que faltaría para dejar de estimar valores a ojo.

## Nota de calidad de fuentes

- **Sólidas y de comunidad**: `justinbasil.com` (recurso de referencia del competitivo),
  `sixprizes.com` (artículo clásico sobre misplays, 2012 — la taxonomía técnico/desarrollo
  sigue siendo la mejor que hay), `pokebeach.com` (no se pudo descargar: **HTTP 403**; lo
  citado viene solo de los extractos del buscador y está marcado).
- **Corroborar antes de usar en el writeup**: los artículos de `tcgprotectors.com` son el
  blog de una tienda y varios tienen pinta de contenido generado; sus **principios** coinciden
  con el resto de fuentes, pero no citaría de ahí ningún dato numérico ni nombre de carta sin
  contrastarlo con `cards_clean.csv`.
- Todo lo referido a **nuestro motor** (tipos de select, logs, premios, condiciones de fin,
  contenidos del pool) sale de `motor-mecanica.md`, `cartas-pool.md`, `lab-barajas.md`,
  `baraja-vs-campo.md` y de consultas hechas para esta nota sobre `research/cards_clean.csv`,
  no de la web.

Añadido en la segunda pasada:

- **La mejor fuente encontrada** es <https://sixprizes.com/2014/10/02/deft-decisions/>, que
  separa *technical play* de *strategic play* y describe al jugador flojo en términos que
  encajan con nuestro agente literalmente: «inexperienced players play the game on autopilot,
  and when their primary strategy cannot be found, they give up at the lack of any other
  strategy». También aporta el concepto de **dead-end play** («one in which nothing was
  achieved... those one or two turns could have been the difference between losing and
  winning»), que es una etiqueta de detección aprovechable tal cual.
- **Trampa de homónimos, importante**: buena parte del contenido reciente sobre «going first vs
  going second», «mejores mazos» y «errores de principiante» que devuelven los buscadores es de
  **Pokémon TCG Pocket**, que es otro juego (energy zone, 3 premios, banca de 3). Antes de
  citar cualquier cosa en el writeup hay que comprobar de qué juego habla. Ya nos habría hecho
  invertir la decisión de primero/segundo en contra de nuestros propios datos (E13).
- Sobre condiciones especiales, las tres fuentes coinciden en la aritmética (veneno 1 contador
  entre turnos, quemadura 2): <https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-special-conditions-guide>,
  <https://www.thegamer.com/pokemon-tcg-every-status-effect-guide/>,
  <https://dotesports.com/guides/news/special-conditions-in-the-pokemon-trading-card-game-explained>.
  No verificada contra el motor: **el campo no las usa** (E19), así que no hay observaciones
  con las que contrastar.
- Nada de lo medido en la segunda pasada viene de la web: sale del corpus de episodios y del
  CSV del pool. Las URLs sirven para **nombrar** el error y para el writeup; los **números**
  son nuestros.

## Pendientes de verificación — estado 2026-08-11

Los tres de la v1 están **cerrados** (detalle y números en «PARTE 2-bis»):

1. ~~¿Cuántos premios da un Mega ex?~~ → **3**, medido en 29/29 KOs limpios. El truco que
   faltaba era hacerlo por `serial` y descartar las ventanas con más de un Pokémon saliendo de
   juego, tal y como sospechaba la v1.
2. ~~¿El primero no puede atacar en el turno 1?~~ → **Sí, no puede**: 0 ataques en `turn == 1`
   sobre 120 episodios. Pero E13 se revisó y la conclusión práctica se invirtió.
3. ~~¿Existe un Counter Catcher?~~ → La **mecánica** sí (Counter Gain 1168, Rosa's
   Encouragement 1240); el **gusting condicionado**, no.

Nuevos pendientes que abre esta pasada:

4. **¿Cuánto vale de verdad E16?** Hay que medir `cartas_inertes_por_partida` sobre nuestros
   propios episodios de ladder (`kaggle competitions episodes 55407312`) antes de estimar el
   winrate que devuelve. Es el n.º 2 de la prioridad.
5. **¿Sobrevive E6 a un A/B?** El campo dice que banca llena correlaciona con ganar, pero está
   confundido. La única forma de separarlo es `arena.py` con la puerta estrecha («no bajar el
   multi-premio hasta usarlo») contra el v2. Hasta entonces, congelado.
6. **¿Qué hace el motor con las cartas que hoy no jugamos?** Switch abre un select `(1,4)` y
   Boss's Orders uno de banca rival; ambos están en la taxonomía de `motor-mecanica.md`, pero
   **nuestro agente nunca los ha visto en producción**. Antes de meter la rama de movilidad,
   un probe corto que confirme la forma de esos selects — el coste de equivocarse es una
   acción ilegal, y a nivel Kaggle la primera excepción mata la partida.

## Cómo se hicieron las medidas de esta pasada (reproducible)

Todo sale de `data/replays/pokemon-tcg-ai-battle-episodes-2026-08-08.zip` (4.669 episodios) y
de `research/cards_clean.csv`, con muestreo aleatorio semilla fija y **un solo proceso** (había
otro trabajo en la máquina). Nada de esto requirió jugar partidas nuevas.

- **Resultado de partida**: `ep["rewards"]` del JSON del episodio. Ojo: `current["result"]`
  vale −1 en la última observación visible y el log 23 **no** aparece en las observaciones del
  corpus — el agente nunca ve el final (ya lo decía `motor-mecanica.md` §5, aquí se confirma
  desde el otro lado). Quien mida winrates leyendo `result` obtendrá 0 partidas y creerá que
  el corpus está roto.
- **Premios por KO**: diferencia de `len(players[j]["prize"])` entre observaciones consecutivas
  cruzada con los `serial` que desaparecen de `active`+`bench` del rival; solo ventanas con
  exactamente un Pokémon saliendo.
- **Energía enterrada**: por `serial`, máximo de `len(energies)` visto; se suman los serials
  que desaparecen y se divide por el total invertido.
- **Muestras**: 500 partidas (primero/segundo), 400 (banca), 350 (energía), 250 (premios), 200
  (estados), 120 (ataques en turno 1). Semillas 11, 21, 33, 3, 5, 7.
