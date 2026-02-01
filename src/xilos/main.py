import sys

from loguru import logger

from ._build.generator import ProjectGenerator
from .xilos_settings import xsettings


def main():
    logger.info("Starting Xilos ML Project Generator...")

    if not xsettings.settings:
        logger.error("Configuration could not be loaded. Exiting.")
        sys.exit(1)

    logger.info(f"Loaded project: {xsettings.settings.project.name}")
    logger.info(f"Cloud Provider: {xsettings.cloud_provider}")
    logger.info(f"Cloud Storage: {xsettings.cloud_storage}")

    generator = ProjectGenerator()
    generator.run()


if __name__ == "__main__":
    main()
