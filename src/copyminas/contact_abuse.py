"""Local defense-in-depth for the public contact endpoint.

This limiter is per process. Cloudflare edge limits are still required for
distributed abuse and multi-worker production deployments.
"""

from collections import deque
from ipaddress import ip_address, ip_network
from math import ceil
import os
from threading import Lock
from time import monotonic

from flask import current_app, request


class ContactRateLimiter:
    def __init__(self, limit=5, window_seconds=900):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("Contact rate limit and window must be positive.")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events = {}
        self._lock = Lock()

    def retry_after(self, identity):
        now = monotonic()
        with self._lock:
            # Bound the in-memory map; an edge/WAF is essential for large floods.
            if len(self._events) > 2000:
                self._events = {
                    key: times
                    for key, times in self._events.items()
                    if times and now - times[-1] < self.window_seconds
                }
            times = self._events.get(identity)
            if times is None:
                if len(self._events) >= 5000:
                    return self.window_seconds
                times = deque()
                self._events[identity] = times

            while times and now - times[0] >= self.window_seconds:
                times.popleft()
            if len(times) >= self.limit:
                return max(1, ceil(self.window_seconds - (now - times[0])))

            times.append(now)
            return 0


def _trusted_proxy_networks(raw):
    networks = []
    for part in raw.split(","):
        value = part.strip()
        if value:
            networks.append(ip_network(value, strict=False))
    return tuple(networks)


def install_contact_abuse(app):
    app.config.setdefault(
        "CONTACT_MAX_BYTES",
        int(os.getenv("CONTACT_MAX_BYTES", "32768")),
    )
    app.config.setdefault(
        "CONTACT_RATE_LIMIT_COUNT",
        int(os.getenv("CONTACT_RATE_LIMIT_COUNT", "5")),
    )
    app.config.setdefault(
        "CONTACT_RATE_WINDOW_SECONDS",
        int(os.getenv("CONTACT_RATE_WINDOW_SECONDS", "900")),
    )
    app.config["CONTACT_TRUSTED_PROXY_NETWORKS"] = _trusted_proxy_networks(
        os.getenv("CONTACT_TRUSTED_PROXY_CIDRS", "")
    )
    if app.config["CONTACT_MAX_BYTES"] < 1024:
        raise RuntimeError("CONTACT_MAX_BYTES must be at least 1024.")
    app.extensions["copyminas_contact_limiter"] = ContactRateLimiter(
        app.config["CONTACT_RATE_LIMIT_COUNT"],
        app.config["CONTACT_RATE_WINDOW_SECONDS"],
    )
    return app


def contact_retry_after():
    remote = request.remote_addr or "unknown"
    try:
        peer = ip_address(remote)
    except ValueError:
        peer = None

    if peer is not None and any(
        peer in network
        for network in current_app.config["CONTACT_TRUSTED_PROXY_NETWORKS"]
    ):
        # Trust this header *only* if the TCP peer is a configured trusted proxy.
        # Never use untrusted X-Forwarded-For values as rate-limit identities.
        forwarded = request.headers.get("CF-Connecting-IP", "").strip()
        if forwarded:
            try:
                remote = str(ip_address(forwarded))
            except ValueError:
                pass

    limiter = current_app.extensions["copyminas_contact_limiter"]
    return limiter.retry_after(remote)
