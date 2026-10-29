import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.core.config import settings
from app.services.escalation_service import escalation_service
from app.services.notification_service import dispatch_pending_outbox

logger = logging.getLogger("eduresolve.scheduler")

class SLABackgroundScheduler:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._is_executing_cycle = False
        self.telemetry: Dict[str, Any] = {
            "is_enabled": settings.SLA_SCHEDULER_ENABLED,
            "poll_interval_seconds": settings.SLA_POLL_INTERVAL_SECONDS,
            "is_running": False,
            "total_runs": 0,
            "last_run_at": None,
            "last_run_status": None,
            "last_escalated_count": 0,
            "last_warned_count": 0,
            "last_outbox_dispatched": 0,
            "last_error": None
        }

    def run_cycle_sync(self, db: Session) -> Dict[str, Any]:
        """
        Execute one SLA check and outbox dispatch cycle synchronously.
        Can be invoked both by the async background loop and by manual API requests.
        """
        if self._is_executing_cycle:
            logger.info("SLA cycle execution already in progress. Skipping overlapping run.")
            return {"status": "SKIPPED", "reason": "Execution in progress"}

        self._is_executing_cycle = True
        result = {
            "escalated_count": 0,
            "escalated_refs": [],
            "warned_count": 0,
            "warned_refs": [],
            "outbox_dispatched": 0,
            "status": "SUCCESS"
        }

        try:
            # 1. Process approaching SLA warnings
            warned = escalation_service.process_sla_warnings(db)
            result["warned_refs"] = warned
            result["warned_count"] = len(warned)

            # 2. Process overdue escalations
            escalated = escalation_service.process_overdue_escalations(db)
            result["escalated_refs"] = escalated
            result["escalated_count"] = len(escalated)

            # 3. Process pending notification outbox
            dispatched = dispatch_pending_outbox(db)
            result["outbox_dispatched"] = dispatched

            now_iso = datetime.now(timezone.utc).isoformat()
            self.telemetry["last_run_at"] = now_iso
            self.telemetry["last_run_status"] = "SUCCESS"
            self.telemetry["last_escalated_count"] = len(escalated)
            self.telemetry["last_warned_count"] = len(warned)
            self.telemetry["last_outbox_dispatched"] = dispatched
            self.telemetry["total_runs"] += 1
            self.telemetry["last_error"] = None

            if len(escalated) > 0 or len(warned) > 0 or dispatched > 0:
                logger.info(
                    f"SLA Cycle Completed: {len(escalated)} escalated, {len(warned)} warned, {dispatched} emails dispatched."
                )
        except Exception as e:
            logger.error(f"Error executing SLA cycle: {e}", exc_info=True)
            result["status"] = "ERROR"
            result["error"] = str(e)
            self.telemetry["last_run_status"] = "ERROR"
            self.telemetry["last_error"] = str(e)
        finally:
            self._is_executing_cycle = False

        return result

    async def _scheduler_loop(self):
        """Asynchronous periodic execution loop."""
        logger.info(
            f"SLA Background Scheduler started (Interval: {settings.SLA_POLL_INTERVAL_SECONDS}s)."
        )
        self.telemetry["is_running"] = True

        if self._stop_event is None:
            self._stop_event = asyncio.Event()

        while not self._stop_event.is_set():
            try:
                # Run cycle in a dedicated DB session
                with SessionLocal() as db:
                    self.run_cycle_sync(db)
            except Exception as e:
                logger.error(f"Unexpected error in SLA scheduler loop: {e}", exc_info=True)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=settings.SLA_POLL_INTERVAL_SECONDS
                )
            except asyncio.TimeoutError:
                # Timeout is normal: time for next cycle
                pass

        self.telemetry["is_running"] = False
        logger.info("SLA Background Scheduler stopped gracefully.")

    def start(self):
        """Start background scheduler task if enabled."""
        if not settings.SLA_SCHEDULER_ENABLED:
            logger.info("SLA Background Scheduler is disabled via configuration (SLA_SCHEDULER_ENABLED=False).")
            return

        if self._task and not self._task.done():
            logger.warning("SLA Background Scheduler is already running.")
            return

        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._scheduler_loop())

    def stop(self):
        """Stop background scheduler task gracefully."""
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()

sla_scheduler = SLABackgroundScheduler()
