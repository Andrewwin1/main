"""Тестовый отправитель MQTT. Публикует несколько сообщений для проверки слушателя."""

import asyncio
import json
import logging
from asyncio_mqtt import Client

BROKER_HOST = "localhost"
BROKER_PORT = 1883

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt_sender")

TEST_MESSAGES = [
    ("test/temperature", json.dumps({"value": 23.5, "unit": "Celsius"})),
    ("test/humidity", json.dumps({"value": 67, "unit": "%"})),
    ("test/motion", json.dumps({"detected": True, "zone": "kitchen"})),
    ("test/door/sensor", '{"open": false}'),
    ("test/alert", "manual alert from test sender"),
]


async def send_messages():
    log.info("Connecting to broker at %s:%d ...", BROKER_HOST, BROKER_PORT)
    try:
        async with Client(BROKER_HOST, port=BROKER_PORT) as client:
            log.info("Connected, publishing %d messages...", len(TEST_MESSAGES))
            for topic, payload in TEST_MESSAGES:
                await client.publish(topic, payload=payload)
                log.info("  Published: topic='%s' | payload='%s'", topic, payload)
                await asyncio.sleep(0.3)
            log.info("All messages published successfully.")
    except Exception as exc:
        log.exception("Failed to connect: %s", exc)
        raise


if __name__ == "__main__":
    asyncio.run(send_messages())
