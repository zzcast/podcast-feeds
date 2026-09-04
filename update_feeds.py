import urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime

SOURCES = {"zhivoy-gvozd.xml": ("https://cloud.mave.digital/41353", "Живой Гвоздь — избранное", "Выпуски с Венедиктовым и Белковским."), "diletant.xml": ("https://cloud.mave.digital/41365", "Дилетант", "Дилетант, включая Параграф 43, без выпусков чтения Сергея Бунтмана."), "chitalka.xml": ("https://cloud.mave.digital/41365", "Читалка — Дилетант", "Выпуски чтения Сергея Бунтмана, кроме Параграфа 43.")}

def text(item, tag):
    x=item.find(tag); return (x.text or "").strip().lower() if x is not None else ""
def alltext(item): return " ".join(text(item,t) for t in ("title","description","itunes:summary"))
def selected(name, item):
    s=alltext(item)
    if name == "zhivoy-gvozd.xml": return "венедиктов" in s or "белковск" in s
    paragraph="параграф 43" in s
    reading="читает сергей бунтман" in s or "читалка" in s
    return (not reading or paragraph) if name == "diletant.xml" else (reading and not paragraph)

for name,(url,title,desc) in SOURCES.items():
    req=urllib.request.Request(url,headers={"User-Agent":"podcast-feeds"})
    src=ET.fromstring(urllib.request.urlopen(req,timeout=60).read()).find("./channel")
    rss=ET.Element("rss",{"version":"2.0","xmlns:itunes":"http://www.itunes.com/dtds/podcast-1.0.dtd"}); ch=ET.SubElement(rss,"channel")
    for tag,val in (("title",title),("description",desc),("link","https://github.com/zzcast/podcast-feeds"),("language","ru"),("lastBuildDate",format_datetime(datetime.now(timezone.utc)))): ET.SubElement(ch,tag).text=val
    for item in src.findall("./item"):
        if not selected(name,item): continue
        out=ET.SubElement(ch,"item")
        for tag in ("title","description","link","guid","pubDate","itunes:title","itunes:summary","itunes:duration","itunes:explicit","itunes:episodeType"):
            x=item.find(tag)
            if x is not None and (x.text or "").strip(): ET.SubElement(out,tag).text=x.text
        x=item.find("enclosure")
        if x is not None: ET.SubElement(out,"enclosure",dict(x.attrib))
    ET.ElementTree(rss).write(name,encoding="utf-8",xml_declaration=True)
