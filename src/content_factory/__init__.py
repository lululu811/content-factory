"""content-factory: 投研型公众号深度文生产流水线。

Public API is re-exported from submodules for convenience.
"""

from content_factory import cninfo, compliance, images, pipeline, research, utils

__version__ = "0.2.0"
__author__ = "chenliitaz"
__email__ = "chenliitaz@gmail.com"

__all__ = [
    "cninfo",
    "compliance",
    "images",
    "pipeline",
    "research",
    "utils",
    "__version__",
]
