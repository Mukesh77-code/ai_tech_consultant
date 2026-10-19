"""
Polite, Resumable Crawler for Brilliant Directories Solution Center.
Features rate-limiting, retries with exponential backoff, checkpointing, idempotency, and failure isolation.
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional
import aiohttp
import requests

from .sitemap_parser import SitemapParser
from .article_parser import ArticleParser
from .multimodal_processor import MultimodalProcessor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class PoliteCrawler:
    def __init__(
        self,
        storage_dir: str = "task1_knowledge_brain/storage",
        delay_seconds: float = 0.5,
        max_retries: int = 3,
        user_agent: str = "AITechConsultantBot/1.0 (Educational Project; Polite Ingestion)"
    ):
        self.storage_dir = storage_dir
        self.articles_dir = os.path.join(storage_dir, "articles")
        os.makedirs(self.articles_dir, exist_ok=True)

        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.headers = {"User-Agent": user_agent}

        manifest_path = os.path.join(storage_dir, "manifest.json")
        self.sitemap_parser = SitemapParser(manifest_path=manifest_path)
        self.article_parser = ArticleParser()
        self.multimodal_processor = MultimodalProcessor(
            cache_path=os.path.join(storage_dir, "image_cache.json")
        )

        self.is_running = False
        self.current_progress = {
            "total": 0,
            "processed": 0,
            "added": 0,
            "updated": 0,
            "unchanged": 0,
            "failed": 0,
            "status": "idle"
        }

    def _get_article_filename(self, url: str) -> str:
        # Generate safe filename from url
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", url.replace("https://", "").replace("http://", ""))
        return os.path.join(self.articles_dir, f"{clean_name[:80]}.json")

    def fetch_page_with_retries(self, url: str) -> Optional[str]:
        """
        Synchronous/blocking HTTP request with exponential backoff retries.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, headers=self.headers, timeout=15)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code in [404, 410]:
                    logger.warning(f"Permanent HTTP error {resp.status_code} for {url}. No retry.")
                    return None
                else:
                    logger.warning(f"HTTP {resp.status_code} for {url} (attempt {attempt}/{self.max_retries})")
            except Exception as e:
                logger.warning(f"Network error on {url} (attempt {attempt}/{self.max_retries}): {e}")

            if attempt < self.max_retries:
                time.sleep(self.delay_seconds * (2 ** (attempt - 1)))

        return None

    def process_single_article(self, url_item: dict) -> dict:
        """
        Process a single article URL:
        1. Fetch HTML
        2. Parse structured content
        3. Check idempotency (content_hash)
        4. Multimodal screenshot extraction
        5. Save checkpoint
        """
        url = url_item["url"]
        lastmod = url_item.get("lastmod")

        html = self.fetch_page_with_retries(url)
        if not html:
            self.sitemap_parser.update_page_status(
                url=url,
                status="failed",
                error="Failed to download page after max retries"
            )
            return {"url": url, "status": "failed", "error": "Fetch failed"}

        parsed = self.article_parser.parse(html, url)
        existing_meta = self.sitemap_parser.manifest.get(url)

        # Idempotency check: if content hash is identical and previously indexed, skip reprocessing
        if existing_meta and existing_meta.get("content_hash") == parsed["content_hash"] and existing_meta.get("status") == "indexed":
            logger.info(f"Page unchanged: {url}")
            return {"url": url, "status": "unchanged", "title": parsed["title"]}

        # Process screenshots with multimodal processor
        enriched_images = []
        for img in parsed["images"]:
            try:
                img_data = self.multimodal_processor.process_image(img, parsed["title"])
                enriched_images.append(img_data)
            except Exception as e:
                logger.warning(f"Error processing image {img.get('url')}: {e}")

        parsed["enriched_images"] = enriched_images

        # Save article to disk
        filepath = self._get_article_filename(url)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)

        is_update = existing_meta is not None
        status = "updated" if is_update else "added"

        # Checkpoint manifest
        self.sitemap_parser.update_page_status(
            url=url,
            status="indexed",
            content_hash=parsed["content_hash"],
            lastmod=lastmod,
            title=parsed["title"],
            image_count=len(enriched_images)
        )

        logger.info(f"Successfully processed ({status}): {parsed['title']} [{url}]")
        return {
            "url": url,
            "status": status,
            "title": parsed["title"],
            "filepath": filepath,
            "chunks_needed": True
        }

    def run_ingestion(self, max_pages: int = 20, force_all: bool = False) -> dict:
        """
        Run crawler ingestion job politely with rate limits and isolation.
        """
        self.is_running = True
        self.current_progress["status"] = "crawling"
        self.current_progress["added"] = 0
        self.current_progress["updated"] = 0
        self.current_progress["unchanged"] = 0
        self.current_progress["failed"] = 0

        try:
            logger.info("Fetching sitemap...")
            sitemap_urls = self.sitemap_parser.fetch_sitemap_urls()

            new_pages, changed_pages, unchanged_pages, removed_urls = self.sitemap_parser.compare_with_manifest(sitemap_urls)

            # Deactivate removed pages
            for r_url in removed_urls:
                self.sitemap_parser.update_page_status(url=r_url, status="deactivated")
                logger.info(f"Deactivated removed page: {r_url}")

            # Prioritize changed and new pages
            to_crawl = (changed_pages + new_pages) if not force_all else sitemap_urls
            if not to_crawl and unchanged_pages:
                logger.info("All pages up to date! Selecting subset to verify.")
                to_crawl = unchanged_pages[:max_pages]

            to_crawl = to_crawl[:max_pages]
            self.current_progress["total"] = len(to_crawl)

            logger.info(f"Starting ingestion for {len(to_crawl)} pages with {self.delay_seconds}s delay...")

            for i, page_item in enumerate(to_crawl, start=1):
                try:
                    res = self.process_single_article(page_item)
                    status = res.get("status")
                    if status == "added":
                        self.current_progress["added"] += 1
                    elif status == "updated":
                        self.current_progress["updated"] += 1
                    elif status == "unchanged":
                        self.current_progress["unchanged"] += 1
                    else:
                        self.current_progress["failed"] += 1
                except Exception as e:
                    logger.error(f"Failed to process {page_item['url']}: {e}", exc_info=True)
                    self.current_progress["failed"] += 1

                self.current_progress["processed"] = i
                # Polite delay
                time.sleep(self.delay_seconds)

            self.current_progress["status"] = "completed"
        except Exception as e:
            logger.error(f"Ingestion run failed: {e}", exc_info=True)
            self.current_progress["status"] = "error"
            self.current_progress["error"] = str(e)
        finally:
            self.is_running = False

        return self.get_status()

    def get_status(self) -> dict:
        total_manifest = len(self.sitemap_parser.manifest)
        indexed_count = sum(1 for v in self.sitemap_parser.manifest.values() if v.get("status") == "indexed")
        failed_count = sum(1 for v in self.sitemap_parser.manifest.values() if v.get("status") == "failed")
        deactivated_count = sum(1 for v in self.sitemap_parser.manifest.values() if v.get("status") == "deactivated")

        return {
            "crawler_running": self.is_running,
            "current_job": self.current_progress,
            "manifest_summary": {
                "total_tracked": total_manifest,
                "indexed": indexed_count,
                "failed": failed_count,
                "deactivated": deactivated_count
            }
        }
