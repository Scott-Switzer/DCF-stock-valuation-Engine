"""Cloudflare Python WSGI entrypoint; D1 bindings are request scoped."""

from workers import wsgi
from jinja2 import DictLoader
from embedded_assets import ASSETS
from app import app

app.config["CLOUDFLARE"] = True
app.jinja_loader = DictLoader(
    {k.removeprefix("templates/"): v for k, v in ASSETS.items() if k.startswith("templates/")}
)
Default = wsgi.entrypoint(app)
