"""Автопроверка и обновление из GitHub-репозитория."""

import logging
import subprocess

log = logging.getLogger("git_updater")


def _run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", "git not found in PATH"
    except subprocess.TimeoutExpired:
        return -1, "", "git command timed out"


def _get_current_branch():
    """Определяет текущую ветку."""
    rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        return out
    return "master"


def check_for_updates():
    """Проверяет наличие обновлений и делает pull если нужно.
    Возвращает (has_updates, message)."""
    branch = _get_current_branch()
    # Fetch для получения актуального состояния
    rc, out, err = _run(["git", "fetch", "origin", branch])
    if rc != 0:
        log.warning("git fetch failed: %s", err)
        return False, f"git fetch failed: {err}"

    # Сравниваем HEAD с origin/branch
    rc, diff, _ = _run(["git", "rev-list", "HEAD..origin/" + branch, "--count"])
    if rc != 0:
        return False, "could not compare revisions"

    if diff == "0":
        log.info("Already up to date with origin/%s.", branch)
        return False, "Already up to date."

    log.info("New commits available on %s (%s), pulling...", branch, diff)
    rc, out, err = _run(["git", "pull", "origin", branch])
    if rc == 0:
        log.info("Pull successful: %s", out)
        return True, out
    else:
        log.error("Pull failed: %s", err)
        return False, f"pull failed: {err}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Checking for git updates...")
    has_updates, msg = check_for_updates()
    print(msg)
