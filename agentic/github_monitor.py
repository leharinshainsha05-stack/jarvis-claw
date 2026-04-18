"""
agentic/github_monitor.py
──────────────────────────
Jarvis v2.0 — GitHub Monitoring (PRD Pillar 1)

Proactively monitors:
  - Failed CI/CD builds
  - PR reviews awaiting your response
  - Merge conflicts
  - Project milestone status

Setup:
  Set environment variable: GITHUB_TOKEN=your_personal_access_token
  Get token: github.com → Settings → Developer Settings → Personal Access Tokens
"""

from __future__ import annotations
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


GITHUB_API  = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


class GitHubMonitor:
    def __init__(self):
        self._token   = GITHUB_TOKEN
        self._enabled = bool(self._token)
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept"       : "application/vnd.github.v3+json",
            "User-Agent"   : "Jarvis-v2"
        }
        if self._enabled:
            print("[ GitHub ] ✓ GitHub monitoring active")
        else:
            print("[ GitHub ] GITHUB_TOKEN not set — GitHub monitoring disabled")
            print("           Set it: [System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN','your_token','User')")

    def _get(self, endpoint: str) -> dict | list | None:
        if not self._enabled:
            return None
        try:
            req = urllib.request.Request(
                f"{GITHUB_API}{endpoint}",
                headers=self._headers
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"[ GitHub ] HTTP {e.code}: {endpoint}")
            return None
        except Exception as e:
            print(f"[ GitHub ] Error: {e}")
            return None

    def get_notifications(self) -> list[dict]:
        """Get unread GitHub notifications."""
        data = self._get("/notifications?all=false&participating=true")
        if not data:
            return []

        alerts = []
        for notif in data[:10]:
            reason  = notif.get("reason", "")
            subject = notif.get("subject", {})
            repo    = notif.get("repository", {}).get("full_name", "")

            alerts.append({
                "type"  : subject.get("type", ""),
                "title" : subject.get("title", ""),
                "repo"  : repo,
                "reason": reason,
            })
        return alerts

    def get_pr_status(self, owner: str, repo: str) -> list[dict]:
        """Get open PRs for a repository."""
        data = self._get(f"/repos/{owner}/{repo}/pulls?state=open")
        if not data:
            return []

        return [
            {
                "number"    : pr.get("number"),
                "title"     : pr.get("title"),
                "author"    : pr.get("user", {}).get("login"),
                "mergeable" : pr.get("mergeable"),
                "created_at": pr.get("created_at"),
            }
            for pr in data[:5]
        ]

    def get_repo_status(self, owner: str, repo: str) -> dict:
        """Get latest commit + CI status for a repo."""
        commits = self._get(f"/repos/{owner}/{repo}/commits?per_page=1")
        if not commits or not isinstance(commits, list):
            return {"summary": "Could not fetch repo status"}

        latest       = commits[0]
        sha          = latest.get("sha", "")[:7]
        message      = latest.get("commit", {}).get("message", "")[:60]
        author       = latest.get("commit", {}).get("author", {}).get("name", "")
        commit_time  = latest.get("commit", {}).get("author", {}).get("date", "")

        # Check CI status
        ci_data = self._get(f"/repos/{owner}/{repo}/commits/{latest.get('sha','')}/check-runs")
        ci_status = "unknown"
        if ci_data and isinstance(ci_data, dict):
            runs = ci_data.get("check_runs", [])
            if runs:
                conclusions = [r.get("conclusion") for r in runs if r.get("conclusion")]
                if "failure" in conclusions:
                    ci_status = "FAILING"
                elif all(c == "success" for c in conclusions):
                    ci_status = "PASSING"
                else:
                    ci_status = "IN PROGRESS"

        return {
            "sha"       : sha,
            "message"   : message,
            "author"    : author,
            "ci_status" : ci_status,
            "summary"   : f"Latest commit by {author}: {message}. CI: {ci_status}."
        }

    def get_urgent_alerts(self) -> list[str]:
        """
        Pillar 1: Get all urgent GitHub alerts for proactive notification.
        Returns list of alert strings to speak.
        """
        if not self._enabled:
            return []

        alerts  = []
        notifs  = self.get_notifications()

        for n in notifs:
            if n["reason"] in ("review_requested", "mention"):
                alerts.append(
                    f"GitHub: You have a {n['reason'].replace('_',' ')} "
                    f"on {n['title'][:40]} in {n['repo']}."
                )

        return alerts[:3]  # max 3 alerts at once

    @property
    def is_connected(self) -> bool:
        return self._enabled