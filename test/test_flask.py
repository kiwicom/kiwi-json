import sys

from flask import Flask, json

from kw.json.flask import JSONExtension

if sys.version_info[0] == 2:
    items = {"secret": "foo"}.iteritems()
else:
    items = {"secret": "foo"}.items()


def test_mask_dict():
    app = Flask(__name__)
    JSONExtension(app)
    with app.app_context():
        assert json.dumps(items) == '{"secret": "foo"}'


def test_create_extension_without_app():
    assert JSONExtension().app is None
