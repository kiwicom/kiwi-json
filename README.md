# Kiwi JSON

![Kiwi JSON Logo](logo.jpg "Kiwi JSON")

# Purpose

At the time of creating this lib, there were (at least) three implementation of `default_encoder()`
 copy-pasted from one place, evolving its own way and about to being copy-pasted further.
 If you have read the story about AI and paperclips, you have an idea where this would lead us to.

To prevent this from happening, this library should unify all the implementation, and provide reusable
 implementation of the JSON encoding.

# Installation

Add `kiwi-json` into your requirements.in file

```
kiwi-json
```

# Usage

If you use your own JSON encoder as a class, use `default_encoder()` in there.

```python
import simplejson
from kw.json import default_encoder, mask_dict

class OurJSONEncoder(simplejson.JSONEncoder):

    def default(self, obj):
        return default_encoder(obj, mask_dict)
```

`kiwi-json` provides a simple implementation for masking dictionary values with `kw.json.mask_dict`. 
Or you can create a masking function for it by yourself. It supports customizing placeholder, blacklist and whitelist:

```python
from kw.json import mask_dict_factory

mask_dict = mask_dict_factory(placeholder='0_0', blacklist={'secret'}, whitelist={'not-so-secret'})
```

If you want to use `json.dumps` directly, you can do it the following way:

```python
import simplejson
from kw.json import default_encoder

dumps = partial(simplejson.dumps, default=default_encoder)
```

If you have `simplejson` installed, you can use Decimal as JSON `number` type:
```python
from decimal import Decimal
from kw.json import dumps, loads

assert dumps({"num": Decimal("1.234")}, use_decimal=True) == '{"num": 1.234}'
assert loads('{"num": 1.234}', use_decimal=True) == {"num": Decimal("1.234")}
```

Flask-based application could utilize the extension:

```python
from kw.json.flask import JSONExtension


def create_app():
    ...
    JSONExtension(app)
    ...
```

Extension will install an encoder to given app.

If you want to make sure that the encoder dumps classes, you can use the `raw_encoder`:

```python
from kw.json import raw_encoder, dumps

dumps(data, default=raw_encoder)
```

To dump dates and datetimes as unix time, use `date_as_unix_time=True`:

```python
import arrow
from datetime import datetime
from kw.json import dumps

dumps({1: datetime.now(), 2: arrow.now()}, date_as_unix_time=True)
```

If you want to combine the powers of `date_as_unix_time` and `raw_encoder`,
you can create your own encoder using partial:

```python
from kw.json import dumps, raw_encoder
from functools import partial

my_encoder = partial(raw_encoder, date_as_unix_time=True)
dumps(obj, default=my_encoder)
```

# Running tests

To run the tests we use tox. Before you can run the tests please make sure you have postgres database running and the DATABASE_URI env variable set

```bash
export DATABASE_URI='postgres://[username]:[password]@[host]:[port]/[database]'
```

Once you have this set up just execute:

```
tox
```
