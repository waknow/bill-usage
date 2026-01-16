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

def get_next_run_time(cron_list):
    """
    Simpler version of cron next-run calculation for GitHub Actions crons.
    Supports fixed values, ranges (2-10), and lists (1,3,5).
    Assumes * * * * format for (min, hour, day, month, dow).
    """
    from datetime import datetime, timedelta
    
    def parse_part(part, max_val, min_val=0):
        if part == "*":
            return list(range(min_val, max_val + 1))
        res = []
        for segment in part.split(","):
            if "-" in segment:
                start, end = map(int, segment.split("-"))
                res.extend(range(start, end + 1))
            else:
                res.append(int(segment))
        return sorted(list(set(res)))

    now = datetime.utcnow()
    next_runs = []

    for cron in cron_list:
        try:
            parts = cron.split()
            if len(parts) < 2: continue
            
            mins = parse_part(parts[0], 59)
            hours = parse_part(parts[1], 23)
            
            # Simple approach: check the next 48 hours for a match
            for h_offset in range(48):
                candidate_base = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=h_offset)
                if candidate_base.hour in hours:
                    for m in mins:
                        candidate = candidate_base.replace(minute=m)
                        if candidate > now:
                            next_runs.append(candidate)
                            break
                    if next_runs and next_runs[-1].hour == candidate_base.hour:
                        break
        except: continue
    
    if not next_runs:
        return None
    return min(next_runs).isoformat() + "Z"

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
            raw_history = json.load(f)
            # Support both old and new format during migration
            if "data" in raw_history:
                history = raw_history["data"]
            else:
                history = raw_history
    else:
        history = {}

    # Merge data
    for date_str, val in planned.items():
        if date_str not in history:
            history[date_str] = {"planned": val, "actual": 0}
        else:
            history[date_str]["planned"] = val
            
    # Update with actual values (including model breakdown)
    last_update_ts = datetime.now().astimezone()
    last_update_str = last_update_ts.isoformat()
    last_actual = 0
    for date_str, usage_data in actual.items():
        if date_str in history:
            history[date_str]["actual"] = usage_data["total"]
            history[date_str]["models"] = usage_data["models"]
            history[date_str]["last_update"] = last_update_str
        else:
            history[date_str] = {
                "planned": 0, 
                "actual": usage_data["total"], 
                "models": usage_data["models"],
                "last_update": last_update_str
            }
        last_actual = usage_data["total"]

    # Sort by date
    sorted_history = dict(sorted(history.items()))

    # Extract all cron schedules from all workflow files
    all_crons = []
    try:
        workflow_dir = ".github/workflows"
        if os.path.exists(workflow_dir):
            import re
            for filename in os.listdir(workflow_dir):
                if filename.endswith(".yml") or filename.endswith(".yaml"):
                    with open(os.path.join(workflow_dir, filename), "r", encoding="utf-8") as f:
                        content = f.read()
                        all_crons.extend(re.findall(r"cron:\s*'([^']+)'", content))
    except Exception as e:
        print(f"Warning: Could not parse workflow crons: {e}")

    next_run_iso = get_next_run_time(all_crons)

    # Prepare final JSON structure
    output_data = {
        "last_updated": last_update_str,
        "last_actual": last_actual,
        "data": sorted_history
    }

    # Ensure data directory and year directory exist
    os.makedirs(year_dir, exist_ok=True)
    with open(data_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Data for {month_str} updated in {data_file}")
    
    # Update latest pointer for UI
    with open("data/latest.json", "w") as f:
        json.dump({
            "year": year_str, 
            "month": month_str,
            "last_update": datetime.now().astimezone().isoformat(),
            "next_run": next_run_iso,
            "crons": list(set(all_crons)) # Just for record
        }, f, indent=2)

if __name__ == "__main__":
    main()
