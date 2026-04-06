"""Тестовый отправитель MQTT. Публикует тестовые сообщения и команды переключения состояний."""

import json
import logging
import time

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt_sender")

# Тестовые сообщения (имитация Uno -> ESP -> MQTT)
TEST_MESSAGES = [
    ("puzzle/memory", "STATE:ACTIVE"),
    ("puzzle/phone", "STATE:ACTIVE"),
    ("puzzle/pyatnashky", "STATE:ACTIVE"),
    ("test/temperature", json.dumps({"value": 23.5, "unit": "Celsius"})),
    ("test/humidity", json.dumps({"value": 67, "unit": "%"})),
]

# Команды переключения состояний (сервер -> ESP -> Uno)
STATE_COMMANDS = {
    "memory": "SET_STATE:COMPLETED",
    "phone": "SET_STATE:ACTIVE",
    "pyatnashky": "SET_STATE:COMPLETED",
}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to broker, publishing %d messages...", len(TEST_MESSAGES))
        for topic, payload in TEST_MESSAGES:
            client.publish(topic, payload)
            log.info("  Published: topic='%s' | payload='%s'", topic, payload)
            time.sleep(0.3)

        # Ждем и отправляем команды переключения
        time.sleep(1)
        log.info("Sending state commands...")
        for puzzle, cmd in STATE_COMMANDS.items():
            topic = f"home/{puzzle}/set"
            client.publish(topic, cmd)
            log.info("  Command: topic='%s' | payload='%s'", topic, cmd)
            time.sleep(0.3)

        # Симуляция решения головоломки (имитация Uno)
        time.sleep(1)
        log.info("Simulating puzzle solutions...")
        client.publish("puzzle/memory", "UNLOCKED")
        log.info("  puzzle/memory -> UNLOCKED")
        time.sleep(0.3)
        client.publish("puzzle/pyatnashky", "UNLOCKED")
        log.info("  puzzle/pyatnashky -> UNLOCKED")
        time.sleep(0.3)
        client.publish("puzzle/phone", "STATE:COMPLETED")
        log.info("  puzzle/phone -> STATE:COMPLETED")

        log.info("All messages published successfully.")
        client.disconnect()
    else:
        log.error("Connection failed with code %d", rc)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    log.info("Connecting to broker at %s:%d ...", BROKER_HOST, BROKER_PORT)
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
