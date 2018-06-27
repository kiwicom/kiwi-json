from __future__ import absolute_import

from .encode import default_encoder


class JSONExtension(object):
    def __init__(self, app=None, encoder=default_encoder, dict_factory=dict):
        self.app = app
        if app is not None:
            self.init_app(app, encoder, dict_factory)

    def init_app(self, app, encoder=default_encoder, dict_factory=dict):
        from flask import json

        class JSONEncoder(json.JSONEncoder):
            def default(self, obj):
                return encoder(obj, dict_factory)

        app.json_encoder = JSONEncoder
