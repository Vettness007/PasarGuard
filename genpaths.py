"""Per-install secret path for the single Vless config.
Every deploy gets its own random path on first boot (saved on the volume),
so no two panels share the same path. Old installs keep their path so existing configs never break."""
import json, os, secrets, uuid

DATA = os.getenv("JINX_DATA", "/var/lib/pasarguard")
OUT_JSON = f"{DATA}/paths.json"
OUT_INC = f"{DATA}/inbounds.inc"
SLOTS = {"JX-VLESS-WS-1": (10001, "/ws/")}
LEGACY = {"JX-VLESS-WS-1": "/ws/7a5a21d9-60f9-4542-943e-7838b90169e1"}

def load():
    try:
        with open(OUT_JSON) as f: p = json.load(f)
        if all(isinstance(p.get(t), str) and p[t].startswith("/") for t in SLOTS): return p
    except Exception: pass
    return None

def main():
    os.makedirs(DATA, exist_ok=True)
    p = load()
    if p is None:
        if os.path.exists(f"{DATA}/.owner_initialized") or os.path.exists(f"{DATA}/db.sqlite3"):
            p = dict(LEGACY); print("[paths] existing panel detected, keeping old config paths")
        else:
            p = {t: pre + str(uuid.UUID(bytes=secrets.token_bytes(16), version=4)) for t, (_, pre) in SLOTS.items()}
            print("[paths] new install: unique config paths generated")
        tmp = OUT_JSON + ".tmp"
        with open(tmp, "w") as f: json.dump(p, f, indent=1)
        os.replace(tmp, OUT_JSON)
    lines = [f"location = {p[t]} {{ proxy_pass http://127.0.0.1:{port}; include /etc/nginx/ws.inc; }}"
             for t, (port, _) in SLOTS.items()]
    with open(OUT_INC, "w") as f: f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
