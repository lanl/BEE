import requests

url = 'http://localhost:5000/predict_api'
req = requests.post(url,json={'experience':2, 'test_score':9, 'interview_score':6})

print(req.json())
