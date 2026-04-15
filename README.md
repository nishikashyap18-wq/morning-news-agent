# Morning News Digest

This repository includes a GitHub Actions workflow and Python script that generate a morning news digest and send it by email using Gmail SMTP.

## Files

- `.github/workflows/morning_news_digest.yml` - GitHub Actions workflow that runs every weekday at 7 AM Eastern / 12:00 UTC and can also be triggered manually.
- `news_agent.py` - Python script that uses the Anthropic SDK to search the web for the top 5 Business and Technology stories, generate an HTML email, and send it through Gmail SMTP.

## Setup

### 1. Get a Gmail App Password

1. Open your Google Account.
2. Go to `Security`.
3. Ensure `2-Step Verification` is enabled.
4. Under `App passwords`, create a new app password for `Mail` or a custom app.
5. Copy the generated app password.

### 2. Get an Anthropic API Key

1. Go to `https://console.anthropic.com`.
2. Create or sign in to your Anthropic account.
3. Generate a new API key.
4. Copy the API key.

### 3. Add GitHub Secrets

Add the following secrets in GitHub:

- `ANTHROPIC_API_KEY`
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`
- `RECIPIENT_EMAIL`

Go to your repository's `Settings` → `Secrets and variables` → `Actions` and create each secret.

### 4. Trigger the Workflow Manually

After the workflow is configured, you can trigger it manually from the repository's `Actions` tab, select `Morning News Digest`, and click `Run workflow`.

## Notes

- The workflow installs `anthropic` and `requests` before running `news_agent.py`.
- The script sends email through Gmail SMTP using `smtp.gmail.com` port `587` with STARTTLS.
- The subject line is `Your Morning Digest — {today's date}`.
- The workflow opts into Node.js 24 for GitHub JavaScript actions to avoid deprecation warnings on `actions/checkout@v4` and `actions/setup-python@v5`.
