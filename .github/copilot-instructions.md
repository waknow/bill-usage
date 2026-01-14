# Copilot Usage Tracker - AI Instructions

## Architecture Overview
- **Data Flow**: Python script (`scripts/update_usage.py`) fetches billing data -> Hierarchical storage (`data/YYYY/YYYY-MM.json`) -> Dashboard (`index.html`) visualizes via Chart.js.
- **Quota Logic**: Monthly quotas are extracted from the GitHub Billing API. Target lines are calculated based on *workdays* fetched from the `holiday-cn` API.
- **Entry Points**: 
  - `data/latest.json`: Pointer for the frontend to find the most recent month.
  - `scripts/update_usage.py`: Main logic for data aggregation.

## Codebase Patterns
- **Data Storage**: Always use the `data/{year}/{year-month}.json` structure. Values are cumulative for the month.
- **Holiday Integration**: Use the `is_workday` check in Python to adjust the slope of the `planned` linear target.
- **UI Styling**: Minimalist, Inter-font based, indigo/gray palette matching GitHub's look-and-feel.
- **Chart.js Implementation**:
  - Uses a hidden `yEfficiency` scale for the area background.
  - Background areas are clipped to the current date to avoid "predicting" efficiency.
  - Stacked bars for model breakdown, single line for the daily target.

## Developer Workflows
- **Running Locally**: Requires `API_TOKEN` and `API_USER` environment variables.
- **Adding New Models**: The script automatically detects new model names from the API response (`premium_request_usage`). No hardcoding required for specific models like "o1-preview".
- **Debugging**: Inspect the JSON outputs in `data/` to verify calibration between `actual` (total) and `models` (breakdown).

## Integration Points
- **GitHub API**: Targeting `/users/{username}/settings/billing/premium_request/usage`.
- **Holidays**: [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn) raw content (JSON).
