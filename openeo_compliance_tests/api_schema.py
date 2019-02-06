
import json
import pkgutil


schema = json.loads(pkgutil.get_data("openeo_compliance_tests", "openapi.json"))

capabilities_schema = schema["paths"]["/"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
processes_schema = schema["paths"]["/processes"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

collections_schema = schema["paths"]["/collections"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

collection_detail_schema = schema["paths"]["/collections/{name}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

#import sys
#sys.setrecursionlimit(20000)
#import json
#with open("/home/driesj/pythonworkspace/openeo-python-compliance/openapi031-nonrecursive.json","r") as f:
#    schema_non_recursive = json.load(f)

#from openapi_core import create_spec
#openapi_spec = create_spec(schema_non_recursive)