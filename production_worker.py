"""Production WSGI entrypoint with a separate owner-authenticated data route."""

from urllib.parse import urlsplit

from workers import WorkerEntrypoint, wsgi
from jinja2 import DictLoader
from embedded_assets import ASSETS
from app import app
from owner_data_proxy import handle

app.config['CLOUDFLARE'] = True
app.jinja_loader = DictLoader(
    {k.removeprefix('templates/'): v for k, v in ASSETS.items() if k.startswith('templates/')}
)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlsplit(request.url).path
        if path == '/api/data' or path.startswith('/api/data/'):
            return await handle(request, self.env)
        return await wsgi.fetch(app, request, self.env)
