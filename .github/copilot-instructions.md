# Copilot Usage Tracker - AI Instructions

## Project Context
- **Nature**: This project is a pure product of **vibe code**.

## Architecture Overview
- **Data Flow**: Python script (`scripts/update_usage.py`) fetches billing data -> Hierarchical storage (`data/YYYY/YYYY-MM.json`) -> Dashboard (`index.html`) visualizes via Chart.js.
- **Quota Logic**: Uses a default monthly quota (300) as the API limit extraction is currently unreliable. Target lines are calculated based on *workdays* fetched from the `holiday-cn` API.
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
  - Stacked bars for model breakdown, single line for daily target.

## Developer Workflows
- **Secrets**: Uses repository level secrets (`API_TOKEN`, `API_USER`) instead of environment-specific ones.
- **Running Locally**: Requires `API_TOKEN` and `API_USER` environment variables.
- **Adding New Models**: The script automatically detects new model names from the API response (`usageItems`). No hardcoding required.
- **Debugging**: Inspect JSON outputs in `data/` to verify calibration between `actual` (total) and `models` (breakdown).

## Integration Points
- **GitHub API**: Targeting `/users/{username}/settings/billing/premium_request/usage`.
- **Holidays**: [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn) raw content (JSON).
