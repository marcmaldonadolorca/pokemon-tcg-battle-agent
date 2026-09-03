#!/usr/bin/env python3
"""Instrumenta la COBERTURA DE CARTAS de un piloto: qué cartas se le ofrecen y cuáles juega.

Envuelve al agente sin tocarlo: en cada select (0,0) resuelve, para cada option, el
card_id al que se refiere (mano para 7/8/9, Pokémon en juego para 10/12/13) y anota
(a) en cuántos puntos de decisión estuvo OFRECIDA cada carta y (b) cuántas veces la
política la ELIGIÓ. Una carta con ofrecida>0 y jugada==0 es papel.

Uso:
  .venv/bin/python research/cobertura.py --agente research/agentes/heuristico.py \
      --deck research/decks/propios/mega-lucario.csv --n 300 --procs 2
"""
import argparse
import collections
import importlib.util
import json
import multiprocessing as mp
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def carga_deck(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [int(l) for l in f if l.strip()]


def _carga_mod(ruta):
    s = importlib.util.spec_from_file_location("agente_cob", ruta)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def _ids_de_opciones(sel, cur, me):
    """dict índice_de_option -> card_id (o None si no resuelve)."""
    yo = cur["players"][me]
    mano = yo.get("hand") or []
    activo = yo.get("active") or []
    banca = yo.get("bench") or []
    est = cur.get("stadium") or []
    out = {}
    for i, o in enumerate(sel["option"]):
        t = o.get("type")
        cid = None
        if t in (7, 8, 9):
            idx = o.get("index")
            if idx is not None and 0 <= idx < len(mano):
                cid = mano[idx]["id"]
        elif t == 10:
            a, idx = o.get("area"), o.get("index")
            zona = activo if a == 4 else banca if a == 5 else est if a == 7 else None
            if zona is not None and idx is not None and 0 <= idx < len(zona):
                cid = zona[idx]["id"]
        elif t in (12, 13):
            if activo:
                cid = activo[0]["id"]
        out[i] = cid
    return out


def _juega(t):
    ruta_ag, ruta_deck, _ = t
    from kaggle_environments import make

    mod = _carga_mod(ruta_ag)
    deck = carga_deck(ruta_deck)
    ofrecida = collections.Counter()
    jugada = collections.Counter()
    en_mano = collections.Counter()
    ofrecida_tipo = collections.Counter()   # (card_id, option_type)
    jugada_tipo = collections.Counter()
    puntos = [0]

    def instr(obs):
        sel = obs["select"]
        if sel is None:
            return list(deck)
        acc = mod.agent(obs)
        if sel.get("type") == 0 and sel.get("context") == 0 and sel.get("option"):
            cur = obs["current"]
            me = cur["yourIndex"]
            ids = _ids_de_opciones(sel, cur, me)
            puntos[0] += 1
            for c in {x["id"] for x in (cur["players"][me].get("hand") or [])}:
                en_mano[c] += 1
            vistos = collections.defaultdict(set)
            for i, cid in ids.items():
                if cid is not None:
                    vistos[cid].add(sel["option"][i].get("type"))
            for cid, tipos in vistos.items():
                ofrecida[cid] += 1
                for tp in tipos:
                    ofrecida_tipo[(cid, tp)] += 1
            for i in (acc or []):
                cid = ids.get(i)
                if cid is not None:
                    jugada[cid] += 1
                    jugada_tipo[(cid, sel["option"][i].get("type"))] += 1
        return acc

    env = make("cabt", configuration={"decks": [list(deck), list(deck)]}, debug=False)
    env.run([instr, instr])
    fb = dict(getattr(mod, "FALLBACKS", {}))
    return (dict(ofrecida), dict(jugada), dict(en_mano), puntos[0],
            {f"{k[0]}|{k[1]}": v for k, v in ofrecida_tipo.items()},
            {f"{k[0]}|{k[1]}": v for k, v in jugada_tipo.items()}, fb)


def mide(ruta_ag, ruta_deck, n, procs):
    tareas = [(ruta_ag, ruta_deck, i) for i in range(n)]
    with mp.Pool(procs) as pool:
        res = pool.map(_juega, tareas)
    ofr, jug, mano, ofrt, jugt, fbs = (collections.Counter() for _ in range(6))
    puntos = 0
    for a, b, c, p, d, e, f in res:
        ofr.update(a)
        jug.update(b)
        mano.update(c)
        puntos += p
        ofrt.update(d)
        jugt.update(e)
        fbs.update(f)
    return {"ofrecida": dict(ofr), "jugada": dict(jug), "en_mano": dict(mano),
            "puntos": puntos, "n": n, "ofrecida_tipo": dict(ofrt),
            "jugada_tipo": dict(jugt), "fallbacks": dict(fbs)}


def informe(r, deck, nombres, salida=None):
    ofr, jug, mano = r["ofrecida"], r["jugada"], r["en_mano"]
    cuentas = collections.Counter(deck)
    print(f"n={r['n']} partidas · {r['puntos']} puntos de decisión (0,0) · "
          f"{r['puntos']/r['n']:.1f} por partida")
    print(f"fallbacks: {r['fallbacks']}")
    print(f"{'id':>5} {'x':>2} {'carta':<26} {'en_mano':>8} {'ofrec':>7} {'jugada':>7} {'%jug':>6}")
    muertas = []
    for cid in sorted(set(deck), key=lambda c: -ofr.get(c, 0)):
        o, j, m = ofr.get(cid, 0), jug.get(cid, 0), mano.get(cid, 0)
        pct = 100 * j / o if o else 0.0
        print(f"{cid:>5} {cuentas[cid]:>2} {nombres.get(cid,'?')[:26]:<26} "
              f"{m:>8} {o:>7} {j:>7} {pct:>5.1f}%")
        if o > 0 and j == 0:
            muertas.append((cid, cuentas[cid], nombres.get(cid, "?"), o, m))
    print("\nCARTAS MUERTAS (ofrecidas y nunca jugadas):")
    tot = 0
    for cid, k, nom, o, m in muertas:
        tot += k
        print(f"  {cid} x{k} {nom}: ofrecida en {o} decisiones "
              f"({o/r['n']:.2f}/partida), en mano en {m} ({m/r['n']:.2f}/partida)")
    print(f"  TOTAL copias muertas: {tot}/60")
    cubiertas = sum(k for cid, k in cuentas.items()
                    if jug.get(cid, 0) > 0 or ofr.get(cid, 0) == 0)
    print(f"  cobertura = {60-tot}/60 = {(60-tot)/60:.3f}  (cubiertas={cubiertas})")
    if salida:
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(r, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agente", default=os.path.join(RAIZ, "agentes/heuristico.py"))
    ap.add_argument("--deck", default=os.path.join(RAIZ, "decks/propios/mega-lucario.csv"))
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    deck = carga_deck(a.deck)
    nombres = {}
    import csv as _csv
    with open(os.path.join(RAIZ, "cards_clean.csv"), encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            nombres[int(row["card_id"])] = row["name"]
    r = mide(os.path.abspath(a.agente), os.path.abspath(a.deck), a.n, a.procs)
    print(f"\n=== {os.path.basename(a.agente)} sobre {os.path.basename(a.deck)} ===")
    informe(r, deck, nombres, a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
