import os, json, requests
from datetime import datetime, timezone

METAL_KEY = os.environ["METAL_API_KEY"]
TG_TOKEN  = os.environ["TG_TOKEN"]
TG_CHAT   = os.environ["TG_CHAT"]
OZ_TO_G   = 31.1035

def metal_usd(symbol):
    r = requests.get(f"https://www.goldapi.io/api/{symbol}/USD",
                     headers={"x-access-token": METAL_KEY}, timeout=20)
    return r.json()["price"]

usd_npr = requests.get("https://open.er-api.com/v6/latest/USD", timeout=20).json()["rates"]["NPR"]
per10 = lambda usd_oz: usd_oz / OZ_TO_G * 10 * usd_npr

now = {"gold": per10(metal_usd("XAU")), "silver": per10(metal_usd("XAG"))}

try:
    data = json.load(open("data.json"))
except Exception:
    data = {"history": []}

prev = data["history"][-1] if data["history"] else None
def change(k):
    return round((now[k] - prev[k]) / prev[k] * 100, 2) if prev else None

stamp = datetime.now(timezone.utc).isoformat(timespec="minutes")
data["history"].append({"t": stamp, "gold": round(now["gold"]), "silver": round(now["silver"])})
data["history"] = data["history"][-60:]
data.update({"updated": stamp, "usd_npr": round(usd_npr, 2),
             "gold": {"npr10g": round(now["gold"]), "change_pct": change("gold")},
             "silver": {"npr10g": round(now["silver"]), "change_pct": change("silver")}})
json.dump(data, open("data.json", "w"), indent=1)

def line(name, k):
    c = data[k]["change_pct"]
    arrow = "" if c is None else f"  ({'▲' if c >= 0 else '▼'} {c:+.2f}%)"
    return f"{name}: NPR {data[k]['npr10g']:,} per 10g{arrow}"

msg = "📊 Daily Metals Update\n" + line("Gold", "gold") + "\n" + line("Silver", "silver")
requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
              data={"chat_id": TG_CHAT, "text": msg})
