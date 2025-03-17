# Daemon client-specific mappings
def keyboard_key_to_daemon(key: Union[KeyboardKey, str]) -> ClientKeyboardKey:
    """Convert KeyboardKey to Daemon client KeyboardKey.

    The daemon client uses its own KeyboardKey enum that should match our KeyboardKey values.
    This function ensures proper conversion between the two.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # The daemon client's KeyboardKey enum should have the same values as our KeyboardKey enum
    # We just need to convert to the client's enum type
    try:
        return ClientKeyboardKey(key.value)
    except ValueError:
        # If the key value doesn't exist in the client's enum, use a fallback
        logging.warning(
            f"Key {key} not found in daemon client KeyboardKey enum, using fallback"
        )
        return ClientKeyboardKey.ENTER  # Use a safe default
