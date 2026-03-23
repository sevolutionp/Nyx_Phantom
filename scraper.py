# scraper.py — Crawls the SWG Legends wiki using httpx + cf_clearance cookie
import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://swglegends.com/wiki/index.php"
START_URL = f"{BASE_URL}?title=Home"
OUTPUT_FILE = Path(__file__).parent / "wiki_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://swglegends.com/",
}

SKIP_PATTERNS = [
    "Special:", "Talk:", "User:", "User_talk:", "File:", "File_talk:",
    "MediaWiki:", "Help:", "Category_talk:", "action=", "oldid=",
    "diff=", "printable=", "redlink=", "limit=",
]

# Individual item/deed/schematic pages to skip — too many, low value for chat
SKIP_TITLE_SUFFIXES = [
    "_Deed", "_deed", "_Schematic", "_schematic",
    "_(Deed)", "_(deed)", "_(Schematic)", "_(schematic)",
    "_(weapon)", "_(armor)", "_(item)", "_(loot)",
]

# Only follow links from these high-value categories
ALLOWED_TITLE_KEYWORDS = [
    "Profession", "profession", "Class", "Skill", "skill",
    "Planet", "planet", "Location", "location", "City", "city",
    "Instance", "instance", "Quest", "quest", "Mission", "mission",
    "Crafting", "crafting", "Resource", "resource",
    "Space", "space", "PvP", "pvp", "Combat", "combat",
    "Jedi", "jedi", "Sith", "sith", "Force", "force",
    "Guild", "guild", "Faction", "faction",
    "Category:Gameplay", "Category:Professions", "Category:Planets",
    "Category:Instances", "Category:SWG_Legends", "Category:Guides",
    "Guide", "guide", "Tutorial", "tutorial",
    "Medic", "Officer", "Smuggler", "Bounty", "Commando", "Entertainer",
    "Spy", "Trader", "Beast", "Pilot", "Officer",
    "Home",  # always include the homepage
]

def is_wiki_page(url: str) -> bool:
    if "index.php" not in url:
        return False
    if any(p in url for p in SKIP_PATTERNS):
        return False
    if not "title=" in url:
        return False
    title = get_title(url)
    if any(title.endswith(s) for s in SKIP_TITLE_SUFFIXES):
        return False
    return True

def is_high_value(url: str) -> bool:
    """Only queue links that are likely to contain useful gameplay info."""
    title = get_title(url)
    return any(kw in title for kw in ALLOWED_TITLE_KEYWORDS)

def get_title(url: str) -> str:
    parsed = parse_qs(urlparse(url).query)
    return parsed.get("title", [""])[0]

def parse_page(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    content_div = soup.find(id="mw-content-text")
    if not content_div:
        return None

    for tag in content_div.find_all(["table", "div"], class_=re.compile(r"navbox|toc|mw-editsection|infobox")):
        tag.decompose()

    text = content_div.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) < 100:
        return None

    title = get_title(url)
    return {"title": title.replace("_", " "), "url": url, "text": text}

def extract_links(html: str, visited: set) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin("https://swglegends.com", href)
        if is_wiki_page(full) and full not in visited:
            links.add(full)
    return list(links)

async def main():
    cf_clearance = os.getenv("CF_CLEARANCE")
    if not cf_clearance:
        print("ERROR: CF_CLEARANCE not set in .env")
        return

    cookies = {"cf_clearance": cf_clearance}
    pages = []
    visited = set()
    queue = [START_URL]

    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, follow_redirects=True, timeout=30) as client:
        while queue:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            title = get_title(url)
            print(f"[{len(pages)+1}] Scraping: {title}")

            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    print(f"  [skip] HTTP {resp.status_code}")
                    continue
            except Exception as e:
                print(f"  [skip] {e}")
                continue

            result = parse_page(resp.text, url)
            if result:
                pages.append(result)
                new_links = [l for l in extract_links(resp.text, visited) if is_high_value(l)]
                queue.extend(new_links)
                print(f"  -> {len(new_links)} new links | queue: {len(queue)}")
            else:
                print(f"  [skip] no content found")

            await asyncio.sleep(0.5)  # polite delay

    OUTPUT_FILE.write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone! Scraped {len(pages)} pages -> {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
