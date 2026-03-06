import re

text = """
Field
Information
Full Name
John Doe
Email
john.doe@gmail.com
Phone Number
+91 9876543210
Address
Hyderabad, Telangana
LinkedIn
linkedin.com/in/sampleprofile
Company
ABC Technologies Pvt Ltd
Position
Software Engineer
Experience
3 Years

This document contains personal identifiable information (PII) for testing OCR, NER detection, and regex extraction pipelines. The text includes names, emails, phone numbers, and addresses which should be detected and redacted by the system.
"""

NAME_PART = r"[A-Z][a-z]*(?:['\-][A-Z][a-z]*)*"

pattern_name = re.compile(
    r"(?:\b(?:Full\s+Name|Name|Contact\s+Name)[ \t:\-]*\n?[ \t]*)([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){0,3})\b",
    flags=re.IGNORECASE
)

pattern_address = re.compile(
    r"(?:\b(?:Address|Location)[ \t:\-]*\n?[ \t]*)([A-Za-z0-9.,/:\\\- \n]{5,250}?(?:(?:\d{6}\b)|RAJ\b|TIRUPATI\b|HYDERABAD\b|TAMIL NADU\b|TELANGANA\b|MAHARASHTRA\b))|"
    r"\b(?:hyderabad|mumbai|delhi|bangalore|pune|chennai|kolkata|jaipur)[,\s]+(?:telangana|maharashtra|karnataka|tamil nadu|west bengal|rajasthan)\b|"
    r"\b(?:hyderabad|telangana|mumbai|delhi|bangalore|pune|chennai|kolkata|jaipur|rajasthan)\b",
    flags=re.IGNORECASE
)

# Test name pattern
print("--- NAME MATCHES ---")
for match in pattern_name.finditer(text):
    if match.lastindex and match.start(match.lastindex) != -1:
        print(f"Matched Full Name: {match.group(match.lastindex).strip()}")
    else:
        print(f"Matched Full Name: {match.group().strip()}")


print("\n--- ADDRESS MATCHES ---")
for match in pattern_address.finditer(text):
    if match.lastindex and match.start(match.lastindex) != -1:
        print(f"Matched Address Group: {match.group(match.lastindex).strip()}")
    else:
        print(f"Matched Address: {match.group().strip()}")

