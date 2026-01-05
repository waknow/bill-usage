# Copilot Usage Tracker

This project tracks GitHub Copilot (or other model) usage and compares it against a planned linear growth target based on actual workdays.

## Features

- **Daily Updates**: A GitHub Action runs every day to fetch usage data.
- **Planned Usage**: Calculated based on a total target and a list of holidays/workdays.
- **Visualization**: A GitHub Pages site to view the progress.

## Setup

1.  **Configure Settings**: Edit `config/settings.json` with your target and GitHub Org/Enterprise details.
2.  **Configure Holidays**: Edit `config/holidays.json` to mark holidays and makeup workdays for the year.
3.  **GitHub Token**: Ensure the GitHub Action has access to a token with `read:org` or `manage_billing:enterprise` permissions (depending on the API used). The default `GITHUB_TOKEN` might not have enough permissions for Copilot usage APIs; you might need a Personal Access Token (PAT) stored as a secret.
4.  **Enable GitHub Pages**: Go to repository settings and enable GitHub Pages, pointing to the root directory or `docs` folder.

## Data Structure

- `data/usage.json`: Contains the merged planned and actual usage data.

## Development

To run the update script locally:

```bash
export GITHUB_TOKEN=your_token
python scripts/update_usage.py
```
