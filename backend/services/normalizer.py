import re
from typing import Optional, Tuple

# Patterns to immediately identify non-subscription financial transactions
EXCLUDED_PATTERNS = [
    r"\bTRANSFER\b",
    r"\bWIRE\s+TRANS\b",
    r"\bINTERNAL\s+TRANSFER\b",
    r"\bZELLE\b",
    r"\bVENMO\b",
    r"\bPAYROLL\b",
    r"\bGUSTO\s+PAYROLL\b",
    r"\bADP\s+PAYROLL\b",
    r"\bATM\s+WITHDRAWAL\b",
    r"\bCHECK\s+#?\d+\b",
    r"\bINTEREST\s+PAYMENT\b",
    r"\bFEE\s+REVERSAL\b",
]

# Known vendor signatures: pattern -> (Normalized Name, Vendor Domain, Category)
KNOWN_VENDORS = [
    (r"AMZN\s+(?:MKTP|WEB|AWS)|AMAZON\s+WEB\s+SERVICES", "Amazon Web Services", "aws.amazon.com", "Infrastructure"),
    (r"GITHUB", "GitHub", "github.com", "Engineering"),
    (r"FIGMA", "Figma", "figma.com", "Design"),
    (r"ADOBE", "Adobe Creative Cloud", "adobe.com", "Design"),
    (r"GOOGLE\s*(?:\*|WORKSPACE|GSUITE|CLOUD)", "Google Workspace", "google.com", "Productivity"),
    (r"NOTION", "Notion", "notion.so", "Productivity"),
    (r"SLACK", "Slack", "slack.com", "Communication"),
    (r"ZOOM(?:\.US)?", "Zoom Workplace", "zoom.us", "Communication"),
    (r"HETZNER", "Hetzner Cloud", "hetzner.com", "Infrastructure"),
    (r"NAMECHEAP", "Namecheap", "namecheap.com", "Domains"),
    (r"STRIPE", "Stripe", "stripe.com", "Finance"),
]


def is_non_subscription_transaction(raw_desc: str) -> bool:
    """Returns True if the transaction is a transfer, payroll, fee, or one-off bank movement."""
    upper = raw_desc.upper()
    for pat in EXCLUDED_PATTERNS:
        if re.search(pat, upper):
            return True
    return False


def normalize_merchant(raw_desc: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Normalizes a noisy raw payment descriptor string.
    Returns: (Normalized Name, Vendor Domain or None, Category or None)
    """
    upper = raw_desc.upper()

    for pattern, name, domain, category in KNOWN_VENDORS:
        if re.search(pattern, upper):
            return name, domain, category

    # Clean generic noise
    cleaned = raw_desc
    cleaned = re.sub(r"[*#]\S+", "", cleaned)  # remove *INV48201 or #1182
    cleaned = re.sub(r"\b(INC|LLC|CORP|LTD|CO|WWW|COM|US|DIR DEP)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d+", "", cleaned)  # remove digits
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    normalized_name = cleaned.title() if cleaned else raw_desc.strip()
    return normalized_name, None, "Other"
