# dify-plugin-mediawiki

A Dify tool plugin to search and read pages on any MediaWiki site. The target wiki is
chosen per credential through a `base_url` parameter, so a single installation works
with any MediaWiki instance. Requests are made only to the site you configure.

## Configuration

The provider has one credential, `base_url`, which accepts either a bare domain
(`https://example.com`) or a direct API path (`https://example.com/api.php`,
`https://example.com/w/api.php`). The plugin derives the `api.php` endpoint on its own
and validates the credential with `action=query&meta=siteinfo`; if the site is
unreachable or is not a MediaWiki instance, the credential is rejected with a clear
error message.

## Tools

### `wiki_search`

Full-text search (`action=query&list=search`).

- `query` (string, required) — search query.
- `limit` (number, optional, default 5, range 1–50) — number of results.

Returns a list of entries with `title`, `snippet` (HTML stripped), and the page `url`.

### `wiki_get_page`

Read a page (`action=parse&page=<title>&prop=text`, following redirects).

- `title` (string, required) — exact page title.

Returns the article as clean markdown together with its `source_url`. A missing page
yields a clear message.

## Example

1. Set `base_url = https://example.com`.
2. Call `wiki_search` with `query = systemd` to get matching titles and URLs.
3. Call `wiki_get_page` with `title = Systemd` to get the article as markdown.

## Development

```sh
python3 -m pytest -q
ruff check .
yamllint .
```

The MediaWiki logic (endpoint discovery, siteinfo, search, parse, HTML→markdown) lives
in the `mediawiki_client` package, which is independent of the Dify SDK and covered by
unit tests with mocked network calls. The tool and provider classes are thin adapters
over it.

## License

Apache-2.0. Copyright © 2026 Alexey Shabalin.

## Repository

<https://github.com/shaba/dify-plugin-mediawiki> — issues and pull requests welcome.
