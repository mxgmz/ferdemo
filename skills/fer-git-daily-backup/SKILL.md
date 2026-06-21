---
name: fer-git-daily-backup
description: Safely back up Fer Health OS to GitHub. Use when Codex needs to commit and push local Fer Health OS changes, run the daily midnight Git backup automation, preserve health CSV/report updates, or recover from a missed daily repo sync without force-pushing or overwriting remote work.
---

# Fer Git Daily Backup

Use this skill in:

```txt
/Users/maxgomez/Documents/Fer/fer-health-os
```

## Workflow

1. Run the bundled script from the repo root:

```bash
python3 skills/fer-git-daily-backup/scripts/daily_git_backup.py
```

2. Verify the script output:
   - `NO_CHANGES` means the repo was already current locally.
   - `PUSHED` means a new backup commit reached GitHub.
   - `BLOCKED` means the script refused a risky action, usually because the remote has commits not present locally.

3. If blocked by remote divergence, fetch and inspect before changing history:

```bash
git fetch origin
git status --short --branch
git log --oneline --decorate --graph --max-count=12 --all
```

Do not use force-push for daily backups.

## Rules

- Commit all tracked and untracked repo changes except files ignored by `.gitignore`.
- Use the remote already configured as `origin`.
- Keep the branch on `main`.
- Never reset, checkout away, rebase, or force-push in the automated path.
- Report the commit hash and push result when a backup happens.
