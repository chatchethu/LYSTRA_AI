import requests

url = "https://api.sarvam.ai/speech-to-text"
headers = {"api-subscription-key": "fake-key"}
data = {"model": "saaras:v3"}
files = {"file": ("test.wav", b"fake", "audio/wav")}

resp = requests.post(url, headers=headers, data=data, files=files)
print(resp.status_code, resp.text)
