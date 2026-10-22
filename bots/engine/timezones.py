"""Finding a user's timezone. Telegram doesn't tell bots where users are, so people pick
from common zones or type a city."""
import re
from datetime import datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, available_timezones

# Shown as buttons during setup: (label, IANA name).
COMMON = [
    ("New York", "America/New_York"),
    ("Chicago", "America/Chicago"),
    ("Denver", "America/Denver"),
    ("Los Angeles", "America/Los_Angeles"),
    ("London", "Europe/London"),
    ("Berlin / Paris", "Europe/Berlin"),
    ("India", "Asia/Kolkata"),
    ("Sydney", "Australia/Sydney"),
]

# Common names that don't appear in IANA zone names.
ALIASES = {
    "nyc": "America/New_York", "new york city": "America/New_York",
    "eastern": "America/New_York", "est": "America/New_York", "edt": "America/New_York",
    "central": "America/Chicago", "cst": "America/Chicago", "cdt": "America/Chicago",
    "mountain": "America/Denver", "mst": "America/Denver", "mdt": "America/Denver",
    "arizona": "America/Phoenix",
    "pacific": "America/Los_Angeles", "pst": "America/Los_Angeles", "pdt": "America/Los_Angeles",
    "la": "America/Los_Angeles", "san francisco": "America/Los_Angeles",
    "seattle": "America/Los_Angeles", "boston": "America/New_York",
    "miami": "America/New_York", "atlanta": "America/New_York", "dallas": "America/Chicago",
    "houston": "America/Chicago", "austin": "America/Chicago",
    "uk": "Europe/London", "england": "Europe/London", "scotland": "Europe/London",
    "ireland": "Europe/Dublin", "gmt": "Europe/London", "bst": "Europe/London",
    "france": "Europe/Paris", "germany": "Europe/Berlin", "spain": "Europe/Madrid",
    "italy": "Europe/Rome", "netherlands": "Europe/Amsterdam", "india": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata", "delhi": "Asia/Kolkata", "bangalore": "Asia/Kolkata",
    "japan": "Asia/Tokyo", "philippines": "Asia/Manila", "brazil": "America/Sao_Paulo",
    "mexico": "America/Mexico_City", "canada": "America/Toronto", "hawaii": "Pacific/Honolulu",
    "alaska": "America/Anchorage", "melbourne": "Australia/Melbourne",
    "brisbane": "Australia/Brisbane", "perth": "Australia/Perth",
    "new zealand": "Pacific/Auckland", "nz": "Pacific/Auckland", "utc": "UTC",
}


def _norm(text):
    return re.sub(r"[^a-z]+", " ", text.lower()).strip()


@lru_cache(maxsize=1)
def _by_city():
    """Normalized city name -> IANA zone, from the last part of each zone name."""
    out = {}
    for name in available_timezones():
        if "/" in name and not name.startswith(("Etc/", "SystemV/", "US/")):
            out.setdefault(_norm(name.rsplit("/", 1)[1]), name)
    return out


def find_timezones(query):
    """Up to 5 IANA zones matching what the user typed, best match first."""
    q = _norm(query)
    if not q:
        return []
    if q in ALIASES:
        return [ALIASES[q]]
    exact = query.strip().replace(" ", "_")
    if exact in available_timezones():
        return [exact]
    cities = _by_city()
    if q in cities:
        return [cities[q]]
    starts = sorted(z for c, z in cities.items() if c.startswith(q))
    contains = sorted(z for c, z in cities.items() if q in c and z not in starts)
    return (starts + contains)[:5]


def local_now(tz_name, now=None):
    return (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(tz_name or "UTC"))


def describe(tz_name, now=None):
    """'Europe/London (now 14:05)' for showing in settings."""
    return f"{tz_name} (now {local_now(tz_name, now):%H:%M})"
