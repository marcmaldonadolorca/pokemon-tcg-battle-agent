#!/usr/bin/env python3
"""Construye submission.tar.gz para la división Simulation y lo valida antes de subir.

El paquete es autocontenido según el contrato del sample oficial: `main.py` y
`deck.csv` en la raíz del tar (no anidados) más el paquete `cg/` con el motor.
En producción los ficheros aterrizan en /kaggle_simulations/agent/.

Uso:
    .venv/bin/python empaquetar.py --deck research/decks/propios/hops-snorlax.csv
    .venv/bin/python empaquetar.py --deck ... --validar     # juega partidas reales
    .venv/bin/python empaquetar.py --deck ... --politica research/agentes/heuristico_v3.py
"""
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
CG_SAMPLE = os.path.join(RAIZ, "data", "sample")   # cg/ oficial (api.py incluido)
LIMITE_MIB = 197.7

MAIN = '''"""Agente del envío — política heurística blindada (ver research/notas/).

OJO: Kaggle ejecuta este fichero con exec(), NO lo importa como módulo, así que
`__file__` NO EXISTE aquí. Usar __file__ da NameError y el envío entero queda en
ERROR (nos pasó con el envío 55407115 el 2026-08-10). Rutas literales.
"""
import os
import sys

_AQUI = "/kaggle_simulations/agent"
if not os.path.exists(os.path.join(_AQUI, "deck.csv")):
    _AQUI = os.getcwd()
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

# __ENV__
from agentes import politica


def _lee_deck():
    with open(os.path.join(_AQUI, "deck.csv")) as f:
        ids = [int(l) for l in f.read().split("\\n") if l.strip()]
    assert len(ids) == 60, f"deck.csv tiene {len(ids)} cartas, deben ser 60"
    return ids


DECK = _lee_deck()
politica.DECK = DECK


def agent(obs_dict: dict) -> list:
    """Contrato: devuelve índices únicos sobre obs.select.option,
    de longitud entre minCount y maxCount. Nunca puede lanzar: una acción
    ilegal o una excepción pierde la partida en el acto."""
    try:
        if obs_dict.get("select") is None:
            return DECK
        return politica.agent(obs_dict)
    except Exception:
        sel = obs_dict.get("select") or {}
        n = len(sel.get("option") or [])
        lo = sel.get("minCount", 0) or 0
        if n == 0:
            return [0] if (sel.get("maxCount") or 0) >= 1 else []
        return list(range(min(max(lo, 1), n)))
'''


POLITICA_DEFECTO = os.path.join(RAIZ, "research", "agentes", "heuristico.py")


def construir(deck_csv: str, salida: str, politica: str = POLITICA_DEFECTO,
              extra: list | None = None, entorno: dict | None = None) -> str:
    tmp = tempfile.mkdtemp(prefix="envio_")
    try:
        # La política vive en agentes/ para que su `../cards_clean.csv` resuelva
        # a la raíz del paquete, igual que en el repo.
        os.makedirs(os.path.join(tmp, "agentes"), exist_ok=True)
        open(os.path.join(tmp, "agentes", "__init__.py"), "w").close()
        shutil.copy(politica, os.path.join(tmp, "agentes", "politica.py"))
        # Politicas de mas de un fichero (p.ej. el clon: rasgos.py, features*.py,
        # heuristico.py de respaldo y politica.npz con los pesos). Todo cae en
        # agentes/, que es donde esas politicas lo buscan primero.
        for e in (extra or []):
            if not os.path.exists(e):
                raise SystemExit("--extra no existe: %s" % e)
            shutil.copy(e, os.path.join(tmp, "agentes", os.path.basename(e)))
        shutil.copy(os.path.join(RAIZ, "research", "cards_clean.csv"),
                    os.path.join(tmp, "cards_clean.csv"))
        # Los parametros de busqueda se leen con os.environ.get EN TIEMPO DE
        # IMPORT, asi que hay que fijarlos antes del `from agentes import politica`.
        # Sin esto un envio con configuracion no-por-defecto sale con los valores
        # por defecto y nadie se entera.
        bloque = "\n".join('os.environ[%r] = %r' % (k, str(v))
                            for k, v in sorted((entorno or {}).items()))
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write(MAIN.replace("# __ENV__", bloque or "# (sin entorno fijado)"))
        ids = [l.strip() for l in open(deck_csv) if l.strip()]
        if len(ids) != 60:
            raise SystemExit(f"{deck_csv}: {len(ids)} cartas, deben ser 60")
        with open(os.path.join(tmp, "deck.csv"), "w") as f:
            f.write("\n".join(ids) + "\n")
        # cg/ oficial del sample_submission (api.py + libcg.so)
        dst = os.path.join(tmp, "cg")
        os.makedirs(dst, exist_ok=True)
        for n in ("__init__.py", "api.py", "game.py", "sim.py", "utils.py", "libcg.so"):
            o = os.path.join(CG_SAMPLE, n)
            if os.path.exists(o):
                shutil.copy(o, os.path.join(dst, n))

        with tarfile.open(salida, "w:gz") as tar:
            for n in ("main.py", "agentes", "deck.csv", "cards_clean.csv", "cg"):
                tar.add(os.path.join(tmp, n), arcname=n)
        return tmp
    finally:
        pass


def validar(tmp: str, n: int) -> int:
    """Juega partidas reales cargando main.py EXACTAMENTE como Kaggle: con exec()
    y sin `__file__` en el espacio de nombres.

    Importarlo como módulo NO vale: `__file__` existiría y un fallo real pasaría
    desapercibido — así se coló el NameError del envío 55407115. Aquí se replica
    kaggle_environments/agent.py:get_last_callable, que hace exec(code, env) y se
    queda con el último callable definido.
    """
    from kaggle_environments import make

    # El agente en producción tiene su carpeta como cwd y en sys.path; nada del repo.
    cwd0, path0 = os.getcwd(), list(sys.path)
    for m in ("main", "politica", "agentes", "agentes.politica"):
        sys.modules.pop(m, None)
    os.chdir(tmp)
    sys.path.insert(0, tmp)
    try:
        with open(os.path.join(tmp, "main.py")) as f:
            codigo = compile(f.read(), "main.py", "exec")
        env_ns = {}
        exec(codigo, env_ns)          # <- sin __file__, igual que Kaggle
        fn = [v for v in env_ns.values() if callable(v) and getattr(v, "__name__", "") == "agent"]
        if not fn:
            print("validación: main.py no define una función agent()")
            return 1
        agente = fn[-1]

        malos, pasos = 0, []
        for _ in range(n):
            partida = make("cabt", debug=False)
            partida.run([agente, "first"])
            for e in partida.state:
                if e.status not in ("DONE", "INACTIVE", "ACTIVE"):
                    malos += 1
            pasos.append(len(partida.steps))
        print(f"validación: {n} partidas · estados anómalos: {malos} · "
              f"pasos {min(pasos)}-{max(pasos)}")
        return malos
    finally:
        os.chdir(cwd0)
        sys.path[:] = path0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--salida", default=os.path.join(RAIZ, "submission.tar.gz"))
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--politica", default=POLITICA_DEFECTO,
                    help="módulo con agent(obs); por defecto el heurístico v2 de la ladder")
    ap.add_argument("--env", action="append", default=[], metavar="K=V",
                    help="variable de entorno fijada en main.py antes de importar "
                         "la politica (repetible; p.ej. CB2_R=32)")
    ap.add_argument("--extra", action="append", default=[],
                    help="fichero suelto que la política necesita, copiado a agentes/ "
                         "(repetible; para políticas de varios ficheros como el clon)")
    args = ap.parse_args()

    entorno = dict(e.split("=", 1) for e in args.env)
    tmp = construir(args.deck, args.salida, args.politica, args.extra, entorno)
    mib = os.path.getsize(args.salida) / 1024 / 1024
    print(f"paquete   : {args.salida} ({mib:.1f} MiB / límite {LIMITE_MIB})")
    print(f"política  : {args.politica}")
    if args.extra:
        print(f"extra     : {', '.join(os.path.basename(e) for e in args.extra)}")
    if entorno:
        print("entorno   : " + ", ".join("%s=%s" % kv for kv in sorted(entorno.items())))
    print(f"baraja    : {args.deck}")
    with tarfile.open(args.salida) as t:
        print("contenido :", ", ".join(sorted(m.name for m in t.getmembers())[:8]))
    if mib > LIMITE_MIB:
        print("ERROR: excede el límite de tamaño")
        return 1
    if args.validar:
        if validar(tmp, args.n):
            print("VEREDICTO : FALLO — hay estados anómalos")
            return 1
        print("VEREDICTO : OK — listo para subir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
