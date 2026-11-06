"""Background scheduler for automated post generation and publishing."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.database import db
from platforms.manager import platform_manager

logger = logging.getLogger(__name__)


class Scheduler:
    """Automates social media publishing and queue processing."""

    def __init__(self) -> None:
        self.interval = settings.SCHEDULER_INTERVAL_SECONDS
        self._is_running = False

    def process_pending_queue(self) -> List[Dict[str, Any]]:
        """Find pending scheduled posts and publish them."""
        pending_jobs = db.get_pending_scheduled_jobs()
        if not pending_jobs:
            return []

        logger.info(f"Found {len(pending_jobs)} scheduled post(s) ready to publish.")
        results = []

        for job in pending_jobs:
            job_id = job["id"]
            post_id = job["post_id"]
            platforms = job["platforms"]

            db.mark_job_status(job_id, "processing", "Dispatching to platforms...")

            post_data = db.get_post(post_id)
            if not post_data:
                db.mark_job_status(job_id, "failed", f"Post ID {post_id} not found in database.")
                continue

            try:
                res = platform_manager.publish_post(
                    post_data=post_data,
                    target_platforms=platforms,
                )
                db.mark_job_status(job_id, "completed", f"Published with status: {res['overall_status']}")
                results.append({"job_id": job_id, "post_id": post_id, "result": res})
            except Exception as e:
                err_msg = f"Failed to publish job {job_id}: {e}"
                logger.error(err_msg)
                db.mark_job_status(job_id, "failed", err_msg)
                results.append({"job_id": job_id, "post_id": post_id, "error": str(e)})

        return results

    def start_loop(self, interval_seconds: Optional[int] = None) -> None:
        """Run continuous scheduler loop in the foreground."""
        sleep_time = interval_seconds or self.interval
        self._is_running = True
        logger.info(
            f"Scheduler loop started. Polling pending jobs every {sleep_time} seconds. (Press Ctrl+C to stop)"
        )
        print(
            f"[*] Background Scheduler running. Polling queue every {sleep_time}s... (Ctrl+C to stop)"
        )

        try:
            while self._is_running:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                jobs_processed = self.process_pending_queue()
                if jobs_processed:
                    print(f"[{now_str}] Successfully processed {len(jobs_processed)} scheduled post(s).")
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n[*] Scheduler stopped by user.")
            self._is_running = False

    def stop(self) -> None:
        self._is_running = False


scheduler = Scheduler()
