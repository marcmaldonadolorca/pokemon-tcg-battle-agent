#!/usr/bin/env python3
"""Laboratorio de barajas: convierte arquetipos en listas medidas contra el motor real.

Subcomandos (resultados JSON incrementales en --out, por defecto en el scratchpad):
  validar   battle_start real de cada baraja (propias y meta) -> errorPlayer/errorType
  mulligan  P(mano inicial sin basico): hipergeometrica exacta + empirica con el motor
            (cada re-robo tras mulligan es una muestra iid del mismo experimento)
  medir     por baraja, con el heuristico pilotando ambos lados:
              n vs baraja ejemplo del motor (heuristico.py) y n en espejo
  chequeo   partidas sondeo instrumentadas: ¿aparecen las cartas clave como opcion
            jugable y ocurre el efecto observable (energia adjuntada, robo, veneno...)?

Uso: .venv/bin/python research/lab_barajas.py <subcomando> [--decks a,b] [--n 300]
"""
import argparse
import collections
import csv
import glob
import json
import math
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(RAIZ, "research")
SCRATCH = os.environ.get(
    "LAB_SCRATCH",
    "/tmp/claude-1000/-home-ftpx100/22cc5bac-f709-4c82-bb90-dc55cdddf099/scratchpad",
)
sys.path.insert(0, RAIZ)

BASIC_E = {1, 2, 3, 4, 5, 6, 7, 8}


def cargar_cartas():
    cartas = {}
    with open(os.path.join(RESEARCH, "cards_clean.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cartas[int(r["card_id"])] = r
    return cartas


def barajas(filtro=None):
    """{nombre: (ruta, lista60)} de decks/propios y decks/meta."""
    out = {}
    for sub in ("propios", "meta"):
        for fp in sorted(glob.glob(os.path.join(RESEARCH, "decks", sub, "*.csv"))):
            nombre = os.path.splitext(os.path.basename(fp))[0]
            if filtro and nombre not in filtro:
                continue
            out[nombre] = (fp, [int(x) for x in open(fp).read().split()])
    return out


def guardar(out, clave, datos):
    res = {}
    if os.path.exists(out):
        res = json.load(open(out))
    res.setdefault(clave, {}).update(datos)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- validar
def cmd_validar(args):
    from kaggle_environments.envs.cabt.cg.game import battle_finish, battle_start
    from kaggle_environments.envs.cabt.cabt import deck as EJEMPLO

    res = {}
    for nombre, (_, ids) in barajas(args.decks).items():
        obs, sd = battle_start(list(ids), list(EJEMPLO))
        ok = sd.errorPlayer < 0 and obs is not None
        if ok:
            battle_finish()
        res[nombre] = {"ok": ok, "errorPlayer": sd.errorPlayer, "errorType": sd.errorType}
        print(f"{nombre:20s} {'OK' if ok else 'ERROR'} (errorPlayer={sd.errorPlayer}, errorType={sd.errorType})")
    guardar(args.out, "validar", res)


# ---------------------------------------------------------------- mulligan
def p_mulligan_exacta(ids, cartas):
    b = sum(1 for i in ids if cartas[i]["supertype"] == "Basic Pokémon")
    # P(0 basicos en 7) hipergeometrica
    return math.comb(60 - b, 7) / math.comb(60, 7), b


def _setup_una(ids):
    """Una partida espejo solo hasta la fase principal; devuelve lista de checks type1."""
    from kaggle_environments.envs.cabt.cg.game import battle_finish, battle_select, battle_start

    obs, sd = battle_start(list(ids), list(ids))
    assert sd.errorPlayer < 0
    checks = []  # (playerIndex, hasBasicPokemon) desde la perspectiva de p0 (deltas sin solape)
    try:
        for _ in range(14):
            if obs["current"]["yourIndex"] == 0:
                checks += [(l["playerIndex"], l["hasBasicPokemon"])
                           for l in obs["logs"] if l.get("type") == 1]
            s = obs["select"]
            if s is None or s["type"] == 0:
                break
            obs = battle_select([0] if s["minCount"] >= 1 else [])
        # ultimo delta de p0 si quedo pendiente
        if obs["current"]["yourIndex"] == 0:
            checks += [(l["playerIndex"], l["hasBasicPokemon"])
                       for l in obs["logs"] if l.get("type") == 1]
    finally:
        battle_finish()
    return checks


def cmd_mulligan(args):
    cartas = cargar_cartas()
    res = {}
    for nombre, (_, ids) in barajas(args.decks).items():
        p_ex, b = p_mulligan_exacta(ids, cartas)
        muls = tot = 0
        for _ in range(args.setups):
            for _, has in _setup_una(ids):
                tot += 1
                muls += 0 if has else 1
        p_emp = muls / max(tot, 1)
        se = math.sqrt(p_ex * (1 - p_ex) / max(tot, 1))
        veredicto = "COINCIDE" if abs(p_emp - p_ex) <= 3 * se else "DESVIA"
        res[nombre] = {"basicos": b, "p_exacta": round(p_ex, 4), "p_empirica": round(p_emp, 4),
                       "checks": tot, "veredicto": veredicto}
        print(f"{nombre:20s} basicos={b:2d} exacta={p_ex:.4f} empirica={p_emp:.4f} (n={tot}) {veredicto}")
    guardar(args.out, "mulligan", res)


# ---------------------------------------------------------------- medir
def escribir_wrapper(nombre, ids):
    os.makedirs(os.path.join(SCRATCH, "wrappers"), exist_ok=True)
    fp = os.path.join(SCRATCH, "wrappers", f"w_{nombre.replace('-', '_')}.py")
    with open(fp, "w") as f:
        f.write(
            "import importlib.util\n"
            f"_s = importlib.util.spec_from_file_location('heur', {os.path.join(RESEARCH, 'agentes', 'heuristico.py')!r})\n"
            "_h = importlib.util.module_from_spec(_s); _s.loader.exec_module(_h)\n"
            f"DECK = {ids!r}\n"
            "def agent(obs):\n"
            "    if obs['select'] is None:\n"
            "        return list(DECK)\n"
            "    return _h.agent(obs)\n"
        )
    return fp


def _resumen_partidas(res_lista, tareas):
    from arena import wilson

    n = len(res_lista)
    vict = sum(r[0] for r in res_lista)
    pasos = [r[1] for r in res_lista]
    media = sum(pasos) / n
    var = sum((x - media) ** 2 for x in pasos) / max(n - 1, 1)
    p, lo, hi = wilson(vict, n)
    v1 = sum(r[0] for r, t in zip(res_lista, tareas) if t.a_empieza)
    n1 = sum(1 for t in tareas if t.a_empieza)
    return {"n": n, "tasa": round(p, 3), "ic95": [round(lo, 3), round(hi, 3)],
            "tasa_1o": round(v1 / max(n1, 1), 3), "tasa_2o": round((vict - v1) / max(n - n1, 1), 3),
            "pasos_media": round(media, 1), "pasos_std": round(math.sqrt(var), 1)}


def cmd_medir(args):
    import multiprocessing as mp
    from arena import Tarea, _juega

    res_file = json.load(open(args.out)) if os.path.exists(args.out) else {}
    hechas = res_file.get("medir", {})
    heur = os.path.join(RESEARCH, "agentes", "heuristico.py")
    for nombre, (_, ids) in barajas(args.decks).items():
        if nombre in hechas and not args.forzar:
            print(f"{nombre}: ya medida, salto")
            continue
        w = escribir_wrapper(nombre, ids)
        t0 = time.time()
        fila = {}
        for etiqueta, spec_b in (("vs_ejemplo", heur), ("espejo", w)):
            tareas = [Tarea(w, spec_b, i % 2 == 0, i) for i in range(args.n)]
            with mp.Pool(args.procs) as pool:
                lst = pool.map(_juega, tareas)
            fila[etiqueta] = _resumen_partidas(lst, tareas)
        fila["segundos"] = round(time.time() - t0, 1)
        guardar(args.out, "medir", {nombre: fila})
        ve, es = fila["vs_ejemplo"], fila["espejo"]
        print(f"{nombre:20s} vsEj {ve['tasa']:.3f} {ve['ic95']} pasos {ve['pasos_media']:.0f} | "
              f"espejo 1o {es['tasa_1o']:.2f} pasos {es['pasos_media']:.0f}±{es['pasos_std']:.0f} | {fila['segundos']}s")


# ---------------------------------------------------------------- chequeo
def _estado(cur, me):
    yo, riv = cur["players"][me], cur["players"][1 - me]
    en_juego = list(yo.get("active") or []) + list(yo.get("bench") or [])
    return {
        "mano": yo["handCount"], "mazo": yo["deckCount"], "descarte": len(yo.get("discard") or []),
        "banca": len(yo.get("bench") or []),
        "energias": sum(len(p.get("energies") or []) for p in en_juego if p),
        "tools": sum(len(p.get("tools") or []) for p in en_juego if p),
        "veneno_rival": 1 if riv.get("poisoned") else 0, "veneno_propio": 1 if yo.get("poisoned") else 0,
        "hp_rival": (riv.get("active") or [{}])[0].get("hp") or 0,
        "maxhp_propio": sum((p.get("maxHp") or 0) for p in en_juego if p),
        "premios_rival": len(riv.get("prize") or []),
    }


def _carta_de_opcion(o, cur, me):
    """id de la carta que la opcion tocaria (mano por index, o en juego por area)."""
    yo = cur["players"][me]
    mano = yo.get("hand") or []
    t = o.get("type")
    if t in (7, 8, 9) and o.get("index") is not None and 0 <= o["index"] < len(mano):
        return mano[o["index"]]["id"]
    area, idx = o.get("area"), o.get("index")
    if area == 4 and (yo.get("active") or []):
        return (yo["active"][0] or {}).get("id")
    if area == 5 and idx is not None and 0 <= idx < len(yo.get("bench") or []):
        return yo["bench"][idx]["id"]
    if area == 9 and cur.get("stadium"):
        return cur["stadium"][0]["id"]
    return None


def cmd_chequeo(args):
    from kaggle_environments.envs.cabt.cg.game import battle_finish, battle_select, battle_start
    import importlib.util

    s = importlib.util.spec_from_file_location("heur", os.path.join(RESEARCH, "agentes", "heuristico.py"))
    heur = importlib.util.module_from_spec(s)
    s.loader.exec_module(heur)

    claves = json.loads(args.claves) if args.claves else CLAVES
    res = {}
    for nombre, (_, ids) in barajas(args.decks).items():
        if nombre not in claves:
            continue
        objetivo = set(claves[nombre])
        evidencia = {c: {"ofrecida": 0, "clicada": 0, "efectos": [], "tipos_opcion": set()} for c in objetivo}
        tipos_raros = collections.Counter()
        for _ in range(args.partidas):
            obs, sd = battle_start(list(ids), list(ids))
            assert sd.errorPlayer < 0
            try:
                pendiente = None  # (cardId, estado_pre, me)
                for _ in range(args.max_selects):
                    sel, cur = obs["select"], obs["current"]
                    if sel is None or cur["result"] >= 0:
                        break
                    me = cur["yourIndex"]
                    if pendiente and sel["type"] == 0 and sel["context"] == 0:
                        cid, pre, quien = pendiente
                        if quien == me:
                            post = _estado(cur, me)
                            evidencia[cid]["efectos"].append({k: post[k] - pre[k] for k in pre if post[k] != pre[k]})
                            pendiente = None
                    acc = None
                    if sel["type"] == 0 and sel["option"]:
                        for i, o in enumerate(sel["option"]):
                            ot = o.get("type")
                            if ot not in (7, 8, 9, 10, 12, 13, 14):
                                tipos_raros[(ot, json.dumps(sorted(o.keys())))] += 1
                            cid = _carta_de_opcion(o, cur, me)
                            if ot == 13:  # atacar: id del ataque pertenece al activo
                                cid = ((cur["players"][me].get("active") or [{}])[0] or {}).get("id")
                            if cid in objetivo:
                                evidencia[cid]["ofrecida"] += 1
                                evidencia[cid]["tipos_opcion"].add(ot)
                                if evidencia[cid]["clicada"] < args.max_clicks and pendiente is None:
                                    acc = [i]
                                    evidencia[cid]["clicada"] += 1
                                    pendiente = (cid, _estado(cur, me), me)
                                    break
                    if acc is None:
                        acc = heur.agent(obs)
                    obs = battle_select(acc)
            finally:
                battle_finish()
        fila = {}
        for cid, ev in evidencia.items():
            efectos = collections.Counter(json.dumps(e, sort_keys=True) for e in ev["efectos"])
            fila[str(cid)] = {"ofrecida": ev["ofrecida"], "clicada": ev["clicada"],
                              "tipos_opcion": sorted(ev["tipos_opcion"]),
                              "efectos_top": efectos.most_common(5)}
        fila["_tipos_opcion_raros"] = {str(k): v for k, v in tipos_raros.items()}
        res[nombre] = fila
        print(f"== {nombre}")
        for cid in sorted(objetivo):
            f = fila[str(cid)]
            print(f"  {cid}: ofrecida={f['ofrecida']} clicada={f['clicada']} tipos={f['tipos_opcion']} efectos={f['efectos_top'][:3]}")
        if tipos_raros:
            print(f"  tipos raros: {dict(tipos_raros)}")
    guardar(args.out, "chequeo", res)


# cartas clave por baraja (3-4 por arquetipo; ver notas/cartas-pool.md)
CLAVES = {
    "mega-lucario": [678, 447, 1142, 1238],
    "ethans-hooh": [357, 1215, 1232, 354],
    "iono-bellibolt": [269, 271, 1254, 1233],
    "tr-mewtwo": [431, 1216, 1134, 463],
    "okidogi": [138, 1195, 1162, 1122, 1097],
    "hops-snorlax": [304, 1171, 1115, 310],
    "ns-zekrom": [906, 1113, 1221, 293],
    "mega-kangaskhan": [756, 1145, 1159, 66],
    "abomasnow-plus": [723, 1126, 1163, 721],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validar", "mulligan", "medir", "chequeo"])
    ap.add_argument("--decks", type=lambda s: set(s.split(",")), default=None)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--setups", type=int, default=150, help="partidas de setup para mulligan empirico")
    ap.add_argument("--partidas", type=int, default=12, help="partidas sondeo por baraja en chequeo")
    ap.add_argument("--max-selects", type=int, default=400)
    ap.add_argument("--max-clicks", type=int, default=25)
    ap.add_argument("--claves", default=None, help="JSON {baraja: [ids]} para chequeo")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--out", default=os.path.join(SCRATCH, "lab_resultados.json"))
    args = ap.parse_args()
    {"validar": cmd_validar, "mulligan": cmd_mulligan,
     "medir": cmd_medir, "chequeo": cmd_chequeo}[args.cmd](args)


if __name__ == "__main__":
    main()
