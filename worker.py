"""Production WSGI entrypoint with a separate owner-authenticated data route."""

from urllib.parse import urlsplit

from workers import WorkerEntrypoint, wsgi
from jinja2 import DictLoader
from embedded_assets import ASSETS
from app import app
from edge_limits import enforce
from owner_data_proxy import handle

app.config['CLOUDFLARE'] = True
app.jinja_loader = DictLoader(
    {k.removeprefix('templates/'): v for k, v in ASSETS.items() if k.startswith('templates/')}
)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Awaited here because the WSGI before_request hook cannot await the binding.
        limited = await enforce(self.env, request)
        if limited is not None:
            return limited
        path = urlsplit(request.url).path
        if path == '/api/data/query':
            return await wsgi.fetch(app, request, self.env)
        if (path in ('/api/data', '/private/v1')
                or path.startswith(('/api/data/', '/private/v1/'))):
            return await handle(request, self.env)
        return await wsgi.fetch(app, request, self.env)
