def mouse_button_to_daemon(button: Union[MouseButton, str]) -> ClientMouseButton:
    """Convert MouseButton to Daemon client MouseButton.

    The daemon client uses its own MouseButton enum that should match our MouseButton values.
    This function ensures proper conversion between the two.
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # The daemon client's MouseButton enum should have the same values as our MouseButton enum
    # We just need to convert to the client's enum type
    try:
        return ClientMouseButton(button.value)
    except ValueError:
        # If the button value doesn't exist in the client's enum, use a
        # fallback
        logging.warning(
            f"Button {button} not found in daemon client MouseButton enum, using fallback"
        )
        return ClientMouseButton.LEFT  # Use a safe default
