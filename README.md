# Copilot Usage Tracker

> **Note**: This project is a pure product of **vibe code**.

This project tracks GitHub Copilot "Premium Request" usage and compares it against a planned linear growth target based on actual workdays. It is specifically designed for tracking newer Copilot tiers that use a monthly quota for advanced models.

## Features

- **Daily Automation**: A GitHub Action runs daily to fetch your latest billing data.
- **Quota Management**: Currently uses a default monthly limit (e.g., 300) to calculate targets. *Note: Dynamic detection from API is a planned optimization.*
- **Intelligent Visualization**:
  - **Stacked Bar Chart**: Visualizes usage breakdown for different models (Claude, Gemini, GPT).
  - **Efficiency Background**: A smart area background that highlights "Over" (Warm/Red) or "Under" (Cold/Blue) usage relative to the daily plan.
- **Smart Holiday Logic**: Automatically fetches official holiday data to calculate a realistic linear target (Planned vs. Actual).
- **Modern Dashboard**: A minimalist dashboard built with Chart.js, featuring responsive design and browser-native localization.

## How it Works

1. **Monthly Tracking**: Data is calculated and segmented by month. Each day's snapshot is stored in `data/YYYY/YYYY-MM.json`.
2. **Quota Logic**: The script calculates how many "working days" are in the current month using the [holiday-cn](https://github.com/NateScarlet/holiday-cn) API. It then builds a linear target line from the 1st to the last day of the month.
3. **Billing Integration**: Uses the GitHub Billing API (`/users/{username}/settings/billing/premium_request/usage`) to pull actual consumption data.
4. **Efficiency Metrics**: The dashboard calculates usage efficiency in real-time, helping you stay within your monthly budget.

## Setup

1. **Fork/Clone**: Set up this repository.
2. **Configure Secrets & Variables**: 
   - Add the following **Repository Secret**:
     - `API_TOKEN`: A Personal Access Token (PAT) with `read:user` or `billing:read` scope.
   - Add the following **Repository Variables**:
     - `API_USER`: Your GitHub username.
     - `COPILOT_QUOTA` (Optional): Your monthly usage limit (defaults to `300`).
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
