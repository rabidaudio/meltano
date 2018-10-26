import os
from enum import Enum
from meltano.core.project import Project


class PluginType(str, Enum):
    PROJECT = Project.find()
    EXTRACTORS = "extractors"
    LOADERS = "loaders"
    ALL = "all"
    EXTRACTORS_DIR = PROJECT.meltano_dir(EXTRACTORS)
    LOADERS_DIR = PROJECT.meltano_dir(LOADERS)

    def __str__(self):
        return self.value
