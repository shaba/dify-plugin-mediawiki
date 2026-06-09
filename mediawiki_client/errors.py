class MediaWikiError(Exception):
    """Base error for the MediaWiki client."""


class MediaWikiAPIError(MediaWikiError):
    """The API returned HTTP 200 with a top-level ``error`` object.

    Carries the MediaWiki error ``code`` so callers can map specific codes
    (e.g. ``missingtitle``) to their own semantics.
    """

    def __init__(self, code: str, info: str) -> None:
        self.code = code
        self.info = info
        super().__init__(info or code or "MediaWiki API error")


class NotMediaWiki(MediaWikiError):
    """The site at base_url is unreachable or is not a MediaWiki."""


class PageNotFound(MediaWikiError):
    """The requested page was not found in the wiki."""
