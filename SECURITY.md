# Security Remediation Guide

Immediate steps (run now):

- Rotate all compromised API keys and credentials that may have been exposed (Gemini, Groq, OpenRouter, SMTP, AWS/R2, etc.).
- Revoke previous keys and create new ones in your secret manager.
- Purge sensitive files from git history (see `scripts/remove_env_from_git.sh`).
- Do NOT re-commit `.env` or credentials. Use environment variables in your deployment platform or a secrets manager.
- Rotate SMTP password and any cloud keys referenced in the deleted `.env`.

Recommended commands (local):

```bash
# Inspect commits that referenced .env
git log --all --full-history -- '**/.env' -p

# Purge .env from history using BFG (example):
# 1. Install BFG: https://rtyley.github.io/bfg-repo-cleaner/
# 2. Run:
#    java -jar bfg.jar --delete-files .env
# 3. Follow with:
#    git reflog expire --expire=now --all && git gc --prune=now --aggressive
# 4. Force-push to remote: git push --force
```

Audit & prevention:

- Add repository secret scanning (GitHub secret scanning or tools like `trufflehog`, `gitleaks`).
- Add a pre-commit hook to prevent committing `.env` or high-entropy strings (use `pre-commit` and `detect-secrets`).
- Store secrets in a secret manager (AWS Secrets Manager, Hashicorp Vault, Render/Heroku environment variables).

Contact actions:

- For any third-party providers (Google, Groq, OpenRouter, SMTP) contact their support if you suspect abuse.
- Revoke and reissue credentials immediately.

See `scripts/scan_repo_secrets.py` to locate remaining potential secret strings.
