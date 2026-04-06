"""Асинхронный MQTT-слушатель. Подключается к брокеру, принимает все сообщения и сохраняет в SQLite."""

import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone

from aiosqlite import connect as aiosqlite_connect
from asyncio_mqtt import Client, MqttError

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_FILTER = "#"  # подписка на все топики
DB_PATH = "mqtt_messages.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt_listener")


async def init_db(db):
    """Создаёт таблицу для хранения сообщений."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            payload TEXT,
            qos INTEGER,
            retain INTEGER,
            timestamp TEXT NOT NULL
        )
    """)
    await db.commit()
    log.info("Database initialized: %s", DB_PATH)


async def save_message(db, topic, payload, qos, retain):
    """Сохраняет одно MQTT-сообщение в БД."""
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO messages (topic, payload, qos, retain, timestamp) VALUES (?, ?, ?, ?, ?)",
        (topic, payload, qos, int(retain), ts),
    )
    await db.commit()


async def listener_loop():
    stop_event = asyncio.Event()

    def _signal_handler():
        log.info("Received stop signal, shutting down...")
        stop_event.set()

    if os.name != "nt":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _signal_handler)

    db = await aiosqlite_connect(DB_PATH)
    await init_db(db)

    log.info("Connecting to %s:%d ...", BROKER_HOST, BROKER_PORT)

    try:
        async with Client(BROKER_HOST, port=BROKER_PORT) as client:
            log.info("Connected to broker, subscribing to '%s'", TOPIC_FILTER)
            async with client.messages(filtered=TOPIC_FILTER) as messages:
                async for message in messages:
                    payload_str = message.payload.decode("utf-8", errors="replace")
                    log.info(
                        "Received: topic='%s' | payload='%s' | qos=%d | retain=%s",
                        message.topic, payload_str, message.qos, message.retain,
                    )
                    await save_message(db, str(message.topic), payload_str, message.qos, message.retain)
    except MqttError as exc:
        log.exception("MQTT error: %s", exc)
    finally:
        await db.close()
        log.info("Disconnected. Messages saved to %s", DB_PATH)


def main():
    log.info("Starting MQTT listener...")
    asyncio.run(listener_loop())


if __name__ == "__main__":
    main()
