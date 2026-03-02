import re

PII_BLACKLIST = {
    "GITHUB", "LINKEDIN", "BITBUCKET", "DOCKER", "KUBERNETES", "PYTHON", "JAVA", "ORACLE", 
    "AWS", "GCP", "AZURE", "POSTGRESQL", "MYSQL", "MONGODB", "REDIS", "REACT", "NODE", "FLASK",
    "FASTAPI", "FAST API", "SPRING", "HIBERNATE", "POSTMAN", "GIT", "GOOGLE", "MICROSOFT",
    "LOOKER", "DEEPGRAM", "GEMINI", "GPT", "OPENAI", "CHROME", "CHIPS", "DEVOPS", "CI/CD",
    "CODEZEN", "SAFELENS", "DOCUSENSE", "TALENTFLOW", "AIVA", "DEEPGRAM-ASR", "PIOPIY",
    "MBA", "BTECH", "B.TECH", "PHD", "MS", "MTECH", "BCA", "MCA", "HR", "TA", "QA",
    "SUMMARY", "EXPERIENCE", "SKILLS", "EDUCATION", "PROJECTS", "ACHIEVEMENTS", "LANGUAGES",
    "CERTIFICATIONS", "OBJECTIVE", "INTERESTS", "PROFILE", "PROFESSIONAL", "ASSOCIATE",
    "LOAN", "AGREEMENT", "BORROWER", "LENDER", "APPLICANT", "DETAILS", "FATHER", "MOTHER",
    "SPOUSE", "RELATIONSHIP", "GENDER", "FORMAT", "CASE", "MIXED", "LEGAL", "CONFIRMATION",
    "EMPLOYER", "EMPLOYEE", "EMPLOYMENT", "INFORMATION", "SALARY", "ANNUAL", "AMOUNT", "TENURE", 
    "IFSC", "AADHAAR", "PAN", "ACCOUNT", "NUMBER", "MOBILE", "ALTERNATE", "CONTACT", "EMAIL", 
    "PERSONAL", "PERMANENT", "ADDRESS", "OFFICE", "SIGNATURE", "DECLARATION", "HEREBY", 
    "CONFIRM", "TRUE", "CORRECT", "BETWEEN", "MADE", "DISBURSEMENT", "EMI", "RATE", "PERCENT", 
    "ANNUM", "TITLE", "LABEL", "HEADER", "FOOTER", "PAGE", "TOTAL", "SUBTOTAL", "BALANCE",
    "DUPLICATE", "STATEMENT", "BANK", "HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "CITI", 
    "HSBC", "BARCLAYS", "MINIMUM", "MAXIMUM", "AVAILABLE", "CREDIT", "LIMIT", "CASH", 
    "DUE", "DATE", "AMOUNT", "CHARGES", "INCURRED", "PLEASE", "ENSURE", "DALLY", "REDUCING", 
    "METHOD", "HOTLIST", "NETBANKING", "PHONBANKING", "LOCATE", "RESERVE", "INDIA", 
    "FACILITATE", "EFFECTIVE", "INFORMED", "ASSESSMENT", "CONDUCT", "STATUTORY", "BODIES", 
    "ACCORDANCE", "VOLUNTARY", "CODES", "PRESCRIBED", "COMMITMENT", "PLATINUM", "CONSUMER", 
    "PRIVILEGE", "SERVE", "OUTSTANDING", "AUTHORISED", "REGULARISE", "WITHOUT", "THESE", 
    "WITHIN", "THROUGH", "FOLLOWING", "PREVIOUS", "REVISED", "TERMS", "CONDITIONS", "GENERAL", 
    "SCHEDULE", "REWARD", "POINTS", "WEBSITE", "CARD", "CARDS", "ACCOUNT", "ACCOUNTING",
    "OFFICER", "MANAGER", "DIRECTOR", "ADMINISTRATOR", "DEPARTMENT", "DIVISION", "BRANCH",
    "JAIPUR", "CHENNAI", "HYDERABAD", "BANGALORE", "MUMBAI", "DELHI", "PUNE", "KOLKATA",
    "RAJASTHAN", "TAMIL NADU", "TELANGANA", "KARNATAKA", "MAHARASHTRA", "GUJARAT",
    "HHSN", "GSTIN", "GST", "IGST", "CGST", "SGST", "TAX", "INVOICE", "BILL", "RECEIPT",
    "PAYMENT", "TRANSACTION", "REFERENCE", "DESCRIPTION", "MERCHANT", "CATEGORY",
    "DEBIT", "CREDIT", "CURRENCY", "INR", "USD", "EUR", "GBP", "SUCCESSFUL", "FAILED",
    "PENDING", "COMPLETED", "SETTLED", "REVERSED", "VOID", "REFUND", "AUTHORIZED",
    "PAYTM", "GSTIN", "HSN", "GST", "CSB", "BCSBI", "CICS", "CIC", "AAN", "TOTAL", 
    "MINIMUM", "MAXIMUM", "AMOUNT", "DUE", "DATE", "CASE", "NOTE", "PLEASE", "WRITE",
    "LETTER", "DIVISION", "DIVISIONAL", "MANAGER", "AVAILABLE", "LIMIT", "CHARGES",
    "IN", "NO", "FOR", "TO", "THE", "AND", "WITH", "FROM", "ON", "AT", "BY", "OF",
    "CARD", "NUMBER", "NO.", "AAN:", "CARD:", "NAME:", "EMAIL:", "ADDRESS:", "MOBILE:", "PHONE:"
}

PERSON_NAME_REGEX = re.compile(
    r"(?i:\b(?:mr\.|mrs\.|ms\.|dr\.|shri|smt\.?|prof\.?)\s+[a-z]+(?:\s+[a-z]+){0,3}\b)|"
    r"\b(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+\b|"
    r"\b(?:[a-z]{3,}\s+){2,3}[a-z]{3,}\b|"
    r"\b[A-Z][a-z]+(?:[A-Z][a-z]+){2,}\b|"
    r"\b(?:[a-z]{3,}_){1,3}[a-z]{3,}\b|"
    r"\b(?!(?:.*?\b(?:SUMMARY|EXPERIENCE|EDUCATION|PROJECTS|SKILLS|ACHIEVEMENTS|ACTIVITIES|LANGUAGES|OBJECTIVE|CERTIFICATIONS|INTERESTS|PROFILE|PROFESSIONAL|ASSOCIATE|TECHNICAL|AIVA|DOCUSENSE|TALENTFLOW|SAFELENS|CODEZEN|TALENT|FLOW|SAFE|LENS|DOCU|SENSE|CODE|ZEN|DEVOPS|GITHUB|LINKEDIN|DATA|SCIENTIST|SCIENCE|ENGINEER|ENGINEERING|INTERN|RESEARCHER|ANALYST|DEVELOPER|ARCHITECT|CONSULTANT|UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL|FOUNDATION|CERTIFICATION|LOAN|AGREEMENT|BORROWER|LENDER|APPLICANT|DETAILS|GENDER|FORMAT|RELATIONSHIP|EMPLOYER|EMPLOYEE|CONFIRMATION|SIGNATURE|DECLARATION|BETWEEN|MADE)\b))(?:[A-Z]{3,}\s+){1,3}[A-Z]{3,}\b|"
    r"\b(?:[A-Z]\.?\s*){1,2}[A-Z][a-z]+\s+[A-Z][a-z]+\b|"
    r"\b[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+)?[A-Z]\.?\b"
)

GOVT_ID_REGEX = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]\b")
CC_REGEX = re.compile(r"\b\d[ \-*X\d]{11,17}\d\b")

# Simulate Luhn Check
def luhn_check(number):
    if "X" in number.upper() or "*" in number: return True
    clean = re.sub(r"[ -]", "", number)
    if not clean.isdigit() or len(clean) < 13: return False
    total = sum(int(d) if i % 2 == 0 else sum(divmod(int(d) * 2, 10)) for i, d in enumerate(clean[::-1]))
    return total % 10 == 0

def test_precision():
    inputs = [
        "AAN: 0001016260002513455",
        "Card No: 4695 25XX XXXX 3458",
        "Name > NIKHIL KHANDELWAL",
        "Email > khandelwal@gmail.com",
        "Address : Jaipur",
        "DUPLICATE STATEMENT HDFC Bank",
        "Available Credit Limit",
        "Minimum Amount Due",
        "In case you wish to update",
    ]
    
    full_text = "\n".join(inputs)
    
    print("Testing Regex + Label-Aware + Multi-Separator Logic:\n")
    for text in inputs:
        # Scan for all
        found_entities = []
        
        # 1. Card check
        cc_matches = CC_REGEX.finditer(text)
        for m in cc_matches:
             val = m.group().strip()
             if luhn_check(val): found_entities.append(("CC", val, m.start(), m.end()))
        
        # 2. Govt ID
        id_matches = GOVT_ID_REGEX.finditer(text)
        for m in id_matches: found_entities.append(("ID", m.group().strip(), m.start(), m.end()))
        
        # 3. Name
        name_matches = PERSON_NAME_REGEX.finditer(text)
        for m in name_matches:
            val = m.group().strip()
            # Label Check simulation
            idx_in_full = full_text.find(text) + m.end()
            context = full_text[idx_in_full:idx_in_full+5]
            is_label = re.match(r"^\s*[:>|—]", context)
            
            if is_label:
                found_entities.append(("LABEL", val, m.start(), m.end()))
            else:
                upper = val.upper().strip()
                tokens = [t.strip().upper() for t in re.split(r"[\s_/-]+", val) if t.strip()]
                if upper in PII_BLACKLIST or any(t in PII_BLACKLIST for t in tokens):
                    found_entities.append(("BLACKLISTED", val, m.start(), m.end()))
                else:
                    found_entities.append(("NAME", val, m.start(), m.end()))

        if not found_entities:
            print(f"Input: {text:35} | Result: NO MATCH")
        else:
            for etype, evalue, start, end in found_entities:
                status = "REDACTED" if etype in ["NAME", "CC", "ID", "EMAIL"] else "NOT REDACTED"
                print(f"Input: {text:35} | Result: {status} ({etype}) | Value: '{evalue}'")

if __name__ == "__main__":
    test_precision()
