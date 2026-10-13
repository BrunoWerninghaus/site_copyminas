"""HTTP response protections for the Copy Minas public site and admin."""

from flask import request

# External hosts here are temporary, explicit globe dependencies. When the
# globe becomes local-only, remove these allowances instead of widening CSP.
_CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "script-src 'self' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' https://raw.githubusercontent.com https://servicodados.ibge.gov.br",
        "worker-src 'self' blob:",
    )
)


def install_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = _CONTENT_SECURITY_POLICY

        # Cloudflare Tunnel can terminate TLS before the local HTTP origin.
        # This header is seen by the public browser only over the HTTPS route.
        if app.config["IS_PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"

        if request.path.startswith("/admin") or request.method == "POST":
            response.headers["Cache-Control"] = "no-store"
        return response

    return app
