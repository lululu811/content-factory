"""
content-factory-server: HTTP API 服务

提供 RESTful API 接口，触发和监控文章生产流程。
"""

from content_factory_server.app import create_app

__version__ = "1.0.0"

__all__ = ["create_app"]
