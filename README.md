# Copilot Usage Tracker

This project tracks GitHub Copilot "Premium Request" usage and compares it against a planned linear growth target based on actual workdays. It is specifically designed for tracking newer Copilot tiers that use a monthly quota for advanced models.

## Features

- **Daily Automation**: A GitHub Action runs daily to fetch your latest billing data.
- **Dynamic Quota Detection**: Automatically detects your monthly usage limit (e.g., 300 or 1000 requests) directly from the GitHub API.
- **Per-Model Breakdown**: Tracks and visualizes usage for different models (Claude, Gemini, GPT) in a stacked bar chart.
- **Smart Holiday Logic**: Automatically fetches official holiday data to calculate a realistic linear target (Planned vs. Actual).
- **Modern Dashboard**: A minimalist, high-performance dashboard built with Chart.js, featuring historical browsing and browser-native localization.

## How it Works

1. **Monthly Tracking**: Data is calculated and segmented by month. Each day's snapshot is stored in `data/YYYY/YYYY-MM.json`.
2. **Quota Logic**: The script calculates how many "working days" are in the current month using the `holiday-cn` API. It then builds a linear target line from the 1st to the last day of the month.
3. **Billing Integration**: Uses the GitHub Billing API (`/users/{username}/settings/billing/premium_request/usage`) to pull actual consumption data.

## Setup

1. **Fork/Clone**: Set up this repository.
2. **Configure Secrets**: 
   - Add two Secrets to that repository environment:
     - `API_TOKEN`: A Personal Access Token (PAT) with `read:user` or `billing:read` scope.
     - `API_USER`: Your GitHub username.
3. **Enable GitHub Pages**: Go to **Settings > Pages** and set the source to the `main` branch root.

## Development

## Data Structure

- **`data/latest.json`**: Pointer to the most recent month's data.
- **`data/YYYY/YYYY-MM.json`**: Monthly snapshot containing:
  - `planned`: Cumulative linear target for that date.
  - `actual`: Total monthly usage recorded on that date.
  - `models`: Dictionary of usage per model.

## Credits

- Holiday data provided by [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn).
- Visualized with [Chart.js](https://www.chartjs.org/).
