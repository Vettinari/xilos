from typing import Any, Dict

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
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

def to_toml_string(data: Dict[str, Any]) -> str:
    """
    Simple TOML serializer for pyproject.toml structure.
    Does not support all TOML features, mainly nested dicts and basic types.
    """
    lines = []
    
    # Process [tool.poetry] first if exists, to keep it at top
    if "tool" in data and "poetry" in data["tool"]:
        # We'll flatten this later or just handle sections recursively
        pass

    def _format_value(v):
        if isinstance(v, bool):
            return str(v).lower()
        elif isinstance(v, list):
            # rudimentary list formatting
            items = ", ".join([f'"{x}"' if isinstance(x, str) else str(x) for x in v])
            return f"[{items}]"
        elif isinstance(v, str):
            # basic escaping
            return f'"{v}"'
        return str(v)

    def _write_section(prefix, section_data):
        for key, value in section_data.items():
            if isinstance(value, dict):
                new_prefix = f"{prefix}.{key}" if prefix else key
                # Check if it's a section (dict of dicts or values)
                # In TOML, [a.b]
                # We defer writing the header until we know it has primitive children or we recurse
                # Actually, standard TOML usually groups primitives then subsections.
                
                # Check if this dict has sub-dicts (sections) or just values
                has_subsections = any(isinstance(v, dict) for v in value.values())
                
                if not has_subsections:
                     # It's a leaf section like [tool.poetry.dependencies]
                     lines.append(f"\n[{new_prefix}]")
                     for k, v in value.items():
                         lines.append(f"{k} = {_format_value(v)}")
                else:
                    # It has mixed or just subsections.
                    # Write primitives first?
                    # For pyproject.toml, usually it's deep nesting.
                    # simpler approach: Flatten keys?
                    _write_section(new_prefix, value)
            else:
                # Top level key-value? (Only valid if prefix is empty or we are inside a section)
                # If prefix is empty, it's global.
                if not prefix:
                    lines.append(f"{key} = {_format_value(value)}")
                # If prefix exists, we should have written the header already? 
                # Our recursive logic above prints headers only for leaf dicts. 
                # This is tricky for [tool.poetry] which has mixed content.
                pass

    # Better approach for TOML serialization of specific pyproject structure:
    # 1. Flatten into (Section, Key, Value) tuples?
    # 2. Or recursive walk that prints [Section] when it enters a dict that contains primitives.
    
    seen_sections = set()
    
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
    for k, v in top_dicts.items():
        _walk(k, v)
        
    return "\n".join(lines).strip() + "\n"
