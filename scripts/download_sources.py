"""Download every document listed in data/sources.csv into data/raw/.

Files are saved exactly as the server sends them. Nothing is cleaned here.
A manifest with the size and checksum of every file is written to
data/raw/manifest.csv so anyone can check they have the same copies we used.

Run from the project root:
    python scripts/download_sources.py
"""

import csv
import hashlib
import time
from datetime import date
from pathlib import Path

import requests

SOURCES_FILE = Path("data/sources.csv")
RAW_FOLDER = Path("data/raw")
MANIFEST_FILE = RAW_FOLDER / "manifest.csv"

USER_AGENT = "Mozilla/5.0 (compatible; ask-my-pension student research project)"
SECONDS_BETWEEN_DOWNLOADS = 2
TIMEOUT_SECONDS = 90


def read_sources():
    with open(SOURCES_FILE, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def download(url):
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.content


def looks_like_the_right_type(content, file_type):
    if file_type == "pdf":
        return content.startswith(b"%PDF")
    if file_type == "html":
        start = content[:2000].lower()
        return b"<html" in start or b"<!doctype html" in start
    return False


def sha256_of(content):
    return hashlib.sha256(content).hexdigest()


def save_manifest(rows):
    columns = [
        "source_id",
        "file_name",
        "url",
        "style",
        "file_type",
        "in_core",
        "bytes",
        "sha256",
        "downloaded_on",
        "status",
    ]
    with open(MANIFEST_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    RAW_FOLDER.mkdir(parents=True, exist_ok=True)
    sources = read_sources()
    manifest_rows = []

    for source in sources:
        source_id = source["source_id"]
        file_type = source["file_type"]
        file_name = f"{source_id}.{file_type}"
        file_path = RAW_FOLDER / file_name

        if file_path.exists():
            print(f"already have {file_name}, skipping download")
            content = file_path.read_bytes()
            status = "ok"
        else:
            print(f"downloading {file_name}")
            try:
                content = download(source["url"])
            except requests.RequestException as error:
                print(f"  failed: {error}")
                content = b""

            if not content:
                status = "download_failed"
            elif not looks_like_the_right_type(content, file_type):
                status = "unexpected_content"
            else:
                file_path.write_bytes(content)
                status = "ok"

            time.sleep(SECONDS_BETWEEN_DOWNLOADS)

        if status == "ok":
            saved_at = file_path.stat().st_mtime
            downloaded_on = date.fromtimestamp(saved_at).isoformat()
            size = len(content)
            checksum = sha256_of(content)
        else:
            downloaded_on = date.today().isoformat()
            size = 0
            checksum = ""

        manifest_rows.append(
            {
                "source_id": source_id,
                "file_name": file_name,
                "url": source["url"],
                "style": source["style"],
                "file_type": file_type,
                "in_core": source["in_core"],
                "bytes": size,
                "sha256": checksum,
                "downloaded_on": downloaded_on,
                "status": status,
            }
        )

    save_manifest(manifest_rows)

    ok_count = sum(1 for row in manifest_rows if row["status"] == "ok")
    print(f"\n{ok_count} of {len(manifest_rows)} sources saved to {RAW_FOLDER}")
    print(f"manifest written to {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
