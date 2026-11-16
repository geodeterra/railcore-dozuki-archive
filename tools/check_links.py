"""Crawl the published Pages site and report broken internal links and images."""
import re
import sys
import time
import urllib.parse

import requests


class LinkChecker:
    def __init__(self, base):
        self.base = base
        self.prefix = urllib.parse.urlparse(base).path
        self.seen = {}
        self.pages = 0

    def run(self):
        queue = [self.base]
        s = requests.Session()
        while queue:
            url = queue.pop()
            if url in self.seen:
                continue
            r = s.get(url, timeout=60)
            self.seen[url] = r.status_code
            time.sleep(0.05)
            if r.status_code != 200 or not r.headers.get("Content-Type", "").startswith("text/html"):
                continue
            self.pages += 1
            for href in re.findall(r'(?:href|src)="([^"]+)"', r.text):
                u = urllib.parse.urljoin(url, href).split("#")[0]
                if urllib.parse.urlparse(u).netloc == urllib.parse.urlparse(self.base).netloc and \
                        urllib.parse.urlparse(u).path.startswith(self.prefix) and u not in self.seen:
                    queue.append(u)
        bad = {u: c for u, c in self.seen.items() if c != 200}
        print("pages", self.pages, "urls", len(self.seen), "bad", len(bad))
        for u, c in bad.items():
            print(c, u)
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(LinkChecker("https://geodeterra.github.io/railcore-dozuki-archive/").run())
