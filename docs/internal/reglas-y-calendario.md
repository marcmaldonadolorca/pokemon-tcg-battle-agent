# Reglas, calendario y gates — Pokémon TCG AI Battle Challenge

Verificado el 2026-08-06 leyendo las páginas de Kaggle renderizadas (Firefox
headless vía geckodriver; la web es una SPA y `curl` solo devuelve el esqueleto).

## 1. Son dos competiciones acopladas, no una

De la página de la Strategy, literal:

> Participation in the Simulation Category of the Pokémon TCG AI Battle Challenge
> **is required** to enter this Strategy Category competition. Participants must
> enter in **both** the Simulation Category and Strategy Category for a complete
> submission.

Y de las reglas oficiales de la Strategy (§4.c de las Competition-Specific Rules):

> In order to be eligible for prizes, participants must compete as part of the
> **same Team registered in the Simulation division**. Cross-division Team
> composition must remain identical.

La página de la Simulation dice lo simétrico en negativo — «Participation in the
Hackathon is **not** required to enter this competition» — que es coherente: se
puede competir solo en Simulation, pero no solo en Strategy.

**Consecuencia:** el plan anterior («intake la semana del 7-sep, entre entrega del
TFM y defensa») **no es viable**. Para entonces la Simulation llevará tres semanas
cerrada y no habrá forma de entrar en la Strategy.

## 2. Calendario real

| fecha | qué | quién |
|---|---|---|
| **2026-08-09** | **Entry deadline de la Simulation.** «You must accept the competition rules before this date in order to compete.» También es el team merger deadline | **Propietario (un clic)** |
| 2026-08-16 | Envío final del agente a la Simulation | Claude + propietario |
| 2026-08-17 → ~08-31 | Se siguen jugando partidas hasta que converge el leaderboard | — |
| 2026-09-06 | Entry deadline de la Strategy (ya inscrito) | hecho |
| 2026-09-13 | Envío final del writeup | Claude + propietario |
| 2026-09-14 → 10-11 | Periodo de evaluación por el jurado | — |

Todos los cortes son a las 23:59 UTC.

Estado de inscripción medido con la CLI el 2026-08-06:
`pokemon-tcg-ai-battle-challenge-strategy` → `userHasEntered: True`;
`pokemon-tcg-ai-battle` → `userHasEntered: False` (y `competitions download` de
esa competición devuelve **403**, que es la prueba de que faltan sus reglas).

## 3. Qué se entrega

### Simulation
`.tar.gz` con `main.py` en la raíz (no anidado) y un `deck.csv`.
`tar -czvf submission.tar.gz *`. Los ficheros acaban en
`/kaggle_simulations/agent/`.

Límites del entorno de evaluación: **197,7 MiB** de envío, 11,8 GiB de disco,
12,2 GiB de RAM, **2 vCPU**. Cinco envíos al día, solo los **2 últimos** siguen
activos.

Ranking por rating gaussiano N(μ, σ²) con μ₀ = 600, emparejando rivales de
rating parecido. El margen de victoria no influye: solo ganar, perder o empatar.

### Strategy
Writeup de Kaggle, **≤ 2.000 palabras** («submissions over this limit may be
subject to penalty»), con título, subtítulo y análisis. Media gallery opcional.
Un writeup en borrador sin pulsar *Submit* **no se evalúa**.

Aviso de las reglas: si adjuntas un recurso privado de Kaggle a un writeup
público, **se hace público automáticamente** tras el deadline.

## 4. Cómo puntúa la Strategy

| categoría | peso | qué miran |
|---|---|---|
| Model Score | **70%** | Claridad del enfoque y de su justificación; originalidad y solidez técnica; **consistencia bajo partidas repetidas**; que la estrategia **no dependa de estados iniciales, emparejamientos o ventajas situacionales concretas**; rendimiento en el track |
| Deck Score | **20%** | Claridad del concepto de baraja y su alineación con la estrategia; elección y uso de las cartas clave |
| Report Score | **10%** | Estructura y redacción; uso eficaz de figuras, tablas y gráficos |

Dos frases que fijan la estrategia de este proyecto:

> High leaderboard ranking **may provide an advantage** in performance scoring,
> but **it does not guarantee** a strong result in the Strategy Category.

> Participants in middle or lower tiers of the competition **can still achieve
> high overall scores** through deep analysis, originality, and well-structured
> reporting.

Es decir: con 6.400 equipos en la Simulation, pelear por el top del leaderboard
es mal negocio. Lo que paga es un agente **decente y medido** más un informe que
demuestre por qué funciona. La palabra que se repite en el 70% es *consistencia*,
no *máximo*.

## 5. Premios y jurado

Main Track, 240.000 USD: **ocho finalistas a 30.000 USD cada uno**, con posible
invitación a un torneo presencial en Tokio. No da puntos ni medallas de Kaggle
(la Simulation sí da medallas).

Jurado: dos data scientists del Matsuo Institute (`shige`, `choya`) y tres
personas de The Pokémon Company.

## 6. Reglas que condicionan cómo trabajamos

- **Equipo:** máximo 5. Composición idéntica en ambas divisiones.
- **Una sola cuenta.** Enviar desde dos cuentas es descalificación.
- **Datos externos:** permitidos si son públicos, accesibles a todos y de coste
  mínimo («Reasonableness Standard»). Una suscripción pequeña tipo Gemini
  Advanced es aceptable; un dataset propietario que cueste más que el premio, no.
- **Licencia del ganador:** hay que liberar la solución ganadora y su código bajo
  licencia OSI que no limite el uso comercial. **Excepción explícita:** no se
  puede incluir en el código liberado nada provisto por Kaggle o Pokémon.
- **Propiedad intelectual:** los derechos sobre lo que construimos son nuestros,
  pero se concede a Pokémon y Kaggle una licencia perpetua e irrevocable para usar
  la entrega en la operación de la competición.
- **Datos de la competición:** licencia revocable, solo para la competición, con
  obligación de **borrarlos al acabar**. Imágenes de cartas que violen la licencia
  → descalificación.
- **Elegibilidad:** abierta a residentes de España. Sin restricción aplicable.
- **Uso posterior:** no se puede explotar la entrega con elementos Pokémon de
  forma que compita con sus productos, sin permiso previo.

## 7. Motor de batalla

Documentación pública: <https://matsuoinstitute.github.io/cabt/>.
Detalle técnico y lo que se ha medido en la torre: [motor-cabt.md](motor-cabt.md).
