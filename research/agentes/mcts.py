#!/usr/bin/env python3
"""Agente ISMCTS anytime sobre la Search API nativa de libcg.so.

Arquitectura (ver research/notas/agente-mcts.md):
- Determinized MCTS de raíz (ISMCTS): en cada decisión no trivial, K
  determinizaciones del InfoTracker (search_begin, ~0,13 ms); por cada una un
  árbol UCT corto apoyado en la persistencia de searchId (re-step determinista);
  rollouts con la política heurística PARA LOS DOS JUGADORES truncados a
  ROLLOUT_PASOS y evaluación terminal/heurística (premios como señal principal,
  desempate con daño en mesa y energías). Agregación por acción-raíz: cada
  determinización vota con peso total 1,0 repartido por fracción de visitas
  (sin normalizar, las dets «resueltas» cerca del terminal inflaban su voto
  ×100 con re-walks deterministas; ITER_MAX_DET además las corta).
- Controlador de reloj (semántica en notas/presupuesto-tiempo.md):
  presupuesto = min(TOPE, (remainingOverageTime − RESERVA) / max(rest, 20)),
  automedido con perf_counter; si < UMBRAL_DEGRADA se degrada a heurístico puro.
  La PRIMERA llamada paga los imports (CARGA_S los mide).
- Blindaje: validador de legalidad del heurístico sobre TODA acción devuelta +
  try/except alrededor de la búsqueda entera con fallback al heurístico.

Contrato: agent(obs) -> list[int]; DECK = 60 IDs. Estado entre llamadas: el
tracker de la partida en curso (el módulo se re-ejecuta por partida en arena).

Config por entorno (leída al importar): MCTS_K (determinizaciones, def. 8),
MCTS_TOPE (tope duro s/decisión, def. 1.0).
"""
import math
import os
import random
import sys
import time as _time

_T_IMPORT = _time.perf_counter()

_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (_DIR, os.path.dirname(_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import heuristico                     # política de rollout y fallback
import search_wrapper as sw           # binding ctypes verificado (importa libcg)
from tracker import InfoTracker, MirrorModel

CARGA_S = _time.perf_counter() - _T_IMPORT   # coste de imports (1ª decisión lo paga)

DECK = list(heuristico.DECK)

# --- función de valor aprendida (opcional: si falta, se usa la heurística)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "valor"))
    import features as _feats
    import valor as _valor
    _VALOR_OK = bool(int(os.environ.get("MCTS_VALOR", "1"))) and _valor.disponible()
except Exception:
    _feats = _valor = None
    _VALOR_OK = False

# ----------------------------------------------------------------- parámetros
K_DETS = int(os.environ.get("MCTS_K", "8"))
TOPE = float(os.environ.get("MCTS_TOPE", "1.0"))   # tope duro s/decisión
RESERVA = 40.0          # s de banco que nunca se tocan
UMBRAL_DEGRADA = 0.15   # presupuesto menor => heurístico puro
ROLLOUT_PASOS = 50      # truncado del rollout (selects de ambos jugadores)
ITER_MAX_DET = int(os.environ.get("MCTS_ITERS", "600"))  # tope iters/determinización
                        # (árboles cerca del final se saturan y giran en vacío:
                        # sin tope, ~2.100 iters/det medidos, la mayoría re-walks
                        # terminales deterministas que solo inflan N)
CAP_RAIZ = 24           # máx acciones candidatas en la raíz
CAP_HIJO = 12           # máx candidatas en nodos internos
C_UCT = 0.9

# ------------------------------------------------------- estado y estadística
_TRACKER = None
_MODELO = None
_TRACKER_ROTO = False
_RNG = random.Random((os.getpid() << 16) ^ int(_time.time_ns() & 0xFFFF))

TIEMPOS = []            # s de pared por llamada a agent() (incluye la del mazo)
ESTAD = {
    "decisiones": 0, "triviales": 0, "buscadas": 0, "heuristicas": 0,
    "degradadas_presupuesto": 0, "fallback_busqueda": 0,   # búsqueda falló/None
    "accion_ilegal": 0,          # la búsqueda devolvió algo ilegal (no debería)
    "det_fallida": 0, "dets": 0, "iteraciones": 0,
    "errores_step": 0, "errores_rollout": 0, "tracker_roto": 0,
    "primera_llamada_s": 0.0, "carga_s": CARGA_S,
}


# ------------------------------------------------------------------ utilidades
def _plano(st):
    """El motor devuelve {"searchId", "observation": {select, current, logs}};
    aplana a {searchId, select, current} (tolera también la forma plana)."""
    ob = st.get("observation")
    if ob is not None:
        return {"searchId": st["searchId"], "select": ob.get("select"),
                "current": ob.get("current")}
    return st


def _terminal(st, me):
    """Valor terminal [0,1] desde mi perspectiva, o None si no es terminal."""
    cur = st.get("current")
    r = (cur or {}).get("result", -1)
    if st.get("select") is None or (r is not None and r >= 0):
        if r == me:
            return 1.0
        if r == 1 - me:
            return 0.0
        return 0.5
    return None


def _evalua(cur, me):
    """Evaluación de un nodo hoja en [0,1] = probabilidad de que gane `me`.

    Usa la red de valor aprendida por self-play si está disponible (72,7% de
    acierto en validación con corte por partida, frente al 52,4% de la base
    trivial); si no, cae a la heurística de premios+daño de siempre. La red
    espera los rasgos SIEMPRE desde la perspectiva de quien decide, así que hay
    que evaluar con `yourIndex == me`.
    """
    if not cur:
        return 0.5
    if _VALOR_OK:
        try:
            if cur.get("yourIndex") == me:
                c = cur
            else:                       # copia superficial con la perspectiva volteada
                c = dict(cur)
                c["yourIndex"] = me
            return float(_valor.evalua(_feats.extrae(c)))
        except Exception:
            pass                        # nunca romper una partida por la red
    return _evalua_heuristica(cur, me)


def _evalua_heuristica(cur, me):
    """Respaldo sin red: premios restantes (señal principal), desempate con daño
    en mesa, energías desarrolladas y presencia."""
    yo, riv = cur["players"][me], cur["players"][1 - me]

    def prem(p):
        return sum(1 for c in (p.get("prize") or []) if c is None)

    def mesa(p):
        return [k for z in ("active", "bench") for k in (p.get(z) or []) if k]

    def danho(p):
        return sum(max((k.get("maxHp") or 0) - (k.get("hp") or 0), 0) for k in mesa(p))

    def ener(p):
        return sum(len(k.get("energies") or []) for k in mesa(p))

    s = ((prem(riv) - prem(yo))                       # premio ganado ≈ 1.0
         + 0.003 * (danho(riv) - danho(yo))           # 100 HP de ventaja ≈ 0.3
         + 0.05 * (ener(yo) - ener(riv))
         + 0.05 * (len(mesa(yo)) - len(mesa(riv))))
    return 0.5 + 0.5 * math.tanh(0.5 * s)


def _accion_heuristica(sel, cur):
    """Política heurística blindada: siempre devuelve una acción legal."""
    acc = None
    try:
        acc = heuristico._politica(sel, cur)
    except Exception:
        acc = None
    if not heuristico._es_legal(acc, sel):
        acc = heuristico._fallback(sel)
    return acc


def _candidatas(sel, cur, rng, cap):
    """Acciones legales candidatas; la heurística SIEMPRE primera."""
    ops = sel["option"]
    mn, mx, n = sel["minCount"], sel["maxCount"], len(sel["option"])
    if n == 0:
        return [[0]] if mn >= 1 else [[]]
    out, vistos = [], set()

    def anhade(a):
        k = tuple(sorted(a))
        if k not in vistos and heuristico._es_legal(a, sel):
            vistos.add(k)
            out.append(a)

    if mx <= 1:                       # selects de 1 (la inmensa mayoría)
        if mn == 0:
            anhade([])
        for i in range(n):
            anhade([i])
    elif mn == n:                     # todo forzado (p. ej. 3/3 con 3 opciones)
        anhade(list(range(n)))
    else:                             # multi-selección: heurística + muestras
        anhade(heuristico._fallback(sel))
        if mn == 0:
            anhade([])
        idx = list(range(n))
        for k in {mn, min(mx, n)}:
            if mn <= k <= min(mx, n) and k > 0:
                for _ in range(8):
                    anhade(sorted(rng.sample(idx, k)))
    heur = None
    try:
        h = heuristico._politica(sel, cur)
        if heuristico._es_legal(h, sel):
            heur = h
    except Exception:
        pass
    if heur is not None:
        kh = tuple(sorted(heur))
        out = [a for a in out if tuple(sorted(a)) != kh]
        out.insert(0, heur)
    out = out[:cap]
    return out or [heuristico._fallback(sel)]


class _Nodo:
    __slots__ = ("sid", "sel", "cur", "actor", "vterm", "untried", "hijos", "N", "W")

    def __init__(self, st, me, rng, cap=CAP_HIJO):
        self.sid = st["searchId"]
        self.sel = st.get("select")
        self.cur = st.get("current")
        self.vterm = _terminal(st, me)
        self.hijos = {}
        self.N = 0
        self.W = 0.0
        if self.vterm is None:
            self.actor = self.cur["yourIndex"]
            # pop() saca del final => la heurística (posición 0) se expande primero
            self.untried = list(reversed(_candidatas(self.sel, self.cur, rng, cap)))
        else:
            self.actor = None
            self.untried = []


def _uct(nodo, me):
    logn = math.log(nodo.N + 1)
    mio = nodo.actor == me

    def puntua(item):
        h = item[1]
        q = h.W / h.N
        if not mio:
            q = 1.0 - q
        return q + C_UCT * math.sqrt(logn / h.N)

    return max(nodo.hijos.items(), key=puntua)[1]


def _rollout(nodo, me, rng):
    """Ambos jugadores juegan la política heurística; truncado + evaluación."""
    # Presupuesto fresco de activaciones type 10 por rollout (el heurístico v2
    # capa 12/turno en _T10; sin esto el primer rollout satura el contador del
    # turno actual y el resto de rollouts no activan habilidades).
    getattr(heuristico, "_T10", {}).clear()
    st = {"select": nodo.sel, "current": nodo.cur, "searchId": nodo.sid}
    for _ in range(ROLLOUT_PASOS):
        v = _terminal(st, me)
        if v is not None:
            return v
        acc = _accion_heuristica(st["select"], st["current"])
        res = sw.search_step(st["searchId"], acc)
        st2 = res.get("state")
        if res.get("error") or not st2:
            ESTAD["errores_rollout"] += 1
            return _evalua(st["current"], me)
        st = _plano(st2)
    return _evalua(st["current"], me)


def _itera(raiz, me, rng):
    """Una iteración MCTS: selección UCT → expansión → rollout → backprop."""
    nodo, camino = raiz, [raiz]
    while True:
        if nodo.vterm is not None:
            valor = nodo.vterm
            break
        if nodo.untried:
            acc = nodo.untried.pop()
            res = sw.search_step(nodo.sid, acc)
            st = res.get("state")
            if res.get("error") or not st:
                ESTAD["errores_step"] += 1
                valor = 0.0 if nodo.actor == me else 1.0   # castigo al actor
                break
            hijo = _Nodo(_plano(st), me, rng)
            nodo.hijos[tuple(acc)] = hijo
            camino.append(hijo)
            valor = hijo.vterm if hijo.vterm is not None else _rollout(hijo, me, rng)
            break
        if not nodo.hijos:
            valor = _evalua(nodo.cur, me)
            break
        nodo = _uct(nodo, me)
        camino.append(nodo)
    for nd in camino:
        nd.N += 1
        nd.W += valor
    ESTAD["iteraciones"] += 1


def _busca(obs, sel, presupuesto, t0):
    """ISMCTS de raíz: K determinizaciones, agrega visitas por acción-raíz.
    Devuelve la acción o None (el llamante degrada a heurístico)."""
    me = obs["current"]["yourIndex"]
    rng = _RNG
    cands = _candidatas(sel, obs["current"], rng, CAP_RAIZ)
    if len(cands) == 1:
        return cands[0]
    margen = 0.05 * presupuesto + 0.01
    votos = {}
    for k in range(K_DETS):
        resto = presupuesto - margen - (_time.perf_counter() - t0)
        if resto <= 0.02:
            break
        tramo = resto / (K_DETS - k)
        det = _TRACKER.sample(rng, _MODELO)
        res = sw.search_begin(obs, **det)
        st = res.get("state")
        if res.get("error") or not st:
            ESTAD["det_fallida"] += 1
            c = f"det_err_{res.get('error')}"
            ESTAD[c] = ESTAD.get(c, 0) + 1
            continue
        raiz = _Nodo(_plano(st), me, rng, cap=CAP_RAIZ)
        if raiz.vterm is not None:
            continue
        raiz.untried = [list(a) for a in reversed(cands)]
        fin = min(_time.perf_counter() + tramo, t0 + presupuesto - margen)
        iters = 0
        while _time.perf_counter() < fin and iters < ITER_MAX_DET:
            _itera(raiz, me, rng)
            iters += 1
        ESTAD["dets"] += 1
        totn = sum(h.N for h in raiz.hijos.values())
        if totn <= 0:
            continue
        for acc, h in raiz.hijos.items():
            v = votos.setdefault(acc, [0.0, 0.0, 0])
            v[0] += h.N / totn          # cada det vota con peso total 1,0
            v[1] += (h.W / h.N) * (h.N / totn)   # Q medio ponderado por cuota
            v[2] += h.N                 # visitas brutas (solo desempate/diagnóstico)
    if not votos:
        return None
    mejor = max(votos.items(), key=lambda kv: (kv[1][0], kv[1][1], kv[1][2]))
    return list(mejor[0])


def _jugadas_restantes(cur):
    """Estimación conservadora de decisiones propias restantes."""
    try:
        prem = max(sum(1 for c in (p.get("prize") or []) if c is None)
                   for p in cur["players"])
        return 8 + 12 * prem
    except Exception:
        return 60


# ------------------------------------------------------------------ el agente
def agent(obs) -> list:
    global _TRACKER, _MODELO, _TRACKER_ROTO
    t0 = _time.perf_counter()
    primera = not TIEMPOS
    try:
        sel = obs["select"]
        # -- tracker: consume TODAS las obs
        if not _TRACKER_ROTO:
            try:
                if _TRACKER is None:
                    _TRACKER = InfoTracker(DECK)
                    _MODELO = MirrorModel(DECK)
                _TRACKER.update(obs)
            except Exception:
                _TRACKER_ROTO = True
                ESTAD["tracker_roto"] += 1

        if sel is None:                       # paso 0: la baraja
            return list(DECK)

        ESTAD["decisiones"] += 1
        n, mn, mx = len(sel["option"]), sel["minCount"], sel["maxCount"]

        # -- triviales: sin opciones reales, no se busca
        if n == 0:
            ESTAD["triviales"] += 1
            return [0] if mn >= 1 else []
        if n == 1 and mn >= 1:
            ESTAD["triviales"] += 1
            return [0]
        if mn == n and mx >= n:               # todo forzado
            ESTAD["triviales"] += 1
            return list(range(n))

        # -- controlador de reloj
        rot = obs.get("remainingOverageTime", 600) or 600
        rest = max(_jugadas_restantes(obs.get("current")), 20)
        presupuesto = min(TOPE, (rot - RESERVA) / rest)

        acc = None
        # Con CUALQUIER carta rival boca abajo (setup: su activo sin voltear) el motor
        # rechaza la determinización con error 2 — medido 2026-08-10: 8/230 sondas, el
        # 100% de los fallos, y solo en (1,1) activo inicial, (1,2) banca y (8,38) robo
        # por mulligan. Buscar ahí es tiempo tirado: caía al heurístico igual.
        buscable = (presupuesto >= UMBRAL_DEGRADA and not _TRACKER_ROTO
                    and _TRACKER is not None and _TRACKER._cur is not None
                    and getattr(_TRACKER, "rival_bocabajo_n", 0) == 0)
        if buscable:
            _t10 = getattr(heuristico, "_T10", {})
            _t10_bak = {k: list(v) for k, v in _t10.items()}
            try:
                acc = _busca(obs, sel, presupuesto, t0)
                if acc is None:
                    ESTAD["fallback_busqueda"] += 1
            except Exception:
                ESTAD["fallback_busqueda"] += 1
                acc = None
            finally:
                _t10.clear()                  # restaura el contador type 10 real
                _t10.update(_t10_bak)
                try:
                    sw.search_end()           # reutiliza la memoria de estados
                except Exception:
                    pass
            if acc is not None:
                ESTAD["buscadas"] += 1
        else:
            ESTAD["degradadas_presupuesto"] += 1

        if acc is None:
            ESTAD["heuristicas"] += 1
            acc = _accion_heuristica(sel, obs["current"])
        if not heuristico._es_legal(acc, sel):
            ESTAD["accion_ilegal"] += 1
            acc = heuristico._fallback(sel)
        return acc
    finally:
        dt = _time.perf_counter() - t0
        TIEMPOS.append(dt)
        if primera:
            ESTAD["primera_llamada_s"] = dt + CARGA_S
