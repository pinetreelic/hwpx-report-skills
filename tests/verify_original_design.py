"""Compare emitted design with the sanitized source, resolving resource IDs independently."""
import base64
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as E

N={'p':'http://www.hancom.co.kr/hwpml/2011/paragraph','h':'http://www.hancom.co.kr/hwpml/2011/head'}
REFS={'charPrIDRef':'charProperties','paraPrIDRef':'paraProperties','styleIDRef':'styles',
      'nextStyleIDRef':'styles','borderFillIDRef':'borderFills','tabPrIDRef':'tabProperties'}
def signature(root,resources,seen=()):
    attributes=[]
    for key,value in sorted(root.attrib.items()):
        if key in ('id','binaryItemIDRef'):continue
        kind=REFS.get(key)
        if kind:
            item=next(e for e in resources.find('h:'+kind,N) if e.get('id')==value)
            value=('cycle',kind) if (kind,value) in seen else signature(item,resources,seen+((kind,value),))
        attributes.append((key,value))
    if root.tag.endswith('fontRef'):
        attributes=[]
        for lang,id in sorted(root.attrib.items()):
            face=next(f for f in resources.find('h:fontfaces',N) if f.get('lang')==lang.upper())
            font=next(f for f in face if f.get('id')==id)
            attributes.append((lang,font.get('face')))
    children=[signature(e,resources,seen) for e in root if not e.tag.endswith('linesegarray')]
    return (root.tag,tuple(attributes),tuple(children))
def verify(hwpx,asset_path):
    asset=json.loads(Path(asset_path).read_text(encoding='utf-8'));source=E.fromstring(asset['resources'])
    with zipfile.ZipFile(hwpx) as z:
        h=E.fromstring(z.read('Contents/header.xml')).find('h:refList',N)
        section=E.fromstring(z.read('Contents/section0.xml'));tables=section.findall('.//p:tbl',N)
        assert signature(tables[0],h)==signature(E.fromstring(asset['title_table']),source),'Title design differs from original.'
        for i,table in enumerate(tables[1:3]):
            expected=E.fromstring(asset['section_paragraphs'][i]).find('.//p:tbl',N)
            assert signature(table,h)==signature(expected,source),'Section design differs from original.'
        for image in asset['images'].values():
            assert z.read('BinData/style_'+image['name'])==base64.b64decode(image['base64']),'Original decoration changed.'
    print('Original title/section geometry, resolved fonts, paragraph properties, borders and bitmap preserved.')
