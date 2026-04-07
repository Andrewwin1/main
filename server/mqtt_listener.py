"""Асинхронный MQTT-слушатель. Принимает состояния головоломок и сохраняет в SQLite."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from queue import Queue

import paho.mqtt.client as mqtt
from aiosqlite import connect as aiosqlite_connect

# Все серверные файлы лежат в одной директории
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_FILTER = "#"
DB_PATH = os.path.join(SERVER_DIR, "mqtt_messages.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt_listener")

# MQTT-клиент для отправки команд обратно (переключение состояний)
mqtt_client = None


async def init_db(db):
    # Лог всех сообщений
    await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            payload TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    # Текущие состояния головоломок
    await db.execute("""
        CREATE TABLE IF NOT EXISTS puzzle_states (
            puzzle_name TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'active',
            updated_at TEXT NOT NULL
        )
    """)
    # Трекинг устройств (heartbeat)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS puzzle_devices (
            device_name TEXT PRIMARY KEY,
            last_seen TEXT NOT NULL,
            topic TEXT
        )
    """)
    await db.commit()
    log.info("Database initialized: %s", DB_PATH)


async def save_message(db, topic, payload):
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO messages (topic, payload, timestamp) VALUES (?, ?, ?)",
        (topic, payload, ts),
    )
    await db.commit()


async def update_puzzle_state(db, payload):
    """
    Обрабатывает данные от Uno через ESP.
    Форматы входящих сообщений от ESP:
      STATE:ACTIVE       -> начальное состояние
      STATE:COMPLETED    -> загадка разгадана
      UNLOCKED           -> сигнал о решении
    """
    ts = datetime.now(timezone.utc).isoformat()

    # Определяем имя головоломки по топику
    puzzle_name = payload.get("puzzle_name", "unknown")
    state = payload.get("state", "active")

    if state == "UNLOCKED":
        log.info("Puzzle '%s' UNLOCKED! Setting state to COMPLETED", puzzle_name)
        state = "completed"
    elif state == "ACTIVE":
        state = "active"
    elif state == "COMPLETED":
        state = "completed"

    await db.execute(
        """INSERT OR REPLACE INTO puzzle_states (puzzle_name, state, updated_at)
           VALUES (?, ?, ?)""",
        (puzzle_name, state, ts),
    )
    await db.commit()
    log.info("Puzzle '%s' state -> '%s'", puzzle_name, state)


async def send_state_command(puzzle_name, command):
    """Отправляет команду смены состояния через MQTT обратно на ESP."""
    topic = f"home/{puzzle_name}"
    if mqtt_client:
        mqtt_client.publish(topic, command)
        log.info("Sent command to '%s': %s", topic, command)


async def update_device_heartbeat(db, device_name, topic):
    """Обновляет last_seen устройства в puzzle_devices."""
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT OR REPLACE INTO puzzle_devices (device_name, last_seen, topic)
           VALUES (?, ?, ?)""",
        (device_name, ts, topic),
    )
    await db.commit()


async def schedule_auto_reset(db, puzzle_name, delay=30):
    """Через delay секунд сбросить головоломку в active."""
    await asyncio.sleep(delay)
    log.info("Auto-reset puzzle '%s' after %ds timeout", puzzle_name, delay)
    await send_state_command(puzzle_name, "SET_STATE:ACTIVE")
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT OR REPLACE INTO puzzle_states (puzzle_name, state, updated_at)
           VALUES (?, 'active', ?)""",
        (puzzle_name, ts),
    )
    await db.commit()


def mqtt_on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        log.info("Connected to broker, subscribing to '%s'", TOPIC_FILTER)
        client.subscribe(TOPIC_FILTER)
        client.subscribe("puzzle/#")
        client.subscribe("home/#")
    else:
        log.error("Connection failed with code %d", reason_code)


def mqtt_on_message(client, userdata, msg):
    queue = userdata["queue"]
    payload = msg.payload.decode("utf-8", errors="replace")
    queue.put_nowait({
        "topic": msg.topic,
        "payload": payload,
        "qos": msg.qos,
        "retain": msg.retain,
    })


# Карта: имя головоломки -> последний статус (для определения по топику)
PUZZLE_TOPICS = {
    "memory": "puzzle/memory",
    "phone": "puzzle/phone",
    "pyatnashky": "puzzle/pyatnashky",
    "safe": "puzzle/safe",
}


async def listener_loop():
    global mqtt_client
    queue: Queue = Queue()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.user_data_set({"queue": queue})
    client.on_connect = mqtt_on_connect
    client.on_message = mqtt_on_message

    mqtt_client = client

    log.info("Connecting to %s:%d ...", BROKER_HOST, BROKER_PORT)
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()

    db = await aiosqlite_connect(DB_PATH)
    await init_db(db)

    try:
        while True:
            msg = await asyncio.get_event_loop().run_in_executor(None, queue.get)
            topic = msg["topic"]
            payload = msg["payload"]

            # Лог всех сообщений
            await save_message(db, topic, payload)
            log.info("Received: topic='%s' | payload='%s'", topic, payload)

            # Парсим состояние головоломки (puzzle/<name>)
            if topic.startswith("puzzle/"):
                # Ищем имя головоломки
                puzzle_name = None
                for name, p_topic in PUZZLE_TOPICS.items():
                    if topic == p_topic:
                        puzzle_name = name
                        break
                if puzzle_name is None:
                    # Пробуем извлечь имя из топика
                    parts = topic.split("/")
                    if len(parts) >= 2:
                        puzzle_name = parts[1]

                payload_upper = payload.upper().strip()
                if payload_upper in ("STATE:ACTIVE", "STATE:COMPLETED", "UNLOCKED"):
                    if puzzle_name:
                        # Извлекаем чистый статус
                        if payload_upper == "UNLOCKED":
                            status = "UNLOCKED"
                        elif payload_upper == "STATE:ACTIVE":
                            status = "ACTIVE"
                        else:
                            status = "COMPLETED"

                        await update_puzzle_state(db, {
                            "puzzle_name": puzzle_name,
                            "state": status,
                        })
                        # Запуск автосброса через 30 сек при completion
                        if status in ("COMPLETED", "UNLOCKED"):
                            asyncio.ensure_future(schedule_auto_reset(db, puzzle_name))
                        # Heartbeat: обновляем last_seen при любом сообщении от головоломки
                        asyncio.ensure_future(update_device_heartbeat(db, puzzle_name, topic))

            # Heartbeat от ESP: /home/alive
            if topic == "/home/alive":
                device_name = payload.strip()
                if device_name:
                    await update_device_heartbeat(db, device_name, topic)

            # Команды от веб-интерфейса: home/<name> с SET_STATE:TOGGLE
            if topic.startswith("home/") and payload == "SET_STATE:TOGGLE":
                parts = topic.split("/")
                pname = parts[1] if len(parts) >= 2 else None
                if pname:
                    # Инвертируем текущее состояние
                    ts2 = datetime.now(timezone.utc).isoformat()
                    async with db.execute(
                        "SELECT state FROM puzzle_states WHERE puzzle_name=?", (pname,)
                    ) as cursor:
                        row = await cursor.fetchone()
                    cur = row[0] if row else "active"
                    new_state = "active" if cur == "completed" else "completed"
                    await db.execute(
                        "INSERT OR REPLACE INTO puzzle_states (puzzle_name, state, updated_at) VALUES (?, ?, ?)",
                        (pname, new_state, ts2),
                    )
                    await db.commit()
                    # Отправляем ESP правильную команду
                    await send_state_command(pname, f"SET_STATE:{new_state.upper()}")
                    log.info("Toggle %s: %s -> %s", pname, cur, new_state)

            # Команды администратора: home/<puzzle_name>/set
            elif topic.startswith("home/") and topic.endswith("/set"):
                parts = topic.split("/")
                puzzle_name = parts[1] if len(parts) >= 2 else "unknown"
                cmd = payload.strip().upper()
                if cmd == "ACTIVE":
                    await send_state_command(puzzle_name, "SET_STATE:ACTIVE")
                    await update_puzzle_state(db, {
                        "puzzle_name": puzzle_name,
                        "state": "active",
                    })
                elif cmd == "COMPLETED":
                    await send_state_command(puzzle_name, "SET_STATE:COMPLETED")
                    await update_puzzle_state(db, {
                        "puzzle_name": puzzle_name,
                        "state": "completed",
                    })
                elif cmd == "RESET":
                    await send_state_command(puzzle_name, "SET_STATE:ACTIVE")
                    await update_puzzle_state(db, {
                        "puzzle_name": puzzle_name,
                        "state": "active",
                    })

    except asyncio.CancelledError:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        await db.close()
        log.info("Disconnected. Messages saved to %s", DB_PATH)


def main():
    log.info("Starting MQTT puzzle listener...")
    asyncio.run(listener_loop())


if __name__ == "__main__":
    main()
