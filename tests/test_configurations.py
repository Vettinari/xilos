import shutil
import tomllib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from xilos._build.generator import ProjectGenerator
from xilos.xilos_settings import XilosSettings, CloudSettings, DescriptiveSettings, RepositorySettings, MonitorSettings


# Re-creating a simplified version of the settings dataclasses for creating test data
# Note: In the actual code, xsettings are instantiated from a dict, but for mocking
# it's cleaner to mock the object attributes directly or the `load` result.

def create_mock_settings(project_name, cloud_provider, cloud_source, cloud_metrics):
    # Mocking the xsettings object structure
    mock_settings = MagicMock(spec=XilosSettings)
    
    # Project
    mock_settings.project = MagicMock()
    mock_settings.project.name = project_name
    
    # Cloud
    mock_settings.cloud = MagicMock()
    mock_settings.cloud.provider = cloud_provider
    mock_settings.cloud.source = cloud_source
    mock_settings.cloud.metrics = cloud_metrics
    
    # Repository (Standard defaults)
    mock_settings.repository = MagicMock()
    mock_settings.repository.type = "github"
    
    # Monitor (Standard defaults)
    mock_settings.monitor = MagicMock()
    mock_settings.monitor.numeric_threshold = 0.05
    mock_settings.monitor.numerical = "wasserstein"
    mock_settings.monitor.categorical = "pci"
    mock_settings.monitor.source = "gcs"
    mock_settings.monitor.metrics = "bigquery"
    
    # Root paths
    # We need to ensure XILOS_ROOT points to the actual project root so templates are found
    # Assuming tests are run from project root or `tests/`
    # If run from project root, `Path.cwd()` or `Path(__file__).parent.parent`
    
    # Let's try to detect the project root relative to this test file
    # This file: tests/test_configurations.py
    # Root: tests/../
    project_root = Path(__file__).resolve().parent.parent
    mock_settings.XILOS_ROOT = project_root
    
    return mock_settings


class TestProjectGenerationConfigs:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Setup: nothing specific besides what's locally created
        self.created_paths = []
        yield
        # Teardown: clean up generated projects
        for path in self.created_paths:
            if path.exists():
                shutil.rmtree(path)

    @patch('xilos._build.generator.xsettings')
    def test_gcp_configuration(self, mock_xsettings):
        """Test generation with GCP configuration."""
        name = "TestBuild_GCP"
        mock_xsettings.project.name = name
        mock_xsettings.cloud.provider = "gcp"
        mock_xsettings.cloud.source = "gcs"
        mock_xsettings.cloud.metrics = "bigquery"
        mock_xsettings.repository.type = "github"
        mock_xsettings.XILOS_ROOT = Path(__file__).resolve().parent.parent
        
        generator = ProjectGenerator()
        # generator.settings is assigned in __init__, so we need to ensure the mock is active 
        # BEFORE init. @patch deals with the import in the module.
        # But wait, ProjectGenerator.__init__ does: self.settings = xsettings
        # So passing mock_xsettings to the patch should work.
        
        # Override the bound settings instance on the generator if needed, 
        # but since validation is done in run(), and __init__ copies reference...
        # Let's just double check the patch target.
        # patching 'xilos._build.generator.xsettings' should replace the object imported in generator.py
        
        generator.run()
        
        project_dir = mock_xsettings.XILOS_ROOT / "composed" / name
        self.created_paths.append(project_dir)
        
        assert project_dir.exists(), f"Project directory {project_dir} was not created"
        
        # Check pyproject.toml
        pyproject_path = project_dir / "pyproject.toml"
        assert pyproject_path.exists()
        
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
            
        deps = config.get("tool", {}).get("poetry", {}).get("dependencies", {})
        dev_deps = config.get("tool", {}).get("poetry", {}).get("group", {}).get("dev", {}).get("dependencies", {})
        
        # Check GCP specific dependencies often land in a group or main
        # In the template `src/xilos/_template/xgcp/pyproject.toml`, they are in [tool.poetry.group.gcp.dependencies]
        # Our merger should preserve groups
        gcp_group = config.get("tool", {}).get("poetry", {}).get("group", {}).get("gcp", {}).get("dependencies", {})
        assert "google-cloud-storage" in gcp_group, "google-cloud-storage missing from generated config"
        
        # Check provider module existence
        assert (project_dir / "src" / "xilos" / "xgcp").exists()

    @patch('xilos._build.generator.xsettings')
    def test_aws_configuration(self, mock_xsettings):
        """Test generation with AWS configuration."""
        name = "TestBuild_AWS"
        mock_xsettings.project.name = name
        mock_xsettings.cloud.provider = "aws"
        mock_xsettings.cloud.source = "s3"
        mock_xsettings.cloud.metrics = "none" # or whatever
        mock_xsettings.repository.type = "github"
        mock_xsettings.XILOS_ROOT = Path(__file__).resolve().parent.parent

        generator = ProjectGenerator()
        generator.run()
        
        project_dir = mock_xsettings.XILOS_ROOT / "composed" / name
        self.created_paths.append(project_dir)
        
        assert project_dir.exists()
        
        pyproject_path = project_dir / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
            
        aws_group = config.get("tool", {}).get("poetry", {}).get("group", {}).get("aws", {}).get("dependencies", {})
        assert "boto3" in aws_group, "boto3 missing from generated config"
        
        assert (project_dir / "src" / "xilos" / "xaws").exists()

    @patch('xilos._build.generator.xsettings')
    def test_azure_configuration(self, mock_xsettings):
        """Test generation with Azure configuration."""
        name = "TestBuild_Azure"
        mock_xsettings.project.name = name
        mock_xsettings.cloud.provider = "azure"
        mock_xsettings.cloud.source = "blob"
        mock_xsettings.cloud.metrics = "none"
        mock_xsettings.repository.type = "github"
        mock_xsettings.XILOS_ROOT = Path(__file__).resolve().parent.parent

        generator = ProjectGenerator()
        generator.run()
        
        project_dir = mock_xsettings.XILOS_ROOT / "composed" / name
        self.created_paths.append(project_dir)
        
        assert project_dir.exists()
        
        pyproject_path = project_dir / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
            
        azure_group = config.get("tool", {}).get("poetry", {}).get("group", {}).get("azure", {}).get("dependencies", {})
        assert "azure-storage-blob" in azure_group, "azure-storage-blob missing from generated config"
        
        assert (project_dir / "src" / "xilos" / "xazure").exists()
