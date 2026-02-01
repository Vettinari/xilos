from ._build.generator import ProjectGenerator
from .xilos_settings import xsettings

try:
    import loguru

    plot = loguru.logger.info
except ImportError:
    plot = print


def main():
    plot("Starting Xilos ML Project Generator...")

    plot(f"Loaded project: {xsettings.project.name}")
    plot(f"Cloud Provider: {xsettings.cloud.provider}")
    plot(f"Cloud Storage: {xsettings.cloud.source}")
    plot(f"Cloud Metrics: {xsettings.cloud.metrics}")

    generator = ProjectGenerator()
    generator.run()


if __name__ == "__main__":
    main()
