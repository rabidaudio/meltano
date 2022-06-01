"""Snowplow Tracker."""

from __future__ import annotations

import re
import sys
from typing import Any
from urllib.parse import urlparse
import uuid

from snowplow_tracker import Emitter, SelfDescribingJson, Tracker
from structlog.stdlib import get_logger

import meltano
from meltano.core.project import Project
from meltano.core.project_settings_service import ProjectSettingsService

URL_REGEX = (
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)

logger = get_logger(__name__)


def check_url(url: str) -> bool:
    """Check if the given URL is valid.

    Args:
        url: The URL to check.

    Returns:
        True if the URL is valid, False otherwise.
    """
    return bool(re.match(URL_REGEX, url))


class SnowplowTracker(Tracker):
    """Meltano Snowplow Tracker."""

    def __init__(self, project: Project, *, request_timeout: int = 2.0, **kwargs: Any):
        """Create a Snowplow Tracker for the Meltano project.

        Args:
            project: The Meltano project.
            request_timeout: The timeout for all the event emitters.
            kwargs: Additional arguments to pass to the parent snowplow Tracker class.
        """
        settings_service = ProjectSettingsService(project)
        endpoints = settings_service.get("snowplow.collector_endpoints")

        emitters: list[Emitter] = []
        for endpoint in endpoints:
            if not check_url(endpoint):
                logger.warning("invalid_snowplow_endpoint", endpoint=endpoint)
                continue
            parsed_url = urlparse(endpoint)
            emitters.append(
                Emitter(
                    endpoint=parsed_url.hostname + parsed_url.path,
                    protocol=parsed_url.scheme or "http",
                    port=parsed_url.port,
                    request_timeout=request_timeout,
                )
            )

        # TODO: Should this be instantiated upstream, e.g. at the project level?
        self.meltano_context = SelfDescribingJson(
            "TODO",
            {
                "project_id": ProjectSettingsService(project).get("project_id"),
                "meltano_version": meltano.__version__,
                "python_version": sys.version,
                "operating_system": sys.platform,  # TODO: check if it has all the info we want
                "context_uuid": uuid.uuid4(),
                "environment": (
                    project.active_environment.name
                    if project.active_environment
                    else None
                ),
            },
        )

        super().__init__(emitters=emitters, **kwargs)
