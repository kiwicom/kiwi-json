DEFAULT_PLACEHOLDER = "-- MASKED --"
DEFAULT_BLACKLIST = frozenset(("secret", "token", "password", "key", "zoozappkey"))
DEFAULT_WHITELIST = frozenset(("booking_token", "public_key", "idempotency_key"))


def mask_dict_factory(
    placeholder=DEFAULT_PLACEHOLDER,
    blacklist=DEFAULT_BLACKLIST,
    whitelist=DEFAULT_WHITELIST,
):
    def mask_dict(pairs):
        """Return a dict with dangerous looking key/value pairs masked."""
        if pairs is None:
            return {}

        if isinstance(pairs, dict):
            items = pairs.items()
        else:
            items = pairs

        return {
            key: (
                placeholder
                if key.lower() not in whitelist
                and any(word in key.lower() for word in blacklist)
                else value
            )
            for key, value in items
        }

    return mask_dict


mask_dict = mask_dict_factory()
