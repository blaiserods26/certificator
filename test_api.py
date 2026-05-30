import requests
import os

url = "http://127.0.0.1:5000/api/generate"
files = {
    'csvFile': open('participants.csv', 'rb'),
    'templateFile': open('certificate.png', 'rb')
}
data = {
    'nameFont': 'Roboto',
    'instFont': 'Charm',
    'nameSize': 90,
    'instSize': 72,
    'nameColor': '#8C6A24',
    'instColor': '#8C6A24'
}

try:
    response = requests.post(url, files=files, data=data)
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
