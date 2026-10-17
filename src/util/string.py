_VALID_VAR_CHARS = (
    {chr(i) for i in range(ord("a"), ord("z") + 1)}
    | {chr(i) for i in range(ord("A"), ord("Z") + 1)}
    | {chr(i) for i in range(ord("0"), ord("9") + 1)}
    | {"_", "[", "]"}
)


def is_valid_var_name(name: str) -> bool:
    return all(c in _VALID_VAR_CHARS for c in name)


def to_var_name(display_name: str) -> str:
    name = display_name.strip().lower().replace(" ", "_")
    if not is_valid_var_name(name):
        raise ValueError(
            f"display name '{display_name}' could not "
            "be converted to a valid formatted name"
        )

    return name
