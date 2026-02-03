from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merges two dictionaries.
    Override values replace base values, except for dictionaries which are merged recursively.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def to_toml_string(data: dict[str, Any]) -> str:
    """
    Simple TOML serializer for pyproject.toml structure.
    Does not support all TOML features, mainly nested dicts and basic types.
    """
    lines = []

    def _format_value(v):
        if isinstance(v, bool):
            return str(v).lower()
        elif isinstance(v, list):
            # Format list elements
            items = [_format_value(x) for x in v]
            return f"[{', '.join(items)}]"
        elif isinstance(v, dict):
            # Format inline table
            items = [f"{k} = {_format_value(val)}" for k, val in v.items()]
            return f"{{ {', '.join(items)} }}"
        elif isinstance(v, str):
            # basic escaping
            return f'"{v}"'
        return str(v)

    def _write_section(prefix, section_data):
        for key, value in section_data.items():
            if isinstance(value, dict):
                new_prefix = f"{prefix}.{key}" if prefix else key
                has_subsections = any(isinstance(v, dict) for v in value.values())

                if not has_subsections:
                    lines.append(f"\n[{new_prefix}]")
                    for k, v in value.items():
                        lines.append(f"{k} = {_format_value(v)}")
                else:
                    _write_section(new_prefix, value)
            else:
                if not prefix:
                    lines.append(f"{key} = {_format_value(value)}")
                pass

    def _walk(path, node):
        # Separate children into primitives and dicts
        primitives = {k: v for k, v in node.items() if not isinstance(v, dict)}
        dicts = {k: v for k, v in node.items() if isinstance(v, dict)}

        if path and primitives:
            lines.append(f"\n[{path}]")
            for k, v in primitives.items():
                lines.append(f"{k} = {_format_value(v)}")

        for k, v in dicts.items():
            new_path = f"{path}.{k}" if path else k
            _walk(new_path, v)

    # Handle top-level primitives first
    top_primitives = {k: v for k, v in data.items() if not isinstance(v, dict)}
    for k, v in top_primitives.items():
        lines.append(f"{k} = {_format_value(v)}")

    # Then sections
    top_dicts = {k: v for k, v in data.items() if isinstance(v, dict)}

    # Force [tool] to be first if present
    if "tool" in top_dicts:
        _walk("tool", top_dicts["tool"])
        del top_dicts["tool"]

    for k, v in top_dicts.items():
        _walk(k, v)

    return "\n".join(lines).strip() + "\n"
