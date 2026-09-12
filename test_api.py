import urllib.request
import json
import urllib.error

url = 'http://127.0.0.1:8000/api/chat/stream'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer asdf' # any token, we don't know the user's token though... Wait, auth is required!
}
data = {
    'message': 'hi',
    'conversation_id': '00000000-0000-0000-0000-000000000000'
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
