
import asyncio
import logging
import os
from typing import Optional

import yaml
from sqlalchemy import select

from server.sega.config import ArtemisConfig
from server.sega.data.schema import metadata
from server.sega.data.schema.user import aime_user
from server.sega.titles.chuni.database import ChuniData
from server.sega.titles.chuni.schema.profile import profile
from server.sega.titles.chuni.schema.cozynet import web_permissions


async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s | %(message)s",
    )
    logger = logging.getLogger("migrate_web_permissions")

    # Load config
    cfg_dir = os.environ.get("ARTEMIS_CFG_DIR", "config")
    config_path = os.path.join(cfg_dir, "core.yaml")

    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}")
        logger.error("Please set ARTEMIS_CFG_DIR environment variable or run from project root")
        return

    logger.info(f"Loading config from {config_path}")
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    artemis_cfg = ArtemisConfig()
    artemis_cfg.update(config_dict)

    # Initialize data handler
    logger.info("Connecting to database...")
    data = ChuniData(artemis_cfg)

    # Find all unique user IDs from Chunithm profiles
    logger.info("Finding all Chunithm users...")
    sql = select(profile.c.user).distinct()  # type: ignore
    result = await data.base.execute(sql)

    if result is None:
        logger.error("Failed to query Chunithm profiles")
        return

    all_users = [row.user for row in result.fetchall()]
    logger.info(f"Found {len(all_users)} unique Chunithm users")

    # Find users that already have web permissions
    logger.info("Checking existing web permissions...")
    sql = select(web_permissions.c.user)  # type: ignore
    result = await data.base.execute(sql)

    if result is None:
        logger.error("Failed to query web permissions")
        return

    existing_perms = {row.user for row in result.fetchall()}
    logger.info(f"Found {len(existing_perms)} existing web permission entries")

    # Find users that need web permissions created
    users_to_migrate = [user_id for user_id in all_users if user_id not in existing_perms]

    if not users_to_migrate:
        logger.info("✓ All users already have web permissions entries!")
        return

    logger.info(f"Need to create web permissions for {len(users_to_migrate)} users")

    # Get aime_user data for each user to extract their username
    created_count = 0
    failed_count = 0

    for user_id in users_to_migrate:
        # Get the aime_user record for this user
        sql = select(aime_user).where(aime_user.c.id == user_id)  # type: ignore
        result = await data.base.execute(sql)

        if result is None:
            logger.warning(f"Failed to get aime_user for user {user_id}")
            failed_count += 1
            continue

        user_record = result.fetchone()
        if user_record is None:
            logger.warning(f"No aime_user record found for user {user_id}")
            failed_count += 1
            continue

        username = user_record.username if user_record.username else None

        # Create web permission entry
        try:
            await data.cozynet.put_web_permission(
                user_id=user_id,
                username=username,
                status=0,  # 0 = inactive/pending by default
            )
            created_count += 1
            logger.info(f"✓ Created web permission for user {user_id} (username: {username if username else 'NULL'})")
        except Exception as e:
            logger.error(f"✗ Failed to create web permission for user {user_id}: {e}")
            failed_count += 1

    # Summary
    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info(f"  Created: {created_count}")
    logger.info(f"  Failed:  {failed_count}")
    logger.info(f"  Total:   {len(users_to_migrate)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
