from . import xsettings
from ._build.builder import ProjectBuilder
from ._build.steps import (
    BaseAssetsStep,
    CodeDeployStep,
    ConfigStep,
    PipelineStep,
    StructureStep,
)


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

    builder = ProjectBuilder()
    builder.register(StructureStep())
    builder.register(BaseAssetsStep())
    builder.register(PipelineStep())
    builder.register(CodeDeployStep())
    builder.register(ConfigStep())

    builder.build()


if __name__ == "__main__":
    main()
