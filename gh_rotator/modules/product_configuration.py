import json
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class Verbosity(Enum):
    VERBOSE = auto()
    SILENT = auto()


@dataclass
class ConfigurationIdentifiers:
    repo: str
    event_name: str
    event_type: str


@dataclass
class ProductConfiguration:
    name: str
    components: list[ConfigurationIdentifiers]


def get_configurations_path(git_root: Path, file: Path | None) -> Path:
    """Get a Path to the most preferential configurations

    In order of precedence:
        - User passed configurations file (relative to repository root)
        - Repository configurations file ("config-rotator.json" in repo root)
        - Default configurations file ("config/config-rotator.json" in extension repo)

    Returns:
        configurations_path (Path): Path corresponding to the configurations to be used

    Raises:
        FileNotFoundError: when the user passed file is not found
    """

    if file is not None:
        p = Path(git_root / file)
        if Path.exists(p):
            return p

        raise FileNotFoundError

    repo_configurations = Path(git_root / "config-rotator.json")
    if Path.exists(repo_configurations):
        return repo_configurations

    default_configurations = (
        Path(__file__).resolve().parent.parent / "config" / "config-rotator.json"
    )
    assert Path.exists(default_configurations), (
        "A default configuration must exist in gh_rotator/config/config-rotator.json"
    )
    return default_configurations


def load_configurations(file: Path) -> dict:
    with Path.open(file) as f:
        return dict(json.load(f))


class ConfigurationsValidationError(Exception):
    """The configurations file is invalid"""


def validate_configurations(configurations: dict) -> set[ProductConfiguration]:
    # Configuration
    keys = set()
    for key in configurations:
        if key not in keys:
            keys.add(key)
        else:
            raise ConfigurationsValidationError(
                f"Duplicate key found: '{key}'. Configuration keys must be unique. Make sure keys are unique by renaming duplicates."
            )

    if len(configurations.keys()) != len(set(configurations.keys())):
        raise ConfigurationsValidationError("Each configuration must have a unique name.")


def get_config_name(
    configurations: set[ProductConfiguration],
    identifiers: ConfigurationIdentifiers,
    *,
    verbosity: Verbosity = Verbosity.SILENT,
) -> str | None:
    pass
