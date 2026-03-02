import subprocess

print("Calling API...")
result = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:8000/api/v1/mask", "-F", "policy=default_policy", "-F", "file=@test_pii.pdf"],
    capture_output=True,
    text=True
)

import json
try:
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2))
except json.JSONDecodeError:
    print("Failed to decode JSON. Raw output:")
    print(result.stdout)
