"""
Daily Scheduled Ingestion Job for Knowledge Brain.
Periodically queries the Brilliant Directories sitemap, detects modified/added/removed pages,
re-indexes updates, and generates an audit report.
"""

import logging
import threading
import time
from datetime import datetime
from ..crawler.polite_crawler import PoliteCrawler

logger = logging.getLogger(__name__)


class IngestionScheduler:
    def __init__(self, crawler: PoliteCrawler, interval_hours: float = 24.0):
        self.crawler = crawler
        self.interval_seconds = interval_hours * 3600
        self.is_running = False
        self._thread = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"IngestionScheduler started. Runs every {self.interval_seconds/3600} hours.")

    def stop(self):
        self.is_running = False

    def run_check_now(self) -> dict:
        """
        Manually trigger an incremental sitemap freshness sync.
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting scheduled sitemap sync at {start_time.isoformat()}...")
        status = self.crawler.run_ingestion(max_pages=50, force_all=False)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        report = {
            "timestamp": start_time.isoformat() + "Z",
            "duration_seconds": round(duration, 2),
            "summary": status
        }
        logger.info(f"Daily sync completed in {duration:.1f}s: {status['current_job']}")
        return report

    def _run_loop(self):
        while self.is_running:
            try:
                self.run_check_now()
            except Exception as e:
                logger.error(f"Error during scheduled ingestion run: {e}", exc_info=True)

            # Sleep until next interval in short steps to allow clean shutdown
            sleep_step = 60
            elapsed = 0
            while self.is_running and elapsed < self.interval_seconds:
                time.sleep(sleep_step)
                elapsed += sleep_step
