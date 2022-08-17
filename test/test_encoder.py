import datetime
import os
import sys
import uuid
from collections import namedtuple
from decimal import Decimal
from functools import partial
from json import dumps as json_dumps
from json import load as json_load
from json import loads

import arrow
import asyncio
import asyncpg
import attr
import pytest
from pytz import UTC
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from kw.json import (
    KiwiJSONEncoder,
    MaskedJSONEncoder,
    default_encoder,
    dump,
    dumps,
    raw_encoder,
)
from kw.json._compat import DataclassItem, enum
from kw.json.exceptions import KiwiJsonError

try:
    from simplejson import dumps as simplejson_dumps
except ImportError:
    simplejson_dumps = None


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def asdict(self):
        return {"id": self.id, "name": self.name}


class Custom:
    pass


Namedtuple = namedtuple("Namedtuple", ["a", "b"])
test_namedtuple = Namedtuple(1.3333, 2.3333)
test_namedtuple_complex = Namedtuple(1.3333, Namedtuple(1.3333, {1: 1.3333}))


@attr.s
class AttrsItem(object):
    attrib = attr.ib(type=int)


class NotDataclassesItem(object):
    __dataclass_fields__ = {}


class NotAttrsItem(object):
    __attrs_attrs__ = ()


class HTML:
    def __html__(self):
        return "foo"


UUID = uuid.uuid4()

items_view = {"foo": 1}.items()
items_view_float = {"foo": 1.333}.items()
items_view_complex = {1: 1.333, 2: {2: 0.333}.items()}.items()


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


@pytest.mark.skipif(
    simplejson_dumps is None, reason="Decimal encoding with simplejson only"
)
@pytest.mark.parametrize(
    "value, expected",
    (
        (Decimal("1"), "1"),
        (Decimal("-1"), "-1"),
        (Decimal("0.123456789123456789"), "0.123456789123456789"),
    ),
)
def test_simplejson_encoder_with_decimal(value, expected):
    assert dumps(value, use_decimal=True) == expected


@pytest.mark.skipif(simplejson_dumps is not None, reason="Standard json only")
def test_json_with_use_decimal_argument():
    with pytest.raises(KiwiJsonError, match=r".*Decimal.*"):
        dumps(Decimal(0), use_decimal=True)


def test_default_encoder_defaults():
    # By default `default_encoder` encodes datetimes as ISO
    assert default_encoder(datetime.datetime(2018, 1, 1)) == "2018-01-01T00:00:00"


@pytest.mark.parametrize(
    "value, expected, date_as_unix_time",
    (
        ({1}, "[1]", False),
        (Decimal("1"), '"1"', False),
        (UUID, f'"{str(UUID)}"', False),
        (datetime.datetime(2018, 1, 1), '"2018-01-01T00:00:00"', False),
        (
            datetime.datetime(2018, 1, 1, tzinfo=UTC),
            '"2018-01-01T00:00:00+00:00"',
            False,
        ),
        (arrow.get("2018-01-01"), '"2018-01-01T00:00:00+00:00"', False),
        (datetime.date(2018, 1, 1), '"2018-01-01"', False),
        (datetime.datetime(2018, 1, 1), "1514764800", True),
        (datetime.datetime(2018, 1, 1, tzinfo=UTC), "1514764800", True),
        (datetime.date(2018, 1, 1), "1514764800", True),
        (arrow.get("2018-01-01"), "1514764800.0", True),
        (HTML(), '"foo"', False),
        (items_view, '{"foo": 1}', False),
    ),
)
def test_dumps(value, expected, date_as_unix_time):
    assert dumps(value, date_as_unix_time=date_as_unix_time) == expected


@pytest.mark.parametrize(
    "values, expected, precision",
    (
        ((1.333, 1.333), "1.33", 2),
        (({1: 1.333}, {1: 1.333}), '{"1": 1.33}', 2),
        (([1.333, 2.333], [1.333, 2.333]), "[1.33, 2.33]", 2),
        (([1.333, {1: 1.333}], [1.333, {1: 1.333}]), '[1.33, {"1": 1.33}]', 2),
        (
            ([1.333, {1: 1.333}, {1.333}], [1.333, {1: 1.333}, {1.333}]),
            '[1.33, {"1": 1.33}, [1.33]]',
            2,
        ),
        ((items_view_float, items_view_float), '{"foo": 1.33}', 2),
        ((items_view_complex, items_view_complex), '{"1": 1.33, "2": {"2": 0.33}}', 2),
        ((HTML(), None), '"foo"', 2),
        (([set()], [set()]), "[[]]", 2),
        (((1.3333, 2.3333), (1.3333, 2.3333)), "[1.33, 2.33]", 2),
        ((({1: 1.33333}, 1.33333), ({1: 1.33333}, 1.33333)), '[{"1": 1.33}, 1.33]', 2),
        (
            (
                [{1: 1.222, 2: [1.333, {1: 1.333}, {3: {3.333}}]}],
                [{1: 1.222, 2: [1.333, {1: 1.333}, {3: {3.333}}]}],
            ),
            '[{"1": 1.22, "2": [1.33, {"1": 1.33}, {"3": [3.33]}]}]',
            2,
        ),
    ),
)
def test_rounding(values, expected, precision):
    before, after = values
    assert dumps(before, precision=precision) == expected
    if after:
        # check if object was not modified by rounding and removing of dict_items
        assert before == after


@pytest.mark.parametrize(
    "values, expected, precision",
    (
        (
            (test_namedtuple, test_namedtuple),
            {"as_object": '{"a": 1.33, "b": 2.33}', "as_list": "[1.33, 2.33]"},
            2,
        ),
        (
            (test_namedtuple_complex, test_namedtuple_complex),
            {
                "as_object": '{"a": 1.33, "b": {"a": 1.33, "b": {"1": 1.33}}}',
                "as_list": '[1.33, [1.33, {"1": 1.33}]]',
            },
            2,
        ),
    ),
)
def test_rounding_tuples(values, expected, precision):
    before, after = values
    if simplejson_dumps:
        # simplejson supports `namedtuple_as_object` param unlike json
        assert dumps(before, precision=precision) == expected["as_object"]
        assert (
            dumps(before, precision=precision, namedtuple_as_object=False)
            == expected["as_list"]
        )
    else:
        assert dumps(before, precision=precision) == expected["as_list"]
    assert before == after


def test_date_as_unix_time_default():
    # When `date_as_unix_time` is not passed, then it is disabled and dates are converted as ISO
    assert dumps(datetime.date(2018, 1, 1)) == '"2018-01-01"'


def test_raw_encoder_with_date_unix_time_default():
    class Foo(object):
        def __repr__(self):
            return "<Foo>"

    # by default `raw_encoder` encodes dates as ISO
    assert dumps(
        {"foo": Foo(), "bar": datetime.date(2018, 1, 1)}, default=raw_encoder
    ) == dumps({"foo": "<Foo>", "bar": "2018-01-01"})


def test_dump_with_default():
    # by default `dumps` encodes dates as ISO
    assert dumps(datetime.date(2018, 1, 1), default=str) == '"2018-01-01"'


def test_dump_with_default_and_date_as_unix_time():
    with pytest.raises(TypeError):
        # `date_as_unix_time` leads to failing when `default` is specified
        dumps(datetime.date(2018, 1, 1), default=str, date_as_unix_time=True)


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
def test_dump(tmpdir, value, expected):
    filename = str(tmpdir.join("test_file.json"))
    with open(filename, "w+", encoding="UTF-8") as fp:
        dump(value, fp)
        fp.seek(0, 0)
        assert json_load(fp) == expected


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

    with pytest.raises(
        TypeError, match="^Object of type Foo is not JSON serializable$"
    ):
        default_encoder(Foo())


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
def test_masked_json_encoders(value, expected):
    _dumps = simplejson_dumps or json_dumps
    assert _dumps(value, cls=MaskedJSONEncoder) == expected


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
def test_dataclasses(dumper, expected):
    assert dumper(DataclassItem(attrib=1)) == expected  # pylint: disable=not-callable


@pytest.mark.parametrize(
    "dumper, expected",
    (
        (default_encoder, {"attrib": 1}),
        (partial(json_dumps, default=default_encoder), '{"attrib": 1}'),
    ),
)
def test_attrs(dumper, expected):
    assert dumper(AttrsItem(attrib=1)) == expected


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


def test_no_attrs():
    # Need to re-import
    del sys.modules["kw.json"]
    del sys.modules["kw.json.encode"]
    sys.modules["attr"] = None
    from kw.json import (  # pylint: disable=reimported,import-outside-toplevel
        default_encoder,
    )

    with pytest.raises(
        TypeError, match="Object of type NotAttrsItem is not JSON serializable"
    ):
        default_encoder(NotAttrsItem())


async def get_asyncpg_record(dsn):
    connection = await asyncpg.connect(dsn)
    result = await connection.fetch("SELECT 1 as value")
    await connection.close()
    return result


def test_asyncpg():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_asyncpg_record(os.getenv("DATABASE_URI")))
    assert json_dumps(result, default=default_encoder) == '[{"value": 1}]'
