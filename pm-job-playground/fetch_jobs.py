#!/usr/bin/env python3
"""Fetch Product Manager openings from company job boards (Greenhouse, Ashby,
Lever, SmartRecruiters, Amazon) and write the top 20 that fit Mehreen's rules:
  - Stuttgart area: any work mode
  - elsewhere in Germany: remote or hybrid only
  - remote roles open to Germany (or EMEA/Europe-wide remote)
Every row links straight to the posting itself.

Usage: python3 fetch_jobs.py [--out daily.json] [--prev history/<yesterday>.json]
"""
import argparse, datetime as dt, json, re, sys, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

# (company, ats, board token, on Mehreen's 30-company target list, default mode in German offices)
BOARDS = [
    ("GitLab", "gh", "gitlab", True, "remote"),
    ("Stripe", "gh", "stripe", True, "hybrid"),
    ("Databricks", "gh", "databricks", True, "hybrid"),
    ("Contentful", "gh", "contentful", True, "hybrid"),
    ("N26", "gh", "n26", True, "hybrid"),
    ("Celonis", "gh", "celonis", True, "hybrid"),
    ("HelloFresh", "gh", "hellofresh", True, "hybrid"),
    ("Trade Republic", "gh", "traderepublicbank", True, "onsite"),
    ("Wolt", "gh", "wolt", True, "hybrid"),
    ("Miro", "gh", "realtimeboardglobal", True, "hybrid"),
    ("Grafana Labs", "gh", "grafanalabs", False, "remote"),
    ("Mozilla", "gh", "mozilla", False, "remote"),
    ("Datadog", "gh", "datadog", False, "hybrid"),
    ("Elastic", "gh", "elastic", False, "remote"),
    ("Cloudflare", "gh", "cloudflare", False, "hybrid"),
    ("MongoDB", "gh", "mongodb", False, "hybrid"),
    ("commercetools", "gh", "commercetools", False, "hybrid"),
    ("GetYourGuide", "gh", "getyourguide", False, "hybrid"),
    ("DeepL", "ashby", "deepl", True, "hybrid"),
    ("Snowflake", "ashby", "snowflake", True, "hybrid"),
    ("Miro", "ashby", "miro", True, "hybrid"),
    ("ElevenLabs", "ashby", "elevenlabs", False, "remote"),
    ("n8n", "ashby", "n8n", False, "hybrid"),
    ("Langfuse", "ashby", "langfuse", False, "hybrid"),
    ("Spotify", "lever", "spotify", True, "remote"),
    ("Veeva Systems", "lever", "veeva", False, "remote"),
    ("Bosch", "sr", "BoschGroup", True, "hybrid"),
    ("Delivery Hero", "sr", "DeliveryHero", True, "hybrid"),
    ("Celonis", "sr", "Celonis", True, "hybrid"),
    ("Continental", "sr", "Continental", False, "hybrid"),
    ("SumUp", "gh", "sumup", False, "hybrid"),
    ("Raisin", "gh", "raisin", False, "hybrid"),
    ("Grover", "gh", "grover", False, "hybrid"),
    ("trivago", "gh", "trivago", False, "hybrid"),
    ("Staffbase", "gh", "staffbase", False, "hybrid"),
    ("IONOS", "gh", "ionos", False, "hybrid"),
    ("Bitpanda", "gh", "bitpanda", False, "hybrid"),
    ("Parloa", "ashby", "parloa", False, "hybrid"),
    ("Enpal", "ashby", "enpal", False, "hybrid"),
    ("Buena", "ashby", "buena", False, "hybrid"),
    ("Cosuno", "ashby", "cosuno", False, "hybrid"),
    ("Ramp", "ashby", "ramp", False, "remote"),
    ("Linear", "ashby", "linear", False, "remote"),
    ("Supabase", "ashby", "supabase", False, "remote"),
    ("PostHog", "ashby", "posthog", False, "remote"),
    ("ClickHouse", "ashby", "clickhouse", False, "remote"),
    ("Amazon", "amazon", "", True, "onsite"),
]

PM = re.compile(r"product\s+(manager|owner|lead)|produktmanager|product management\b|\b(senior|staff|principal|group|lead|technical)\s+pm\b|\bhead of product\b", re.I)
EXCLUDE = re.compile(r"intern\b|internship|working student|werkstudent|praktik|trainee|thesis|abschlussarbeit|marketing manager|product marketing|duales studium|ausbildung", re.I)
STUTTGART = re.compile(r"stuttgart|b[öo]blingen|sindelfingen|ludwigsburg|esslingen|fellbach|leonberg|renningen|g[öo]ppingen|waiblingen|ehningen|weissach|weissach|zuffenhausen|vaihingen|feuerbach|gerlingen|kornwestheim|filderstadt|leinfelden|ditzingen|abstatt|immendingen|reutlingen|tübingen|tuebingen|heilbronn|schwieberdingen", re.I)
GERMANY = re.compile(r"germany|deutschland|\bDE\b|\bDEU\b|berlin|m[üu]nchen|munich|hamburg|frankfurt|k[öo]ln|cologne|d[üu]sseldorf|walldorf|karlsruhe|leipzig|dresden|hannover|n[üu]rnberg|nuremberg|erlangen|aachen|bonn|essen|dortmund|mannheim|heidelberg|potsdam|jena|freiburg|augsburg|regensburg|ingolstadt|wolfsburg|darmstadt|" + STUTTGART.pattern, re.I)
EUROPE_REMOTE = re.compile(r"emea|europe|\beu\b|european", re.I)
TRAVEL = [(r"walldorf|karlsruhe|heidelberg|mannheim|ulm", 1.2), (r"frankfurt|m[üu]nchen|munich|n[üu]rnberg|nuremberg|augsburg|darmstadt|erlangen|ingolstadt|würzburg", 2.2),
          (r"k[öo]ln|cologne|bonn|d[üu]sseldorf|aachen|essen|dortmund", 2.8), (r"berlin|hamburg|leipzig|dresden|hannover|potsdam|jena|wolfsburg", 5.0)]

UA = {"User-Agent": "Mozilla/5.0 (job-search helper)", "Accept": "application/json"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return json.load(r)

def day(s):
    if not s: return "n/a"
    if isinstance(s, (int, float)): return dt.datetime.fromtimestamp(s / 1000, dt.timezone.utc).date().isoformat()
    m = re.search(r"\d{4}-\d{2}-\d{2}", str(s))
    if m: return m.group(0)
    try: return dt.datetime.strptime(str(s).strip(), "%B %d, %Y").date().isoformat()
    except Exception: return "n/a"

def fetch(board):
    name, ats, tok, target, default = board
    out = []
    try:
        if ats == "gh":
            for j in get(f"https://boards-api.greenhouse.io/v1/boards/{tok}/jobs").get("jobs", []):
                out.append(dict(role=j["title"], location=(j.get("location") or {}).get("name", ""), url=j["absolute_url"],
                                posted=day(j.get("first_published") or j.get("updated_at")), wp=""))
        elif ats == "ashby":
            for j in get(f"https://api.ashbyhq.com/posting-api/job-board/{tok}").get("jobs", []):
                locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
                country = (((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry")) or ""
                wp = (j.get("workplaceType") or "").lower() or ("remote" if j.get("isRemote") else "")
                out.append(dict(role=j["title"], location="; ".join(l for l in locs if l) + (f" ({country})" if country and country not in locs[0] else ""),
                                url=j.get("jobUrl"), posted=day(j.get("publishedAt")), wp=wp))
        elif ats == "lever":
            for j in get(f"https://api.lever.co/v0/postings/{tok}?mode=json"):
                cats = j.get("categories") or {}
                locs = cats.get("allLocations") or [cats.get("location", "")]
                out.append(dict(role=j["text"], location="; ".join(locs) + (f" ({j.get('country')})" if j.get("country") else ""),
                                url=j.get("hostedUrl"), posted=day(j.get("createdAt")), wp=(j.get("workplaceType") or "").lower()))
        elif ats == "sr":
            seen_sr = {}
            for term in ("product", "produkt"):
                q = urllib.parse.urlencode({"q": term, "country": "de", "limit": 100})
                for j in get(f"https://api.smartrecruiters.com/v1/companies/{tok}/postings?{q}").get("content", []):
                    seen_sr[j["id"]] = j
            for j in seen_sr.values():
                loc = j.get("location") or {}
                wp = "remote" if loc.get("remote") else ("hybrid" if loc.get("hybrid") else "")
                out.append(dict(role=j["name"], location=", ".join(x for x in [loc.get("city"), "Germany" if (loc.get("country") or "").lower() == "de" else loc.get("country")] if x),
                                url=f"https://jobs.smartrecruiters.com/{tok}/{j['id']}", posted=day(j.get("releasedDate")), wp=wp))
        elif ats == "amazon":
            q = urllib.parse.urlencode({"base_query": "product manager", "country": "DEU", "result_limit": 100, "sort": "recent"})
            for j in get(f"https://www.amazon.jobs/en/search.json?{q}").get("jobs", []):
                out.append(dict(role=j["title"], location=j.get("normalized_location") or j.get("location", ""),
                                url="https://www.amazon.jobs" + j.get("job_path", ""), posted=day(j.get("posted_date")), wp=""))
    except Exception as e:
        print(f"[warn] {name} ({ats}:{tok}) failed: {e}", file=sys.stderr)
        return name, []
    res = []
    for o in out:
        if not o["url"] or not PM.search(o["role"]) or EXCLUDE.search(o["role"]): continue
        text = f"{o['location']} {o['role']}"
        local = bool(STUTTGART.search(o["location"]))
        de = bool(GERMANY.search(o["location"]))
        remote = o["wp"] == "remote" or bool(re.search(r"remote|anywhere|home office", text, re.I))
        hybrid = o["wp"] == "hybrid" or bool(re.search(r"hybrid", text, re.I))
        if local:
            mode = "remote" if remote else ("hybrid" if hybrid else (o["wp"] or "check posting"))
        elif remote and (de or EUROPE_REMOTE.search(o["location"]) or o["location"].strip().lower() in ("remote", "")):
            if not (de or EUROPE_REMOTE.search(o["location"])): continue  # plain "Remote" is usually US-only
            mode = "remote"
        elif de and (hybrid or (o["wp"] != "onsite" and default in ("hybrid", "remote"))):
            mode = "hybrid" if hybrid or o["wp"] == "hybrid" else "hybrid (company policy)"
        else:
            continue
        city_h = 0.4 if local else next((h for p, h in TRAVEL if re.search(p, o["location"], re.I)), None)
        travel = city_h if city_h is not None else (0 if mode == "remote" else 3.0)
        res.append(dict(company=name, role=o["role"].strip(), location=o["location"].strip() or "n/a", mode=mode, posted=o["posted"],
                        travel_h=travel, target=target, germany_explicit=de, url=o["url"], source=ats))
    return name, res

def rank_key(x):
    # Mehreen's priority: 1 Stuttgart area, 2 other German cities, 3 remote (no fixed city), then remote before hybrid inside each group
    loc = x["location"]
    if STUTTGART.search(loc): group = 1
    elif x["travel_h"] and GERMANY.search(loc) and not re.fullmatch(r"\W*(remote|germany|deutschland|de)\W*(\(.*\))?\W*", loc, re.I): group = 2
    else: group = 3
    mode_rank = 0 if x["mode"] == "remote" else 1 if x["mode"] == "hybrid" else 2
    newest = -int(x["posted"].replace("-", "")) if x["posted"][:4].isdigit() else 0
    try: stale = (dt.date.today() - dt.date.fromisoformat(x["posted"])).days > 90
    except Exception: stale = True
    return (group, mode_rank, stale, not x["target"], newest, x["travel_h"] or 0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="daily.json")
    ap.add_argument("--prev", default="")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(fetch, BOARDS))
    allrows, seen = [], set()
    for name, rows in results:
        for r in rows:
            if r["url"] in seen: continue
            seen.add(r["url"]); allrows.append(r)
    allrows.sort(key=rank_key)
    top, per = [], {}
    for r in allrows:
        if per.get(r["company"], 0) >= 3: continue
        per[r["company"]] = per.get(r["company"], 0) + 1
        top.append(r)
        if len(top) == a.top: break
    prev = set()
    if a.prev:
        try: prev = {x["url"] for x in json.load(open(a.prev))["items"]}
        except Exception: pass
    for r in top:
        r["new"] = bool(prev) and r["url"] not in prev
    checked = sum(1 for _, rows in results)
    data = {"updated": dt.date.today().isoformat(),
            "note": f"Pulled from {checked} company job boards; {len(allrows)} PM roles qualified (Stuttgart area, or remote/hybrid in Germany). Every link opens the posting itself. 'hybrid (company policy)' means the ad does not say, so the company's usual office policy is assumed.",
            "total_qualified": len(allrows), "items": top}
    json.dump(data, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(allrows)} qualified, wrote top {len(top)} to {a.out}")
    for i, r in enumerate(top, 1):
        print(f"{i:2}. {r['company']:<16} {r['mode']:<24} {r['location'][:40]:<40} {r['posted']}  {r['role'][:60]}")

if __name__ == "__main__":
    main()
