# TODO: Implement utility functions here
# Consider functions for:
# - Generating short codes
# - Validating URLs
# - Any other helper functions you need

import string
import random
from urllib.parse import urlparse

def generate_short_code(length=6): 
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False