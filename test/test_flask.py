from flask import Flask, json

from kw.json.flask import JSONExtension

items = {"secret": "foo"}.items()


def test_mask_dict():
    app = Flask(__name__)
    extension = JSONExtension(app)
    assert extension.app is app
    with app.app_context():
        assert json.dumps(items) == '{"secret": "foo"}'


def test_create_extension_without_app():
    assert JSONExtension().app is None
