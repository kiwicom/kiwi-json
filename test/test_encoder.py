from collections import ItemsView
import datetime
from decimal import Decimal
from functools import partial
from json import dumps as json_dumps
from json import loads
import os
import sys
import uuid

import arrow
import attr
from dictalchemy import DictableModel
import pytest
from pytz import UTC
from sqlalchemy import Column, create_engine, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from kw.json import default_encoder, dumps, KiwiJSONEncoder, MaskedJSONEncoder, raw_encoder
from kw.json._compat import DataclassItem, enum

from ._compat import get_asyncpg_record

try:
    from simplejson import dumps as simplejson_dumps
except ImportError:
    simplejson_dumps = None


Base = declarative_base(cls=DictableModel)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Custom:
    pass


@attr.s
class AttrsItem(object):
    attrib = attr.ib(type=int)


class NotDataclassesItem(object):
    __dataclass_fields__ = ()


class NotAttrsItem(object):
    __attrs_attrs__ = ()


class HTML:
    def __html__(self):
        return "foo"


UUID = uuid.uuid4()

if sys.version_info[0] == 2:
    items_view = ItemsView({"foo": 1})
else:
    items_view = {"foo": 1}.items()


@pytest.mark.parametrize(
    "value, expected, date_as_unix_time",
    (
        ({1}, [1], False),
        (Decimal("1"), "1", False),
        (UUID, str(UUID), False),
        (datetime.datetime(2018, 1, 1), "2018-01-01T00:00:00", False),
        (datetime.datetime(2018, 1, 1, tzinfo=UTC), "2018-01-01T00:00:00+00:00", False),
        (arrow.get("2018-01-01"), "2018-01-01T00:00:00+00:00", False),
        (datetime.date(2018, 1, 1), "2018-01-01", False),
        (datetime.datetime(2018, 1, 1), 1514764800, True),
        (datetime.datetime(2018, 1, 1, tzinfo=UTC), 1514764800, True),
        (datetime.date(2018, 1, 1), 1514764800, True),
        (arrow.get("2018-01-01"), 1514764800, True),
        (HTML(), "foo", False),
        (items_view, {"foo": 1}, False),
    ),
)
def test_default_encoder(value, expected, date_as_unix_time):
    assert default_encoder(value, date_as_unix_time=date_as_unix_time) == expected


if simplejson_dumps is not None:
    # simplejson converts Decimal to float, but kw.json needs strings
    # There are possible workarounds listed in #7
    decimal_expected = "1"
else:
    decimal_expected = '"1"'


@pytest.mark.parametrize(
    "value, expected",
    (
        ({1}, "[1]"),
        (Decimal("1"), decimal_expected),
        (UUID, '"{}"'.format(str(UUID))),
        (datetime.datetime(2018, 1, 1), '"2018-01-01T00:00:00"'),
        (datetime.datetime(2018, 1, 1, tzinfo=UTC), '"2018-01-01T00:00:00+00:00"'),
        (datetime.date(2018, 1, 1), '"2018-01-01"'),
        (HTML(), '"foo"'),
        (items_view, '{"foo": 1}'),
    ),
)
def test_dumps(value, expected):
    assert dumps(value) == expected


@pytest.mark.skipif(sys.version_info[0] == 3, reason="Not applicable to Python 3")
def test_iteritems():
    assert default_encoder({"foo": 1}.iteritems()) == {"foo": 1}


@pytest.mark.skipif(enum is None, reason="Enum is not available")
def test_enum():
    class SomeEnum(enum.Enum):
        red = 1
        green = 2

    assert default_encoder(SomeEnum.red) == "red"


@pytest.mark.skipif(enum is None, reason="Enum is not available")
def test_enum_raw_encoder():
    class SomeEnum(enum.Enum):
        red = 1
        green = 2

    assert raw_encoder(SomeEnum.red) == "red"


def test_class_raw_encoder():
    class Foo(object):
        bar = True  # pylint: disable=C0102

    assert isinstance(raw_encoder(Foo), str)


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
        (("regular_stuff", "FOOO"), '["regular_stuff", "FOOO"]'),
    ),
)
def test_masked_json_encoders(dumps, value, expected):
    assert dumps(value, cls=MaskedJSONEncoder) == expected


@pytest.mark.parametrize(
    "dumper, expected",
    (
        (default_encoder, {"attrib": 1}),
        (raw_encoder, {"attrib": 1}),
        (partial(json_dumps, default=default_encoder), '{"attrib": 1}'),
        (partial(json_dumps, default=raw_encoder), '{"attrib": 1}'),
        (partial(json_dumps, cls=KiwiJSONEncoder), '{"attrib": 1}'),
        (partial(json_dumps, cls=MaskedJSONEncoder), '{"attrib": 1}'),
    ),
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


@pytest.fixture
def alchemy_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine)()

    user = User(name="test")
    session.add(user)
    session.commit()
    return session


def assert_json(value, expected):
    """To simplify tests for Python versions that don't preserve ordering in dicts."""
    encoded = json_dumps(value, default=default_encoder)
    assert loads(encoded) == expected


def test_dictalchemy(alchemy_session):
    instance = alchemy_session.query(User).first()
    assert_json(instance, {"id": 1, "name": "test"})


def test_sqlalchemy_cursor_row(alchemy_session):
    data = alchemy_session.execute("SELECT * FROM users").fetchall()
    assert_json(data, [{"id": 1, "name": "test"}])


@pytest.mark.skipif(sys.version_info[0] == 2, reason="That trick doesn't work on Python 2")
def test_no_attrs():
    # Need to re-import
    del sys.modules["kw.json"]
    del sys.modules["kw.json.encode"]
    sys.modules["attr"] = None
    from kw.json import default_encoder  # pylint: disable=reimported

    with pytest.raises(TypeError, match="Object of type NotAttrsItem is not JSON serializable"):
        default_encoder(NotAttrsItem())


@pytest.mark.skipif(get_asyncpg_record is None, reason="Asyncpg is available only on Python 3.5+.")
def test_asyncpg():
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_asyncpg_record(os.getenv("DATABASE_URI")))  # pylint: disable=not-callable
    assert json_dumps(result, default=default_encoder) == '[{"value": 1}]'
