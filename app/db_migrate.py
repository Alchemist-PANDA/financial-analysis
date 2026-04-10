import asyncio
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
sys.path.insert(0, ROOT_DIR)

from app.database import init_db


async def run_migrations() -> None:
    await init_db()
    print("✅ Database migrations complete.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
