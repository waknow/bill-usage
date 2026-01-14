import json
import os
from datetime import datetime, timedelta
import requests

def is_workday(date: datetime, holidays_config):
    date_str = date.strftime("%Y-%m-%d")
    year = str(date.year)
    
    if year in holidays_config:
        year_config = holidays_config[year]
        # Handle new format: list of days with isOffDay
        if "days" in year_config:
            for day in year_config["days"]:
                if day["date"] == date_str:
                    return not day["isOffDay"]
    
    # If not defined, Saturday (5) and Sunday (6) are holidays
    return date.weekday() < 5

def fetch_holiday_config(year):
    url = f"https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
    try:
        print(f"Fetching holidays for {year} from {url}...")
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Failed to fetch holidays for {year}: {e}")
        return None

def calculate_planned_usage(settings, holidays_config, start_date, end_date):
    total_target = settings["total_target"]
    
    workdays = []
    curr = start_date
    while curr <= end_date:
        if is_workday(curr, holidays_config):
            workdays.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    
    if not workdays:
        return {}
    
    daily_increment = total_target / len(workdays)
    planned = {}
    cumulative = 0
    
    curr = start_date
    while curr <= end_date:
        date_str = curr.strftime("%Y-%m-%d")
        if is_workday(curr, holidays_config):
            cumulative += daily_increment
        planned[date_str] = round(cumulative, 2)
        curr += timedelta(days=1)
        
    return planned

def fetch_actual_usage(settings):
    # This is a placeholder for the GitHub API call.
    # Note: The GITHUB_TOKEN needs 'read:org' or 'manage_billing:enterprise' permissions.
    # For Copilot usage, see: https://docs.github.com/en/rest/copilot/copilot-usage
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not found, skipping actual usage fetch.")
        return {}

    org = settings.get("github_org")
    enterprise = settings.get("github_enterprise")
    
    # Example for Org-level Copilot usage
    # If using Enterprise, the URL would be:
    # f"https://api.github.com/enterprises/{enterprise}/copilot/usage"
    url = f"https://api.github.com/orgs/{org}/copilot/usage"
    if enterprise and enterprise != "YOUR_ENTERPRISE_SLUG":
        url = f"https://api.github.com/enterprises/{enterprise}/copilot/usage"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        print(f"Fetching usage from {url}...")
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            print("API returned 404. Check your ORG_NAME or ENTERPRISE_SLUG.")
            return {}
        response.raise_for_status()
        data = response.json()
        
        actual = {}
        for day in data:
            date_str = day["day"]
            # GitHub returns daily stats. We might want cumulative or daily.
            # The user asked for "comparison", usually cumulative is better for "planned vs actual".
            # But the API returns daily. Let's store daily and we can sum in the UI or here.
            # For now, let's store the 'total_suggestions_count' as a sample metric.
            actual[date_str] = day.get("total_suggestions_count", 0) 
        return actual
    except Exception as e:
        print(f"Error fetching actual usage: {e}")
        return {}

def main():
    with open("config/settings.json", "r") as f:
        settings = json.load(f)
    
    # Calculate for the current month
    today = datetime.now()
    start_date = today.replace(day=1)
    # Get last day of month
    if today.month == 12:
        end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    holidays_config = {}
    config = fetch_holiday_config(today.year)
    if config:
        holidays_config[str(today.year)] = config
        
    planned = calculate_planned_usage(settings, holidays_config, start_date, end_date)
    actual = fetch_actual_usage(settings)
    
    # Data per month
    month_str = today.strftime("%Y-%m")
    data_file = f"data/usage_{month_str}.json"
    
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            history = json.load(f)
    else:
        history = {}

    # Merge data
    # Calculate cumulative actuals from daily values for this month
    sorted_actual_dates = sorted([d for d in actual.keys() if d.startswith(month_str)])
    cumulative_actual = 0
    actual_cumulative_map = {}
    
    for date_str in sorted_actual_dates:
        cumulative_actual += actual[date_str]
        actual_cumulative_map[date_str] = cumulative_actual

    for date_str, val in planned.items():
        if date_str not in history:
            history[date_str] = {"planned": val, "actual": 0}
        else:
            history[date_str]["planned"] = val
            
    for date_str, val in actual_cumulative_map.items():
        if date_str in history:
            history[date_str]["actual"] = val
        else:
            history[date_str] = {"planned": 0, "actual": val}

    # Sort by date
    sorted_history = dict(sorted(history.items()))

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    with open(data_file, "w") as f:
        json.dump(sorted_history, f, indent=2)
    print(f"Data for {month_str} updated in {data_file}")

if __name__ == "__main__":
    main()
