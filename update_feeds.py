import hashlib
from functools import cache
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = 'https://raw.githubusercontent.com/zzcast/podcast-feeds/main/'
LINK = 'https://github.com/zzcast/podcast-feeds'
ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
NS = {'itunes': ITUNES}
ITEM_TAGS = ('title', 'description', 'link', 'guid', 'pubDate', 'itunes:title', 'itunes:summary', 'itunes:duration', 'itunes:explicit', 'itunes:episodeType')
COLONEL = re.compile(r'настоящ\w* полковник')


def is_reading(text):
    return 'читает сергей бунтман' in text or 'читалка' in text


GVOZD_PEOPLE = ('венедиктов', 'белковск', 'кашин', 'латынин', 'левиев')


def gvozd(text):
    return any(name in text for name in GVOZD_PEOPLE)


def diletant(text):
    paragraph = 'параграф 43' in text
    return (not is_reading(text) or paragraph) and not COLONEL.search(text)


def chitalka(text):
    return is_reading(text) and 'параграф 43' not in text


# chitalka-v2.xml is a second published URL for the same feed; both stay in sync so neither subscription goes stale.
FEEDS = (
    (('zhivoy-gvozd.xml',), 'https://cloud.mave.digital/41353', 'Живой Гвоздь — избранное', 'Выпуски с Венедиктовым, Белковским, Кашиным, Латыниной и Левиевым.', 'zhivoy-gvozd.png', gvozd),
    (('diletant.xml',), 'https://cloud.mave.digital/41365', 'Дилетант', 'Дилетант, включая Параграф 43, без чтений Сергея Бунтмана и «Настоящего полковника».', 'diletant.png', diletant),
    (('chitalka.xml', 'chitalka-v2.xml'), 'https://cloud.mave.digital/41365', 'Читалка — Дилетант', 'Выпуски чтения Сергея Бунтмана, кроме Параграфа 43.', 'chitalka.png', chitalka),
)


@cache
def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'podcast-feeds'})
    return ET.fromstring(urllib.request.urlopen(request, timeout=60).read()).findall('./channel/item')


def lower(item, tag):
    return item.findtext(tag, '', NS).strip().lower()


def newest_date(items):
    dates = []
    for item in items:
        try:
            date = parsedate_to_datetime(item.findtext('pubDate', ''))
        except (TypeError, ValueError):
            continue
        # A '-0000' zone parses naive and 'GMT' parses aware; max() cannot compare the two.
        dates.append(date if date.tzinfo else date.replace(tzinfo=timezone.utc))
    return max(dates, default=None)


def build(source_url, title, description, icon, keep):
    # Content hash, not a hand-bumped version: apps cache artwork by URL.
    art = f'{RAW}{icon}?v={hashlib.sha1((ROOT / icon).read_bytes()).hexdigest()[:8]}'
    items = [i for i in fetch(source_url) if keep(' '.join(lower(i, tag) for tag in ('title', 'description', 'itunes:summary')))]
    # A source that is empty, truncated or reworded past the filters must not publish an empty feed.
    if not items:
        raise SystemExit(f'{title}: no episodes selected from {source_url}')
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')
    # Newest episode date, not the run time, so an unchanged feed writes byte-identical XML.
    newest = newest_date(items)
    for tag, value in (('title', title), ('description', description), ('link', LINK), ('language', 'ru'), ('lastBuildDate', newest and format_datetime(newest))):
        if value:
            ET.SubElement(channel, tag).text = value
    image = ET.SubElement(channel, 'image')
    for tag, value in (('url', art), ('title', title), ('link', LINK)):
        ET.SubElement(image, tag).text = value
    ET.SubElement(channel, f'{{{ITUNES}}}image', {'href': art})
    for item in items:
        output = ET.SubElement(channel, 'item')
        for tag in ITEM_TAGS:
            node = item.find(tag, NS)
            if node is not None and (node.text or '').strip():
                ET.SubElement(output, node.tag, dict(node.attrib)).text = node.text
        enclosure = item.find('enclosure')
        if enclosure is not None:
            ET.SubElement(output, 'enclosure', dict(enclosure.attrib))
    return ET.ElementTree(rss)


ET.register_namespace('itunes', ITUNES)
# Build every feed before writing any, so a failing source never leaves them half-updated.
trees = [(filenames, build(*spec)) for filenames, *spec in FEEDS]
for filenames, tree in trees:
    for filename in filenames:
        tree.write(ROOT / filename, encoding='utf-8', xml_declaration=True)
