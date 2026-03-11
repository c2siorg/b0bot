"""
Rate limiter configuration module
Shared limiter instance for use across the application
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter (will be bound to app in app.py)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
