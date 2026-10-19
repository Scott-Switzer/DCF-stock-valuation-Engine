"""Same-app private data explorer; credentials and records are browser-memory only."""
from flask import make_response, render_template


def register_data_workspace(app):
    @app.get('/data')
    def data_workspace():
        response = make_response(render_template('data_workspace.html'))
        response.headers['Cache-Control'] = 'private, no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response
