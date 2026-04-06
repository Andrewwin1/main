"""Интеграционный тест: запускает слушателя и отправителя, проверяет состояния головоломок."""

import logging
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / "mqtt_messages.db"
LISTENER_SCRIPT = PROJECT_DIR / "mqtt_listener.py"
SENDER_SCRIPT = PROJECT_DIR / "test_sender.py"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("test_integration")


def cleanup_db():
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
            log.info("Removed old database: %s", DB_PATH)
        except PermissionError:
            log.warning("Could not remove DB (locked), will overwrite")


def check_puzzle_states(expected):
    """Проверяет, что все ожидаемые состояния головоломок совпадают."""
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT puzzle_name, state FROM puzzle_states")
        states = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()

        all_ok = True
        for name, exp_state in expected.items():
            actual = states.get(name)
            if actual != exp_state:
                log.warning("Puzzle '%s': expected '%s', got '%s'", name, exp_state, actual)
                all_ok = False
            else:
                log.info("Puzzle '%s': '%s' (OK)", name, actual)
        return all_ok
    except Exception as e:
        log.error("DB error: %s", e)
        return None


def main():
    log.info("=" * 60)
    log.info("Integration test: MQTT Puzzle Listener + Sender")
    log.info("=" * 60)

    cleanup_db()

    # 1. Запускаем слушателя
    log.info("Starting MQTT listener...")
    listener = subprocess.Popen(
        [sys.executable, "-u", str(LISTENER_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(PROJECT_DIR),
    )

    # Ждем подключения
    time.sleep(3)
    if listener.poll() is not None:
        out, _ = listener.communicate()
        log.error("Listener crashed:\n%s", out)
        sys.exit(1)

    log.info("Listener running, starting sender...")

    # 2. Запускаем отправителя
    sender = subprocess.Popen(
        [sys.executable, "-u", str(SENDER_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(PROJECT_DIR),
    )
    sender.wait()
    log.info("Sender finished with code %d", sender.returncode)

    # 3. Ждем обработки сообщений
    time.sleep(3)

    # 4. Проверяем состояния головоломок
    expected_states = {
        "memory": "completed",
        "phone": "completed",
        "pyatnashky": "completed",
    }

    log.info("Checking puzzle states...")
    ok = check_puzzle_states(expected_states)

    if ok:
        log.info("\nSUCCESS: All puzzle states match!")
    else:
        log.error("\nFAILURE: Some puzzle states do not match")

    # 5. Останавливаем слушателя
    log.info("Stopping listener...")
    listener.terminate()
    try:
        listener.wait(timeout=3)
    except subprocess.TimeoutExpired:
        listener.kill()
        listener.wait()

    # 6. Вывод всех сохраненных сообщений
    log.info("\nAll messages in database:")
    print("-" * 60)
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        cur.execute("SELECT topic, payload, timestamp FROM messages ORDER BY id")
        for row in cur.fetchall():
            print(f"  {row[0]} | {row[1]} | {row[2]}")

        print("\n  Puzzle states:")
        cur.execute("SELECT puzzle_name, state, updated_at FROM puzzle_states")
        for row in cur.fetchall():
            print(f"    {row[0]} -> {row[1]} (updated: {row[2]})")
        conn.close()
    print("-" * 60)

    log.info("\nTest complete.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
