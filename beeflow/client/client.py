import requests


resp = requests.get('http://localhost/bee_orc/v1/jobs')
if resp.status_code != 200:
    raise ApiError("GET /jobs".format(resp.status_code))

job = {"Job name": "Kripke" }
resp = requests.post('http://localhost/bee_orc/v1/jobs', json=job)
