import datetime
from decimal import Decimal
import enum
import uuid


def default_encoder(self, obj):
    # Start ignoring RadonBear
    if isinstance(obj, datetime.datetime):
        if obj.tzinfo:
            # eg: 2015-09-25T23:14:42.588601+00:00
            return obj.isoformat('T')
        else:
            # No timezone present - assume UTC.
            # eg: 2015-09-25T23:14:42.588601Z
            return obj.isoformat('T') + 'Z'

    if isinstance(obj, datetime.date):
        return obj.isoformat()

    if isinstance(obj, (Decimal, uuid.UUID)):
        return str(obj)

    if isinstance(obj, set):
        return list(obj)

    if isinstance(obj, enum.Enum):
        return obj.name

    if obj.__class__.__name__ == 'RowProxy':
        return dict(obj.items())

    if obj.__class__.__name__ == 'ItemsView':
        return dict(obj)

    if hasattr(obj, '__dataclass_fields__'):  # dataclasses
        return {}
        # WIP return mask_dict(dataclasses.asdict(obj).items())

    if hasattr(obj, '__attrs_attrs__'):  # attrs
        return {}
        # return mask_dict(attr.asdict(obj).items())

    if hasattr(obj, 'asdict'):
        obj_dict = obj.asdict()
        return mask_dict(obj_dict.items())

    if hasattr(obj, '__html__'):
        return str(obj.__html__())

    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def mask_dict(dict):
    """Sanitize sensitive data."""
    return dict  # XXX - make pluggable
