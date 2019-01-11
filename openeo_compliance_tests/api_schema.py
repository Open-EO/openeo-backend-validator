import requests

schema = requests.get("https://raw.githubusercontent.com/Open-EO/openeo-api/master/openapi.json").json()

capabilities_schema = schema["paths"]["/"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
processes_schema = schema["paths"]["/processes"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]