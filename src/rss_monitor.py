import feedparser
import subprocess
import os
import json
from datetime import datetime

# Configuration
STANDFM_RSS_URL = "https://stand.fm/rss/5fba3d73c64654659098efa4"
VOICY_CHANNEL_URL = "https://voicy.jp/channel/821320"  # User's Voicy channel

# Determine paths relative to this script's location
# __file__ is the path to the current script (rss_monitor.py)
# src_dir is C:\Users\owner\CascadeProjects\standfm-voicy-automation\src
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# Determine project root: Use GITHUB_WORKSPACE if in GitHub Actions, otherwise derive from script location.
if os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("GITHUB_WORKSPACE"):
    PROJECT_ROOT = os.environ["GITHUB_WORKSPACE"]
    print(f"INFO: Running in GitHub Actions. PROJECT_ROOT set to GITHUB_WORKSPACE: {PROJECT_ROOT}")
else:
    # project_root is C:\Users\owner\CascadeProjects\standfm-voicy-automation
    PROJECT_ROOT = os.path.dirname(SRC_DIR)
    print(f"INFO: Running locally. PROJECT_ROOT derived as: {PROJECT_ROOT}")

VOICY_SCRAPER_SCRIPT_PATH = os.path.join(SRC_DIR, "voicy_scraper.py")
STATE_FILE_PATH = os.path.join(PROJECT_ROOT, "rss_monitor_state.json")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "rss_monitor_log.txt")

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}\n"
    # Print to console for immediate feedback if run manually
    print(full_message.strip())
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(full_message)

def load_last_processed_guid():
    if os.path.exists(STATE_FILE_PATH):
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get("last_processed_guid")
        except json.JSONDecodeError:
            log_message(f"Error: Could not decode JSON from state file: {STATE_FILE_PATH}. Will treat as no last processed GUID.")
            return None
        except Exception as e:
            log_message(f"Error loading state file {STATE_FILE_PATH}: {e}. Will treat as no last processed GUID.")
            return None
    return None

def save_last_processed_guid(guid):
    try:
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_processed_guid": guid}, f, indent=2)
        log_message(f"Successfully saved last processed GUID: {guid} to {STATE_FILE_PATH}")
    except Exception as e:
        log_message(f"Error saving state file {STATE_FILE_PATH}: {e}")

def run_voicy_scraper():
    log_message(f"Attempting to run Voicy scraper for channel: {VOICY_CHANNEL_URL}")
    try:
        env = os.environ.copy()
        env["TEST_VOICY_CHANNEL_URL"] = VOICY_CHANNEL_URL
        # Ensure PYTHONIOENCODING is set for the subprocess as well, if needed for voicy_scraper.py
        env["PYTHONIOENCODING"] = "utf-8"

        log_message(f"Running command: python {VOICY_SCRAPER_SCRIPT_PATH} from CWD: {PROJECT_ROOT}")
        process = subprocess.Popen(
            ["python", VOICY_SCRAPER_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=env,
            cwd=PROJECT_ROOT  # Run voicy_scraper.py from the project root
        )
        stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout

        if process.returncode == 0:
            log_message("Voicy scraper ran successfully.")
        else:
            log_message(f"Voicy scraper failed with exit code {process.returncode}.")
        
        if stdout:
            log_message(f"Voicy scraper STDOUT:\n{stdout.strip()}")
        if stderr:
            log_message(f"Voicy scraper STDERR:\n{stderr.strip()}")

        # Check the main log file of the scraper for confirmation
        scraper_main_log = os.path.join(PROJECT_ROOT, "scraper_run_log.txt")
        if os.path.exists(scraper_main_log):
            with open(scraper_main_log, "r", encoding="utf-8") as f_log:
                log_message(f"Content of {scraper_main_log} after run:\n{f_log.read().strip()}")
        else:
            log_message(f"{scraper_main_log} not found after scraper run.")

    except subprocess.TimeoutExpired:
        log_message("Voicy scraper timed out after 5 minutes.")
    except Exception as e:
        log_message(f"An error occurred while running Voicy scraper: {e}")

def main():
    log_message("--- RSS Monitor Started ---")

    last_processed_guid = load_last_processed_guid()
    log_message(f"Last processed GUID from state file: {last_processed_guid}")

    try:
        log_message(f"Fetching RSS feed from: {STANDFM_RSS_URL}")
        feed = feedparser.parse(STANDFM_RSS_URL)
    except Exception as e:
        log_message(f"Error fetching or parsing RSS feed: {e}")
        log_message("--- RSS Monitor Finished (Error) ---")
        return

    if feed.bozo:
        # feed.bozo is true if the feed is not well-formed XML
        # feed.bozo_exception contains the exception that feedparser raised
        log_message(f"Warning: RSS feed may be malformed. Reason: {feed.bozo_exception}")
        # Depending on the severity, you might want to stop or try to proceed

    if not feed.entries:
        log_message("No entries found in RSS feed.")
        log_message("--- RSS Monitor Finished ---")
        return

    # Entries are usually sorted newest first by feedparser if not specified by the feed itself
    latest_entry = feed.entries[0]
    latest_guid = latest_entry.get("guid")
    latest_title = latest_entry.get("title", "(No Title)")
    latest_pubdate = latest_entry.get("published", latest_entry.get("updated", "(No Date)"))

    log_message(f"Latest entry in RSS: GUID='{latest_guid}', Title='{latest_title}', PubDate='{latest_pubdate}'")

    if latest_guid:
        if latest_guid != last_processed_guid:
            log_message(f"New episode detected! GUID: {latest_guid} (Title: {latest_title}). Previous GUID was: {last_processed_guid}.")
            run_voicy_scraper()
            save_last_processed_guid(latest_guid) # Save new GUID only after successful processing or attempt
        else:
            log_message("No new episode. Latest GUID matches the last processed GUID.")
    else:
        log_message("Error: Could not find GUID for the latest entry in the RSS feed. Cannot determine if new.")

    log_message("--- RSS Monitor Finished ---")

if __name__ == "__main__":
    main()
