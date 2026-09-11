#!/usr/bin/env python3
"""
Shared Flask extension instances (created without an app so they can be
imported by blueprint modules without circular imports, then bound to
the real app with .init_app() in phase5_api_server.py).
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, default_limits=['200 per hour'])
