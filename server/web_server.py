"""Flask веб-сервер для мониторинга и управления загадками."""

import logging
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template

from git_updater import check_for_updates
from mqtt_listener import DB_PATH
import mqtt_listener

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("web_server")

# Путь к frontend/ (на уровень выше серверной папки)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

KNOWN_PUZZLES = ["memory", "phone", "pyatnashky", "safe"]


def _get_db():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _online_since(last_seen_iso, seconds=15):
    """Проверяет, видел ли устройство за последние N секунд."""
    if not last_seen_iso:
        return False
    try:
        ls = datetime.fromisoformat(last_seen_iso)
        now = datetime.now(timezone.utc)
        # Если last_seen без tzinfo, делаем без tz
        if ls.tzinfo is None:
            now = now.replace(tzinfo=None)
        return (now - ls).total_seconds() < seconds
    except (ValueError, TypeError):
        return False


def load_puzzles():
    """Загружает состояния загадок из БД и вычисляет цвет."""
    con = _get_db()
    rows = con.execute("SELECT puzzle_name, state, updated_at FROM puzzle_states").fetchall()
    state_map = {r["puzzle_name"]: r["state"] for r in rows}

    # Загружаем устройства
    device_rows = con.execute("SELECT device_name, last_seen FROM puzzle_devices").fetchall()
    online_devices = {r["device_name"]: r["last_seen"] for r in device_rows}
    con.close()

    result = []
    for name in KNOWN_PUZZLES:
        state = state_map.get(name, "active")
        is_online = name in online_devices and _online_since(online_devices[name])
        if not is_online:
            color = "red"
        elif state == "completed":
            color = "green"
        else:
            color = "yellow"
        result.append({"name": name, "state": state, "color": color})

    # Добавляем неизвестные головоломки из БД
    known_set = set(KNOWN_PUZZLES)
    for key in state_map:
        if key not in known_set:
            state = state_map[key]
            is_online = key in online_devices and _online_since(online_devices[key])
            color = "green" if state == "completed" else ("yellow" if is_online else "red")
            result.append({"name": key, "state": state, "color": color})

    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/puzzles")
def api_puzzles():
    return jsonify(load_puzzles())


@app.route("/api/puzzles/refresh", methods=["POST"])
def api_refresh():
    return jsonify({"ok": True})


@app.route("/api/puzzles/<name>/toggle", methods=["POST"])
def api_toggle(name):
    con = _get_db()
    row = con.execute(
        "SELECT state FROM puzzle_states WHERE puzzle_name=?", (name,)
    ).fetchone()
    state = row["state"] if row else "active"

    if state == "completed":
        new_state = "active"
    else:
        new_state = "completed"

    # Публикуем команду напрямую через глобальный mqtt_client
    client = mqtt_listener.mqtt_client
    if client:
        topic = f"home/{name}"
        client.publish(topic, f"SET_STATE:{new_state.upper()}")

    ts = datetime.now(timezone.utc).isoformat()
    con.execute(
        "INSERT OR REPLACE INTO puzzle_states (puzzle_name, state, updated_at) VALUES (?, ?, ?)",
        (name, new_state, ts),
    )
    con.commit()
    con.close()

    # Обновим статус в списке
    return jsonify({"ok": True, "new_state": new_state})


@app.route("/api/git/update", methods=["POST"])
def api_git_update():
    has_updates, message = check_for_updates()
    return jsonify({"ok": has_updates, "message": message})


def _run_git_check():
    """При запуске проверяем обновления."""
    try:
        has_updates, message = check_for_updates()
        if has_updates:
            log.info("Git update applied: %s", message)
        else:
            log.info("Git status: %s", message)
    except Exception as e:
        log.error("Git check failed: %s", e)


def start_flask():
    _run_git_check()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)


if __name__ == "__main__":
    start_flask()
