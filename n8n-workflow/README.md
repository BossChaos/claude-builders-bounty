# n8n + Claude Weekly Dev Summary Workflow

Automated weekly GitHub activity summary powered by n8n and Claude AI. Delivers to Discord every Friday at 5pm.

## Features

- 📅 **Automated Schedule** - Runs every Friday at 5pm
- 🐙 **GitHub Integration** - Fetches commits, closed issues, and merged PRs
- 🤖 **AI-Powered** - Claude generates narrative summary
- 💬 **Discord Delivery** - Posts formatted summary to your Discord channel

## Prerequisites

- n8n instance (self-hosted or cloud)
- GitHub account with repo access
- Anthropic API key (Claude)
- Discord webhook URL

## 5-Step Setup

### Step 1: Import Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Add Workflow**
3. Click the three dots menu → **Import from File**
4. Select `workflow.json`
5. Save the workflow (do not activate yet)

### Step 2: Configure GitHub Credentials

1. In n8n, go to **Credentials** → **Add Credential**
2. Select **GitHub API**
3. Enter your GitHub Personal Access Token (classic)
   - Token needs: `repo` scope
   - Create at: https://github.com/settings/tokens
4. Name it `GitHub API` (must match workflow reference)
5. Save credentials

### Step 3: Configure Anthropic API Credentials

1. In n8n, go to **Credentials** → **Add Credential**
2. Select **HTTP Header Auth**
3. Configure:
   - **Name**: `Anthropic API`
   - **Header Name**: `x-api-key`
   - **Header Value**: `sk-ant-api03-...` (your Anthropic API key)
4. Save credentials
5. Get your API key at: https://console.anthropic.com/settings/keys

### Step 4: Set Environment Variables

In n8n workflow settings, add these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO_OWNER` | GitHub username/org | `claude-builders-bounty` |
| `GITHUB_REPO_NAME` | Repository name | `claude-builders-bounty` |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook | `https://discord.com/api/webhooks/...` |

**To get Discord webhook:**
1. Open Discord channel settings
2. Go to **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Copy the webhook URL

### Step 5: Activate and Test

1. Click **Activate** toggle in workflow (top right)
2. Click **Execute Workflow** to test immediately
3. Check Discord for the summary message
4. Verify schedule: Next run shows Friday 5pm

## Output Example

```
📊 Weekly Dev Summary

🎉 Great week! Here's what happened:

**Commits (23):**
- feat: Add n8n workflow automation by @BossChaos
- fix: Discord webhook payload format by @contributor
- docs: Update README with setup steps by @BossChaos

**Closed Issues (5):**
- #42: Add weekly summary workflow by @BossChaos
- #41: Fix GitHub API rate limiting by @contributor

**Merged PRs (8):**
- #38: Feature: Claude integration by @BossChaos
- #37: Fix: Discord formatting by @contributor

Total: 36 activities this week! 🚀
```

## Troubleshooting

### No data in summary
- Check GitHub credentials have `repo` scope
- Verify repo owner/name in environment variables
- Ensure there was activity in the last 7 days

### Claude API error
- Verify Anthropic API key is valid
- Check credit balance at https://console.anthropic.com
- Ensure `x-api-key` header is set correctly

### Discord not receiving
- Test webhook URL with curl:
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    -d '{"content":"test"}' \
    YOUR_WEBHOOK_URL
  ```
- Check webhook hasn't been deleted in Discord

### Schedule not running
- Verify workflow is **Activated** (green toggle)
- Check n8n timezone settings (should match your expected 5pm)
- Review n8n execution logs for errors

## Customization

### Change schedule
Edit the **Schedule Trigger** node:
- `dayOfWeek`: 0-6 (0=Sunday, 5=Friday)
- `hours`: 0-23 (24h format)
- `minutes`: 0-59

### Change Claude model
Edit the **Generate Summary with Claude** node:
- Update `model` parameter (e.g., `claude-3-5-sonnet-20241022`)

### Custom summary prompt
Edit the `messages` parameter in Claude node to change the summary style.

## License

MIT - Free to use and modify
