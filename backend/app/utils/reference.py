import random
import string
from datetime import datetime

def generate_reference_number(prefix: str = "GRV") -> str:
    """Generate a unique reference number formatted as GRV-YYYY-XXXXXX."""
    year = datetime.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"
