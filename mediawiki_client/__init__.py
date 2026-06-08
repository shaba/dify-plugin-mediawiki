"""Pure MediaWiki plugin core: derive_api, siteinfo, search, get_page.

Does not depend on dify_plugin — covered by unit tests with mocked requests.
The Tool/Provider (Dify SDK) layers are thin adapters on top of this module.
Requests are made only to the base_url from credentials; no third-party
addresses are used by this module.
"""

from .api import derive_api, siteinfo, validate_mediawiki
from .errors import MediaWikiError, NotMediaWiki, PageNotFound
from .page import get_page
from .search import format_search, search

__all__ = [
    "derive_api",
    "siteinfo",
    "validate_mediawiki",
    "search",
    "format_search",
    "get_page",
    "MediaWikiError",
    "NotMediaWiki",
    "PageNotFound",
]
