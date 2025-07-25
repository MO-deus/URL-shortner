# TODO: Implement your data models here
# Consider what data structures you'll need for:
# - Storing URL mappings
# - Tracking click counts
# - Managing URL metadata

import datetime

# considering the reads will be more than the number of writes
# I have mapped the "long_url" with "short_url"
# when firing a GET request, it will take 1 cycle (in theory) to fetch the data related to the <short_code>


# Structure: {short_code: {"long_url": "...", "clicks": 0, "created_at": "..."}}
url_database = {}

class URLMap:
    def __init__(self, long_url, short_code):
        self.long_url = long_url
        self.short_code = short_code
        self.clicks = 0
        self.created_at = datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            "long_url": self.long_url,
            "short_code": self.short_code,
            "clicks": self.clicks,
            "created_at": self.created_at
        }