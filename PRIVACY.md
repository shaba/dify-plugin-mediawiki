# Privacy Policy / Политика конфиденциальности

## English

This plugin (`dify-plugin-mediawiki`) does not collect, store or transmit any
personal data to the plugin author or any third party.

- The only configured credential is `base_url` — the URL of the MediaWiki site
  you choose. It is stored by your Dify instance, not by the plugin author.
- When you invoke a tool, the plugin sends HTTP GET requests **only** to that
  `base_url` (its `api.php` endpoint), carrying the search query or page title
  you provided. Requests use the User-Agent `dify-plugin-mediawiki/0.0.1`.
- No analytics, telemetry or external hosts are involved. No data is persisted
  by the plugin itself.

Your queries and the wiki content you read are subject to the privacy policy of
the MediaWiki site configured in `base_url`.

## Русский

Плагин (`dify-plugin-mediawiki`) не собирает, не хранит и не передаёт никаких
персональных данных автору плагина или третьим лицам.

- Единственный креденшл — `base_url`, URL выбранного вами сайта MediaWiki. Он
  хранится вашим экземпляром Dify, а не автором плагина.
- При вызове инструмента плагин отправляет HTTP GET-запросы **только** на этот
  `base_url` (его endpoint `api.php`), передавая ваш поисковый запрос или
  заголовок страницы. Запросы используют User-Agent `dify-plugin-mediawiki/0.0.1`.
- Никакой аналитики, телеметрии или внешних хостов. Сам плагин ничего не сохраняет.

Ваши запросы и читаемый контент подпадают под политику конфиденциальности сайта
MediaWiki, указанного в `base_url`.
