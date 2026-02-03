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

    builder = ProjectBuilder()
    builder.register(StructureStep())
    builder.register(BaseAssetsStep())
    builder.register(PipelineStep())
    builder.register(CodeDeployStep())
    builder.register(ConfigStep())

    builder.build()


if __name__ == "__main__":
    main()
