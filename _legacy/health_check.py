import requests
import sys

try:
    response = requests.get("http://localhost:8502")
    if response.status_code == 200:
        print("SUCCESS: Server is reachable (HTTP 200).")
        # Streamlit usually returns a small HTML shell. We can check for "Streamlit" in it.
        if "Streamlit" in response.text or "noscript" in response.text:
            print("SUCCESS: Streamlit HTML shell detected.")
        else:
            print("WARNING: Server returned 200 but content doesn't look like Streamlit.")
    else:
        print(f"FAILURE: Server returned status code {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"FAILURE: Could not connect to server. Error: {e}")
    sys.exit(1)
