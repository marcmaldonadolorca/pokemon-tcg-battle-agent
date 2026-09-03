# DECISIONS — kaggle-pokemon-tcg

## Pendientes de decidir

### PKM-D01 · ¿Se entra o no? (del propietario, antes del 2026-08-09)

Entrar cuesta un clic ahora y, después, tiempo en la ventana más cargada del
año: envío del agente el **16-ago** (un día después del corte del TFM) y writeup
el **13-sep** (entre la entrega del 1-sep y la defensa del 21-sep).

A favor: 8 finalistas a 30.000 USD sobre 313 equipos en la Strategy, con un
criterio que premia el análisis por encima del puesto en el leaderboard —
justo lo que sabemos hacer y lo que ya funcionó en `kaggle-rogii`. El motor
corre en la torre a 31,5 partidas/s y no depende de comprar nada.

En contra: el TFM manda hasta el 21-sep y esto se come días de agosto.

**Aceptar las reglas no obliga a enviar nada.** No hacerlo antes del 9-ago sí
cierra la puerta del todo. Recomendación de Claude: aceptar ahora y decidir el
esfuerzo después, con el baseline ya medido.

### PKM-D02 · ¿Cuánto esfuerzo? (después de PKM-002)

Tres niveles, para decidir con el baseline delante y no antes:

1. **Mínimo digno** — agente heurístico decente + writeup honesto. Pocos días.
2. **Serio** — MCTS con determinización, baraja diseñada y medida. Es donde está
   el ratio premio/esfuerzo según los criterios publicados.
3. **Todo** — self-play/RL sobre el motor. Choca de frente con el TFM.

## Decisiones tomadas

### PKM-018 · Un compromiso con plazo en ausencia del propietario exige tarea programada, no aviso en segundo plano (2026-08-17)

**Medido:** el 14-ago el propietario autorizo por escrito (`PKM-017`) que Claude
empaquetase y subiese el envio final antes del corte del 16-ago 23:59 UTC. La arena
que decidia termino ese mismo dia a las **19:35** con un resultado holgado —
`30d+RC` gana **0,7462 [0,7244, 0,7670]** al agente de la ladder, n=1.600 — es decir,
la regla del IC limpio daba luz verde con dos dias de margen. **El envio no se subio.**
La Simulation cerro con el agente del 12-ago: puesto **2.138 de 6.892**, score 690,7.

**Causa raiz:** el resultado llego 15 minutos despues de acabar el turno de la sesion.
Los guardianes de segundo plano (`Bash run_in_background`, `Monitor`) **informan pero
no ejecutan**: no reactivan una sesion dormida. Sus notificaciones se entregaron el
17-ago, con el plazo ya cerrado. Se confio un compromiso con fecha a un mecanismo que
solo avisa, y no se programo ninguna tarea real que lo disparase.

**Decision:** cuando exista un compromiso de ejecutar algo con plazo y sin el
propietario delante, se crea en el mismo turno una **tarea programada** (`/schedule`,
cron) que lo ejecute, o se ejecuta de forma sincrona antes de cerrar el turno. Un
aviso en segundo plano no cuenta como plan de ejecucion. Si no se puede programar,
se dice explicitamente que la accion queda pendiente de una nueva sesion, para que
el propietario decida si la asume el.

**Consecuencia:** coste real acotado al rank de la Simulation, que es la parte que
menos pesa (`PKM-004`: el top-8 de la Strategy se elige por evaluacion holistica y
el puesto de la ladder solo «se considera»). El material medido sigue intacto para el
writeup del 13-sep, que es donde esta el premio.


### PKM-017 · El envío final lo ejecuta Claude con una regla fija; la baraja queda delegada (2026-08-14)

**Contexto:** corte de envíos el 2026-08-16 a las 23:59 UTC, y el propietario no
trabaja este fin de semana. El calendario oficial aclara que del **17-ago al ~31-ago
se siguen jugando partidas hasta que converge el leaderboard**, así que subir en el
último momento **no penaliza la convergencia**: la urgencia era decidir, no subir.

**Decisión del propietario (autorización explícita, 2026-08-14):**

1. **Claude empaqueta, verifica y sube** el envío final sin gate adicional.
2. **Qué sube — regla del IC limpio:** entra la configuración cuyo intervalo de
   confianza al 95% contra el agente que está en la ladder **no toque 0,5**. Si
   `30d+RC` lo consigue, sube `30d+RC`; si no llega, sube `RC` solo, ya validado
   (0,6350 [0,6111, 0,6582], n=1.600); si `RC` tampoco valiera en `c1-grimmsnarl`,
   ese slot **se queda como está**. Ninguna palanca entra sin arena.
3. **Baraja delegada en Claude:** si el margen sobre el de la ladder es holgado, puede
   entrar la lista propia `mia-crustle-tijeras` en un slot (compra el 20% de Deck
   Score de la Strategy); si el margen es justo, se mantienen las dos de campo.

**Consecuencia:** el criterio de PKM-004 (consistencia por encima del puesto) sigue
mandando — la regla del IC limpio es exactamente eso aplicado al envío. Lo que no
esté medido en arena no viaja en el paquete.


### PKM-016 · Cómo se mide un duelo entre redes: envoltorio a los DOS lados y BLAS a un hilo (2026-08-12)

**Medido:** dos cosas independientes que afectan a todo número futuro del proyecto.
(1) `clon.py` y `clon_busq.py` resuelven sus pesos leyendo una variable de entorno
**en tiempo de importación**, y `arena.py` carga los dos agentes en el mismo proceso;
si un lado es un envoltorio que fija la variable y el otro es el módulo pelado, el
segundo hereda los pesos del primero y el duelo se convierte en self-play, que da
0,50 pase lo que pase (`clon-escalado.md` §0: ~20 celdas invalidadas). Fijar la
variable *antes* de cada carga arregla el caso simétrico pero deja viva la trampa en
cuanto alguien vuelve a meter un módulo pelado. (2) Con BLAS multihilo, una arena de
120 partidas tarda **30,8 s y quema ~11 núcleos**; con `OMP_NUM_THREADS=1` tarda
**21,4 s y quema 3**. Las matrices del clon son diminutas y el hilado solo añade
sincronización. **Decisión:** todo duelo entre juegos de pesos se corre con los dos
lados envueltos y con los pesos fijados **después** del `exec_module`
(`_m._RUTA = ...`, `scratchpad/final/mk.py`), nunca por entorno; y toda medida va con
`OMP_NUM_THREADS=1`. **Consecuencia:** el orden de carga deja de importar y la misma
máquina rinde ~3× más medidas por hora. **Reversión:** no procede, es más barato y
más correcto.

### PKM-015 · Las dos listas del envío se eligen por criterios distintos: `c2-alakazam` por suelo, `c1-grimmsnarl` por media (2026-08-12)

**Medido** con `research/clon/campo_sp.py` (nuestro agente + nuestra lista contra los
12 arquetipos del campo, 96,3% de cobertura, pilotados por el clon de la ladder) y con
**el piloto que se envía**, `busq(d7h384)`, n=150 por emparejamiento (1.800 partidas
por fila):

| lista | POND | IC95 | PEOR emparejamiento |
|---|---|---|---|
| `c1-grimmsnarl` | **0,7378** | [0,7091, 0,7665] | **c6-ogerpon 0,147** (5,0% del campo) |
| `c2-alakazam` | 0,7067 | [0,6761, 0,7373] | **c1-grimmsnarl 0,547** |

Las dos empatan en media (IC solapados) y se separan en el suelo: **`c2-alakazam` no
tiene una sola casilla de las doce por debajo de 0,50**; `c1-grimmsnarl` tiene un
agujero de 0,147 contra Ogerpon y dos casillas en 0,52-0,54. **Decisión:** slot 1
`c2-alakazam` (el 70% del Model Score puntúa *no depender del emparejamiento*, y es
además la lista que ya está en la ladder, así que el A/B aísla el piloto); slot 2
`c1-grimmsnarl` (media, y cobertura del riesgo de que el rating premie la media).
**Consecuencia:** el envío ya no cambia lista y piloto a la vez. **Aviso
metodológico:** el orden entre listas NO se invirtió en este salto de piloto (al
contrario que en PKM-012), pero las distancias cambiaron mucho — con la red sola
`c1-grimmsnarl` sacaba +0,157 a `c2-alakazam`, con la búsqueda encima +0,031 y sin
significación, porque la búsqueda le compra a `c2-alakazam` +0,128 de POND y le sube
el suelo de 0,405 a 0,547. La regla de PKM-012 (re-medir la lista con el piloto que
se envía) sigue siendo obligatoria. **Necesita decisión del propietario:** las dos
listas son copias del líder de su arquetipo; la lista propia `mia-crustle-tijeras`
está medida y su coste está cuantificado (§4 de `verificacion-y-envio-final.md`).

### PKM-014 · El envío lo pilota la BÚSQUEDA sobre la red grande: `clon_busq.py` + `politica_7d_h384_mejorval.npz` (2026-08-12)

**Medido** (arena, misma lista a los dos lados, asientos intercambiados, muestras
frescas, `--procs 3`, contra `research/agentes/clon.py` que es lo que está en la
ladder con μ 547,8):

| agente, c2-alakazam | n | tasa | IC95 |
|---|---:|---:|---|
| solo red nueva `d7h384` | 2.000 | 0,724 | [0,704, 0,743] |
| solo búsqueda `busq(politica.npz)` | 2.000 | 0,709 | [0,688, 0,728] |
| **las dos, `busq(d7h384)`** | **2.000** | **0,859** | **[0,843, 0,873]** |

**Los dos ejes se suman y se suman en log-odds**: 0,964 + 0,891 = 1,855 predicho
contra 1,807 observado (0,865 contra 0,859 medido). Comprobado además de frente, con
la búsqueda encendida en los dos lados: **`busq(d7h384)` vs `busq(politica.npz)`
0,731 [0,705, 0,755]** (n=1.200) contra el 0,714 que predice la aditividad — cambiar
la red debajo de la búsqueda sigue comprando +0,23. No hay interferencia. La
verificación independiente de los dos informes del día confirmó las cuatro
afirmaciones vivas (0,6778→**0,696**, 0,7190→**0,724**, 0,699→**0,680**,
0,705→**0,709**); las vías 1 y 2 del auto-juego siguen descartadas por su propio
informe. La red se eligió con un torneo en **las dos** listas candidatas porque la
báscula de redes se invierte con la baraja: `d7h384` bate a `e20` 0,584 y a `d7h192`
0,589 en c2-alakazam y 0,529 en c1-grimmsnarl, mientras `e20` y `d7h192` empatan
entre sí (0,489). **Decisión:** el piloto del envío es `research/agentes/clon_busq.py`
con `research/clon/politica_7d_h384_mejorval.npz` copiada como `politica.npz` dentro
del paquete. **Consecuencia:** el envío pasa de 0,206 ms a ~32 ms por decisión; la
auditoría de 1.000 estados (500 partidas contra los 12 arquetipos) da **0 anomalías,
0 ilegales, 0 fallbacks, 0 determinizaciones fallidas**, p95 100,7 ms, máximo 193,3 ms
y peor partida 3,88 s — **×155 de margen** sobre el banco de 600 s, midiendo con un
solo hilo y la máquina cargada. **Reversión:** trivial, `envios/clon-c2-alakazam.tar.gz`
(el clon sin búsqueda) sigue construido y validado.

### PKM-013 · El clon entra como piloto del envío; los híbridos y `heuristico_v6` se quedan fuera (2026-08-12)

**Medido** (arena, mega-lucario a los dos lados, asientos intercambiados, `--procs 3`,
muestras frescas e independientes de las que reportaron los informes): el clon de
política bate al piloto de la ladder **0,651 [0,630, 0,672]** n=2.000, al mejor
heurístico del repo (`heuristico_v6` = v5+`recupera`) **0,539 [0,517, 0,561]** n=2.000, y
el propio v6 bate al v2 **0,611 [0,589, 0,632]** n=2.000. Las tres cifras confirman lo
reportado (el 0,563 del informe baja a 0,539: maldición del ganador, sigue significativo).
Además el clon **ya juega las cuatro cartas que la tanda de cobertura tuvo que resucitar
a mano** (Night Stretcher 0,48/partida, Tarragon 0,42, Switch 0,28, Premium Power Pro
0,44, contra 0 del v5/v6 sin la familia): la familia `recupera` que sobrevivió al gate es
redundante dentro del clon. **Decisión:** el envío lo pilota `research/agentes/clon.py`
con `research/clon/politica.npz` (2 épocas, H1=96); el `heuristico_v6` queda como rival de
banco, no como candidato. **Consecuencia:** la línea de refinar reglas a mano se cierra
después de once hipótesis; el trabajo futuro va a la red. **Reversión:** trivial, los
paquetes del v2, v5 y v6 siguen en `envios/`. **Negativo medido:** el híbrido por
confianza (la red decide salvo cuando su softmax top-1 < 0,17) da 0,550 [0,529, 0,572]
contra el v6 frente a 0,539 del clon puro — +1,1 pp con IC solapados, **no entra**; pero
a diferencia de los híbridos por clase de decisión (0,486 y 0,445) ya no hace daño, así
que el problema de los híbridos es el VOLUMEN de decisiones cedidas, no mezclar.

### PKM-012 · La báscula de barajas se invierte con el piloto: mega-lucario estaba elegida con el instrumento equivocado (2026-08-12)

**Medido:** `research/gauntlet.py` con las mismas 12 listas del campo y n=200 por
emparejamiento (2.400 partidas por fila), cambiando SOLO el piloto de los dos lados:

| lista | POND piloto v2 (flojo) | POND piloto clon (fuerte) |
|---|---|---|
| mega-lucario | **0,758** [0,746, 0,769] | **0,362** [0,337, 0,386] |
| c1-grimmsnarl | 0,413 [0,385, 0,441] | **0,558** [0,530, 0,586] |
| c2-alakazam | 0,358 [0,330, 0,385] | **0,454** [0,427, 0,482] |

El orden se da la vuelta entero, con IC disjuntos. El espejo lo confirma por otra vía: la
ventaja del clon sobre el heurístico depende de la lista — +4 pp en mega-lucario (0,539),
+29 en alakazam (0,789), +41 en grimmsnarl (0,906). **Interpretación:** mega-lucario es un
aggro que un puñado de reglas ejecuta casi óptimamente; las listas del meta ganan montando
secuencias que la heurística no sabe montar y la red sí. **Decisión:** toda elección de
lista se re-mide con el piloto que se va a enviar, y la tabla del gauntlet queda indexada
por piloto (ya lo estaba). Esto **cierra PKM-006**, que aplazó la decisión de lista a
«cuando el piloto sea bueno». **Consecuencia:** es el material más fuerte del writeup —
el 70% del Model Score premia detectar exactamente este tipo de trampa de evaluación.
**Reversión:** ninguna, es una medida.

### PKM-011 · El envío es `clon + c2-alakazam`, con `clon + c1-grimmsnarl` en el segundo slot (2026-08-12)

**Medido:** contra el campo con el clon pilotando también al rival (el rival más fuerte
disponible; no existe `sparring.md`), `clon+c2-alakazam` da POND **0,454** con **peor
emparejamiento 0,299** (confirmado aparte con n=1.000), frente a 0,362 / **0,105** de
`clon+mega-lucario`. Contra el campo flojo, 0,8252 [0,8054, 0,8449] con peor 0,720 frente
a 0,8155 con peor 0,322. En duelo directo, `clon+c2-alakazam` gana **0,882 [0,867, 0,895]**
(n=2.000) a `clon+mega-lucario` y **0,880** (n=1.000) al par que está empaquetado hoy
(`heuristico_v6`+mega-lucario). Tapa los dos agujeros históricos (kangaskhan 0,278→0,736,
ogerpon 0,335→0,720 contra el campo flojo). Auditoría de 500 partidas contra los 12
arquetipos: **1.000/1.000 DONE, 0 ilegales, 0 fallbacks, 0 excepciones**, 0,206 ms por
decisión (p95 0,371) y **×10.961 de margen** sobre el banco de 600 s con un solo núcleo.
**Decisión:** primer slot `envios/clon-c2-alakazam.tar.gz`; segundo slot
`envios/clon-c1-grimmsnarl.tar.gz`, que tiene mejor media (0,558 / 0,8654) pero un suelo
de 0,125 en el 11,8% del campo. Los dos slots activos sirven además de experimento real
sobre qué criterio manda. **Consecuencia:** `mega-lucario` deja de ser la lista del envío
(sigue intacta en el repo y en la ladder). **Riesgo asumido:** las dos listas son copias
exactas de la líder de su arquetipo tomadas del censo de replays públicos, no listas
propias; el writeup lo dice, y si el propietario prefiere lista propia el coste medido es
de 0,882 a 0,500 en el duelo directo. **Reversión:** `envios/clon-mega-lucario.tar.gz` ya
está construido y validado.

### PKM-010 · El eje para elegir baraja era el equivocado (2026-08-10)

**Medido:** censo de las barajas rivales reales extraídas de 12 replays de la
ladder — **Mega Lucario 42%**, Alakazam 17%, tipo-ejemplo 17%, Garchomp 8%.
**El campo real no juega la baraja de ejemplo del motor**, que es precisamente
contra la que se rankearon las 15 listas. Contra la incumbente `hops-snorlax`
(n=300 por rival, asientos intercambiados) **pierde frente a 10 de 14 listas**;
y contra un proxy del campo real (6 listas del meta + la de ejemplo, n=200 cada
una) `mega-lucario` saca **0,606** frente al **0,497** de `hops-snorlax`.
**Decisión:** el segundo slot va con `mega-lucario` y el mismo piloto byte a byte
(md5 de la política idéntico), para aislar **la lista** como única variable.
**Consecuencia:** el A/B de la ladder resuelve la elección de baraja con datos
reales en vez de con el proxy sesgado. **Hallazgo metodológico extra:** el swing
de asiento medido en espejo (+0,174) **no predice** el del campo (+0,054) —
otra medida local que no transfiere.

### PKM-009 · Retirada y gusting: dos negativos medidos (2026-08-10)

**Medido:** implementadas ambas palancas en `heuristico_v3.py` y medidas por
separado contra el v2 con la misma baraja en ambos lados —
retirada **0,476 [0,451, 0,501]** (n=1.500), gusting **0,495 [0,469, 0,520]**
(n=1.500), ambas juntas **0,498 [0,475, 0,520]** (n=1.900). Ninguna mejora, y
los intervalos excluyen ganancias mayores de 3 puntos.
**No es por falta de uso:** en 400 partidas se contaron 27 retiradas y 149
gustings (141 de ellos por KO). **Decisión:** quedan implementadas y
**apagadas por defecto**; el envío sigue con el v2. **Consecuencia:** invalida
la hipótesis que sugería el replay perdido («llevamos 2 Boss's Orders muertas,
por eso perdemos») — la observación era cierta pero la conclusión no: usarlas
bien no cambia el resultado. **Hallazgo lateral:** el select de banca **rival**
llega con el mismo `context` 3 que la promoción propia tras KO y solo se
distingue por el `playerIndex` del option; el v2 estaba puntuando la banca
propia con índices de la rival.

### PKM-008 · Función de valor: los rasgos tácticos sí aportan (2026-08-10)

**Medido, con protocolo honesto** (corte por id de partida, 70/15/15, época
elegida en validación y resultado reportado en test, 3 semillas):

| | acierto | log-loss | sobre base 0,5419 |
|---|---|---|---|
| v1 (30 rasgos densos) | 0,7238 ± 0,0054 | 0,5132 | +0,182 |
| **v2 (62 rasgos, + tácticos)** | **0,7539 ± 0,0057** | **0,4886** | **+0,212** |

Diferencia pareada por partida **+0,0276 ± 0,0042 (z = 6,6)**. Con la capacidad
igualada (red doble de ancha para la v1) la ventaja de los rasgos sigue siendo
**+0,0189 (z = 4,5)**: es información nueva, no más parámetros. Los rasgos que
aportan son los de combate y premios (`mata_ya`, `me_mata_ya`, cuántos premios
concede cada Pokémon al caer).
**Corrección:** el 72,66% que se reportó primero para la v1 **estaba inflado**.
El corte troceaba por cambios de etiqueta, y como cada partida aporta sus dos
perspectivas con etiquetas opuestas, mitades de la misma partida caían a los dos
lados; la fuga valía +0,0051. La cifra honesta de la v1 es **0,7238**.
**Decisión:** adoptar la v2 de rasgos y mantener la red pequeña (32→16 satura).

### PKM-007 · La búsqueda pura no rinde: la palanca es la función de valor (2026-08-10)

**Medido:** ISMCTS (K=8 determinizaciones, 13.920 iteraciones por decisión)
contra el heurístico: **0,529 IC95 [0,466, 0,591]** en 240 partidas — empate
estadístico gastando **~9.000× más cómputo** (0,785 s por decisión frente a
0,083 ms; equivalentemente 19,9 s por partida frente a ~2,2 ms).
**Corrección 2026-08-10:** una versión previa de este ADR decía «~230.000×»,
cifra errónea por comparar segundos **por partida** del MCTS contra milisegundos
**por decisión** del heurístico. El ratio correcto es ~9.000×.
**Añadido 2026-08-10:** con la función de valor aprendida enchufada como
evaluación de hoja, el resultado es **0,487 IC95 [0,425, 0,550]** (n=240) — sigue
siendo empate. La red predice bien el ganador pero no mejora las decisiones del
árbol, así que el cuello no está en la evaluación de las hojas. Concuerda con dos evidencias externas: el sample oficial de HEROZ guía
su MCTS con una red **value+policy** y le bastan **10** expansiones, y en los
foros de la competición se reporta que «los value heads son flojos y por eso la
búsqueda no ayuda» en este juego de información imperfecta.
**Decisión (del propietario, 2026-08-10):** invertir el tiempo restante en una
**función de valor aprendida** por self-play, no en más búsqueda ni en afinar la
heurística. **Consecuencia:** el envío base va con el heurístico (empata al MCTS
por una fracción ínfima del coste) y la red se integra como evaluación de nodos
hoja cuando bata al heurístico en arena. **Reversión:** el MCTS queda intacto en
`research/agentes/mcts.py`; cambiar la evaluación es un punto de enganche.

### PKM-006 · El ranking de barajas mide baraja × piloto, no baraja (2026-08-10)

**Medido:** con el heurístico pilotando ambos lados, la baraja de ejemplo del
motor bate a **13 de 15** listas, incluidas las del meta real de la ladder
(Grimmsnarl 0,257, Alakazam 0,260, Garchomp 0,253). Eso contradice frontalmente
la realidad observable: Grimmsnarl tiene el 51% de share y lo juega el nº1.
**Interpretación:** la de ejemplo es un aggro simplísimo (33 energías básicas)
que el heurístico ejecuta bien, mientras que los mazos del meta ganan con
secuencias de combo que no sabe montar; los pasos lo delatan (48 frente a 65-80).
**Decisión:** no elegir baraja con esta tabla. Se usa `hops-snorlax` (propia,
single-prize) para el primer envío por ser lo mejor propio, y la elección final
se decide con **rating real de la ladder** y con el ranking rehecho cuando el
piloto sea bueno. **Consecuencia:** el sesgo piloto↔baraja pasa a ser material
del writeup — es exactamente el tipo de trampa que el 70% de Model Score premia
detectar. **Señal limpia rescatada:** en espejo (misma lista y piloto en ambos
lados) la ventaja de salir primero sí es real y varía por baraja — Mega
Kangaskhan 0,633 contra 0,300.

### PKM-005 · Validar el envío con `exec` y sin `__file__` (2026-08-10)

**Medido:** el envío `55407115` quedó en `ERROR` con
`NameError: name '__file__' is not defined` — Kaggle **ejecuta** `main.py` con
`exec(code_object, env)` en vez de importarlo. La validación local lo hacía con
`import main`, donde `__file__` sí existe, así que daba verde con un paquete roto.
**Decisión:** la validación replica el entorno real (chdir al paquete, repo fuera
de `sys.path`, `compile`+`exec` sin `__file__`) y además comprueba que el
catálogo carga **completo** dentro del tar, porque el heurístico degrada en
silencio si no encuentra su CSV. **Consecuencia:** ningún envío sale sin
reproducir el arranque de producción. Detalle en `docs/empaquetado-y-envio.md`.

### PKM-001 · El motor se toma de PyPI, no de la competición (2026-08-06)

**Medido:** `kaggle-environments` incluye `envs/cabt/` con `libcg.so` x86-64, y
una partida completa corre en la torre sin haber aceptado las reglas de la
Simulation. **Decisión:** desarrollar contra el paquete de PyPI y no bloquear
nada esperando al gate. **Consecuencia:** la preparación entera se pudo cerrar
sin intervención del propietario. **Riesgo asumido:** la competición cita la
versión 1.14.10, inexistente en PyPI; usamos la 1.32.4 (ficheros de `cabt` del
2026-08-04). Si aparece una discrepancia de comportamiento, este es el primer
sospechoso. **Reversión:** trivial, fijar otra versión en `requirements.txt`.

### PKM-002 · Paralelizar solo con procesos (2026-08-06)

**Medido:** cuatro hilos jugando partidas matan el proceso —primero
`std::length_error` desde el C++, luego SIGSEGV limpio—, porque `Battle.battle_ptr`
es estado global del módulo. No es capturable con `try/except`.
**Decisión:** todo experimento paralelo va con `multiprocessing`, un `env` por
partida, punto de trabajo en 8 procesos (a 16 solo se gana un 16%).
**Consecuencia:** ningún diseño puede apoyarse en hilos ni en un pool compartido
de entornos. Comprobado por `research/smoke_paralelo.py`, que aísla la prueba en
un subproceso precisamente porque tumba a quien la lanza.

### PKM-003 · Usar las variantes de CSV con guion bajo (2026-08-06)

**Medido:** Kaggle publica dos versiones de cada CSV de cartas con md5 distinto.
Las de espacio (`EN Card Data.csv`) llevan BOM UTF-8 y la errata `Previos stage`
en la cabecera; las de guion bajo (`EN_Card_Data.csv`) están corregidas.
**Decisión:** trabajar solo con las de guion bajo. **Consecuencia:** evita un
`KeyError` silencioso al leer la columna de evolución previa.

### PKM-004 · Optimizar consistencia, no puesto en el leaderboard (2026-08-06)

**Base:** los criterios publicados de la Strategy dan 70% a un «Model Score»
cuyos puntos son claridad del enfoque, originalidad, **consistencia bajo partidas
repetidas** y **no depender de estados iniciales o emparejamientos concretos**.
Las reglas dicen explícitamente que un puesto alto no garantiza buen resultado y
que la zona media puede puntuar alto con buen análisis.
**Decisión:** el objetivo es un agente estable y bien medido con un informe que
demuestre por qué lo es, no trepar entre 6.400 equipos.
**Consecuencia:** el presupuesto va a arnés de evaluación e intervalos de
confianza antes que a exprimir el rating. Es la misma tesis que en `kaggle-rogii`,
donde la solución propia y simple batió en privado al pipeline público.
