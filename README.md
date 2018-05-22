# Kiwi JSON

![Kiwi JSON Logo](logo.jpg "Kiwi JSON")


# Purpose

At the time of creating this lib, there were (at least) three implementation of `default_encoder()`
 copy-pasted from one place, evolving its own way and about to being copy-pasted further.
 If you have read the story about AI and paperclips, you have an idea where this would lead us to.

To prevent this from happening, this library should unify all the implementation, and provide reusable
 implementation of the JSON encoding.



# Installation

Add `kiwi-json` into your requirements (plus our PyPI, if you don't have it there already)

```
--extra-index-url https://pypi.skypicker.com/pypi

kiwi-json
```

# Usage

If you use your own JSON encoder as a class, use `default_encoder()` in there.

```
from kw.json import default_encoder

class OurJSONEncoder(simplejson.JSONEncoder):

    def default(self, obj):
        return default_encoder(obj, mask_dict)
```


If you want to use `json.dumps` directly, you can do it the following way:

```
from kw.json import default_encoder

dumps = partial(simplejson.dumps, default=default_encoder)
```
