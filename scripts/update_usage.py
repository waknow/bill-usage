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
    # Get user billing premium request usage report
    # https://docs.github.com/en/rest/billing/usage?apiVersion=2022-11-28#get-billing-premium-request-usage-report-for-a-user
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not found, skipping actual usage fetch.")
        return {}, None

    username = os.getenv("GITHUB_USER") or settings.get("github_user")
    if not username or username == "YOUR_GITHUB_USERNAME":
        print("GITHUB_USER environment variable or settings.github_user not set.")
        return {}, None

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
        
        # Try to get the limit/quota from the response if available
        fetched_limit = data.get("limit") or data.get("quota")
        
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
        return {today_str: {"total": round(total_month_usage, 2), "models": model_stats}}, fetched_limit
    except Exception as e:
        print(f"Error fetching actual usage: {e}")
        return {}, None

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
        
    actual, fetched_limit = fetch_actual_usage(settings)
    
    if fetched_limit:
        print(f"Fetched limit from API: {fetched_limit}")
        settings["total_target"] = fetched_limit
    elif "total_target" not in settings:
        settings["total_target"] = 300 # Default if everything else fails
        
    planned = calculate_planned_usage(settings, holidays_config, start_date, end_date)
    
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
