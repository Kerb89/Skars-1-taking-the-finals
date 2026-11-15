"""Runner dei test Playwright di Giralettere (nessuna dipendenza oltre a playwright).

Uso:
    python giralettere/tests/run_tests.py                 # tutti i test locali
    python giralettere/tests/run_tests.py parole bocciato # solo i file test_parole.py, test_bocciato.py
    python giralettere/tests/run_tests.py --headed

Il test sulla preview reale è separato: test_preview.py (vedi lì).
Exit code 0 solo se tutti i test passano.
"""
import importlib.util
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from aiuti import avvia_server  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    headed = "--headed" in sys.argv
    files = sorted(p for p in QUI.glob("test_*.py") if p.stem != "test_preview")
    if args:
        files = [p for p in files if p.stem.removeprefix("test_") in args]
    esiti = []
    if not args or "functions" in args:
        # Functions (sync, tracciamento) su D1 finto node:sqlite + schema reale.
        import subprocess
        t0 = time.time()
        r = subprocess.run(["node", "--test", str(QUI / "functions.test.mjs")], capture_output=True, text=True, encoding="utf-8")
        esiti.append((r.returncode == 0, "functions.test.mjs", time.time() - t0, "" if r.returncode == 0 else r.stdout[-3000:] + r.stderr[-1000:]))
        print(f"  {'OK  ' if r.returncode == 0 else 'FAIL'} functions.test.mjs ({esiti[-1][2]:.1f}s)")
        if r.returncode:
            print("       " + esiti[-1][3].strip().replace("\n", "\n       "))
    srv, base = avvia_server()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        for f in files:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for nome in sorted(n for n in dir(mod) if n.startswith("test_")):
                t0 = time.time()
                try:
                    getattr(mod, nome)(browser, base)
                    esiti.append((True, f"{f.stem}::{nome}", time.time() - t0, ""))
                except Exception:
                    esiti.append((False, f"{f.stem}::{nome}", time.time() - t0, traceback.format_exc()))
                ok, n, dt, tb = esiti[-1]
                print(f"  {'OK  ' if ok else 'FAIL'} {n} ({dt:.1f}s)")
                if tb:
                    print("       " + tb.strip().replace("\n", "\n       "))
        browser.close()
    srv.shutdown()
    falliti = [e for e in esiti if not e[0]]
    print(f"\n{len(esiti) - len(falliti)}/{len(esiti)} test passati")
    sys.exit(1 if falliti or not esiti else 0)


if __name__ == "__main__":
    main()
