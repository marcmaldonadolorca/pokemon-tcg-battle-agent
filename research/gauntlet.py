#!/usr/bin/env python3
"""Gauntlet: mide UNA lista candidata contra el CAMPO REAL, ponderando cada
emparejamiento por la frecuencia medida del arquetipo en la ladder.

Por que existe: la bascula vieja enfrentaba nuestras listas contra la baraja de
ejemplo del motor (Mega Abomasnow/Kyogre), que aparece **0 veces en 18.674 barajas**
del campo. El ranking que salio de ahi eligio mal. Aqui el rival es una de las listas
LIDER de los arquetipos realmente jugados (censo `research/replays/censo_campo.py`
sobre `data/replays/idx/idx_0808.json` + `idx_0809.json`).

Control experimental: **el mismo piloto en los dos lados** (por defecto
`research/agentes/heuristico.py`), asientos intercambiados mitad y mitad. Lo unico
que cambia entre las dos ramas es la lista de 60 IDs, asi que la diferencia medida
es atribuible a la baraja y no al agente ni a quien empieza.

Metricas por candidata:
  - WR por emparejamiento con IC95 de Wilson
  - WR PONDERADA por el share real del campo, con IC95 normal
    (se = sqrt(sum w_i^2 p_i(1-p_i)/n_i)); los pesos se renormalizan sobre los
    rivales realmente medidos y se reporta la COBERTURA del campo que suman
  - PEOR emparejamiento (el 70% del rubric premia consistencia, no la media)

Uso:
  .venv/bin/python research/gauntlet.py --cands mega-lucario,hops-snorlax --n 200
  .venv/bin/python research/gauntlet.py --cands todas --rivales ampliado --n 200
  .venv/bin/python research/gauntlet.py --politica research/agentes/heuristico_v3.py ...
  .venv/bin/python research/gauntlet.py --tabla            # reimprime lo ya medido
  .venv/bin/python research/gauntlet.py --validar          # bascula vs ladder real
  .venv/bin/python research/gauntlet.py --calibrar --n 200 # campo contra campo

Resultados en `data/gauntlet.json`, indexados por PILOTO (los numeros no son
comparables entre pilotos distintos) y acumulables: una celda ya medida con n
suficiente no se vuelve a medir salvo `--forzar`.
"""
import argparse
import csv
import glob
import json
import math
import multiprocessing as mp
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "research"))
SCRATCH = os.environ.get("LAB_SCRATCH", os.path.join(RAIZ, "scratchpad"))
OUT = os.path.join(RAIZ, "data", "gauntlet.json")
POLITICA_DEF = os.path.join(RAIZ, "research", "agentes", "heuristico.py")

# --------------------------------------------------------------------------
# Share real del campo. Fuente: research/replays/censo_campo.py sobre
# idx_0808+idx_0809 (9.337 episodios, 18.674 barajas, 203 listas unicas,
# agrupadas por solapamiento de multiconjunto >= 0,62). Cada fichero de
# research/decks/campo/ es la lista LIDER exacta de su grupo, copiada del replay.
CAMPO = {
    # nucleo: los 8 arquetipos mas jugados = 89,6% del campo
    "c1-grimmsnarl": 0.3117,
    "c2-alakazam": 0.1825,
    "c3-lopunny-froslass": 0.1278,
    "c4-dragapult": 0.0816,
    "c5-kangaskhan-crustle": 0.0686,
    "c6-ogerpon": 0.0495,
    "c7-lucario-campo": 0.0395,
    "c8-dipplin-grookey": 0.0349,
    # cola: arquetipos 9-12, suben la cobertura a 96,3%
    "x2-hydrapple": 0.0254,
    "x1-slowking": 0.0175,
    "x3-cynthia-garchomp": 0.0157,
    "x4-ns-zoroark": 0.0084,
}
NUCLEO = [k for k in CAMPO if k.startswith("c")]
AMPLIADO = list(CAMPO)
# x5/x6/x7 son duplicados byte a byte de c4/c8/c7 (mismo lider): NO son rivales nuevos.
DUPES = {"x5-dragapult": "c4-dragapult", "x6-dipplin-grookey": "c8-dipplin-grookey",
         "x7-lucario-campo": "c7-lucario-campo"}

# WR del arquetipo en la ladder real (censo_campo.json), con SUS pilotos, sin espejos.
# Sirve para la validacion externa de la bascula, no para ponderar.
WR_LADDER = {
    "c1-grimmsnarl": 0.4658, "c2-alakazam": 0.4974, "c3-lopunny-froslass": 0.5101,
    "c4-dragapult": 0.5870, "c5-kangaskhan-crustle": 0.4450, "c6-ogerpon": 0.4627,
    "c7-lucario-campo": 0.5461, "c8-dipplin-grookey": 0.5515,
    "x2-hydrapple": 0.5612, "x1-slowking": 0.6327, "x3-cynthia-garchomp": 0.5034,
    "x4-ns-zoroark": 0.5769,
}
# mu de la ladder de nuestros DOS envios vivos (mismo piloto, distinta lista).
# Es el unico contraste limpio disponible: piloto constante, baraja variable.
LADDER_PROPIA = {"mega-lucario": 464.8, "hops-snorlax": 378.4}


# ------------------------------------------------------------------ utilidades
def lee(fp):
    return [int(x) for x in open(fp).read().split()]


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - r, c + r


def candidatas(filtro=None, extra=None):
    out = {}
    for sub in ("propios", "meta", "campo"):
        for fp in sorted(glob.glob(os.path.join(RAIZ, "research", "decks", sub, "*.csv"))):
            out[os.path.splitext(os.path.basename(fp))[0]] = fp
    for fp in extra or []:
        out[os.path.splitext(os.path.basename(fp))[0]] = fp
    if filtro and filtro != "todas":
        pedidas = [x for x in filtro.split(",") if x]
        out = {k: out[k] for k in pedidas if k in out}
    return out


def rivales(cual):
    todos = {os.path.splitext(os.path.basename(fp))[0]: fp
             for fp in sorted(glob.glob(os.path.join(RAIZ, "research", "decks", "campo", "*.csv")))}
    if cual == "nucleo":
        nombres = NUCLEO
    elif cual == "ampliado":
        nombres = AMPLIADO
    else:
        nombres = [x for x in cual.split(",") if x]
    return {n: todos[n] for n in nombres if n in todos}


def nombre_politica(ruta):
    return os.path.splitext(os.path.basename(ruta))[0]


def escribir_wrapper(nombre, ids, politica):
    """Agente-modulo: entrega DECK en el paso de baraja y delega el resto en el piloto."""
    d = os.path.join(SCRATCH, "wrappers")
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, "g_%s_%s.py" % (nombre_politica(politica), nombre.replace("-", "_")))
    with open(fp, "w") as f:
        f.write(
            "import importlib.util\n"
            f"_s = importlib.util.spec_from_file_location('piloto', {politica!r})\n"
            "_m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)\n"
            f"DECK = {ids!r}\n"
            "def agent(obs):\n"
            "    if obs['select'] is None:\n"
            "        return list(DECK)\n"
            "    return _m.agent(obs)\n"
        )
    return fp


# ------------------------------------------------------------------ validacion legal
def valida(fp):
    """battle_start real: 60 cartas, <=4 copias, >=1 basico, <=1 ACE SPEC, errorPlayer -1."""
    ids = lee(fp)
    prob = []
    if len(ids) != 60:
        prob.append("no son 60 (%d)" % len(ids))
    from collections import Counter
    cta = Counter(ids)
    basicas = set(range(1, 9))
    for cid, k in cta.items():
        if k > 4 and cid not in basicas:
            prob.append("%dx id %d" % (k, cid))
    from kaggle_environments.envs.cabt.cg.game import battle_finish, battle_start
    from kaggle_environments.envs.cabt.cabt import deck as EJEMPLO
    obs, sd = battle_start(list(ids), list(EJEMPLO))
    ok = sd.errorPlayer < 0 and obs is not None
    if ok:
        battle_finish()
    else:
        prob.append("battle_start errorPlayer=%s errorType=%s" % (sd.errorPlayer, sd.errorType))
    return ok and not prob, prob


def _valida_proc(fp):
    return valida(fp)


def valida_todas(rutas, procs):
    """Cada battle_start en su proceso: el motor es global y no se re-entra limpio."""
    with mp.Pool(min(procs, len(rutas))) as pool:
        res = pool.map(_valida_proc, rutas)
    return dict(zip(rutas, res))


# ------------------------------------------------------------------ medida
def mide(fp_a, fp_b, n, procs, nombre_a, nombre_b, politica):
    from arena import Tarea, _juega

    wa = escribir_wrapper(nombre_a, lee(fp_a), politica)
    wb = escribir_wrapper(nombre_b, lee(fp_b), politica)
    tareas = [Tarea(wa, wb, i % 2 == 0, i) for i in range(n)]
    with mp.Pool(procs) as pool:
        r = pool.map(_juega, tareas)
    v = sum(x[0] for x in r)
    v1 = sum(x[0] for x, t in zip(r, tareas) if t.a_empieza)
    n1 = sum(1 for t in tareas if t.a_empieza)
    p, lo, hi = wilson(v, n)
    return {"n": n, "v": v, "wr": p, "ic95": [lo, hi],
            "wr_1o": v1 / max(n1, 1), "wr_2o": (v - v1) / max(n - n1, 1),
            "pasos": sum(x[1] for x in r) / n, "ts": time.strftime("%Y-%m-%dT%H:%M")}


def agrega(fila, pesos):
    """WR ponderada por share del campo + IC95 normal + peor emparejamiento."""
    ws = {k: pesos[k] for k in fila if k in pesos and fila[k].get("n")}
    tot = sum(ws.values())
    if not tot:
        return None
    p = sum(ws[k] / tot * fila[k]["wr"] for k in ws)
    var = sum((ws[k] / tot) ** 2 * fila[k]["wr"] * (1 - fila[k]["wr"]) / fila[k]["n"] for k in ws)
    se = math.sqrt(var)
    peor = min(ws, key=lambda k: fila[k]["wr"])
    # peor ponderado por relevancia: el peor entre los que pesan >= 5% del campo
    gordos = [k for k in ws if pesos[k] >= 0.05]
    peor_gordo = min(gordos, key=lambda k: fila[k]["wr"]) if gordos else None
    return {"wr_pond": p, "ic95": [p - 1.96 * se, p + 1.96 * se],
            "peor": peor, "wr_peor": fila[peor]["wr"], "ic95_peor": fila[peor]["ic95"],
            "peor_gordo": peor_gordo,
            "wr_peor_gordo": fila[peor_gordo]["wr"] if peor_gordo else None,
            "cobertura": tot, "n_total": sum(fila[k]["n"] for k in ws),
            "rivales": len(ws)}


# ------------------------------------------------------------------ persistencia
def carga():
    if os.path.exists(OUT):
        return json.load(open(OUT))
    return {}


def _funde(dst, src):
    """Copia de src a dst SOLO lo que dst no tenga (dst manda en los conflictos)."""
    for k, v in src.items():
        if k not in dst:
            dst[k] = v
        elif isinstance(v, dict) and isinstance(dst[k], dict):
            _funde(dst[k], v)


def guarda(res):
    """Escritura atomica y fusionada: hay otro workflow midiendo contra el mismo
    JSON, y un json.dump plano le borraria las celdas nuevas (lost update)."""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.exists(OUT):
        try:
            _funde(res, json.load(open(OUT)))
        except Exception:
            pass
    tmp = OUT + ".%d.tmp" % os.getpid()
    json.dump(res, open(tmp, "w"), indent=1)
    os.replace(tmp, OUT)


def rama(res, politica, cual="gauntlet"):
    return res.setdefault("pilotos", {}).setdefault(nombre_politica(politica), {}) \
              .setdefault(cual, {})


# ------------------------------------------------------------------ salida
def tabla(res, pesos, titulo="GAUNTLET"):
    rivs = sorted(pesos, key=lambda k: -pesos[k])
    print("\n== %s ==  (WR de la CANDIDATA; mismo piloto en los dos lados)" % titulo)
    cab = "".join("%8s" % r.split("-", 1)[1][:7] for r in rivs)
    print("%-22s%s %8s %15s %7s %-14s %5s" %
          ("candidata", cab, "POND", "IC95", "PEOR", "(vs)", "cob"))
    print("%-22s%s" % ("share campo", "".join("%7.1f%%" % (100 * pesos[r]) for r in rivs)))
    orden = []
    for nombre, fila in res.items():
        a = agrega(fila, pesos)
        if a:
            orden.append((a["wr_pond"], nombre, fila, a))
    for _, nombre, fila, a in sorted(orden, reverse=True):
        cel = "".join(("%8.3f" % fila[r]["wr"]) if r in fila else "       -" for r in rivs)
        print("%-22s%s %8.3f [%.3f,%.3f] %7.3f %-14s %4.0f%%"
              % (nombre[:22], cel, a["wr_pond"], a["ic95"][0], a["ic95"][1],
                 a["wr_peor"], a["peor"].split("-", 1)[1][:14], 100 * a["cobertura"]))
    return orden


def spearman(xs, ys):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(s):
            r[i] = pos + 1.0
        return r
    a, b = rk(xs), rk(ys)
    n = len(xs)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else 0.0


def validar(g, pesos, h2h=None):
    """Validacion de la bascula: dos contrastes externos y dos internos."""
    print("\n== VALIDACION DE LA BASCULA ==")

    print("\n[A] contraste limpio: nuestros DOS envios vivos (mismo piloto, distinta lista)")
    filas = []
    for nombre, mu in sorted(LADDER_PROPIA.items(), key=lambda x: -x[1]):
        a = agrega(g.get(nombre, {}), pesos)
        if a:
            filas.append((nombre, mu, a))
            print("  %-16s ladder mu=%6.1f   gauntlet POND=%.3f [%.3f,%.3f]  peor=%.3f vs %s"
                  % (nombre, mu, a["wr_pond"], a["ic95"][0], a["ic95"][1],
                     a["wr_peor"], a["peor"]))
    if len(filas) >= 2:
        (n1, m1, a1), (n2, m2, a2) = filas[0], filas[1]
        ok = a1["wr_pond"] > a2["wr_pond"]
        sep = a1["ic95"][0] > a2["ic95"][1]
        print("  -> orden ladder %s > %s ; orden gauntlet %s : %s%s"
              % (n1, n2, "IGUAL" if ok else "INVERTIDO",
                 "COINCIDE" if ok else "FALLA",
                 " (IC95 disjuntos, margen %.3f)" % (a1["ic95"][0] - a2["ic95"][1]) if sep
                 else " (IC95 solapan: sin margen)"))

    print("\n[B] contraste confundido: WR real de cada arquetipo del campo (SUS pilotos)")
    xs, ys, nom = [], [], []
    for r in sorted(pesos, key=lambda k: -pesos[k]):
        a = agrega(g.get(r, {}), pesos)
        if a and r in WR_LADDER:
            xs.append(WR_LADDER[r])
            ys.append(a["wr_pond"])
            nom.append(r)
            print("  %-22s WR ladder %.3f   gauntlet POND %.3f" % (r, WR_LADDER[r], a["wr_pond"]))
    if len(xs) >= 4:
        rho = spearman(xs, ys)
        print("  -> Spearman(WR ladder, POND gauntlet) = %+.3f  sobre n=%d arquetipos" % (rho, len(xs)))
        print("     OJO: el WR de ladder de cada arquetipo lo produce el piloto de SU dueno,")
        print("     asi que esta prueba mezcla calidad de lista y calidad de agente. Un rho bajo")
        print("     o negativo NO invalida [A]; dice que la lista no explica el WR del campo.")

    print("\n[C] calibracion nula: ESPEJOS (la misma lista en los dos lados) -> debe dar 0,500")
    esp, dentro = [], 0
    for r in sorted(pesos, key=lambda k: -pesos[k]):
        c = g.get(r, {}).get(r)
        if c:
            esp.append(c["wr"])
            ok = c["ic95"][0] <= 0.5 <= c["ic95"][1]
            dentro += ok
            print("  %-22s wr=%.3f [%.3f,%.3f] n=%d %s"
                  % (r, c["wr"], c["ic95"][0], c["ic95"][1], c["n"], "" if ok else "<-- FUERA de 0,5"))
    if esp:
        m = sum(esp) / len(esp)
        se = math.sqrt(0.25 / sum(g[r][r]["n"] for r in pesos if r in g and r in g[r]))
        print("  -> media de espejos %.4f (esperado 0,5000; se=%.4f); %d/%d con IC95 cubriendo 0,5"
              % (m, se, dentro, len(esp)))
        print("     Mide el sesgo del banco de pruebas: intercambio de asientos, wrappers y")
        print("     agregacion. Una media != 0,5 seria sesgo de la bascula, no de las listas.")

    if h2h:
        print("\n[D] consistencia interna: el orden POND, contra el DUELO DIRECTO")
        pond = {}
        for nombre in {k for par in h2h for k in par.split("|")}:
            a = agrega(g.get(nombre, {}), pesos)
            if a:
                pond[nombre] = a["wr_pond"]
        xs, ys, ac = [], [], 0
        for par, c in sorted(h2h.items()):
            a, b = par.split("|")
            if a in pond and b in pond:
                d = pond[a] - pond[b]
                xs.append(d)
                ys.append(c["wr"])
                bien = (d > 0) == (c["wr"] > 0.5)
                ac += bien
                print("  %-16s vs %-16s  dPOND %+.3f   duelo %.3f [%.3f,%.3f] n=%d  %s"
                      % (a, b, d, c["wr"], c["ic95"][0], c["ic95"][1], c["n"],
                         "coincide" if bien else "INVIERTE"))
        if xs:
            print("  -> %d/%d parejas con el mismo signo; Spearman(dPOND, WR duelo) = %+.3f"
                  % (ac, len(xs), spearman(xs, ys)))


def compara_replica(g, rp, pesos):
    """[E] test-retest: la misma celda re-medida con partidas NUEVAS.

    El RNG del motor no es sembrable: que una celda sea estable es una hipotesis
    hasta que se replica. Si sd(z) >> 1 hay una fuente de varianza que el IC
    binomial no recoge y todos los IC del gauntlet estan subestimados.
    """
    print("\n[E] test-retest: celdas re-medidas con partidas nuevas")
    zs = []
    for cand, fila in sorted(rp.items()):
        for riv, r in sorted(fila.items()):
            o = g.get(cand, {}).get(riv)
            if not o:
                continue
            p1, n1, p2, n2 = o["wr"], o["n"], r["wr"], r["n"]
            pp = (p1 * n1 + p2 * n2) / (n1 + n2)
            se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
            z = (p2 - p1) / se if se else 0.0
            zs.append(z)
            print("  %-22s vs %-22s orig %.3f (n=%d) | rep %.3f (n=%d)  d=%+.3f z=%+.2f %s"
                  % (cand, riv, p1, n1, p2, n2, p2 - p1, z,
                     "" if abs(z) < 1.96 else "<-- DIFIERE"))
    if len(zs) < 2:
        return
    n = len(zs)
    mz = sum(zs) / n
    sd = math.sqrt(sum((z - mz) ** 2 for z in zs) / (n - 1))
    print("  -> %d celdas; |z|>1,96: %d (esperado %.1f por azar); media z %+.3f; sd z %.2f"
          % (n, sum(1 for z in zs if abs(z) > 1.96), 0.05 * n, mz, sd))
    print("     sd(z)~1 = la celda solo tiene ruido binomial; >>1 = los IC mienten.")
    for cand in sorted(rp):
        o = {k: v for k, v in g.get(cand, {}).items() if k in pesos}
        pool = {k: dict(v) for k, v in o.items()}
        for k, r in rp[cand].items():
            if k in pool:
                pool[k] = {"wr": (o[k]["v"] + r["v"]) / (o[k]["n"] + r["n"]),
                           "n": o[k]["n"] + r["n"], "v": o[k]["v"] + r["v"],
                           "ic95": o[k]["ic95"]}
        a_o, a_r, a_p = (agrega(o, pesos), agrega(rp[cand], pesos), agrega(pool, pesos))
        if a_o and a_r and a_p:
            # la POND de la replica solo es comparable si cubre los mismos rivales:
            # con una replica parcial se renormaliza sobre 2 celdas y no significa nada.
            rep = ("%.3f" % a_r["wr_pond"] if a_r["rivales"] == a_o["rivales"]
                   else "parcial(%d/%d riv)" % (a_r["rivales"], a_o["rivales"]))
            print("  %-16s POND orig %.3f | replica %-16s | POOL %.3f [%.3f,%.3f]  peor POOL %.3f vs %s"
                  % (cand, a_o["wr_pond"], rep, a_p["wr_pond"],
                     a_p["ic95"][0], a_p["ic95"][1], a_p["wr_peor"], a_p["peor"]))


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", default="todas")
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--politica", default=POLITICA_DEF)
    ap.add_argument("--rivales", default="nucleo", help="nucleo | ampliado | lista,separada,por,comas")
    ap.add_argument("--tabla", action="store_true")
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--calibrar", action="store_true")
    ap.add_argument("--replicar", action="store_true",
                    help="re-mide celdas ya medidas con partidas nuevas (rama 'replica') y compara")
    ap.add_argument("--h2h", default="", help="duelo directo todos contra todos entre estas candidatas")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--sin-validar-listas", action="store_true")
    args = ap.parse_args()

    if args.procs > 3:
        print("aviso: hay otro workflow midiendo en esta maquina; capando a 3 procesos")
        args.procs = 3

    riv = rivales(args.rivales)
    pesos = {k: CAMPO[k] for k in riv if k in CAMPO}
    res = carga()
    g = rama(res, args.politica)

    h2h = res.setdefault("pilotos", {}).setdefault(
        nombre_politica(args.politica), {}).setdefault("h2h", {})

    if args.tabla or args.validar:
        tabla(g, pesos, "GAUNTLET (%s)" % nombre_politica(args.politica))
        if args.validar:
            validar(g, pesos, h2h)
            rp = rama(res, args.politica, "replica")
            if rp:
                compara_replica(g, rp, pesos)
        return

    if args.h2h:
        cs = candidatas(args.h2h, args.extra)
        nombres = [x for x in args.h2h.split(",") if x in cs]
        for i, a in enumerate(nombres):
            for b in nombres[i + 1:]:
                k = a + "|" + b
                if k in h2h and h2h[k]["n"] >= args.n and not args.forzar:
                    continue
                t0 = time.time()
                h2h[k] = mide(cs[a], cs[b], args.n, args.procs, a, b, args.politica)
                guarda(res)
                c = h2h[k]
                print("%-18s vs %-18s wr=%.3f [%.3f,%.3f] (%.0fs)"
                      % (a, b, c["wr"], c["ic95"][0], c["ic95"][1], time.time() - t0))
        return

    cands = candidatas(args.cands, args.extra)
    if not cands:
        print("sin candidatas: %r" % args.cands)
        return

    if not args.sin_validar_listas:
        rutas = sorted(set(list(cands.values()) + list(riv.values())))
        v = valida_todas(rutas, args.procs)
        malas = {k: p for k, (ok, p) in v.items() if not ok}
        for k, p in malas.items():
            print("LISTA ILEGAL %s: %s" % (k, p))
        if malas:
            return
        print("listas validadas en battle_start (errorPlayer -1): %d" % len(rutas))

    if args.calibrar:
        cal = res.setdefault("pilotos", {}).setdefault(
            nombre_politica(args.politica), {}).setdefault("calibrar", {})
        nombres = sorted(riv)
        for i, a in enumerate(nombres):
            for b in nombres[i + 1:]:
                k = a + "|" + b
                if k in cal and cal[k]["n"] >= args.n and not args.forzar:
                    continue
                t0 = time.time()
                cal[k] = mide(riv[a], riv[b], args.n, args.procs, a, b, args.politica)
                guarda(res)
                print("%-24s vs %-24s wr=%.3f (%.0fs)" % (a, b, cal[k]["wr"], time.time() - t0))
        return

    destino = rama(res, args.politica, "replica") if args.replicar else g
    for nombre, fp in cands.items():
        fila = destino.setdefault(nombre, {})
        for rn, rfp in sorted(riv.items()):
            if rn in fila and fila[rn]["n"] >= args.n and not args.forzar:
                continue
            if args.replicar and rn not in g.get(nombre, {}):
                continue  # solo se replica lo ya medido
            t0 = time.time()
            fila[rn] = mide(fp, rfp, args.n, args.procs, nombre, rn, args.politica)
            guarda(res)
            c = fila[rn]
            print("%-22s vs %-22s wr=%.3f [%.3f,%.3f] (1o %.2f/2o %.2f) pasos=%.0f %.0fs"
                  % (nombre, rn, c["wr"], c["ic95"][0], c["ic95"][1],
                     c["wr_1o"], c["wr_2o"], c["pasos"], time.time() - t0))
        a = agrega(fila, pesos)
        if a:
            print("  -> %-20s POND %.3f [%.3f,%.3f]  peor %.3f vs %s  (cobertura %.1f%%)"
                  % (nombre, a["wr_pond"], a["ic95"][0], a["ic95"][1],
                     a["wr_peor"], a["peor"], 100 * a["cobertura"]))
    tabla(g, pesos, "GAUNTLET (%s)" % nombre_politica(args.politica))


if __name__ == "__main__":
    main()
