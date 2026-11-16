"""Download every image referenced in backup/api JSON (original and large sizes) and write a manifest."""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_api import PoliteClient  # noqa: E402


class MediaBackup:
    EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
           "image/webp": ".webp", "image/svg+xml": ".svg", "application/pdf": ".pdf"}

    def __init__(self, root):
        self.root = Path(root)
        self.api = self.root / "api"
        self.client = PoliteClient(0.25)
        self.images = {}   # guid -> dict of size urls
        self.extra = set()  # other URLs (inline images, documents)
        self.manifest = []

    def walk(self, o):
        if isinstance(o, dict):
            if "guid" in o and "original" in o and isinstance(o["original"], str):
                self.images[o["guid"]] = o
            for k, v in o.items():
                if isinstance(v, str) and (k.endswith("rendered") or k == "text"):
                    for m in re.findall(r'<img[^>]+src="([^"]+)"', v):
                        self.extra.add(m)
                if k == "documents" and isinstance(v, list):
                    for d in v:
                        for kk in ("download_url", "url"):
                            if isinstance(d, dict) and d.get(kk):
                                self.extra.add(d[kk])
                self.walk(v)
        elif isinstance(o, list):
            for x in o:
                self.walk(x)

    def download(self, url, dest_stem, kind, guid=None):
        r = self.client.get(url)
        entry = {"url": url, "kind": kind, "guid": guid}
        if r is None or r.status_code != 200:
            entry.update(status=None if r is None else r.status_code, path=None)
            print("FAIL", url, entry["status"])
            self.manifest.append(entry)
            return
        ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
        ext = self.EXT.get(ctype, ".bin")
        path = dest_stem.with_suffix(ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        entry.update(status=200, path=str(path.relative_to(self.root)), bytes=len(r.content),
                     sha256=hashlib.sha256(r.content).hexdigest(), content_type=ctype)
        self.manifest.append(entry)

    def run(self):
        for f in sorted(self.api.rglob("*.json")):
            if f.name.startswith("_"):
                continue
            self.walk(json.loads(f.read_text()))
        print(len(self.images), "images,", len(self.extra), "extra urls")
        for i, (guid, d) in enumerate(sorted(self.images.items())):
            safe = re.sub(r"[^A-Za-z0-9_-]", "_", guid)
            self.download(d["original"], self.root / "images" / "original" / safe, "original", guid)
            if d.get("large"):
                self.download(d["large"], self.root / "images" / "large" / safe, "large", guid)
            if i % 50 == 0:
                print(i, "done")
        for url in sorted(self.extra):
            name = re.sub(r"[^A-Za-z0-9_.-]", "_", url.split("//", 1)[-1])[-120:]
            self.download(url, self.root / "images" / "other" / Path(name).stem, "inline")
        (self.root / "images" / "manifest.json").write_text(json.dumps(self.manifest, indent=1))
        ok = [m for m in self.manifest if m.get("status") == 200]
        print("ok", len(ok), "failed", len(self.manifest) - len(ok), "bytes", sum(m["bytes"] for m in ok))


if __name__ == "__main__":
    MediaBackup("/home/ubuntu/Projects/railcore-dozuki/backup").run()
