"""Fetch the raw Dozuki API JSON for railcore.dozuki.com into backup/api/."""
import json
import time
import urllib.parse
from pathlib import Path

import requests


class PoliteClient:
    """HTTP client that waits between requests and retries with backoff."""

    UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

    def __init__(self, delay=0.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = self.UA
        self.last = 0.0
        self.log = []

    def get(self, url, **kw):
        for attempt in range(6):
            wait = self.delay - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            try:
                r = self.session.get(url, timeout=120, **kw)
            except requests.RequestException as e:
                print("error", url, e)
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                print("retry", r.status_code, url)
                time.sleep(2 ** attempt * 2)
                continue
            self.log.append({"url": url, "status": r.status_code, "bytes": len(r.content)})
            return r
        self.log.append({"url": url, "status": "failed"})
        return None


class ApiBackup:
    BASE = "https://railcore.dozuki.com/api/2.0/"

    def __init__(self, root):
        self.root = Path(root)
        self.api = self.root / "api"
        self.client = PoliteClient(0.5)

    def save(self, rel, r):
        p = self.api / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = r.json()
            p.write_text(json.dumps(data, indent=1, ensure_ascii=False))
        except ValueError:
            data = None
            p.with_suffix(".txt").write_text(r.text)
        return data

    def fetch(self, path, rel):
        r = self.client.get(self.BASE + path)
        if r is None:
            print("FAILED", path)
            return None, None
        print(r.status_code, path, len(r.content))
        return r.status_code, self.save(rel, r)

    def run(self):
        _, guides = self.fetch("guides?limit=200", "guides_list.json")
        for path, rel in [("categories", "categories.json"),
                          ("categories/all", "categories_all.json"),
                          ("info", "site_info.json")]:
            self.fetch(path, rel)
        ids = sorted(g["guideid"] for g in guides)
        # also probe ids that are absent from the list (gaps and a few past the end)
        probe = sorted(set(range(1, max(ids) + 6)) - set(ids))
        status = {}
        users = set()
        for gid in ids + probe:
            code, data = self.fetch(f"guides/{gid}", f"guides/{gid}.json")
            status[gid] = code
            if code == 200:
                users.add(data["author"]["userid"])
        wikis = {}
        for ns in ["CATEGORY", "ITEM", "INFO", "WIKI", "TOPIC", "USER", "TEAM"]:
            code, lst = self.fetch(f"wikis/{ns}?limit=500", f"wikis_list_{ns}.json")
            if code != 200 or not lst:
                continue
            wikis[ns] = []
            for w in lst:
                path = urllib.parse.urlparse(w["url"]).path  # e.g. /Item/M3_Nut
                name = path.split("/", 2)[2]
                code, data = self.fetch(f"wikis/{ns}/{name}", f"wikis/{ns}/{w['wikiid']}.json")
                wikis[ns].append({"wikiid": w["wikiid"], "title": w["title"], "url": w["url"], "status": code})
                if code == 200 and data.get("author"):
                    users.add(data["author"]["userid"])
        comments = []
        offset = 0
        while True:
            code, page = self.fetch(f"comments?limit=200&offset={offset}", f"comments/all_offset{offset}.json")
            if code != 200 or not page:
                break
            comments.extend(page)
            offset += len(page)
        (self.api / "comments" / "all_comments.json").write_text(
            json.dumps(comments, indent=1, ensure_ascii=False))
        for c in comments:
            users.add(c["author"]["userid"])
            for rep in c.get("replies") or []:
                users.add(rep["author"]["userid"])
        for uid in sorted(users):
            self.fetch(f"users/{uid}", f"users/{uid}.json")
        # endpoints probed to document what works
        probes = {}
        for path in ["comments/guide/2", "guides/2/comments", "comments/step/7", "teams", "tags", "documents"]:
            r = self.client.get(self.BASE + path)
            probes[path] = r.status_code if r is not None else None
            print("probe", path, probes[path])
        summary = {"guide_status": status, "wikis": wikis, "comments": len(comments),
                   "users": sorted(users), "probes": probes}
        (self.api / "_fetch_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
        (self.api / "_request_log.json").write_text(json.dumps(self.client.log, indent=1))


if __name__ == "__main__":
    ApiBackup("/home/ubuntu/Projects/railcore-dozuki/backup").run()
