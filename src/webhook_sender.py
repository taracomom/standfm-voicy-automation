import requests
import json
import logging
import os
import time

# Determine project root to place log file at the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'webhook_sender_log.txt')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler()  # Also print to console
    ]
)

def send_to_make_webhook(webhook_url: str, voicy_episode_url: str) -> bool:
    """
    Sends the Voicy episode URL to the specified Make.com webhook URL.

    Args:
        webhook_url: The Webhook URL from Make.com.
        voicy_episode_url: The URL of the Voicy episode to send.

    Returns:
        True if the request was successful (2xx status code), False otherwise.
    """
    if not webhook_url:
        logging.error("Webhook URL is not provided. Cannot send data.")
        return False
    if not voicy_episode_url:
        logging.error("Voicy episode URL is not provided. Cannot send data.")
        return False

    payload = {
        "voicy_episode_url": voicy_episode_url, # Key changed to match expected format
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

    headers = {
        "Content-Type": "application/json"
    }

    logging.info(f"Sending Voicy URL to Make.com webhook: {webhook_url}")
    logging.info(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(f"Successfully sent data to webhook. Status code: {response.status_code}")
        # logging.debug(f"Response from webhook: {response.text}") # Uncomment for more details if needed
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send data to webhook: {e}")
        return False

if __name__ == '__main__':
    # Example usage (for testing purposes)
    # You would typically get these from environment variables or arguments
    test_webhook_url = os.environ.get("TEST_MAKE_WEBHOOK_URL") # Replace with your actual Make.com webhook URL for testing
    test_voicy_url = os.getenv("TEST_VOICY_EPISODE_URL", "https://voicy.jp/channel/000/default_test_episode") # Default test URL if env var not set

    if test_webhook_url:
        logging.info("--- Running webhook_sender.py in test mode ---")
        logging.info(f"Attempting to use Make.com Webhook URL from TEST_MAKE_WEBHOOK_URL: {test_webhook_url}")
        if os.getenv("TEST_VOICY_EPISODE_URL"):
            logging.info(f"Using Voicy Episode URL from TEST_VOICY_EPISODE_URL: {test_voicy_url}")
        else:
            logging.info(f"TEST_VOICY_EPISODE_URL not set, using default test Voicy URL: {test_voicy_url}")
        
        success = send_to_make_webhook(test_webhook_url, test_voicy_url)
        if success:
            logging.info("Test data sent successfully.")
        else:
            logging.error("Failed to send test data.")
        logging.info("--- Finished webhook_sender.py test mode ---")
    else:
        logging.info("TEST_MAKE_WEBHOOK_URL environment variable is not set. Skipping test run in __main__.")
