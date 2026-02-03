from ._build.generator import ProjectGenerator
from .xilos_settings import xsettings


def main():
    print("""
        ┌──────────────────────────────────────────────────────────┐
        │                                                          │
        │  :::    ::: ::::::::::: :::        ::::::::   ::::::::   │
        │  :+:    :+:     :+:     :+:       :+:    :+: :+:    :+:  │
        │   +:+  +:+      +:+     +:+       +:+    +:+ +:+         │
        │    +#++:+       +#+     +#+       +#+    +:+ +#++:++#++  │
        │   +#+  +#+      +#+     +#+       +#+    +#+        +#+  │
        │  #+#    #+#     #+#     #+#       #+#    #+# #+#    #+#  │
        │  ###    ### ########### ########## ########   ########   │
        │                                                          │
        │    Xomnia Integrated Launcher for Operational Stacks     │
        └──────────────────────────────────────────────────────────┘
            """)

    print("Starting Xilos ML Project Generator...")

    print(f"\t- Loaded project: {xsettings.project.name}")
    print(f"\t- Cloud Provider: {xsettings.cloud.provider}")

    generator = ProjectGenerator()
    generator.run()


if __name__ == "__main__":
    main()
