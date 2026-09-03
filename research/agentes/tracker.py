"""InfoTracker: contabilidad exacta de la información y muestreador de
determinizaciones para la Search API (search_wrapper.search_begin).

Uso:
    tr = InfoTracker(MI_DECK)            # 60 IDs
    tr.update(obs)                       # en CADA obs que recibe el agente
    det = tr.sample(rng, MirrorModel(MI_DECK))
    res = search_wrapper.search_begin(obs, **det)     # + manual_coin aparte

Qué mantiene (verificado con research/test_tracker.py; nota en
research/notas/tracker.md):
- Mi lado: `pool` = multiconjunto EXACTO de mis cartas en zonas ocultas
  (mazo ∪ premios), recomputado de `current` (mi mano/descarte/tablero/estadio
  son visibles). `mazo` = multiconjunto exacto de mi mazo cuando se conoce:
  cada select de búsqueda (1,7) lo revela entero en select["deck"] y desde ahí
  se mantiene con los logs (robos type 4, movimientos type 6 que tocan área 1);
  premios exactos = pool - mazo. None mientras no haya habido búsqueda.
- Rival: `rival_serial_id` (serial→id de toda copia física suya identificada:
  tablero/descarte de current y logs con cardId+serial — búsquedas 1→2,
  mulligan 2→1, premios cogidos 6→2, trainers/energías/evoluciones/ataques),
  `rival_mano` (serial→id de copias que sabemos AHORA en su mano) y los conteos
  handCount/deckCount/premios/boca abajo.

Áreas: 1 mazo, 2 mano, 3 descarte, 4 activo, 5 banca, 6 premios, 9 en juego.
Logs relevantes (semántica en notas/motor-mecanica.md y notas/tracker.md):
  type 4 robo propio (cardId,serial) → mazo -= carta
  type 6 movimiento visible: propio from/to área 1 ajusta mazo;
         rival to 2 entra a su mano conocida, from 2 sale de ella
  type 7 movimiento oculto: si toca mi área 1 (fuera del reparto inicial de
         premios, cuando mazo aún es None) se pierde el mazo exacto → None
  type 10 trainer jugado → la carta queda EN LIMBO (área 9, en resolución):
         no aparece en NINGUNA lista de current hasta llegar al descarte
         (verificado: durante el (1,7) de 1092 la suma de zonas da 59/60).
"""
from collections import Counter


class InfoTracker:
    def __init__(self, mi_deck):
        if len(mi_deck) != 60:
            raise ValueError(f"mi_deck debe tener 60 IDs, tiene {len(mi_deck)}")
        self.lista = Counter(mi_deck)
        self.pool = Counter(mi_deck)   # mazo ∪ premios propios (contenido exacto)
        self.mazo = None               # Counter exacto del mazo propio, si se conoce
        self.limbo = {}                # serial -> id, carta PROPIA en resolución (área 9)
        self.rival_serial_id = {}      # serial -> id, toda copia rival identificada
        self.rival_mano = {}           # serial -> id, copias rivales ahora en su mano
        self.rival_limbo = {}          # serial -> id, carta rival en resolución
        self.avisos = []               # discrepancias de contabilidad (assert suave)
        self.calibraciones = Counter() # total / pool_ok / con_prevision / exactas
        self.mano_decaida = 0          # serials olvidados por type 7 de mano rival
        self._salidas_inciertas = 0    # salidas de su mano sin identificar (type 7)
        self._cur = None
        self._yo = None

    # ------------------------------------------------------------------ update
    def update(self, obs):
        cur = obs.get("current")
        if not cur:                    # paso 0 (elección de mazo): sin current ni logs
            return
        yo = cur["yourIndex"]
        self._yo = yo
        for lg in obs.get("logs") or []:
            self._log(lg, yo)
        self._cur = cur

        # --- mi lado: pool exacto desde current (visible: mano, descarte, tablero…)
        vis_yo = self._visibles(cur, yo)
        for c in vis_yo:               # una carta visible ya no está en limbo
            self.limbo.pop(c.get("serial"), None)
        vis = Counter(c["id"] for c in vis_yo) + Counter(self.limbo.values())
        sobra = vis - self.lista
        if sobra:
            self._aviso(f"vis_fuera_lista: {dict(sobra)}")
        self.pool = self.lista - vis
        mi = cur["players"][yo]
        self.deck_n = mi["deckCount"]
        self.premios_n = sum(1 for c in mi.get("prize") or [] if c is None)
        if sum(self.pool.values()) != self.deck_n + self.premios_n:
            self._aviso(f"pool_descuadrado: pool={sum(self.pool.values())} "
                        f"deckCount={self.deck_n} premios={self.premios_n}")
        if self.mazo is not None and (
                sum(self.mazo.values()) != self.deck_n or self.mazo - self.pool):
            self._aviso(f"mazo_inconsistente: mazo={dict(self.mazo)} "
                        f"deckCount={self.deck_n} pool={dict(self.pool)}")
            self.mazo = None

        # --- rival: identificados, mano conocida y conteos
        riv = cur["players"][1 - yo]
        vis_riv = self._visibles(cur, 1 - yo)
        self._rival_vis_ser = {c["serial"] for c in vis_riv if c.get("serial") is not None}
        for c in vis_riv:
            if c.get("serial") is not None:
                self.rival_serial_id[c["serial"]] = c["id"]
                self.rival_mano.pop(c["serial"], None)   # visible ⇒ ya no está en mano
                self.rival_limbo.pop(c["serial"], None)
        self.rival_vis = Counter(c["id"] for c in vis_riv)
        self.rival_mano_n = riv["handCount"]
        self.rival_deck_n = riv["deckCount"]
        self.rival_premios_n = sum(1 for c in riv.get("prize") or [] if c is None)
        self.rival_bocabajo_n = sum(
            1 for zona in ("active", "bench") for c in riv.get(zona) or [] if not c)
        total = (sum(self.rival_vis.values()) + self.rival_mano_n + self.rival_deck_n
                 + self.rival_premios_n + self.rival_bocabajo_n + len(self.rival_limbo))
        if total != 60:
            self._aviso(f"rival_descuadrado: vis+zonas+limbo={total} != 60")
        while len(self.rival_mano) > self.rival_mano_n:
            s = next(iter(self.rival_mano))    # FIFO: lo más antiguo es lo menos cierto
            del self.rival_mano[s]
            if self._salidas_inciertas > 0:
                self._salidas_inciertas -= 1
                self.mano_decaida += 1         # pérdida esperada (type 7 desde su mano)
            else:
                self._aviso(f"rival_mano_sobrada: serial {s} expulsado")

        # --- calibración gratis: (1,7) revela mi mazo entero en select["deck"]
        sel = obs.get("select")
        if sel and sel.get("type") == 1 and sel.get("context") == 7 and sel.get("deck"):
            real = Counter(c["id"] for c in sel["deck"] if c.get("playerIndex") == yo)
            self.calibraciones["total"] += 1
            if real - self.pool or sum(real.values()) != self.deck_n:
                self._aviso(f"calibracion_pool: real={dict(real)} pool={dict(self.pool)} "
                            f"deckCount={self.deck_n}")
            else:
                self.calibraciones["pool_ok"] += 1
            if self.mazo is not None:
                self.calibraciones["con_prevision"] += 1
                if self.mazo == real:
                    self.calibraciones["exactas"] += 1
                else:
                    self._aviso(f"calibracion_mazo: previsto={dict(self.mazo)} "
                                f"real={dict(real)}")
            self.mazo = real           # resincronizar SIEMPRE con la verdad

    def _log(self, lg, yo):
        t, p = lg.get("type"), lg.get("playerIndex")
        if p == yo:
            if t == 10:                                  # trainer jugado → limbo
                self.limbo[lg["serial"]] = lg["cardId"]
            elif t == 6:
                if lg.get("toArea") in (4, 5):           # colocada (setup: boca abajo,
                    self.limbo[lg["serial"]] = lg["cardId"]  # current muestra null)
                if lg.get("fromArea") == 9:
                    self.limbo.pop(lg["serial"], None)
            if self.mazo is None:
                return
            if t == 4:                                   # robo propio visible
                self._mazo_quita(lg["cardId"])
            elif t == 6:
                if lg.get("fromArea") == 1:
                    self._mazo_quita(lg["cardId"])
                if lg.get("toArea") == 1:
                    self.mazo[lg["cardId"]] += 1
            elif t == 7 and 1 in (lg.get("fromArea"), lg.get("toArea")):
                self._aviso(f"mazo_perdido: type7 oculto toca mi mazo {lg}")
                self.mazo = None
        elif p == 1 - yo:
            if t == 10:
                self.rival_limbo[lg["serial"]] = lg["cardId"]
            elif t == 6 and lg.get("fromArea") == 9:
                self.rival_limbo.pop(lg["serial"], None)
            if lg.get("cardId") and lg.get("serial") is not None:
                self.rival_serial_id[lg["serial"]] = lg["cardId"]
            if lg.get("cardIdTarget") and lg.get("serialTarget") is not None:
                self.rival_serial_id[lg["serialTarget"]] = lg["cardIdTarget"]
            if t == 6:
                if lg.get("toArea") == 2:
                    self.rival_mano[lg["serial"]] = lg["cardId"]
                if lg.get("fromArea") == 2:
                    self.rival_mano.pop(lg["serial"], None)
            elif t in (10, 11, 12):
                # trainer/energía/evolución salen de su mano SIN type 6 (verificado)
                self.rival_mano.pop(lg["serial"], None)
            elif t == 7 and lg.get("fromArea") == 2:
                # carta NO identificada sale de su mano (p. ej. devolver al mazo):
                # pudo ser cualquier serial conocido → crédito de incertidumbre
                # ACUMULATIVO (el exceso puede aflorar muchos turnos después)
                self._salidas_inciertas += 1

    def _mazo_quita(self, card_id):
        if self.mazo[card_id] <= 0:
            self._aviso(f"mazo_negativo: sale {card_id} que no estaba previsto")
            self.mazo = None
        else:
            self.mazo[card_id] -= 1

    def _aviso(self, msg):
        self.avisos.append(msg)

    @staticmethod
    def _visibles(cur, p):
        """Cartas {id, serial} del jugador p en zonas visibles de current."""
        out = []

        def add(c):
            if c and c.get("id") and c.get("playerIndex", p) == p:
                out.append(c)

        for st in cur.get("stadium") or []:
            add(st)
        pl = cur["players"][p]
        for zona in ("active", "bench"):
            for pk in pl.get(zona) or []:
                if not pk or not pk.get("id"):
                    continue           # null = colocado boca abajo (setup)
                out.append({"id": pk["id"], "serial": pk.get("serial")})
                for k in ("energyCards", "tools", "preEvolution"):
                    for c in pk.get(k) or []:
                        add(c)
        for zona in ("discard", "hand", "prize"):
            for c in pl.get(zona) or []:
                add(c)                 # prize: solo entradas no-null (reveladas)
        for c in cur.get("looking") or []:
            add(c)
        return out

    # ------------------------------------------------------------------ sample
    def sample(self, rng, modelo_rival):
        """Determinización para search_begin: dict con los 6 arrays
        (your_deck, your_prize, opp_deck, opp_prize, opp_hand, opp_active).
        Tamaños EXACTOS a los conteos reales. `modelo_rival(vistas, n) -> n IDs`
        que completan a 60 la lista rival (vistas = Counter de sus copias
        identificadas). Válido desde que el rival no tiene cartas boca abajo en
        juego salvo el activo del setup (opp_active)."""
        if self._cur is None:
            raise RuntimeError("sample() antes del primer update() con current")
        # mi lado: si el mazo es conocido la partición es exacta, si no, uniforme
        if self.mazo is not None:
            your_deck = list(self.mazo.elements())
            your_prize = list((self.pool - self.mazo).elements())
        else:
            pool = list(self.pool.elements())
            rng.shuffle(pool)
            your_deck, your_prize = pool[:self.deck_n], pool[self.deck_n:]

        # rival: copias identificadas fijas + completar la lista con el modelo
        vistas = Counter(self.rival_serial_id.values())
        faltan = 60 - len(self.rival_serial_id)        # copias jamás identificadas
        resto = self._ajusta(list(modelo_rival(vistas, faltan)), faltan, rng)
        otras = [i for s, i in self.rival_serial_id.items()
                 if s not in self._rival_vis_ser and s not in self.rival_mano
                 and s not in self.rival_limbo]
        mano = list(self.rival_mano.values())          # conocidas en mano, fijas
        libres = otras + resto                         # ocultas sin zona conocida
        rng.shuffle(libres)
        corte = self.rival_mano_n - len(mano)
        opp_hand = mano + libres[:corte]
        rest = libres[corte:]
        if self.rival_bocabajo_n > 1:
            self._aviso(f"sample_bocabajo: {self.rival_bocabajo_n} cartas rivales "
                        "boca abajo en juego; opp_active solo admite 1")
        opp_active = rest[:min(self.rival_bocabajo_n, 1)]
        rest = rest[self.rival_bocabajo_n:]            # descarta extras boca abajo
        return {
            "your_deck": your_deck,
            "your_prize": your_prize,
            "opp_deck": rest[:self.rival_deck_n],
            "opp_prize": rest[self.rival_deck_n:self.rival_deck_n + self.rival_premios_n],
            "opp_hand": opp_hand,
            "opp_active": opp_active,
        }

    @staticmethod
    def _ajusta(cartas, n, rng):
        """Fuerza len(cartas)==n: recorta al azar o rellena repitiendo al azar."""
        if len(cartas) > n:
            cartas = rng.sample(cartas, n)
        while len(cartas) < n:
            cartas.append(rng.choice(cartas) if cartas else 3)
        return cartas


class MirrorModel:
    """El rival juega exactamente MI lista (baseline simple y defendible)."""

    def __init__(self, lista60):
        self.lista = Counter(lista60)

    def __call__(self, vistas, n):
        """vistas: multiconjunto de copias rivales identificadas; devuelve n IDs
        que completan la lista a 60. Si lo visto no cabe en la lista (rival real
        distinto), recorta de lo más repetido / rellena con lo más común."""
        c = self.lista - Counter(vistas)
        while sum(c.values()) > n:
            c[max(c, key=c.get)] -= 1
        falta = n - sum(c.values())
        if falta > 0:
            c[max(self.lista, key=self.lista.get)] += falta
        return list(c.elements())


class MetaModel(MirrorModel):
    """Stub: el rival juega la lista de un arquetipo del meta (ver
    notas/meta-recon.md y research/decks/). Construir con esa lista de 60.
    Refinar después: elegir el arquetipo por verosimilitud de lo visto."""
