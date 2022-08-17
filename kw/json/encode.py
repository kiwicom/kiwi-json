import calendar
import uuid
from collections import namedtuple
from collections.abc import ItemsView
from decimal import Decimal
from functools import partial

from ._compat import BaseJSONEncoder, _dump, _dumps, enum, simplejson_available
from .utils import mask_dict


def _fail(obj, *args, **kwargs):
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


try:
    from attr import asdict as attr_asdict
except ImportError:
    attr_asdict = _fail

try:
    from dataclasses import asdict as dc_asdict
except ImportError:
    dc_asdict = _fail


def default_encoder(obj, dict_factory=dict, date_as_unix_time=False):
    if hasattr(obj, "isoformat"):  # date, datetime, arrow
        if date_as_unix_time:
            if obj.__class__.__name__ == "Arrow":
                if callable(obj.timestamp):
                    return obj.timestamp()
                return obj.timestamp
            return calendar.timegm(obj.timetuple())
        return obj.isoformat()

    if isinstance(obj, (Decimal, uuid.UUID)):
        return str(obj)

    if isinstance(obj, set):
        return list(obj)

    if enum is not None and isinstance(obj, enum.Enum):
        return obj.name

    if isinstance(obj, ItemsView):
        return dict_factory(obj)

    if hasattr(obj, "asdict"):
        return dict_factory(obj.asdict().items())

    if hasattr(obj, "__module__") and "sqlalchemy" in obj.__module__:
        if obj.__class__.__name__ == "RowProxy":
            return dict_factory(obj.items())
        if obj.__class__.__name__ == "Row":
            return dict_factory(obj)

    if obj.__class__.__name__ == "Record":  # asyncpg
        return dict_factory(obj)

    if hasattr(obj, "__dataclass_fields__"):  # dataclasses
        return dc_asdict(obj, dict_factory=dict_factory)

    if hasattr(obj, "__attrs_attrs__"):  # attrs
        return attr_asdict(obj, dict_factory=dict_factory)

    if hasattr(obj, "__html__"):
        return str(obj.__html__())

    _fail(obj)


def raw_encoder(obj, date_as_unix_time=False):
    """Return representation of values that are not encodable instead of encoding them."""
    try:
        return default_encoder(
            obj, dict_factory=mask_dict, date_as_unix_time=date_as_unix_time
        )
    except TypeError:
        return repr(obj)


class MaskedJSONEncoder(BaseJSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        return default_encoder(o, mask_dict)

    def encode(self, o):
        if isinstance(o, dict):
            o = mask_dict(o)
        return super().encode(o)


class KiwiJSONEncoder(BaseJSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        return default_encoder(o)


def modify_kwargs(kwargs):
    # To keep consistent behavior even if simplejson behaves differently by default
    # See #7
    if simplejson_available:
        kwargs.setdefault("use_decimal", False)
    if "default" not in kwargs:
        date_as_unix_time = kwargs.pop("date_as_unix_time", False)
        kwargs["default"] = partial(
            default_encoder, date_as_unix_time=date_as_unix_time
        )


def format_value(value, precision):
    """Format provided value."""
    if isinstance(value, float):
        return round(value, precision)
    if isinstance(value, (list, set)):
        return traverse_iterable(value, precision)
    if (
        isinstance(value, ItemsView)
        or value.__class__.__name__ == "dictionary-itemiterator"
    ):
        return traverse_dict(dict(value), precision)
    if isinstance(value, dict):
        return traverse_dict(value, precision)
    if isinstance(value, tuple):
        if getattr(value, "_fields", False):
            # namedtuple should stay namedtuple - simplejson can format it differently
            # depending on the `namedtuple_as_object` param
            NewNamedtuple = namedtuple(type(value).__name__, value._asdict().keys())
            return NewNamedtuple(**format_value(value._asdict(), precision))
        # convert tuple to list; the tuple would be turned to list in simplejson/json anyways
        return traverse_iterable(list(value), precision)
    return value


def traverse_iterable(iterable, precision):
    """Traverse list or set and round floats."""
    return [format_value(value, precision) for value in iterable]


def traverse_dict(obj, precision):
    """Traverse dictionary and round floats."""
    return {key: format_value(value, precision) for key, value in obj.items()}


def round_floats(args, kwargs):
    data = args[0]
    precision = kwargs.pop("precision", False)
    new_args = list(args)
    if precision is not False:
        data = format_value(data, precision)
        new_args[0] = data
    return new_args


def dumps(*args, **kwargs):
    new_args = round_floats(args, kwargs)
    modify_kwargs(kwargs)
    return _dumps(*new_args, **kwargs)


def dump(*args, **kwargs):
    new_args = round_floats(args, kwargs)
    modify_kwargs(kwargs)
    return _dump(*new_args, **kwargs)
