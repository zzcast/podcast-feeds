import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime

RAW = 'https://raw.githubusercontent.com/zzcast/podcast-feeds/main/'
ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
SOURCES = {
    'zhivoy-gvozd.xml': ('https://cloud.mave.digital/41353', 'Живой Гвоздь — избранное', 'Выпуски с Венедиктовым и Белковским.', 'zhivoy-gvozd.png'),
    'diletant.xml': ('https://cloud.mave.digital/41365', 'Дилетант', 'Дилетант, включая Параграф 43, без выпусков чтения Сергея Бунтмана.', 'diletant.png'),
    'chitalka.xml': ('https://cloud.mave.digital/41365', 'Читалка — Дилетант', 'Выпуски чтения Сергея Бунтмана, кроме Параграфа 43.', 'chitalka.png'),
}

def text(item, tag):
    node = item.find(tag)
    return (node.text or '').strip().lower() if node is not None else ''

def selected(name, item):
    value = ' '.join(text(item, tag) for tag in ('title', 'description', 'itunes:summary'))
    if name == 'zhivoy-gvozd.xml':
        return 'венедиктов' in value or 'белковск' in value
    paragraph = 'параграф 43' in value
    reading = 'читает сергей бунтман' in value or 'читалка' in value
    return (not reading or paragraph) if name == 'diletant.xml' else (reading and not paragraph)

ET.register_namespace('itunes', ITUNES)
for filename, (source_url, title, description, icon) in SOURCES.items():
    request = urllib.request.Request(source_url, headers={'User-Agent': 'podcast-feeds'})
    source = ET.fromstring(urllib.request.urlopen(request, timeout=60).read()).find('./channel')
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')
    for tag, value in (('title', title), ('description', description), ('link', 'https://github.com/zzcast/podcast-feeds'), ('language', 'ru'), ('lastBuildDate', format_datetime(datetime.now(timezone.utc)))):
        ET.SubElement(channel, tag).text = value
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'url').text = RAW + icon
    ET.SubElement(image, 'title').text = title
    ET.SubElement(image, 'link').text = 'https://github.com/zzcast/podcast-feeds'
    ET.SubElement(channel, f'{{{ITUNES}}}image', {'href': RAW + icon})
    for item in source.findall('./item'):
        if not selected(filename, item):
            continue
        output = ET.SubElement(channel, 'item')
        for tag in ('title', 'description', 'link', 'guid', 'pubDate', 'itunes:title', 'itunes:summary', 'itunes:duration', 'itunes:explicit', 'itunes:episodeType'):
            node = item.find(tag)
            if node is not None and (node.text or '').strip():
                ET.SubElement(output, tag).text = node.text
        enclosure = item.find('enclosure')
        if enclosure is not None:
            ET.SubElement(output, 'enclosure', dict(enclosure.attrib))
    ET.ElementTree(rss).write(filename, encoding='utf-8', xml_declaration=True)
