class MediaWikiError(Exception):
    """Base error for the MediaWiki client."""


class NotMediaWiki(MediaWikiError):
    """The site at base_url is unreachable or is not a MediaWiki."""


class PageNotFound(MediaWikiError):
    """The requested page was not found in the wiki."""
