"""Build the Markdown/Jekyll mirror in site/ from the raw API backup in backup/."""
import html
import os
import json
import re
import shutil
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from markdownify import markdownify
from PIL import Image, ImageOps

CAPTURE_DATE = "2026-11-16"
SITE_URL = "https://railcore.dozuki.com"


class Attribution:
    """Text blocks shared by every page."""

    LICENSE = ("[Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0)]"
               "(https://creativecommons.org/licenses/by-sa/3.0/)")

    @classmethod
    def footer(cls, original_url, authors):
        who = ", ".join(sorted(authors)) if authors else "the railcore.dozuki.com contributors"
        return (
            "\n---\n\n"
            f"Original page: <{original_url}>. Written by {who} on railcore.dozuki.com. "
            f"This copy was captured on {CAPTURE_DATE} and is licensed under {cls.LICENSE}, "
            "the license stated on the original site. "
            "This is an unofficial community mirror and is not affiliated with RailCore Labs, LLC. "
            "RAILCORE is a registered trademark of RailCore Labs, LLC.\n")


class Slug:
    @staticmethod
    def make(text):
        text = text.replace("®", "")
        text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
        return text or "page"


class Images:
    """Copies the web-sized ("large") image and a 1600 px zoom copy into the site."""

    def __init__(self, backup, site):
        self.backup = backup
        self.site = site
        manifest = json.loads((backup / "images" / "manifest.json").read_text())
        self.files = {}
        for e in manifest:
            if e.get("path") and e.get("guid"):
                self.files.setdefault(e["guid"], {})[e["kind"]] = backup / e["path"]
        self.used = set()

    def paths(self, guid):
        """Return (display path, zoom path) relative to the site root, or None."""
        f = self.files.get(guid)
        if not f:
            return None
        large_dst = self.site / "assets" / "images" / "large" / f"{guid}.jpg"
        zoom_dst = self.site / "assets" / "images" / "zoom" / f"{guid}.jpg"
        if guid not in self.used:
            large_dst.parent.mkdir(parents=True, exist_ok=True)
            zoom_dst.parent.mkdir(parents=True, exist_ok=True)
            if "large" in f:
                shutil.copyfile(f["large"], large_dst)
            else:
                self.resize(f["original"], large_dst, 800)
            if "original" in f:
                self.resize(f["original"], zoom_dst, 1600)
            else:
                shutil.copyfile(f["large"], zoom_dst)
            self.used.add(guid)
        return (f"assets/images/large/{guid}.jpg", f"assets/images/zoom/{guid}.jpg")

    @staticmethod
    def resize(src, dst, size):
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((size, size), Image.LANCZOS)
        im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)


class Builder:
    def __init__(self, root):
        self.root = Path(root)
        self.backup = self.root / "backup"
        self.api = self.backup / "api"
        self.site = self.root / "site"
        self.images = Images(self.backup, self.site)
        self.guides = {}
        for f in sorted((self.api / "guides").glob("*.json")):
            g = json.loads(f.read_text())
            if "steps" in g:
                self.guides[g["guideid"]] = g
        self.categories = {}  # name -> dir slug
        for name in sorted({g["category"] for g in self.guides.values()}):
            self.categories[name] = Slug.make(name)
        self.guide_path = {gid: f"{self.categories[g['category']]}/{Slug.make(g['title'])}.md"
                           for gid, g in self.guides.items()}
        self.items = {}
        for f in sorted((self.api / "wikis" / "ITEM").glob("*.json")):
            w = json.loads(f.read_text())
            self.items[w["wikiid"]] = w
        self.item_path = {}
        self.item_by_url = {}
        for wid, w in self.items.items():
            self.item_path[wid] = f"items/{Slug.make(w['title'])}-{wid}.md"
            self.item_by_url[urllib.parse.unquote(w["url"]).lower()] = wid
        self.cat_wikis = {}
        for f in sorted((self.api / "wikis" / "CATEGORY").glob("*.json")):
            w = json.loads(f.read_text())
            self.cat_wikis[w["title"]] = w
        self.stats = {"guides": 0, "steps": 0, "step_images": 0, "comments": 0, "items": 0}

    # ---------- helpers ----------
    @staticmethod
    def rel(from_path, to_path):
        """Relative link from one site file to another (both relative to site root)."""
        return os.path.relpath(to_path, start=os.path.dirname(from_path) or ".")

    def rewrite_link(self, href, page):
        """Map a Dozuki link to the local Markdown page where one exists."""
        if href.startswith("#") or href.startswith("mailto:"):
            return href
        absu = urllib.parse.urljoin(SITE_URL + "/", href)
        u = urllib.parse.urlparse(absu)
        if u.netloc != "railcore.dozuki.com":
            return href
        path = urllib.parse.unquote(u.path)
        m = re.match(r"/Guide/[^/]*/(\d+)", path)
        if m and int(m.group(1)) in self.guide_path:
            return self.rel(page, self.guide_path[int(m.group(1))])
        if path.lower().startswith("/item/"):
            wid = self.item_by_url.get((SITE_URL + path).lower())
            if wid:
                return self.rel(page, self.item_path[wid])
        m = re.match(r"/c/(.+)", path)
        if m:
            name = m.group(1).replace("_", " ")
            if name in self.categories:
                return self.rel(page, f"{self.categories[name]}/index.md")
        return absu

    def html_to_md(self, text, page, inline=False):
        if not text:
            return ""
        text = re.sub(r'href="([^"]+)"',
                      lambda m: 'href="%s"' % html.escape(self.rewrite_link(html.unescape(m.group(1)), page)),
                      text)
        md = markdownify(text, heading_style="ATX", bullets="-", escape_underscores=False,
                         escape_asterisks=False).strip()
        if inline:
            md = re.sub(r"\s*\n\s*", " ", md)
        return self.liquid_safe(md)

    @staticmethod
    def liquid_safe(md):
        if "{{" in md or "{%" in md:
            return "{% raw %}" + md + "{% endraw %}"
        return md

    @staticmethod
    def date(ts):
        if not ts:
            return ""
        return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def front(title, extra=""):
        return f"---\nlayout: default\ntitle: {json.dumps(title, ensure_ascii=False)}\n{extra}---\n\n"

    def image_md(self, img, page, alt):
        if not img or not img.get("guid"):
            return ""
        p = self.images.paths(img["guid"])
        if not p:
            return ""
        return f"[![{alt}]({self.rel(page, p[0])})]({self.rel(page, p[1])})"

    def comments_md(self, comments, page, depth=0):
        out = []
        for c in comments:
            if c.get("status") == "deleted":
                continue
            self.stats["comments"] += 1
            body = self.html_to_md(c.get("text_rendered") or html.escape(c.get("text_raw", "")), page)
            prefix = "> " * (depth + 1)
            name = c["author"]["username"]
            out.append(f"{prefix}**{name}** wrote on {self.date(c['date'])}:\n{prefix}\n"
                       + "\n".join(prefix + line if line else prefix.rstrip() for line in body.split("\n")))
            if c.get("replies"):
                out.append(self.comments_md(c["replies"], page, depth + 1))
        return "\n\n".join(x for x in out if x)

    def line_md(self, line, page):
        text = self.html_to_md(line["text_rendered"], page, inline=True)
        style = line.get("bullet_style") or {}
        kind = style.get("type", "dot")
        indent = "  " * int(line.get("level") or 0)
        if kind in ("note", "caution", "reminder", "warning") or line["bullet"].startswith("icon_"):
            label = style.get("label") or line["bullet"].replace("icon_", "").title()
            return f"{indent}- **{label}:** {text}"
        if line["bullet"] != "black":
            color = style.get("bullet_color") or "#000"
            return (f'{indent}- <span style="color:{color}" title="{line["bullet"]} bullet">&#9679;</span> '
                    f"{text}")
        return f"{indent}- {text}"

    def item_link(self, entry, page):
        wid = entry.get("wikiid")
        label = entry.get("text") or entry.get("name")
        if wid in self.item_path:
            return f"[{label}]({self.rel(page, self.item_path[wid])})"
        return label

    # ---------- pages ----------
    def guide_page(self, gid, siblings):
        g = self.guides[gid]
        page = self.guide_path[gid]
        authors = {g["author"]["username"]}
        out = [self.front(g["title"]), f"# {g['title']}\n"]
        out.append(f"Category: [{g['category']}]({self.rel(page, self.categories[g['category']] + '/index.md')}) · "
                   f"Original: <{g['url']}>\n")
        if g.get("summary"):
            out.append(f"*{g['summary']}*\n")
        if g.get("image"):
            out.append(self.image_md(g["image"], page, g["title"]) + "\n")
        meta = []
        if g.get("difficulty"):
            meta.append(f"**Difficulty:** {g['difficulty']}")
        if g.get("time_required"):
            meta.append(f"**Time required:** {g['time_required']}")
        meta.append(f"**Author:** {g['author']['username']}")
        meta.append(f"**Steps:** {len(g['steps'])}")
        if g.get("modified_date"):
            meta.append(f"**Last modified on Dozuki:** {self.date(g['modified_date'])}")
        out.append("  \n".join(meta) + "\n")
        if g.get("introduction_rendered"):
            out.append("## Introduction\n\n" + self.html_to_md(g["introduction_rendered"], page) + "\n")
        if g.get("prerequisites"):
            out.append("## Prerequisites\n")
            for p in g["prerequisites"]:
                pid = p.get("guideid")
                if pid in self.guide_path:
                    out.append(f"- [{p.get('title')}]({self.rel(page, self.guide_path[pid])})")
                else:
                    out.append(f"- [{p.get('title')}]({p.get('url')})")
            out.append("")
        if g.get("tools"):
            out.append("## Tools\n")
            for t in g["tools"]:
                q = f"{t['quantity']} × " if t.get("quantity") and t["quantity"] != 1 else ""
                n = f" ({t['notes']})" if t.get("notes") else ""
                out.append(f"- {q}{self.item_link(t, page)}{n}")
            out.append("")
        if g.get("parts"):
            out.append("## Parts\n")
            for t in g["parts"]:
                q = f"{t['quantity']} × " if t.get("quantity") else ""
                n = f" {t['notes']}" if t.get("notes") else ""
                out.append(f"- {q}{self.item_link(t, page)}{n}")
            out.append("")
        if g.get("documents"):
            out.append("## Documents\n")
            for d in g["documents"]:
                out.append(f"- [{d.get('text') or d.get('filename') or 'document'}]({d.get('download_url') or d.get('url')})")
            out.append("")
        for n, s in enumerate(sorted(g["steps"], key=lambda s: s["orderby"]), 1):
            self.stats["steps"] += 1
            title = f"Step {n}" + (f": {s['title']}" if s.get("title") else "")
            out.append(f"## {title}\n")
            imgs = s["media"].get("data") or [] if s["media"].get("type") == "image" else []
            if imgs:
                out.append(" ".join(self.image_md(im, page, f"{title}, image {i + 1}")
                                    for i, im in enumerate(imgs)) + "\n")
                self.stats["step_images"] += len(imgs)
            elif s["media"].get("type") not in ("image", None):
                out.append(f"*(Step media of type {s['media']['type']} is not reproduced; see the original guide.)*\n")
            out.append("\n".join(self.line_md(l, page) for l in s["lines"]) + "\n")
            visible = [c for c in s.get("comments") or [] if c.get("status") != "deleted"]
            if visible:
                word = "comment" if len(visible) == 1 else "comments"
                out.append(f"**{len(visible)} {word} on step {n}:**\n\n" + self.comments_md(visible, page) + "\n")
        if g.get("conclusion_rendered"):
            out.append("## Conclusion\n\n" + self.html_to_md(g["conclusion_rendered"], page) + "\n")
        visible = [c for c in g.get("comments") or [] if c.get("status") != "deleted"]
        if visible:
            out.append(f"## Comments on this guide ({len(visible)})\n\n" + self.comments_md(visible, page) + "\n")
        idx = siblings.index(gid)
        nav = []
        if idx > 0:
            p = siblings[idx - 1]
            nav.append(f"Previous: [{self.guides[p]['title']}]({self.rel(page, self.guide_path[p])})")
        nav.append(f"[{g['category']} guide list]({self.rel(page, self.categories[g['category']] + '/index.md')})")
        if idx < len(siblings) - 1:
            p = siblings[idx + 1]
            nav.append(f"Next: [{self.guides[p]['title']}]({self.rel(page, self.guide_path[p])})")
        out.append("\n" + " · ".join(nav) + "\n")
        out.append(Attribution.footer(g["url"], authors))
        self.write(page, "\n".join(out))
        self.stats["guides"] += 1

    def category_page(self, name, gids):
        page = f"{self.categories[name]}/index.md"
        w = self.cat_wikis.get(name, {})
        url = w.get("fullUrl") or f"{SITE_URL}/c/{urllib.parse.quote(name.replace(' ', '_'))}"
        out = [self.front(name), f"# {name}\n", f"Original: <{url}>\n"]
        if w.get("image"):
            out.append(self.image_md(w["image"], page, name) + "\n")
        if w.get("contents_rendered"):
            out.append(self.html_to_md(w["contents_rendered"], page) + "\n")
        out.append(f"## Guides ({len(gids)})\n")
        out.append("| Guide | Difficulty | Time | Steps |\n|---|---|---|---|")
        for gid in gids:
            g = self.guides[gid]
            out.append(f"| [{g['title']}]({self.rel(page, self.guide_path[gid])}) | {g.get('difficulty') or ''} | "
                       f"{g.get('time_required') or ''} | {len(g['steps'])} |")
        out.append(f"\n[Back to the archive home]({self.rel(page, 'index.md')})\n")
        authors = {self.guides[gid]["author"]["username"] for gid in gids}
        out.append(Attribution.footer(url, authors))
        self.write(page, "\n".join(out))

    def item_pages(self):
        used = {}
        for gid, g in self.guides.items():
            for kind in ("parts", "tools"):
                for e in g.get(kind) or []:
                    used.setdefault(e.get("wikiid"), []).append((gid, kind, e))
        rows = []
        for wid, w in sorted(self.items.items(), key=lambda kv: kv[1]["display_title"].lower()):
            page = self.item_path[wid]
            out = [self.front(w["display_title"]), f"# {w['display_title']}\n", f"Original: <{w['fullUrl']}>\n"]
            img = w.get("image")
            if img and img.get("guid"):
                out.append(self.image_md(img, page, w["display_title"]) + "\n")
            if w.get("contents_rendered"):
                out.append(self.html_to_md(w["contents_rendered"], page) + "\n")
            refs = used.get(wid, [])
            if refs:
                out.append("## Used in these guides\n")
                for gid, kind, e in sorted(refs, key=lambda r: (self.guides[r[0]]["category"], self.guides[r[0]]["title"])):
                    g = self.guides[gid]
                    q = f", quantity {e['quantity']}" if e.get("quantity") else ""
                    out.append(f"- [{g['category']}: {g['title']}]({self.rel(page, self.guide_path[gid])})"
                               f" ({kind[:-1]}{q})")
                out.append("")
            else:
                out.append("This item is not listed in any guide's parts or tools.\n")
            out.append(f"[All parts and tools]({self.rel(page, 'items/index.md')})\n")
            author = {w["author"]["username"]} if w.get("author") else set()
            out.append(Attribution.footer(w["fullUrl"], author))
            self.write(page, "\n".join(out))
            rows.append(f"- [{w['display_title']}]({Path(page).name}) (used in {len({r[0] for r in refs})} guides)")
            self.stats["items"] += 1
        out = [self.front("Parts and tools"), "# Parts and tools\n",
               f"These pages come from the Item wiki pages on railcore.dozuki.com ({len(rows)} pages). "
               "On the original site most of them contain only a title, so each page here also lists the guides "
               "that use the item.\n"] + rows + [f"\n[Back to the archive home](../index.md)\n",
                                                 Attribution.footer(SITE_URL, set())]
        self.write("items/index.md", "\n".join(out))

    def home_page(self, by_cat):
        out = [self.front("RailCore build guides (unofficial archive)"),
               "# RailCore build guides (unofficial archive)\n",
               f"This is an unofficial community mirror of <{SITE_URL}/>, the Dozuki site that hosts the "
               f"RailCore® II and RailCore® Mini Kit build guides. It was captured on {CAPTURE_DATE} "
               "because the Dozuki site may be shut down. Each page links back to its original URL.\n",
               "RailCore® is a family of CoreXY RepRap 3D printers designed by J. Steve White, Tony Akens and "
               "Ben Withem (<https://railcore.org/>). The guides were written on railcore.dozuki.com by "
               "Tony Akens and Ben Withem; comments are credited to their authors on each page.\n"]
        for name, gids in by_cat.items():
            out.append(f"## [{name}]({self.categories[name]}/index.md)\n")
            for gid in gids:
                g = self.guides[gid]
                n = len(g['steps'])
                out.append(f"- [{g['title']}]({self.guide_path[gid]}) ({n} step{'' if n == 1 else 's'})")
            out.append("")
        out.append(f"## Other pages\n\n- [Parts and tools](items/index.md) ({len(self.items)} pages)\n"
                   "- [License and attribution](LICENSE.md)\n")
        out.append("## What this mirror contains\n\n"
                   f"- {self.stats['guides']} guides with {self.stats['steps']} steps and "
                   f"{self.stats['step_images']} step images, plus {self.stats['comments']} comments.\n"
                   "- Images are shown at 800 px; click an image to open a 1600 px copy.\n"
                   "- Left out: comments that were deleted on Dozuki, one guide (id 22) that is not public, "
                   "user profiles, and Dozuki's own help, FAQ and privacy pages.\n")
        out.append("## License\n\n"
                   f"The content is licensed under {Attribution.LICENSE}, the license stated on the original site "
                   "(see [License and attribution](LICENSE.md)). "
                   "RAILCORE is a registered trademark of RailCore Labs, LLC. This mirror is not affiliated "
                   "with RailCore Labs, LLC.\n")
        self.write("index.md", "\n".join(out))

    def write(self, rel, text):
        p = self.site / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text.rstrip() + "\n")

    def run(self):
        for sub in ["assets", "items"] + list(self.categories.values()):
            if (self.site / sub).exists():
                shutil.rmtree(self.site / sub)
        by_cat = {}
        for gid, g in self.guides.items():
            by_cat.setdefault(g["category"], []).append(gid)
        by_cat = dict(sorted(by_cat.items()))
        for name in by_cat:
            by_cat[name].sort(key=lambda i: (self.guides[i]["title"], i))
            for gid in by_cat[name]:
                self.guide_page(gid, by_cat[name])
            self.category_page(name, by_cat[name])
        self.item_pages()
        self.home_page(by_cat)
        for f in (self.root / "site_static").iterdir():
            shutil.copyfile(f, self.site / f.name)
        authors = sorted({g["author"]["username"] for g in self.guides.values()})
        self.stats["authors"] = authors
        self.stats["site_images"] = len(self.images.used)
        (self.root / "site_build_stats.json").write_text(json.dumps(self.stats, indent=1))
        print(json.dumps(self.stats, indent=1))


if __name__ == "__main__":
    Builder("/home/ubuntu/Projects/railcore-dozuki").run()
