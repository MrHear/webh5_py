import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_login(username, password):
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json'
    })
    
    try:
        print(f"Attempting login with username: {username}, password: {password}")
        with urllib.request.urlopen(req) as response:
            print(f"Status Code: {response.status}")
            print(f"Response: {response.read().decode('utf-8')}")
            print("Login Successful!")
            return True
    except urllib.error.HTTPError as e:
        print(f"Status Code: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
        print("Login Failed.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        # Default test
        test_login("admin", "OneSpace_Secure_2026")
    else:
        test_login(sys.argv[1], sys.argv[2])
