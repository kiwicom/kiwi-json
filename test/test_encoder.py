from collections import ItemsView
import datetime
from decimal import Decimal
from functools import partial
from json import dumps as json_dumps
import sys
import uuid

import attr
import pytest
from pytz import UTC

from kw.json import default_encoder, MaskedJSONEncoder
from kw.json._compat import DataclassItem, enum

try:
    from simplejson import dumps as simplejson_dumps
except ImportError:
    simplejson_dumps = None


class Custom:
    pass


@attr.s
class AttrsItem(object):
    attrib = attr.ib(type=int)


class NotDataclassesItem(object):
    __dataclass_fields__ = ()


class HTML:
    def __html__(self):
        return "foo"


UUID = uuid.uuid4()

if sys.version_info[0] == 2:
    items_view = ItemsView({"foo": 1})
else:
    items_view = {"foo": 1}.items()


@pytest.mark.parametrize(
    "value, expected",
    (
        ({1}, [1]),
        (Decimal("1"), "1"),
        (UUID, str(UUID)),
        (datetime.datetime(2018, 1, 1), "2018-01-01T00:00:00"),
        (datetime.datetime(2018, 1, 1, tzinfo=UTC), "2018-01-01T00:00:00+00:00"),
        (datetime.date(2018, 1, 1), "2018-01-01"),
        (HTML(), "foo"),
        (items_view, {"foo": 1}),
    ),
)
def test_daisy_encoder(value, expected):
    assert default_encoder(value) == expected


@pytest.mark.skipif(sys.version_info[0] == 3, reason="Not applicable to Python 3")
def test_iteritems():
    assert default_encoder({"foo": 1}.iteritems()) == {"foo": 1}


@pytest.mark.skipif(enum is None, reason="Enum is not available")
def test_enum():
    class SomeEnum(enum.Enum):
        red = 1
        green = 2

    assert default_encoder(SomeEnum.red) == "red"


def test_unknown_raises():
    class Foo(object):
        bar = True  # pylint: disable=C0102

    with pytest.raises(TypeError):
        default_encoder(Foo())


@pytest.mark.parametrize(
    "dumps",
    (pytest.mark.skipif(simplejson_dumps is None, reason="Simplejson is not available")(simplejson_dumps), json_dumps),
)
@pytest.mark.parametrize(
    "value, expected",
    (
        ({"secret": "FOOO"}, '{"secret": "-- MASKED --"}'),
        ({"booking_token": "FOOO"}, '{"booking_token": "FOOO"}'),
        ({"token": "FOOO"}, '{"token": "-- MASKED --"}'),
        ({"regular_stuff": "FOOO"}, '{"regular_stuff": "FOOO"}'),
    ),
)
def test_masked_json_encoders(dumps, value, expected):
    assert dumps(value, cls=MaskedJSONEncoder) == expected


@pytest.mark.parametrize(
    "dumper, expected",
    ((default_encoder, {"attrib": 1}), (partial(json_dumps, default=default_encoder), '{"attrib": 1}')),
)
@pytest.mark.skipif(DataclassItem is None, reason="Dataclasses are available only on Python 3.7+")
def test_dataclasses(dumper, expected):
    assert dumper(DataclassItem(attrib=1)) == expected  # pylint: disable=not-callable


@pytest.mark.parametrize(
    "dumper, expected",
    ((default_encoder, {"attrib": 1}), (partial(json_dumps, default=default_encoder), '{"attrib": 1}')),
)
def test_attrs(dumper, expected):
    assert dumper(AttrsItem(attrib=1)) == expected


@pytest.mark.skipif(sys.version_info[:2] >= (3, 7), reason="Dataclasses should not be available")
def test_missing_dependency():
    """If we have a class that have the same attributes as attrs provide."""
    with pytest.raises(TypeError, match="Object of type NotDataclassesItem is not JSON serializable"):
        default_encoder(NotDataclassesItem())
