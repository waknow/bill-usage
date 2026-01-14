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
        print(f"Warning: Failed to fetch holidays for {year}: {e}. Falling back to standard weekend logic.")
        return {}

def calculate_planned_usage(total_target, holidays_config, start_date, end_date):
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

def fetch_actual_usage():
    # Get user billing premium request usage report
    # https://docs.github.com/en/rest/billing/usage?apiVersion=2022-11-28#get-billing-premium-request-usage-report-for-a-user
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not found, skipping actual usage fetch.")
        return {}

    username = os.getenv("GITHUB_USER")
    if not username:
        print("GITHUB_USER environment variable not set.")
        return {}

    now = datetime.now()
    year = now.year
    month = now.month
    
    url = f"https://api.github.com/users/{username}/settings/billing/premium_request/usage?year={year}&month={month}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        print(f"Fetching usage from {url}...")
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            print(f"API returned 404 for user {username}. Ensure the token has 'Plan' user permissions (read).")
            return {}, None
        response.raise_for_status()
        data = response.json()
        
        total_month_usage = 0
        model_stats = {}
        if "usageItems" in data:
            for item in data["usageItems"]:
                qty = item.get("grossQuantity", 0)
                total_month_usage += qty
                model_name = item.get("model", "Unknown")
                model_stats[model_name] = round(model_stats.get(model_name, 0) + qty, 2)
        
        # Return today's date with the current month-to-date total and breakdown
        today_str = now.strftime("%Y-%m-%d")
        return {today_str: {"total": round(total_month_usage, 2), "models": model_stats}}
    except Exception as e:
        print(f"Error fetching actual usage: {e}")
        return {}

def main():
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
    holidays_config[str(today.year)] = config
        
    actual = fetch_actual_usage()
    
    # Get target from environment or default
    env_quota = os.getenv("COPILOT_QUOTA")
    try:
        total_target = float(env_quota) if env_quota else 300
        print(f"Using total_target: {total_target}")
    except ValueError:
        total_target = 300
        
    planned = calculate_planned_usage(total_target, holidays_config, start_date, end_date)
    
    # Data per month
    year_str = today.strftime("%Y")
    month_str = today.strftime("%Y-%m")
    year_dir = os.path.join("data", year_str)
    os.makedirs(year_dir, exist_ok=True)
    data_file = os.path.join(year_dir, f"{month_str}.json")
    
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            history = json.load(f)
    else:
        history = {}

    # Merge data
    for date_str, val in planned.items():
        if date_str not in history:
            history[date_str] = {"planned": val, "actual": 0}
        else:
            history[date_str]["planned"] = val
            
    # Update with actual values (including model breakdown)
    for date_str, usage_data in actual.items():
        if date_str in history:
            history[date_str]["actual"] = usage_data["total"]
            history[date_str]["models"] = usage_data["models"]
        else:
            history[date_str] = {
                "planned": 0, 
                "actual": usage_data["total"], 
                "models": usage_data["models"]
            }

    # Sort by date
    sorted_history = dict(sorted(history.items()))

    # Ensure data directory and year directory exist
    os.makedirs(year_dir, exist_ok=True)
    with open(data_file, "w") as f:
        json.dump(sorted_history, f, indent=2)
    print(f"Data for {month_str} updated in {data_file}")
    
    # Update latest pointer for UI
    with open("data/latest.json", "w") as f:
        json.dump({"year": year_str, "month": month_str}, f, indent=2)

if __name__ == "__main__":
    main()
