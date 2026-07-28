#!/usr/bin/env python3
import argparse
import yaml
from os import path, environ, makedirs
import uvicorn
import logging
import asyncio
from logging.handlers import TimedRotatingFileHandler

from server.sega.config import ArtemisConfig
from server.sega.aimedb import AimedbServlette


async def launch_main(cfg: ArtemisConfig, ssl: bool) -> None:
    if ssl:
        server_cfg = uvicorn.Config(
            "server.sega.app:app",
            host=cfg.server.listen_address,
            port=cfg.server.port if args.port == 0 else args.port,
            reload=cfg.server.is_develop,
            log_level="info" if cfg.server.is_develop else "critical",
            ssl_version=3,
            ssl_certfile=cfg.server.ssl_cert,
            ssl_keyfile=cfg.server.ssl_key,
        )
    else:
        server_cfg = uvicorn.Config(
            "server.sega.app:app",
            host=cfg.server.listen_address,
            port=cfg.server.port if args.port == 0 else args.port,
            reload=cfg.server.is_develop,
            log_level="info" if cfg.server.is_develop else "critical",
        )
    server = uvicorn.Server(server_cfg)
    await server.serve()


async def launch_billing(cfg: ArtemisConfig) -> None:
    server_cfg = uvicorn.Config(
        "server.sega.allnet:app_billing",
        host=cfg.server.listen_address,
        port=cfg.billing.port,
        reload=cfg.server.is_develop,
        log_level="info" if cfg.server.is_develop else "critical",
        ssl_version=3,
        ssl_certfile=cfg.billing.ssl_cert,
        ssl_keyfile=cfg.billing.ssl_key,
        ssl_ciphers="DEFAULT:!aNULL:!eNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK",
    )
    server = uvicorn.Server(server_cfg)
    await server.serve()


async def launch_frontend(cfg: ArtemisConfig) -> None:
    server_cfg = uvicorn.Config(
        "server.sega.frontend:app",
        host=cfg.server.listen_address,
        port=cfg.frontend.port,
        reload=cfg.server.is_develop,
        log_level="info" if cfg.server.is_develop else "critical",
    )
    server = uvicorn.Server(server_cfg)
    await server.serve()


async def launch_allnet(cfg: ArtemisConfig) -> None:
    server_cfg = uvicorn.Config(
        "server.sega.allnet:app_allnet",
        host=cfg.server.listen_address,
        port=cfg.allnet.port,
        reload=cfg.server.is_develop,
        log_level="info" if cfg.server.is_develop else "critical",
    )
    server = uvicorn.Server(server_cfg)
    await server.serve()


async def launch_konami(cfg: ArtemisConfig) -> None:
    from server.konami.app import build_konami_app

    logger = logging.getLogger("konami")
    if not getattr(logger, "handler_set", False):
        if not path.exists(cfg.server.log_dir):
            makedirs(cfg.server.log_dir)
        log_path = path.join(cfg.server.log_dir, "konami.log")
        file_handler = TimedRotatingFileHandler(
            log_path, encoding="utf-8", when="d", backupCount=10
        )
        log_format = logging.Formatter(
            "[%(asctime)s] Konami | %(levelname)s | %(message)s"
        )
        file_handler.setFormatter(log_format)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(cfg.konami.loglevel)
        logger.propagate = False
        logger.handler_set = True

    server_cfg = uvicorn.Config(
        build_konami_app(cfg),
        host=cfg.server.listen_address,
        port=cfg.konami.port,
        reload=cfg.server.is_develop,
        log_level="info" if cfg.server.is_develop else "critical",
    )
    server = uvicorn.Server(server_cfg)
    await server.serve()


async def launcher(cfg: ArtemisConfig, ssl: bool) -> None:
    task_list = [asyncio.create_task(launch_main(cfg, ssl))]

    if cfg.billing.standalone:
        task_list.append(asyncio.create_task(launch_billing(cfg)))
    if cfg.frontend.enable:
        task_list.append(asyncio.create_task(launch_frontend(cfg)))
    if cfg.allnet.standalone:
        task_list.append(asyncio.create_task(launch_allnet(cfg)))
    if cfg.konami.enable and cfg.konami.standalone:
        task_list.append(asyncio.create_task(launch_konami(cfg)))
    if cfg.aimedb.enable:
        AimedbServlette(cfg).start()

    done, pending = await asyncio.wait(
        task_list,
        return_when=asyncio.FIRST_COMPLETED,
    )

    logging.getLogger("artemis").info("Shutdown")
    for pending_task in pending:
        pending_task.cancel("Another service died, server is shutting down")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Artemis main entry point")
    parser.add_argument("--port", "-p", type=int, default=0, help="Port override")
    parser.add_argument("--ssl", "-s", type=bool, help="Launch with SSL")
    args = parser.parse_args()

    config_dir = "config"
    config_file = path.join(config_dir, "core.yaml")
    if not path.exists(config_file):
        print(f"The config file {config_file} does not exist. Defaults will be used.\nDid you copy the example folder?")

    cfg: ArtemisConfig = ArtemisConfig()
    if path.exists(config_file):
        cfg.update(yaml.safe_load(open(config_file)))

    environ["ARTEMIS_CFG_DIR"] = config_dir

    asyncio.run(launcher(cfg, args.ssl))
