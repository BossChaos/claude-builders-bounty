#!/usr/bin/env python3
"""
Claude Code PR Review Agent

Analyzes pull request diffs and generates structured review comments.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --diff diff.txt --repo owner/repo

Features:
- Fetches PR diff from GitHub API
- Analyzes code changes with Claude API
- Generates structured markdown review
- Posts comment to PR (optional)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from typing import Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
CLAUDE_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = 'claude-sonnet-4-20250514'

# =============================================================================
# GITHUB API
# =============================================================================

def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR details and diff from GitHub API."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    # Fetch PR details
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        pr_url,
        headers={
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+diff',
            'User-Agent': 'Claude-Review-Agent'
        }
    )
    
    with urllib.request.urlopen(req) as response:
        diff_text = response.read().decode('utf-8')
    
    # Fetch PR metadata
    req = urllib.request.Request(
        pr_url,
        headers={
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'User-Agent': 'Claude-Review-Agent'
        }
    )
    
    with urllib.request.urlopen(req) as response:
        pr_data = json.loads(response.read().decode('utf-8'))
    
    return {
        'diff': diff_text,
        'title': pr_data.get('title', ''),
        'body': pr_data.get('body', ''),
        'author': pr_data.get('user', {}).get('login', ''),
        'files_changed': pr_data.get('changed_files', 0),
        'additions': pr_data.get('additions', 0),
        'deletions': pr_data.get('deletions', 0),
    }

def post_pr_comment(owner: str, repo: str, pr_number: int, comment: str) -> dict:
    """Post comment to PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    
    data = {'body': comment}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'Claude-Review-Agent'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

# =============================================================================
# CLAUDE API
# =============================================================================

def analyze_with_claude(pr_data: dict, owner: str, repo: str, pr_number: int) -> str:
    """Send PR diff to Claude for analysis."""
    if not CLAUDE_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    system_prompt = """You are an expert code reviewer. Analyze the pull request diff and provide a structured, constructive review.

Your review should:
1. Start with a brief summary of what changes were made
2. Highlight positive aspects (good practices, clean code, etc.)
3. Identify potential issues (bugs, security concerns, performance issues)
4. Suggest improvements (code quality, readability, best practices)
5. End with a clear recommendation (LGTM, needs changes, or requires discussion)

Be specific, reference line numbers when possible, and maintain a helpful, encouraging tone."""

    user_prompt = f"""Please review this pull request:

**Repository:** {owner}/{repo}
**PR #{pr_number}**
**Title:** {pr_data['title']}
**Author:** {pr_data['author']}

**Changes:**
- Files changed: {pr_data['files_changed']}
- Additions: {pr_data['additions']}
- Deletions: {pr_data['deletions']}

**PR Description:**
{pr_data['body'] or 'No description provided.'}

**Diff:**
```diff
{pr_data['diff'][:50000]}  # Truncate if too large
```

Please provide a structured code review in markdown format."""

    url = "https://api.anthropic.com/v1/messages"
    data = {
        'model': CLAUDE_MODEL,
        'max_tokens': 4096,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_prompt}]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {CLAUDE_API_KEY}',
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01',
            'User-Agent': 'Claude-Review-Agent'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
    
    return result['content'][0]['text']

# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def format_review_comment(review: str, pr_data: dict, owner: str, repo: str, pr_number: int) -> str:
    """Format the review comment for posting."""
    header = f"""## 🤖 Automated PR Review by Claude

**PR:** #{pr_number} - {pr_data['title']}
**Author:** @{pr_data['author']}
**Changes:** {pr_data['files_changed']} files, +{pr_data['additions']} -{pr_data['deletions']}

---

"""
    footer = f"""
---

*This review was generated automatically by Claude Code PR Review Agent.*
*To report issues or provide feedback, please open an issue.*
"""
    
    return header + review + footer

# =============================================================================
# CLI
# =============================================================================

def parse_github_url(url: str) -> tuple[str, str, int]:
    """Parse GitHub PR URL into owner, repo, pr_number."""
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, url)
    
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    
    return match.group(1), match.group(2), int(match.group(3))

def main():
    parser = argparse.ArgumentParser(
        description='Claude Code PR Review Agent - Automated code review for GitHub PRs'
    )
    parser.add_argument(
        '--pr',
        type=str,
        help='GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)'
    )
    parser.add_argument(
        '--diff',
        type=str,
        help='Path to diff file (alternative to --pr)'
    )
    parser.add_argument(
        '--repo',
        type=str,
        help='Repository in format owner/repo (required with --diff)'
    )
    parser.add_argument(
        '--post',
        action='store_true',
        help='Post review as comment on PR'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save review to file instead of posting'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.pr and not args.diff:
        parser.error("Either --pr or --diff is required")
    
    if args.diff and not args.repo:
        parser.error("--repo is required when using --diff")
    
    try:
        # Fetch or load diff
        if args.pr:
            owner, repo, pr_number = parse_github_url(args.pr)
            print(f"📥 Fetching PR #{pr_number} from {owner}/{repo}...")
            pr_data = fetch_pr_diff(owner, repo, pr_number)
        else:
            owner, repo = args.repo.split('/')
            pr_number = 0
            with open(args.diff, 'r') as f:
                diff_text = f.read()
            pr_data = {
                'diff': diff_text,
                'title': 'Manual diff review',
                'body': '',
                'author': 'unknown',
                'files_changed': diff_text.count('diff --git'),
                'additions': diff_text.count('\n+'),
                'deletions': diff_text.count('\n-'),
            }
        
        print(f"📊 Analyzing {pr_data['files_changed']} files ({pr_data['additions']} additions, {pr_data['deletions']} deletions)...")
        
        # Analyze with Claude
        print("🤖 Sending to Claude for analysis...")
        review = analyze_with_claude(pr_data, owner, repo, pr_number)
        
        # Format output
        formatted_review = format_review_comment(review, pr_data, owner, repo, pr_number)
        
        # Output
        if args.post and args.pr:
            print(f"📝 Posting review to PR #{pr_number}...")
            result = post_pr_comment(owner, repo, pr_number, formatted_review)
            print(f"✅ Review posted! {result['html_url']}")
        elif args.output:
            with open(args.output, 'w') as f:
                f.write(formatted_review)
            print(f"✅ Review saved to {args.output}")
        else:
            print("\n" + "=" * 80)
            print(formatted_review)
            print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
