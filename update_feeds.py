import urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
SOURCES={"zhivoy-gvozd.xml":("https://cloud.mave.digital/41353","Живой Гвоздь — избранное","Выпуски с Венедиктовым и Белковским.","zhivoy-gvozd.png"),"diletant.xml":("https://cloud.mave.digital/41365","Дилетант","Дилетант, включая Параграф 43, без выпусков чтения Сергея Бунтмана.","diletant.png"),"chitalka.xml":("https://cloud.mave.digital/41365","Читалка — Дилетант","Выпуски чтения Сергея Бунтмана, кроме Параграфа 43.","chitalka.png")}
RAW="https://raw.githubusercontent.com/zzcast/podcast-feeds/main/"
def t(i,k):
 x=i.find(k); return (x.text or "").strip().lower() if x is not None else ""
def s(i): return " ".join(t(i,k) for k in ("title","description","itunes:summary"))
def keep(n,i):
 v=s(i)
 if n=="zhivoy-gvozd.xml": return "венедиктов" in v or "белковск" in v
 p="параграф 43" in v; r="читает сергей бунтман" in v or "читалка" in v
 return (not r or p) if n=="diletant.xml" else (r and not p)
for n,(u,title,desc,icon) in SOURCES.items():
 src=ET.fromstring(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"podcast-feeds"}),timeout=60).read()).find("./channel"); rss=ET.Element("rss",{"version":"2.0","xmlns:itunes":"http://www.itunes.com/dtds/podcast-1.0.dtd"}); ch=ET.SubElement(rss,"channel")
 for k,v in (("title",title),("description",desc),("link","https://github.com/zzcast/podcast-feeds"),("language","ru"),("lastBuildDate",format_datetime(datetime.now(timezone.utc)))): ET.SubElement(ch,k).text=v
 im=ET.SubElement(ch,"image"); ET.SubElement(im,"url").text=RAW+icon; ET.SubElement(im,"title").text=title; ET.SubElement(im,"link").text="https://github.com/zzcast/podcast-feeds"; ET.SubElement(ch,"{http://www.itunes.com/dtds/podcast-1.0.dtd}image",{"href":RAW+icon})
 for i in src.findall("./item"):
  if not keep(n,i): continue
  o=ET.SubElement(ch,"item")
  for k in ("title","description","link","guid","pubDate","itunes:title","itunes:summary","itunes:duration","itunes:explicit","itunes:episodeType"):
   x=i.find(k)
   if x is not None and (x.text or "").strip(): ET.SubElement(o,k).text=x.text
  x=i.find("enclosure")
  if x is not None: ET.SubElement(o,"enclosure",dict(x.attrib))
 ET.ElementTree(rss).write(n,encoding="utf-8",xml_declaration=True)
