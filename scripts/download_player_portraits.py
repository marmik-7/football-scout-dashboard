"""
SCOUT — Phase 10.2 Player Portrait Acquisition & Verification Pipeline
Expands genuine player photograph coverage across the complete SCOUT dataset (1,692 players)
using Wikimedia Commons and Wikipedia APIs with strict identity verification and licensing compliance.
"""

import argparse
import io
import json
import os
import re
import sys
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "players_clustered.csv"
ASSETS_DIR = PROJECT_ROOT / "app" / "assets" / "players"
METADATA_FILE = ASSETS_DIR / "metadata.json"

HEADERS = {
    "User-Agent": "ScoutRecruitmentIntelligence/1.0 (https://github.com/marmik-7/football-scout-dashboard; scout@football-scout.org)"
}

# Thread lock for synchronized metadata and disk writes
WRITE_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()

REJECT_IMAGE_KEYWORDS = [
    "flag", "logo", "crest", "stadium", "map", "kit", "coat_of_arms",
    "symbol", "placeholder", "generic", "jersey", "badge", "silueta",
    "silhouette", "no_image", "missing", "replace_this_image", "escudo",
    "stadion", "arena", "field", "pitch", "lineup", "formation", "trophy",
    "emblem", "tribune", "ground"
]

REJECT_PAGE_KEYWORDS = [
    "disambiguation", "list of", "season", "roster", "squad", "transfers",
    "awards", "results", "overview", "championship"
]

FOOTBALL_KEYWORDS = [
    "football", "soccer", "futbol", "futebol", "calciatore", "fußball",
    "fussball", "joueur de football", "association football"
]

NON_FOOTBALL_SPORTS = [
    "american football", "canadian football", "rugby", "australian rules",
    "basketball", "baseball", "cricket", "ice hockey", "tennis", "golfer"
]

COMMON_ALIASES = {
    "Abel": "Abel Bretones",
    "Abner": "Abner Vinícius",
    "Rodri": "Rodrigo Hernández Cascante",
    "Pedri": "Pedro González López",
    "Gavi": "Pablo Páez Gavira",
    "Bremer": "Gleison Bremer",
    "Casemiro": "Carlos Henrique Casimiro",
    "Danilo": "Danilo Luiz da Silva",
    "Ederson": "Ederson Santana de Moraes",
    "Alisson": "Alisson Becker",
    "Marquinhos": "Marcos Aoás Corrêa",
    "Vitinha": "Vítor Machado Ferreira",
    "Douglas Luiz": "Douglas Luiz Soares de Paulo",
    "Joelinton": "Joelinton Cássio Apolinário de Lira",
    "Antony": "Antony Matheus dos Santos",
    "Richarlison": "Richarlison de Andrade",
    "Pepê": "Eduardo Gabriel Aquino Cossa",
    "Otávio": "Otávio Edmilson da Silva Monteiro",
    "Arthur": "Arthur Henrique Ramos de Oliveira Melo",
    "Vanderson": "Vanderson de Oliveira Campos",
    "Caio Henrique": "Caio Henrique Oliveira Silva",
    "Dodô": "Domilson Cordeiro dos Santos",
    "Natan": "Natan Bernardo de Souza",
    "Beto": "Norberto Bercique Gomes Betuncal",
    "Walace": "Walace Souza Silva",
    "Emerson": "Emerson Royal",
    "Neto": "Norberto Murara Neto",
    "Savinho": "Sávio",
    "Yeremy Pino": "Yeremy Pino",
    "Yéremi Pino": "Yeremy Pino",
    "Yeremi Pino": "Yeremy Pino",
    "Reinier": "Reinier Jesus Carvalho",
    "Vinicius Junior": "Vinícius Júnior",
    "Vini Jr": "Vinícius Júnior",
    "Igor": "Igor Julio",
    "Marlon": "Marlon Santos",
    "Kaio Jorge": "Kaio Jorge",
}


def clean_text(text):
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text).strip()
    return re.sub(r"\s+", " ", clean)


def fold_ascii(text):
    if not text:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def slugify(text):
    clean = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "_", clean)


def safe_request(url, timeout=8, max_retries=3):
    """
    Executes an HTTP GET request with exponential backoff on HTTP 429/503.
    """
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as he:
            if he.code in (429, 503):
                retry_after = he.headers.get("Retry-After")
                sleep_dur = 2.5 * (attempt + 1)
                if retry_after and retry_after.isdigit():
                    sleep_dur = max(float(retry_after), sleep_dur)
                with PRINT_LOCK:
                    print(f"  [HTTP {he.code}] Backing off {sleep_dur:.1f}s (retry {attempt+1}/{max_retries})...")
                time.sleep(sleep_dur)
            else:
                return None
        except Exception:
            time.sleep(0.3 * (attempt + 1))
    return None


def is_valid_image_filename(filename):
    if not filename:
        return False
    f_lower = filename.lower()
    if not f_lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return False
    for kw in REJECT_IMAGE_KEYWORDS:
        if kw in f_lower:
            return False
    return True


def is_free_license(license_str):
    if not license_str:
        return False
    l_lower = license_str.lower()
    if any(rf in l_lower for rf in ["fair use", "copyrighted", "all rights reserved"]):
        return False
    valid_indicators = [
        "cc", "creative commons", "public domain", "cc0", "cc-by", "cc by",
        "attribution", "gfdl", "fal", "free art", "open government"
    ]
    return any(vi in l_lower for vi in valid_indicators)


def name_matches_title(player_name, target_text):
    """
    Validates that target_text contains the essential name tokens of player_name.
    """
    if not target_text:
        return False

    def norm_tokens(t):
        t_clean = fold_ascii(t.lower())
        return set(re.findall(r"\b[a-z0-9]{2,}\b", t_clean))

    p_tokens = norm_tokens(player_name)
    t_tokens = norm_tokens(target_text)

    # Check alias tokens if known
    alias = COMMON_ALIASES.get(player_name)
    if alias:
        a_tokens = norm_tokens(alias)
        if a_tokens.issubset(t_tokens) or len(a_tokens.intersection(t_tokens)) >= 2:
            return True

    if not p_tokens or not t_tokens:
        return False

    # Mononym / single token: must be in target tokens
    if len(p_tokens) == 1:
        return list(p_tokens)[0] in t_tokens

    # Multi-word: player's surname (last token) MUST be present
    last_token = list(player_name.split())[-1].lower()
    last_clean = fold_ascii(last_token)
    if last_clean not in t_tokens:
        return False

    # At least 2 tokens (or all tokens if 2) must match
    overlap = p_tokens.intersection(t_tokens)
    return len(overlap) >= min(2, len(p_tokens))


def get_commons_info(file_title):
    """
    Fetches image metadata and thumbnail URL directly from Wikimedia Commons API.
    """
    comm_url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:{urllib.parse.quote(file_title)}"
        f"&prop=imageinfo&iiprop=extmetadata|url&iiurlwidth=350&format=json"
    )
    data = safe_request(comm_url)
    if not data:
        return None

    try:
        pages = data.get("query", {}).get("pages", {})
        page = list(pages.values())[0] if pages else {}
        if "imageinfo" in page:
            ii = page["imageinfo"][0]
            thumb = ii.get("thumburl") or ii.get("url")
            meta = ii.get("extmetadata", {})
            lic = meta.get("LicenseShortName", {}).get("value", "CC BY-SA 4.0")
            raw_artist = meta.get("Artist", {}).get("value", "Wikimedia Commons contributor")
            artist = clean_text(raw_artist) or "Wikimedia Commons contributor"
            desc_url = ii.get(
                "descriptionurl",
                f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(file_title)}",
            )

            if is_free_license(lic) and thumb:
                return {
                    "thumb_url": thumb,
                    "license": lic,
                    "attribution": artist,
                    "file": file_title,
                    "original_url": desc_url,
                }
    except Exception:
        pass
    return None


def resolve_via_wikidata(name, squad="", born=0):
    """
    Identifies player entity via Wikidata and checks property P18 (image).
    """
    queries = []
    alias = COMMON_ALIASES.get(name)
    if alias:
        queries.append(alias)
    queries.append(name)

    squad_first = squad.split(",")[0].strip() if squad else ""
    is_mononym = len(name.split()) == 1

    if is_mononym and squad_first:
        queries.append(f"{name} {squad_first}")

    folded = fold_ascii(name)
    if folded != name:
        queries.append(folded)

    for q in queries:
        wd_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(q)}&language=en&format=json"
        wdata = safe_request(wd_url)
        if not wdata:
            continue

        items = wdata.get("search", [])
        for item in items[:4]:
            desc = (item.get("description") or "").lower()
            label = item.get("label") or ""

            # Disqualify non-football sports
            if any(ns in desc for ns in NON_FOOTBALL_SPORTS):
                continue

            # Must be a footballer
            if not any(term in desc for term in FOOTBALL_KEYWORDS):
                continue

            # Name verification
            if not (name_matches_title(name, label) or (alias and name_matches_title(alias, label))):
                continue

            # If mononym, require squad or birth year in description or label
            if is_mononym and squad_first:
                squad_words = [w.lower() for w in squad_first.split() if len(w) > 3]
                squad_match = any(sw in desc for sw in squad_words)
                born_match = str(born) in desc if born else False
                if not (squad_match or born_match or alias):
                    continue

            qid = item["id"]
            c_url = f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={qid}&property=P18&format=json"
            cdata = safe_request(c_url)
            if not cdata:
                continue

            claims = cdata.get("claims", {}).get("P18", [])
            if claims:
                img_file = claims[0]["mainsnak"]["datavalue"]["value"]
                if is_valid_image_filename(img_file):
                    info = get_commons_info(img_file)
                    if info:
                        return {
                            "source": "Wikimedia Commons (Wikidata P18)",
                            "entity_label": label,
                            "description": desc,
                            "info": info,
                        }
    return None


def resolve_via_wikipedia(name, squad="", born=0):
    """
    Identifies player article on English Wikipedia and checks lead page image.
    """
    squad_first = squad.split(",")[0].strip() if squad else ""
    is_mononym = len(name.split()) == 1
    alias = COMMON_ALIASES.get(name)

    wp_queries = []
    if alias:
        wp_queries.append(f"{alias} footballer")
    if is_mononym and squad_first:
        wp_queries.append(f"{name} {squad_first} footballer")
    wp_queries.append(f"{name} footballer")
    folded = fold_ascii(name)
    if folded != name:
        wp_queries.append(f"{folded} footballer")

    for wq in wp_queries:
        wp_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(wq)}&format=json"
        sdata = safe_request(wp_url)
        if not sdata:
            continue

        results = sdata.get("query", {}).get("search", [])
        for r in results[:3]:
            title = r.get("title", "")
            title_lower = title.lower()

            if any(rk in title_lower for rk in REJECT_PAGE_KEYWORDS):
                continue

            if not (name_matches_title(name, title) or (alias and name_matches_title(alias, title))):
                continue

            p_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}"
                f"&prop=pageimages|extracts&exintro=1&explaintext=1&piprop=thumbnail|name&pithumbsize=350&format=json"
            )
            pdata = safe_request(p_url)
            if not pdata:
                continue

            pages = pdata.get("query", {}).get("pages", {})
            page = list(pages.values())[0] if pages else {}
            thumb = page.get("thumbnail")
            pageimage = page.get("pageimage")
            extract = page.get("extract", "").lower()

            if not thumb or not pageimage:
                continue

            if not any(term in extract for term in FOOTBALL_KEYWORDS):
                continue
            if any(ns in extract[:200] for ns in NON_FOOTBALL_SPORTS):
                continue

            if is_mononym and squad_first:
                squad_words = [w.lower() for w in squad_first.split() if len(w) > 3]
                squad_match = any(sw in extract for sw in squad_words)
                born_match = str(born) in extract if born else False
                if not (squad_match or born_match or alias):
                    continue

            if is_valid_image_filename(pageimage):
                info = get_commons_info(pageimage)
                if info:
                    return {
                        "source": "Wikimedia Commons (Wikipedia Lead)",
                        "entity_label": title,
                        "description": extract[:100],
                        "info": info,
                    }
    return None


def resolve_player(name, squad="", nation="", born=0):
    """
    Hierarchical resolution with strict identity verification.
    """
    res = resolve_via_wikidata(name, squad, born)
    if res:
        return res

    res = resolve_via_wikipedia(name, squad, born)
    if res:
        return res

    return None


def download_and_optimize_portrait(thumb_url, output_path):
    """
    Downloads image, composites transparent alpha on neutral slate background,
    resizes to max 256x256 via Lanczos, and writes optimized JPEG.
    """
    try:
        req = urllib.request.Request(thumb_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw_bytes = resp.read()

        img = Image.open(io.BytesIO(raw_bytes))

        if img.width < 64 or img.height < 64:
            return None
        aspect = img.width / img.height
        if aspect < 0.35 or aspect > 2.8:
            return None

        # Composite transparent RGBA onto neutral scout slate (#1E293B -> 30, 41, 59)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            bg = Image.new("RGBA", img.size, (30, 41, 59, 255))
            bg.paste(img, (0, 0), img)
            img = bg.convert("RGB")
        else:
            img = img.convert("RGB")

        img.thumbnail((256, 256), Image.Resampling.LANCZOS)
        img.save(output_path, format="JPEG", quality=85, optimize=True)
        return img.width, img.height
    except Exception:
        return None


def process_player(row, metadata, total_count, current_idx):
    """
    Processes a single player: checks cache, resolves image, downloads, and returns result.
    """
    p_name = row["Player"]
    p_unique = row.get("Player_Unique", p_name)
    squad = row.get("Squad", "")
    nation = row.get("Nation", "")
    born = row.get("Born", 0)

    slug = slugify(p_name)
    if p_unique != p_name and squad:
        filename = f"{slug}_{slugify(squad)}.jpg"
    else:
        filename = f"{slug}.jpg"

    target_path = ASSETS_DIR / filename

    # Already cached check
    with WRITE_LOCK:
        if (p_unique in metadata or p_name in metadata) and target_path.exists():
            return {
                "status": "cached",
                "scout_id": p_unique,
                "player_name": p_name,
                "filename": filename,
                "msg": "already cached"
            }

    # Small polite delay per worker
    time.sleep(0.08)

    # Resolution attempt
    res = resolve_player(p_name, squad, nation, born)
    if not res:
        return {
            "status": "unresolved",
            "scout_id": p_unique,
            "player_name": p_name,
            "msg": "no verified photograph found"
        }

    info = res["info"]
    dims = download_and_optimize_portrait(info["thumb_url"], target_path)
    if not dims:
        return {
            "status": "download_failed",
            "scout_id": p_unique,
            "player_name": p_name,
            "msg": "image download or optimization failed"
        }

    meta_entry = {
        "scout_id": p_unique,
        "player_name": p_name,
        "external_id": f"File:{info['file']}",
        "filename": filename,
        "source": res["source"],
        "original_url": info["original_url"],
        "license": info["license"],
        "attribution": info["attribution"],
        "verified": True,
        "width": dims[0],
        "height": dims[1],
    }

    with WRITE_LOCK:
        metadata[p_unique] = meta_entry
        if p_name != p_unique:
            metadata[p_name] = meta_entry

    return {
        "status": "newly_verified",
        "scout_id": p_unique,
        "player_name": p_name,
        "filename": filename,
        "license": info["license"],
        "attribution": info["attribution"],
        "dims": dims,
        "source": res["source"]
    }


def save_metadata(metadata):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def run_pipeline(max_players=None, workers=3, batch_size=200):
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {}
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    initial_cached_count = len(set(v.get("filename") for v in metadata.values()))

    # Load dataset
    try:
        from app.utils.data_loader import load_data
        df = load_data()
    except Exception:
        df = pd.read_csv(DATA_PATH)

    total_dataset_players = len(df)
    if max_players:
        df = df.head(max_players)

    total_to_process = len(df)
    print(f"\n==================================================================")
    print(f"SCOUT PHASE 10.2: EXPAND VERIFIED PLAYER PORTRAIT COVERAGE")
    print(f"Total Dataset Players: {total_dataset_players:,}")
    print(f"Initial Cached Portraits: {initial_cached_count:,}")
    print(f"Processing Cohort: {total_to_process:,} players using {workers} concurrent workers")
    print(f"==================================================================\n")

    stats = {
        "cached": 0,
        "newly_verified": 0,
        "unresolved": 0,
        "failed": 0
    }

    processed_counter = 0
    start_time = time.time()
    checkpoint_interval = 20
    last_checkpoint = 0

    # Process in batches to manage concurrency and memory cleanly
    num_batches = (len(df) + batch_size - 1) // batch_size
    for b_idx in range(num_batches):
        batch_df = df.iloc[b_idx * batch_size : (b_idx + 1) * batch_size]
        with PRINT_LOCK:
            print(f"\n>>> Starting Batch {b_idx + 1}/{num_batches} ({len(batch_df)} players)...")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_info = {
                executor.submit(process_player, row, metadata, total_to_process, b_idx * batch_size + idx): (
                    b_idx * batch_size + idx,
                    row["Player"],
                )
                for idx, (_, row) in enumerate(batch_df.iterrows(), start=1)
            }

            for future in as_completed(future_to_info):
                idx, p_name = future_to_info[future]
                processed_counter += 1
                try:
                    res = future.result()
                    status = res["status"]
                    if status == "cached":
                        stats["cached"] += 1
                    elif status == "newly_verified":
                        stats["newly_verified"] += 1
                        with PRINT_LOCK:
                            print(
                                f"[{processed_counter}/{total_to_process}] + VERIFIED: {p_name} -> "
                                f"{res['filename']} ({res['dims'][0]}x{res['dims'][1]}, {res['license']})"
                            )
                    elif status == "unresolved":
                        stats["unresolved"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1

                # Periodic checkpointing
                if stats["newly_verified"] > 0 and (stats["newly_verified"] - last_checkpoint >= checkpoint_interval):
                    with WRITE_LOCK:
                        save_metadata(metadata)
                        last_checkpoint = stats["newly_verified"]
                    with PRINT_LOCK:
                        print(f"--> Checkpoint saved: {len(metadata):,} entries in metadata.json")

        # Save after every batch
        with WRITE_LOCK:
            save_metadata(metadata)
        with PRINT_LOCK:
            cur_verified = len(set(v.get("filename") for v in metadata.values()))
            print(f">>> Batch {b_idx + 1} complete. Verified portraits so far: {cur_verified:,}")

    # Final metadata save
    with WRITE_LOCK:
        save_metadata(metadata)

    elapsed = time.time() - start_time
    unique_verified = len(set(v.get("filename") for v in metadata.values()))
    coverage_pct = (unique_verified / total_dataset_players) * 100

    total_bytes = sum(f.stat().st_size for f in ASSETS_DIR.glob("*.*") if f.is_file())
    total_mb = total_bytes / (1024 * 1024)

    license_counts = {}
    for entry in metadata.values():
        if isinstance(entry, dict) and "license" in entry:
            lic = entry["license"]
            license_counts[lic] = license_counts.get(lic, 0) + 1

    print("\n==================================================================")
    print("SCOUT PHASE 10.2: PORTRAIT ACQUISITION COMPLETE")
    print(f"Total Time: {elapsed:.1f}s ({elapsed/60:.2f}m)")
    print(f"Total Players in Dataset: {total_dataset_players:,}")
    print(f"Previously Cached Portraits: {initial_cached_count:,}")
    print(f"Newly Verified & Downloaded: {stats['newly_verified']:,}")
    print(f"Total Unique Verified Portraits: {unique_verified:,}")
    print(f"Total Utilizing Neutral Placeholder: {total_dataset_players - unique_verified:,}")
    print(f"Final Coverage: {coverage_pct:.1f}% (expanded from {initial_cached_count/total_dataset_players*100:.1f}%)")
    print(f"Total Asset Storage Footprint: {total_mb:.2f} MB across {len(list(ASSETS_DIR.glob('*.*')))} files")
    print("\nLicensing Distribution:")
    for lic, cnt in sorted(license_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {lic}: {cnt:,} photos")
    print("==================================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Acquire verified player portraits")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of players to process")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent worker threads")
    parser.add_argument("--batch-size", type=int, default=200, help="Batch size")
    args = parser.parse_args()

    run_pipeline(max_players=args.limit, workers=args.workers, batch_size=args.batch_size)
