import sys
import time
import requests
from colorama import Fore, Style, init
import os

# Initialize colorama
init()


# ASCII-style welcome text
def ascii_welcome():
    welcome_text ="""
   __         _                _ _               _             _             _       
  /__\__ ___ | | ___        __| (_)_ __ ___  ___| |_ ___      | | ___   __ _(_)_ __  
 /_\/ __/ _ \| |/ _ \_____ / _` | | '__/ _ \/ __| __/ _ \_____| |/ _ \ / _` | | '_ \ 
//_| (_| (_) | |  __/_____| (_| | | | |  __/ (__| ||  __/_____| | (_) | (_| | | | | |
\__/\___\___/|_|\___|      \__,_|_|_|  \___|\___|\__\___|     |_|\___/ \__, |_|_| |_|
                                                                       |___/           
    """
    slow_print(welcome_text, Fore.BLUE)


def slow_print(text, color):
    for char in text:
        sys.stdout.write(color + char + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.005)


# Function to connect to the Ecole Directe API
def login_to_ecole_directe(username, password):
    api_url = "https://api.ecoledirecte.com/v3/login.awp?v=4.62.1"
    payload = {
        "identifiant": username,
        "motdepasse": password,
        "isReLogin": False,
        "uuid": "",
        "fa": []
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "accept-language": "fr,fr-FR;q=0.9",
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "code" in data and data["code"] == 200:
            print("Login successful!")
            return data
        else:
            print("Login failed:", data.get("message", "Unknown error"))
            return None
    except requests.RequestException as e:
        print("An error occurred while connecting to the API:", e)
        return None


# Example usage
if __name__ == "__main__":
    while True:
        ascii_welcome()
        slow_print("Choose an option:\n1: View API Information\n2: Log in\n", Fore.YELLOW)
        choice = input("Enter your choice (1 or 2): ")

        if choice == "1":
            print(
                "Ecole Directe API is used to connect and retrieve user information. Documentation can be found at https://github.com/EduWireApps/ecoledirecte-api-docs.")
            time.sleep(7)
            os.execv(sys.executable, ['python'] + sys.argv)
        elif choice == "2":
            username = input("Enter your username: ")
            password = input("Enter your password: ")

            user_data = login_to_ecole_directe(username, password)

            if user_data:
                print("User data:", user_data)
                break
        else:
            print("Invalid choice. Please restart the script and choose 1 or 2.")
            time.sleep(7)
            os.execv(sys.executable, ['python'] + sys.argv)
