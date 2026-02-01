import tomllib

from ._build.toml_merger import deep_merge, to_toml_string
from .xilos_settings import xsettings


def compile_project():
    """
    Compiles a master pyproject.toml from src/xilos/pyproject.toml
    and all provider/module pyproject.toml files in src/xilos/_template.
    """
    src_dir = xsettings.XILOS_ROOT / "src" / "xilos" / "_template"

    # 1. Load Base Config
    # Base is at src/xilos/_template/pyproject.toml
    base_toml = xsettings.XILOS_ROOT / "src" / "xilos" / "_template" / "pyproject.toml"
    if not base_toml.exists():
        print(f"Base pyproject.toml not found at {base_toml}")
        return

    print(f"Loading base config from {base_toml}")
    with open(base_toml, "rb") as f:
        config = tomllib.load(f)

    # 2. Find and Merge Templates
    # We look for all pyproject.toml files in _template
    template_dir = src_dir
    if template_dir.exists():
        for path in template_dir.rglob("pyproject.toml"):
            if path == base_toml:
                continue  # Skip base config

            print(f"Merging config from {path.relative_to(xsettings.XILOS_ROOT)}")
            with open(path, "rb") as f:
                sub_config = tomllib.load(f)

            config = deep_merge(config, sub_config)

    # 3. Write to Project Root
    output_path = xsettings.XILOS_ROOT / "pyproject.toml"
    print(f"Writing compiled pyproject.toml to {output_path}")

    with open(output_path, "w") as f:
        f.write(to_toml_string(config))

    print("Compilation complete.")


if __name__ == "__main__":
    compile_project()
