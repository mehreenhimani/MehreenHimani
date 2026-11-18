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
    ("JetBrains", "gh", "jetbrains", False, "hybrid"),
    ("Canonical (Ubuntu)", "gh", "canonical", False, "remote"),
    ("Wikimedia Foundation", "gh", "wikimedia", False, "remote"),
    ("Twilio", "gh", "twilio", False, "remote"),
    ("Okta", "gh", "okta", False, "hybrid"),
    ("Figma", "gh", "figma", False, "hybrid"),
    ("Airtable", "gh", "airtable", False, "hybrid"),
    ("PagerDuty", "gh", "pagerduty", False, "hybrid"),
    ("New Relic", "gh", "newrelic", False, "remote"),
    ("Algolia", "gh", "algolia", False, "hybrid"),
    ("Braze", "gh", "braze", False, "hybrid"),
    ("Mixpanel", "gh", "mixpanel", False, "hybrid"),
    ("LaunchDarkly", "gh", "launchdarkly", False, "remote"),
    ("Trustpilot", "gh", "trustpilot", False, "hybrid"),
    ("Typeform", "gh", "typeform", False, "hybrid"),
    ("Storyblok", "gh", "storyblok", False, "remote"),
    ("Neo4j", "gh", "neo4j", False, "remote"),
    ("Cockroach Labs", "gh", "cockroachlabs", False, "remote"),
    ("Sumo Logic", "gh", "sumologic", False, "remote"),
    ("Intercom", "gh", "intercom", False, "hybrid"),
    ("CircleCI", "gh", "circleci", False, "remote"),
    ("Adyen", "gh", "adyen", False, "hybrid"),
    ("Camunda", "ashby", "camunda", False, "hybrid"),
    ("Redis", "ashby", "redis", False, "remote"),
    ("Amplitude", "ashby", "amplitude", False, "hybrid"),
    ("Snyk", "ashby", "snyk", False, "remote"),
    ("Mollie", "ashby", "mollie", False, "hybrid"),
    ("Sentry", "ashby", "sentry", False, "hybrid"),
    ("Docker", "ashby", "docker", False, "remote"),
    ("1Password", "ashby", "1password", False, "remote"),
    ("Zapier", "ashby", "zapier", False, "remote"),
    ("Notion", "ashby", "notion", False, "hybrid"),
    ("Contentsquare", "lever", "contentsquare", False, "hybrid"),
    ("SonarSource", "lever", "sonarsource", False, "hybrid"),
    ("Toptal", "lever", "toptal", False, "remote"),
    ("Sixt", "sr", "Sixt", False, "hybrid"),
    ("ServiceNow", "sr", "ServiceNow", False, "hybrid"),
    ("Canva", "sr", "Canva", False, "hybrid"),
    ("FlixBus", "gh", "flix", False, "hybrid"),
    ("Helsing", "gh", "helsing", False, "hybrid"),
    ("Amazon", "amazon", "", True, "onsite"),
]

PM = re.compile(r"product\s+(manager|owner|lead)|produktmanager|product management\b|\b(senior|staff|principal|group|lead|technical)\s+pm\b|\bhead of product\b", re.I)
EXCLUDE = re.compile(r"intern\b|internship|working student|werkstudent|praktik|trainee|thesis|abschlussarbeit|marketing manager|product marketing|duales studium|ausbildung", re.I)
STUTTGART = re.compile(r"stuttgart|b[öo]blingen|sindelfingen|ludwigsburg|esslingen|fellbach|leonberg|renningen|g[öo]ppingen|waiblingen|ehningen|weissach|weissach|zuffenhausen|vaihingen|feuerbach|gerlingen|kornwestheim|filderstadt|leinfelden|ditzingen|abstatt|immendingen|reutlingen|tübingen|tuebingen|heilbronn|schwieberdingen", re.I)
GERMANY = re.compile(r"germany|deutschland|\bDE\b|\bDEU\b|berlin|m[üu]nchen|munich|hamburg|frankfurt|k[öo]ln|cologne|d[üu]sseldorf|walldorf|karlsruhe|leipzig|dresden|hannover|n[üu]rnberg|nuremberg|erlangen|aachen|bonn|essen|dortmund|mannheim|heidelberg|potsdam|jena|freiburg|augsburg|regensburg|ingolstadt|wolfsburg|darmstadt|" + STUTTGART.pattern, re.I)
EUROPE_REMOTE = re.compile(r"emea|europe|\beu\b|european", re.I)
TRAVEL = [(r"walldorf|karlsruhe|heidelberg|mannheim|ulm", 1.2), (r"frankfurt|m[üu]nchen|munich|n[üu]rnberg|nuremberg|augsburg|darmstadt|erlangen|ingolstadt|würzburg", 2.2),
          (r"k[öo]ln|cologne|bonn|d[üu]sseldorf|aachen|essen|dortmund", 2.8), (r"berlin|hamburg|leipzig|dresden|hannover|potsdam|jena|wolfsburg", 5.0)]

# Early-stage startups Mehreen asked to leave out ("top companies, not the startup kind")
STARTUPS = {"n8n", "Cosuno", "Buena", "Langfuse", "Parloa", "Enpal", "Grover", "Raisin", "Bitpanda", "Linear",
            "Supabase", "PostHog", "Ramp", "ClickHouse", "Staffbase", "commercetools", "GetYourGuide", "ElevenLabs"}

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
            for term in ("product", "produkt", "product manager", "product owner"):
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
        remote = o["wp"] == "remote" or bool(re.search(r"remote|anywhere|home[- ]?office|home[- ]?based|distributed|work from home|\bwfh\b", text, re.I))
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
    ap.add_argument("--max-age", type=int, default=14, help="drop posts older than this many days, or with no date")
    a = ap.parse_args()
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(fetch, [b for b in BOARDS if b[0] not in STARTUPS]))
    allrows, seen = [], set()
    for name, rows in results:
        for r in rows:
            key = (r["company"], re.sub(r"\W+", " ", r["role"].lower()).strip())
            if r["url"] in seen or key in seen: continue
            seen.add(r["url"]); seen.add(key); allrows.append(r)
    def fresh(r):
        try: return (dt.date.today() - dt.date.fromisoformat(r["posted"])).days <= a.max_age
        except Exception: return False  # no posting date: cannot prove it is recent
    dropped = len(allrows)
    allrows = [r for r in allrows if fresh(r)]
    dropped -= len(allrows)
    allrows.sort(key=rank_key)
    top, per = [], {}
    for r in allrows:
        if len(allrows) > a.top and per.get(r["company"], 0) >= 3: continue
        per[r["company"]] = per.get(r["company"], 0) + 1
        top.append(r)
        if len(top) == a.top: break
    prev, prev_remote = set(), set()
    if a.prev:
        try:
            pj = json.load(open(a.prev))
            prev = {x["url"] for x in pj["items"]}
            prev_remote = {x["url"] for x in pj.get("remote_all", [])} | prev
        except Exception: pass
    for r in top:
        r["new"] = bool(prev) and r["url"] not in prev
    def is_remote(r):
        return r["mode"] == "remote"
    remote_all = sorted([dict(r) for r in allrows if is_remote(r)],
                        key=lambda x: (not x["target"], -int(x["posted"].replace("-", "")) if x["posted"][:4].isdigit() else 0))
    for r in remote_all:
        r["new"] = bool(prev) and r["url"] not in prev_remote
    checked = len(results)
    data = {"updated": dt.date.today().isoformat(),
            "note": f"Only posts from the last {a.max_age} days ({dropped} older or undated posts left out). Pulled from {checked} established companies' job boards; {len(allrows)} PM roles qualified (Stuttgart area, or remote/hybrid in Germany). Every link opens the posting itself. 'hybrid (company policy)' means the ad does not say, so the company's usual office policy is assumed.",
            "total_qualified": len(allrows), "items": top, "remote_all": remote_all}
    json.dump(data, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(allrows)} qualified, wrote top {len(top)} + {len(remote_all)} remote roles to {a.out}")
    for r in remote_all: print(f"   remote: {r['company']:<16} {r['location'][:40]:<40} {r['posted']}  {r['role'][:60]}")
    for i, r in enumerate(top, 1):
        print(f"{i:2}. {r['company']:<16} {r['mode']:<24} {r['location'][:40]:<40} {r['posted']}  {r['role'][:60]}")

if __name__ == "__main__":
    main()
