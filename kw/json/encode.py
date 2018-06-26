from collections import ItemsView
from decimal import Decimal
import uuid

from ._compat import enum


def _missing(obj, *args, **kwargs):
    raise TypeError("Dependency missing for serialization of {}".format(obj.__class__.__name__))


try:
    from attr import asdict as attr_asdict
except ImportError:
    attr_asdict = _missing

try:
    from dataclasses import asdict as dc_asdict
except ImportError:
    dc_asdict = _missing


def default_encoder(obj, dict_factory=dict):
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
        return dc_asdict(obj, dict_factory=dict_factory).items()

    if hasattr(obj, "__attrs_attrs__"):  # attrs
        return attr_asdict(obj, dict_factory=dict_factory).items()

    if hasattr(obj, "__html__"):
        return str(obj.__html__())

    raise TypeError("Object of type {} is not JSON serializable".format(obj.__class__.__name__))


def mask_dict_factory(
    placeholder="-- MASKED --",
    blacklist=frozenset(("secret", "token", "password", "key", "zoozappkey")),
    whitelist=frozenset(("booking_token", "public_key", "idempotency_key")),
):
    def mask_dict(pairs):
        """Return a dict with dangerous looking key/value pairs masked."""
        if pairs is None:
            return {}

        return {
            key: (
                placeholder
                if key.lower() not in whitelist and any(word in key.lower() for word in blacklist)
                else value
            )
            for key, value in pairs
        }

    return mask_dict


mask_dict = mask_dict_factory()
