"""Validation helpers for code that is configured by a case."""


def require_parameters(**parameters) -> None:
    """Reject missing execution-specific parameters with a useful message."""

    missing = [name for name, value in parameters.items() if value is None]
    if missing:
        names = ", ".join(missing)
        raise ValueError(
            f"missing execution parameters: {names}; configure them in a script under cases/"
        )
