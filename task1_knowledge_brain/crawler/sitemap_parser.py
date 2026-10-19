"""
Sitemap Parser for Brilliant Directories Knowledge Brain.
Parses sitemap XML, extracts URLs, timestamps, and maintains an ingestion manifest.
"""

import json
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

DEFAULT_SITEMAP_URL = "https://support.brilliantdirectories.com/support/sitemap.xml"


class SitemapParser:
    def __init__(self, manifest_path: str = "task1_knowledge_brain/storage/manifest.json"):
        self.manifest_path = manifest_path
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, dict]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load manifest from {self.manifest_path}: {e}")
        return {}

    def save_manifest(self) -> None:
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)

    def fetch_sitemap_urls(self, sitemap_url: str = DEFAULT_SITEMAP_URL) -> List[dict]:
        """
        Download and parse sitemap XML.
        Returns a list of dicts: [{'url': ..., 'lastmod': ...}]
        """
        headers = {
            "User-Agent": "AITechConsultantBot/1.0 (Polite Knowledge Ingestion Crawler; educational project)"
        }
        resp = requests.get(sitemap_url, headers=headers, timeout=20)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        # XML namespace support
        namespaces = {
            "ns": "http://www.sitemaps.org/schemas/sitemap/0.9"
        }

        urls = []
        # Check if sitemapindex or urlset
        if root.tag.endswith("sitemapindex"):
            logger.info("Found sitemap index, parsing child sitemaps...")
            for sitemap_elem in root.findall("ns:sitemap", namespaces):
                loc_elem = sitemap_elem.find("ns:loc", namespaces)
                if loc_elem is not None and loc_elem.text:
                    child_urls = self.fetch_sitemap_urls(loc_elem.text.strip())
                    urls.extend(child_urls)
        else:
            for url_elem in root.findall("ns:url", namespaces):
                loc = url_elem.find("ns:loc", namespaces)
                lastmod = url_elem.find("ns:lastmod", namespaces)
                if loc is not None and loc.text:
                    url_str = loc.text.strip()
                    # Filter for solution/article pages
                    if "support.brilliantdirectories.com/support/solutions/articles" in url_str:
                        urls.append({
                            "url": url_str,
                            "lastmod": lastmod.text.strip() if (lastmod is not None and lastmod.text) else None
                        })

        # Deduplicate by URL
        seen = set()
        deduped = []
        for item in urls:
            if item["url"] not in seen:
                seen.add(item["url"])
                deduped.append(item)

        logger.info(f"Extracted {len(deduped)} article URLs from sitemap")
        return deduped

    def compare_with_manifest(self, current_urls: List[dict]) -> Tuple[List[dict], List[dict], List[dict], List[str]]:
        """
        Compare current sitemap entries with the saved manifest.
        Returns:
            new_pages: list of dicts
            changed_pages: list of dicts
            unchanged_pages: list of dicts
            removed_urls: list of url strings
        """
        current_map = {item["url"]: item for item in current_urls}
        new_pages = []
        changed_pages = []
        unchanged_pages = []
        removed_urls = []

        for url, item in current_map.items():
            if url not in self.manifest:
                new_pages.append(item)
            else:
                stored = self.manifest[url]
                # Compare lastmod if present, otherwise rely on content hash later
                if item.get("lastmod") and stored.get("lastmod") and item["lastmod"] != stored["lastmod"]:
                    changed_pages.append(item)
                elif stored.get("status") == "failed":
                    changed_pages.append(item)  # retry failed
                else:
                    unchanged_pages.append(item)

        for stored_url, stored_data in self.manifest.items():
            if stored_url not in current_map and stored_data.get("status") != "deactivated" and not stored_data.get("is_seed", False):
                removed_urls.append(stored_url)

        return new_pages, changed_pages, unchanged_pages, removed_urls

    def update_page_status(
        self,
        url: str,
        status: str,
        content_hash: Optional[str] = None,
        lastmod: Optional[str] = None,
        title: Optional[str] = None,
        error: Optional[str] = None,
        image_count: int = 0
    ) -> None:
        """
        Record a page's status in the manifest.
        """
        self.manifest[url] = {
            "url": url,
            "status": status,  # "indexed", "failed", "deactivated"
            "content_hash": content_hash or self.manifest.get(url, {}).get("content_hash"),
            "lastmod": lastmod or self.manifest.get(url, {}).get("lastmod"),
            "title": title or self.manifest.get(url, {}).get("title"),
            "image_count": image_count,
            "error": error,
            "last_processed": datetime.utcnow().isoformat() + "Z",
            "attempts": self.manifest.get(url, {}).get("attempts", 0) + 1
        }
        self.save_manifest()
