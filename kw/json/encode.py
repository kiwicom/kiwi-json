from collections import ItemsView
from decimal import Decimal
from functools import partial
import uuid

from ._compat import BaseJSONEncoder, enum, json_dumps
from .utils import mask_dict


def _fail(obj, *args, **kwargs):
    raise TypeError("Object of type {} is not JSON serializable".format(obj.__class__.__name__))


try:
    from attr import asdict as attr_asdict
except ImportError:
    attr_asdict = _fail

try:
    from dataclasses import asdict as dc_asdict
except ImportError:
    dc_asdict = _fail


def default_encoder(obj, dict_factory=dict):  # Ignore RadonBear
    if hasattr(obj, "isoformat"):  # date, datetime, arrow
        return obj.isoformat()

    if isinstance(obj, (Decimal, uuid.UUID)):
        return str(obj)

    if isinstance(obj, set):
        return list(obj)

    if enum is not None and isinstance(obj, enum.Enum):
        return obj.name

    # Second option is for `iteritems()` on Python 2
    if isinstance(obj, ItemsView) or obj.__class__.__name__ == "dictionary-itemiterator":
        return dict_factory(obj)

    if hasattr(obj, "asdict"):  # dictablemodel
        return dict_factory(obj.asdict().items())

    if obj.__class__.__name__ == "RowProxy":  # sqlalchemy
        return dict_factory(obj.items())

    if hasattr(obj, "__dataclass_fields__"):  # dataclasses
        return dc_asdict(obj, dict_factory=dict_factory)

    if hasattr(obj, "__attrs_attrs__"):  # attrs
        return attr_asdict(obj, dict_factory=dict_factory)

    if hasattr(obj, "__html__"):
        return str(obj.__html__())

    _fail(obj)


class MaskedJSONEncoder(BaseJSONEncoder):
    def default(self, obj):  # pylint: disable=method-hidden
        return default_encoder(obj, mask_dict)

    def encode(self, o):
        if isinstance(o, dict):
            o = mask_dict(o)
        return super(MaskedJSONEncoder, self).encode(o)


class KiwiJSONEncoder(BaseJSONEncoder):
    def default(self, obj):  # pylint: disable=method-hidden
        return default_encoder(obj)


dumps = partial(json_dumps, default=default_encoder)
