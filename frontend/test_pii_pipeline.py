from reportlab.pdfgen import canvas
import subprocess

# 1. Create a PDF with some PII
c = canvas.Canvas("test_pii.pdf")
c.drawString(100, 750, "My name is John Doe and my phone number is 555-123-4567")
c.save()

# 2. Call the API
print("Calling API...")
result = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:8000/api/v1/process", "-F", "policy=default_policy", "-F", "file=@test_pii.pdf"],
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
