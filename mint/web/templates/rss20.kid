<?xml version="1.0"?>
<rss version="2.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:py="http://purl.org/kid/ns#">
<channel>
    <title>$title</title>
    <link>$link</link>
    <language>en</language>
    <description>$desc</description>
    <item py:for="item in items">
        <title>${item['title']}</title>
        <guid>${item['link']}</guid>
        <link>${item['link']}</link>
        <description py:if="'content' in item">${item['content']}</description>
        <pubDate>${item['date_822']}</pubDate>
        <dc:creator>${item['creator']}</dc:creator>
    </item>
</channel>
</rss>
