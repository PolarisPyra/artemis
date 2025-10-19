#!/usr/bin/env python3
"""
Standalone script to create daphnis_web_permissions entries for existing Chunithm users.

This script finds all Chunithm profiles that don't have a web permissions entry
and creates one for them with status 0 (inactive/pending).

Usage:
    python migrate_chuni_web_permissions.py
"""

import asyncio
import logging
import os
from typing import Optional

import yaml
from sqlalchemy import select

from core.config import CoreConfig
from core.data.schema import metadata
from titles.chuni.database import ChuniData
from titles.chuni.schema.profile import profile
from titles.chuni.schema.daphnis import web_permissions


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

    core_cfg = CoreConfig()
    core_cfg.update(config_dict)

    # Initialize data handler
    logger.info("Connecting to database...")
    data = ChuniData(core_cfg)

    # Find all unique user IDs from Chunithm profiles
    logger.info("Finding all Chunithm users...")
    sql = select(profile.c.user).distinct()
    result = await data.base.execute(sql)

    if result is None:
        logger.error("Failed to query Chunithm profiles")
        return

    all_users = [row.user for row in result.fetchall()]
    logger.info(f"Found {len(all_users)} unique Chunithm users")

    # Find users that already have web permissions
    logger.info("Checking existing web permissions...")
    sql = select(web_permissions.c.user)
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

    # Get the latest profile for each user to extract their username
    created_count = 0
    failed_count = 0

    for user_id in users_to_migrate:
        # Get the most recent profile for this user
        sql = (
            select(profile)
            .where(profile.c.user == user_id)
            .order_by(profile.c.version.desc())
            .limit(1)
        )
        result = await data.base.execute(sql)

        if result is None:
            logger.warning(f"Failed to get profile for user {user_id}")
            failed_count += 1
            continue

        user_profile = result.fetchone()
        username = user_profile.userName if user_profile else None

        # Create web permission entry
        try:
            await data.daphnis.put_web_permission(
                user_id=user_id,
                username=username,
                status=0,  # 0 = inactive/pending by default
            )
            created_count += 1
            logger.info(f"✓ Created web permission for user {user_id} (username: {username})")
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

