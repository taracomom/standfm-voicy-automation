import os
import json
import feedparser
import time
from datetime import datetime, timezone

# Path to the file storing the last checked episode's GUID
# Assumes this script is in 'src/', and 'data/' is a sibling directory to 'src/'
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
LAST_CHECK_FILE = os.path.join(DATA_DIR, 'last_check.json')

def _get_guid(entry):
    """Extracts a unique identifier from an RSS entry."""
    return entry.get('id') or entry.get('guid')

def _extract_episode_data(entry):
    """Extracts relevant data from an RSS feed entry."""
    guid = _get_guid(entry)
    if not guid:
        return None

    title = entry.get('title', 'N/A')
    url = entry.get('link', '')
    
    published_iso = None
    published_parsed = entry.get('published_parsed')
    if published_parsed:
        try:
            # Format the time.struct_time (UTC as per feedparser) to ISO 8601 string
            published_iso = time.strftime('%Y-%m-%dT%H:%M:%SZ', published_parsed)
        except TypeError:
            # Fallback or log error if necessary
            # print(f"Warning: Could not parse published_date for entry GUID {guid}")
            published_iso = None

    audio_url = None
    if hasattr(entry, 'enclosures'):
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('audio/'):
                audio_url = enclosure.href
                break
    
    return {
        'title': title,
        'url': url,
        'published': published_iso,
        'guid': guid,
        'audio_url': audio_url
    }

def _load_last_check():
    """Loads the last processed episode GUID from the JSON file."""
    try:
        if not os.path.exists(LAST_CHECK_FILE):
            return None 
        with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('last_processed_episode_guid')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def _save_last_check(new_guid):
    """Saves the new latest processed episode GUID and timestamp to the JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True) # Ensure data directory exists
    data = {
        'last_processed_episode_guid': new_guid,
        'last_checked_timestamp': datetime.now(timezone.utc).isoformat()
    }
    with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def check_new_episodes():
    """
    Checks the StandFM RSS feed for new episodes published since the last check.

    Returns:
        list: A list of dictionaries, each representing a new episode.
              Episodes are sorted oldest-new to newest-new.
              Returns an empty list if no new episodes or an error occurs.
    """
    rss_url = os.getenv("STANDFM_RSS_URL")
    if not rss_url:
        # print("Error: STANDFM_RSS_URL environment variable not set.")
        return []

    feed = feedparser.parse(rss_url)

    if feed.bozo:
        # print(f"Warning: RSS feed parsing may have issues. Bozo reason: {feed.bozo_exception}")
        pass # Depending on severity, might still try to process or return []
    
    if not feed.entries:
        return []

    last_known_guid = _load_last_check()
    
    newly_fetched_episodes_data = [] # Stores episode data dicts, newest from feed first

    for entry in feed.entries: # feed.entries are usually newest first
        current_entry_guid = _get_guid(entry)
        if not current_entry_guid:
            continue # Skip entries without a GUID

        if current_entry_guid == last_known_guid:
            break 
        
        episode_data = _extract_episode_data(entry)
        if episode_data:
            newly_fetched_episodes_data.append(episode_data)

    if not newly_fetched_episodes_data:
        return []

    actual_new_episodes_to_process = []
    guid_to_save_as_last_processed = None

    if last_known_guid is None:
        # First run: process only the very latest episode from the feed.
        # The latest is the first one in newly_fetched_episodes_data.
        actual_new_episodes_to_process = [newly_fetched_episodes_data[0]]
        guid_to_save_as_last_processed = newly_fetched_episodes_data[0]['guid']
    else:
        # Standard run: process all episodes found that are newer than last_known_guid.
        # Reverse to get them in chronological order (oldest new first).
        newly_fetched_episodes_data.reverse() 
        actual_new_episodes_to_process = newly_fetched_episodes_data
        # GUID to save is the GUID of the newest episode identified in this batch.
        # After reversing, it's the last element if list is not empty.
        if actual_new_episodes_to_process:
             guid_to_save_as_last_processed = actual_new_episodes_to_process[-1]['guid']

    if guid_to_save_as_last_processed:
        _save_last_check(guid_to_save_as_last_processed)
    
    return actual_new_episodes_to_process

if __name__ == '__main__':
    # This block is for testing the module directly.
    # It requires a .env file in the project root or environment variables set.
    # Example .env content:
    # STANDFM_RSS_URL=https://your-standfm-rss-feed-url-here

    # Load environment variables from .env file for local testing
    # Ensure python-dotenv is installed: pip install python-dotenv
    try:
        from dotenv import load_dotenv
        # Construct path to .env file, assuming it's in the parent directory of 'src'
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            print(f"Loaded .env file from {dotenv_path}")
        else:
            print(f".env file not found at {dotenv_path}. Ensure STANDFM_RSS_URL is set in your environment.")
    except ImportError:
        print("python-dotenv not installed. Please install it to load .env file for local testing.")
        print("Alternatively, ensure STANDFM_RSS_URL is set in your environment.")

    print(f"\n--- Running rss_checker.py test --- ")
    print(f"Using last_check.json at: {LAST_CHECK_FILE}")

    # Optional: For a clean test, you might want to remove last_check.json
    # if os.path.exists(LAST_CHECK_FILE):
    #     print(f"Temporarily removing {LAST_CHECK_FILE} for a first-run test.")
    #     os.remove(LAST_CHECK_FILE)

    # Optional: To simulate a specific last known GUID for testing subsequent runs
    # _save_last_check("some_guid_that_is_not_the_latest_in_your_feed")
    # _save_last_check("a_guid_of_an_episode_further_down_your_feed")

    new_episodes = check_new_episodes()

    if new_episodes:
        print(f"\nFound {len(new_episodes)} new episodes:")
        for i, ep in enumerate(new_episodes):
            print(f"\nEpisode {i+1}:")
            print(f"  Title: {ep['title']}")
            print(f"  URL: {ep['url']}")
            print(f"  Published: {ep['published']}")
            print(f"  GUID: {ep['guid']}")
            print(f"  Audio URL: {ep['audio_url']}")
    else:
        rss_url_env = os.getenv("STANDFM_RSS_URL")
        if not rss_url_env:
            print("\nNo new episodes found (STANDFM_RSS_URL not set or empty feed).")
        else:
            print("\nNo new episodes found.")

    print(f"\n--- Contents of {LAST_CHECK_FILE} after check --- ")
    try:
        with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
            print(json.dumps(json.load(f), indent=2, ensure_ascii=False))
    except FileNotFoundError:
        print(f"{LAST_CHECK_FILE} not found (this is expected if no new episodes were processed and it was a first run or STANDFM_RSS_URL was not set).")
    print("--- rss_checker.py test finished ---")
