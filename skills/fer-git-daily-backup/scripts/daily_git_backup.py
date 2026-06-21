#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def run(args, check=True):
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and result.returncode != 0:
        print(result.stdout.strip())
        raise SystemExit(result.returncode)
    return result


def output(args):
    return run(args).stdout.strip()


def ensure_repo():
    if not (REPO_ROOT / ".git").exists():
        print(f"BLOCKED: {REPO_ROOT} is not a Git repository.")
        raise SystemExit(1)

    branch = output(["git", "branch", "--show-current"])
    if branch != "main":
        print(f"BLOCKED: expected branch main, found {branch or '(detached)'}")
        raise SystemExit(1)

    remotes = output(["git", "remote"])
    if "origin" not in remotes.splitlines():
        print("BLOCKED: missing origin remote.")
        raise SystemExit(1)


def ensure_identity():
    name = run(["git", "config", "user.name"], check=False).stdout.strip()
    email = run(["git", "config", "user.email"], check=False).stdout.strip()
    if not name:
        run(["git", "config", "user.name", "Max Gomez"])
    if not email:
        run(["git", "config", "user.email", "205664835+mxgmz@users.noreply.github.com"])


def has_changes():
    return bool(output(["git", "status", "--porcelain"]))


def remote_has_unmerged_commits():
    fetch = run(["git", "fetch", "origin", "main"], check=False)
    if fetch.returncode != 0:
        print("BLOCKED: could not fetch origin/main.")
        print(fetch.stdout.strip())
        raise SystemExit(fetch.returncode)

    upstream = run(["git", "rev-parse", "--verify", "origin/main"], check=False)
    if upstream.returncode != 0:
        return False

    result = run(["git", "rev-list", "--count", "HEAD..origin/main"])
    return int(result.stdout.strip() or "0") > 0


def commit_changes():
    run(["git", "add", "--all"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"Daily Fer Health OS backup {timestamp}"
    run(["git", "commit", "-m", message])
    return output(["git", "rev-parse", "--short", "HEAD"])


def push():
    result = run(["git", "push", "origin", "main"], check=False)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("BLOCKED: push failed. Inspect before retrying; do not force-push.")
        raise SystemExit(result.returncode)


def main():
    ensure_repo()
    ensure_identity()

    if remote_has_unmerged_commits():
        print("BLOCKED: origin/main has commits not present locally. Inspect and merge manually.")
        raise SystemExit(1)

    if not has_changes():
        print("NO_CHANGES: Fer Health OS already has no local changes to back up.")
        return

    commit_hash = commit_changes()
    push()
    print(f"PUSHED: backed up Fer Health OS at commit {commit_hash}.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
