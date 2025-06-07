import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
# webdriver_manager can be used to automatically manage ChromeDriver
# from webdriver_manager.chrome import ChromeDriverManager

# Voicy specific selector from the project plan
VOICY_EPISODE_SELECTOR = "a.story-item-content"

def get_latest_voicy_episode_url(voicy_channel_url: str) -> str | None:
    """
    Fetches the URL of the latest episode from a given Voicy channel page.

    Args:
        voicy_channel_url: The URL of the Voicy channel page.

    Returns:
        The URL of the latest episode as a string, or None if an error occurs
        or the episode cannot be found.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu") # Optional, sometimes helps in headless
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

    driver = None # Initialize driver to None
    # Define log file paths
    script_dir_for_log = os.path.dirname(os.path.abspath(__file__))
    project_root_for_log = os.path.dirname(script_dir_for_log)
    
    # Log path for ChromeDriver service logs
    chromedriver_service_log_path = os.path.join(project_root_for_log, "chromedriver.log")
    # Log path for this function's custom internal logs
    function_internal_log_path = os.path.join(project_root_for_log, "function_internal.log")

    # Open the dedicated log file for this function's custom messages
    with open(function_internal_log_path, "a", encoding="utf-8") as f_custom_log:
        print(f"\n--- Logging for get_latest_voicy_episode_url call ({time.strftime('%Y-%m-%d %H:%M:%S')}) --- ", flush=True, file=f_custom_log)
        print(f"Target Voicy Channel URL: {voicy_channel_url}", flush=True, file=f_custom_log)
        try:
            # Configure ChromeDriver path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            chromedriver_path = os.path.join(script_dir, "drivers", "chromedriver.exe")
            print(f"DEBUG: ChromeDriver executable path: {chromedriver_path}", flush=True, file=f_custom_log)
            print(f"DEBUG: ChromeDriver service log output will be configured to: {chromedriver_service_log_path}", flush=True, file=f_custom_log)

            if os.environ.get("GITHUB_ACTIONS") == "true":
                chromedriver_executable_path = "/usr/local/bin/chromedriver"
                print(f"INFO: Running in GitHub Actions, using ChromeDriver path: {chromedriver_executable_path}", flush=True, file=f_custom_log)
                if not os.path.exists(chromedriver_executable_path):
                    print(f"ERROR: ChromeDriver not found at {chromedriver_executable_path}! Checking /usr/local/bin:", flush=True, file=f_custom_log)
                    try:
                        if os.path.exists("/usr/local/bin"):
                            usr_local_bin_contents = os.listdir("/usr/local/bin")
                            print(f"Contents of /usr/local/bin: {usr_local_bin_contents}", flush=True, file=f_custom_log)
                        else:
                            print("/usr/local/bin directory does not exist.", flush=True, file=f_custom_log)
                    except Exception as e:
                        print(f"Could not list /usr/local/bin: {e}", flush=True, file=f_custom_log)
                service = ChromeService(
                    executable_path=chromedriver_executable_path,
                    log_output=chromedriver_service_log_path,
                    service_args=["--verbose"]
                )
            else:
                # Local setup
                print(f"INFO: Running locally, expecting ChromeDriver at {chromedriver_path}.", flush=True, file=f_custom_log)
                if not os.path.exists(chromedriver_path):
                    error_msg = f"ERROR: ChromeDriver not found at {chromedriver_path}\n"
                    print(error_msg.strip(), flush=True, file=f_custom_log) # Also print to console for local runs
                    return None
                service = ChromeService(
                    executable_path=chromedriver_path,
                    log_output=chromedriver_service_log_path, # Service logs to its own file
                    service_args=["--verbose"]
                )
            
            print("DEBUG: ChromeService object initialized.", flush=True, file=f_custom_log)
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("DEBUG: webdriver.Chrome initialized.", flush=True, file=f_custom_log)
            
            print(f"DEBUG: Attempting to driver.get URL: {voicy_channel_url}", flush=True, file=f_custom_log)
            driver.get(voicy_channel_url)
            print(f"DEBUG: driver.get call completed for URL: {voicy_channel_url}", flush=True, file=f_custom_log)

            wait = WebDriverWait(driver, 20) 
            print("DEBUG: WebDriverWait initialized. Waiting for element...", flush=True, file=f_custom_log)
            latest_episode_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, VOICY_EPISODE_SELECTOR))
            )
            print(f"DEBUG: Latest episode element found: {latest_episode_element is not None}", flush=True, file=f_custom_log)

            if latest_episode_element:
                episode_url = latest_episode_element.get_attribute('href')
                print(f"DEBUG: Episode URL found: {episode_url}", flush=True, file=f_custom_log)
                print(f"--- End of get_latest_voicy_episode_url call log (Success) ---", flush=True, file=f_custom_log)
                return episode_url 
            else:
                print(f"DEBUG: Could not find the latest episode element using selector: {VOICY_EPISODE_SELECTOR}", flush=True, file=f_custom_log)
                print(f"--- End of get_latest_voicy_episode_url call log (Element not found) ---", flush=True, file=f_custom_log)
                return None
        except Exception as e:
            print(f"ERROR: An exception occurred in get_latest_voicy_episode_url: {e}", flush=True, file=f_custom_log)
            # Also print to console for immediate visibility if the tool shows it
            print(f"ERROR in get_latest_voicy_episode_url (see {function_internal_log_path} for details): {e}", flush=True)
            print(f"--- End of get_latest_voicy_episode_url call log (Exception) ---", flush=True, file=f_custom_log)
            return None
        finally:
            if driver:
                print(f"DEBUG: Quitting webdriver.", flush=True, file=f_custom_log)
                driver.quit()
                print(f"DEBUG: Webdriver quit.", flush=True, file=f_custom_log)
            else:
                print(f"DEBUG: No webdriver instance to quit (driver was None or not initialized).", flush=True, file=f_custom_log)

if __name__ == '__main__':
    scraper_output_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scraper_run_log.txt")
    with open(scraper_output_log_path, "w", encoding="utf-8") as f_scraper_out:
        print("--- Running voicy_scraper.py test ---", flush=True, file=f_scraper_out)
        
        test_voicy_channel_url = os.getenv("TEST_VOICY_CHANNEL_URL", "https://voicy.jp/channel/1343")

        if test_voicy_channel_url == "https://voicy.jp/channel/1343" and not os.getenv("TEST_VOICY_CHANNEL_URL"):
            print(f"Using default test URL: {test_voicy_channel_url}", flush=True, file=f_scraper_out)
            print("You can set a different URL via the TEST_VOICY_CHANNEL_URL environment variable.", flush=True, file=f_scraper_out)
        else:
            print(f"Using test URL: {test_voicy_channel_url}", flush=True, file=f_scraper_out)

        print("DEBUG: Checkpoint 1 - Before attempting to print fetch message", flush=True, file=f_scraper_out)
        print(f"Attempting to fetch the latest episode URL from: {test_voicy_channel_url}", flush=True, file=f_scraper_out)
        print("DEBUG: Checkpoint 2 - After attempting to print fetch message, before calling function", flush=True, file=f_scraper_out)
        
        latest_url = get_latest_voicy_episode_url(test_voicy_channel_url)
        print(f"DEBUG: Checkpoint 3 - Returned from get_latest_voicy_episode_url. latest_url type: {type(latest_url)}, value: '{latest_url}'", flush=True, file=f_scraper_out)

        if latest_url:
            print(f"\nSuccessfully fetched latest Voicy episode URL:", flush=True, file=f_scraper_out)
            print(f"  {latest_url}", flush=True, file=f_scraper_out)
            # Print the URL to standard output for rss_monitor.py to capture
            print(f"VOICY_EPISODE_URL:{latest_url}")
        else:
            print(f"\nFailed to fetch the latest Voicy episode URL.", flush=True, file=f_scraper_out)
            print("Please ensure:", flush=True, file=f_scraper_out)
            print("  1. ChromeDriver is installed and in your PATH, or its path is correctly specified.", flush=True, file=f_scraper_out)
            print("  2. The Voicy channel URL is correct and accessible.", flush=True, file=f_scraper_out)
            print(f"  3. The CSS selector '{VOICY_EPISODE_SELECTOR}' is still valid for Voicy's structure.", flush=True, file=f_scraper_out)

        print("--- voicy_scraper.py test finished ---", flush=True, file=f_scraper_out)

    # Final message to console (might be garbled, but confirms file write attempt)
    print(f"Main script output written to: {os.path.abspath(scraper_output_log_path)}", flush=True)
