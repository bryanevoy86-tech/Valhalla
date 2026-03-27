import asyncio
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def process_due_jobs() -> None:
    """
    Known-good structure. Replace the placeholder loop with real DB logic later.
    """
    try:
        for i in range(3):
            await asyncio.sleep(0.1)
            logger.info("Processing export job %s", i)
        # TODO: fetch pending jobs, process, update status, etc.
    except asyncio.CancelledError:
        logger.warning("export worker cancelled")
        raise
    except Exception as e:
        logger.exception("Unhandled error in export worker: %s", e)


async def main() -> None:
    await process_due_jobs()


if __name__ == "__main__":
    asyncio.run(main())
