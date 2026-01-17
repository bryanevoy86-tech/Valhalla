def _next_backoff(attempts: int) -> int:
    delay = BACKOFF_BASE_SECONDS * (2 ** max(0, attempts - 1))
    return min(delay, BACKOFF_CAP_SECONDS)
    import asyncio
    import logging
    import os
    import asyncpg
    from typing import Any, Dict, Optional

logger = logging.getLogger("valhalla")

def _next_backoff(attempts: int) -> int:
    delay = 30 * (2 ** max(0, attempts - 1))
    return min(delay, 3600)

async def _do_export(job: dict) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
    try:
        fake_path = f"{job['job_type']}_{job['id']}.txt"
        with open(f"exports/{fake_path}", "w", encoding="utf-8") as f:
            f.write(json.dumps(job.get("params") or {}, indent=2))
        logger.info(f"Exported job {job['id']} to {fake_path}")
        return True, None, fake_path, "text/plain"
    except Exception as e:
        logger.error(f"Export job {job['id']} failed: {e}")
        return False, str(e), None, None

    async def fetch_due_jobs() -> list[Dict[str, Any]]:
        conn = await asyncpg.connect(DB_URL)
        rows = await conn.fetch(
            """
            SELECT id, status, scheduled_at, attempts, max_attempts, payload, last_error
            FROM export_jobs
            WHERE status IN ('queued','retry')
              AND scheduled_at <= NOW()
              AND (attempts < max_attempts OR max_attempts IS NULL)
            ORDER BY scheduled_at ASC
            LIMIT 25
            """
        )
        await conn.close()
        return [dict(r) for r in rows]

    async def handle_job(job: Dict[str, Any]):
        # Mark started_at, set status=running, update progress, write artifact, set finished_at
        logger.info(f"Handling job {job['id']}")
        # TODO: Implement actual export logic
        await asyncio.sleep(0.1)

    async def process_due_jobs():
        try:
            while True:
                jobs = await fetch_due_jobs()
                for job in jobs:
                    try:
                        await handle_job(job)
                    except Exception:
                        logger.exception("job failed")
                await asyncio.sleep(1)
        except Exception:
            logger.exception("worker loop crashed")

    if __name__ == "__main__":
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        asyncio.run(process_due_jobs())

async def process_due_jobs(session: AsyncSession):

    import os
    import time
    from typing import Any, Dict, List, Optional
    import psycopg2
    import psycopg2.extras
    POLL_SECONDS: int = int(os.getenv("WORKER_POLL_SECONDS", "5"))
    MAX_BATCH_SIZE: int = int(os.getenv("WORKER_MAX_BATCH_SIZE", "25"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JOBS_TABLE = os.getenv("JOBS_TABLE", "export_jobs")
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (MAX_BATCH_SIZE,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def mark_in_progress(conn, job_id: int) -> None:
        sql = f"""
            UPDATE {JOBS_TABLE}
            SET status = 'in_progress', updated_at = NOW()
            WHERE id = %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (job_id,))

    def mark_success(conn, job_id: int) -> None:
        sql = f"""
            UPDATE {JOBS_TABLE}
            SET status = 'done', updated_at = NOW(), last_error = NULL
            WHERE id = %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (job_id,))

    def mark_failure(
        conn, job_id: int, attempts: int, max_attempts: Optional[int], err_msg: str
    ) -> None:
        """
        Increment attempts and set either retry or failed depending on max_attempts.
        """
        next_attempts = (attempts or 0) + 1
        if max_attempts is not None and next_attempts >= max_attempts:
            new_status = "failed"
        else:
            new_status = "retry"

        sql = f"""
            UPDATE {JOBS_TABLE}
            SET status = %s,
                attempts = %s,
                last_error = %s,
                updated_at = NOW(),
                scheduled_at = CASE WHEN %s = 'retry' THEN NOW() + INTERVAL '60 seconds' ELSE scheduled_at END
            WHERE id = %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (new_status, next_attempts, err_msg[:1000], new_status, job_id))

    # ------------------------------------------------------------------------------
    # Core export logic (replace with your real export implementation)
    # ------------------------------------------------------------------------------
    def perform_export(payload: Dict[str, Any]) -> None:
        """
        Do the actual export. This is a stub — replace with your business logic.
        Raise an exception to trigger retry/failed paths.
        """
        destination = payload.get("destination", "unknown")
        records = payload.get("records", [])
        export_format = payload.get("format", "json")

        if not records:
            raise ValueError("No records provided for export")

        _serialized = json.dumps(
            {"destination": destination, "format": export_format, "count": len(records)}
        )
        return

    # ------------------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------------------
    def process_loop() -> None:
        logger.info(f"Starting export worker loop (poll={POLL_SECONDS}s, batch={MAX_BATCH_SIZE})")

        while True:
            try:
                with get_conn() as conn:
                    conn.autocommit = False

                    jobs = fetch_due_jobs(conn)
                    if not jobs:
                        while True:
                            try:
                                with get_conn() as conn:
                                    conn.autocommit = False
                                    jobs = fetch_due_jobs(conn)
                                    if not jobs:
                                        conn.commit()
                                        time.sleep(POLL_SECONDS)
                                        continue
                                    for job in jobs:
                                        job_id = job["id"]
                                        attempts = job.get("attempts") or 0
                                        max_attempts = job.get("max_attempts")
                                        try:
                                            mark_in_progress(conn, job_id)
                                            conn.commit()
                                            payload_raw = job.get("payload") or "{}"
                                            if isinstance(payload_raw, str):
                                                payload = json.loads(payload_raw)
                                            else:
                                                payload = payload_raw
                                            perform_export(payload)
                                            mark_success(conn, job_id)
                                            conn.commit()
                                            logger.info(f"Job {job_id} completed")
                                        except Exception as e:
                                            err_msg = f"{type(e).__name__}: {e}"
                                            logger.error(f"Job {job_id} failed: {err_msg}")
                                            try:
                                                mark_failure(conn, job_id, attempts, max_attempts, err_msg)
                                                conn.commit()
                                            except Exception as inner:
                                                logger.exception(f"Failed to update failure state for job {job_id}: {inner}")
                                                conn.rollback()
                            except Exception as loop_err:
                                logger.exception(f"Worker loop error: {loop_err}")
                            time.sleep(POLL_SECONDS)

    if __name__ == "__main__":
        main()
