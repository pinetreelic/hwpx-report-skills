#!/usr/bin/env python3
# Copyright 2026 Sawyer Lee. SPDX-License-Identifier: Apache-2.0
"""Transplant sanitized ORIGINAL design components into a freshly generated report."""
import argparse
import base64
from copy import deepcopy
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

NS={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hh':'http://www.hancom.co.kr/hwpml/2011/head',
    'hc':'http://www.hancom.co.kr/hwpml/2011/core',
    'opf':'http://www.idpf.org/2007/opf/'}
for prefix,uri in NS.items():ET.register_namespace(prefix,uri)
def q(prefix,name):return '{'+NS[prefix]+'}'+name
REFS={'charPrIDRef':'charProperties','paraPrIDRef':'paraProperties','styleIDRef':'styles',
      'nextStyleIDRef':'styles','borderFillIDRef':'borderFills','tabPrIDRef':'tabProperties'}

def import_design(header,asset):
    source=ET.fromstring(asset['resources']);dest=header.find('hh:refList',NS)
    maps={};fonts={}
    for group in source:
        kind=group.tag.split('}')[-1]
        target=dest.find('hh:'+kind,NS)
        if target is None:target=ET.SubElement(dest,group.tag,dict(group.attrib))
        if kind=='fontfaces':
            for face in group:
                lang=face.get('lang');df=next((f for f in target if f.get('lang')==lang),None)
                if df is None:df=ET.SubElement(target,face.tag,dict(face.attrib))
                offset=max([int(e.get('id')) for e in df]+[-1])+1
                fonts[lang]={e.get('id'):str(offset+i) for i,e in enumerate(face)}
                for font in face:
                    new=deepcopy(font);new.set('id',fonts[lang][font.get('id')]);df.append(new)
                df.set('fontCnt',str(len(df)))
        else:
            offset=max([int(e.get('id')) for e in target]+[-1])+1
            maps[kind]={e.get('id'):str(offset+i) for i,e in enumerate(group)}
    def remap(root):
        for e in root.iter():
            for key,value in list(e.attrib.items()):
                kind=REFS.get(key)
                if key=='idRef' and e.tag==q('hh','heading') and e.get('type') in ('OUTLINE','NUMBER','BULLET'):
                    kind='bullets' if e.get('type')=='BULLET' else 'numberings'
                if kind and value in maps.get(kind,{}):e.set(key,maps[kind][value])
            if e.tag==q('hh','fontRef'):
                for key,value in list(e.attrib.items()):
                    if value in fonts.get(key.upper(),{}):e.set(key,fonts[key.upper()][value])
            if e.get('binaryItemIDRef') in asset['images']:
                e.set('binaryItemIDRef','style_'+e.get('binaryItemIDRef'))
        return root
    for group in source:
        kind=group.tag.split('}')[-1]
        if kind=='fontfaces':continue
        target=dest.find('hh:'+kind,NS)
        for record in group:
            new=deepcopy(record);new.set('id',maps[kind][record.get('id')]);remap(new);target.append(new)
        target.set('itemCnt',str(len(target)))
    return remap,maps

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source');ap.add_argument('out');ap.add_argument('--profile',required=True);ap.add_argument('--subtitle',default='')
    a=ap.parse_args()
    if Path(a.out).exists():ap.error('Refusing to overwrite output.')
    profile_path=Path(a.profile);profile=json.loads(profile_path.read_text(encoding='utf-8'))
    asset_path=profile_path.parent/profile.get('components','components.json')
    asset=json.loads(asset_path.read_text(encoding='utf-8'))
    with zipfile.ZipFile(a.source) as z:parts={n:z.read(n) for n in z.namelist()}
    header=ET.fromstring(parts['Contents/header.xml']);section=ET.fromstring(parts['Contents/section0.xml'])
    remap,maps=import_design(header,asset)
    def text_of(p):return ''.join(e.text or '' for e in p.findall('.//hp:t',NS))
    def text_replace(root,values):
        for e in root.findall('.//hp:t',NS):
            if e.text in values:e.text=values[e.text]
        # Cached line layout belongs to old text; let Hancom reflow without changing styles.
        for parent in root.iter():
            for child in list(parent):
                if child.tag==q('hp','linesegarray'):parent.remove(child)
    def paragraph_format(p,before=0,left=0,indent=0,keep=False):
        group=header.find('.//hh:paraProperties',NS);old=p.get('paraPrIDRef')
        new=deepcopy(next(e for e in group if e.get('id')==old))
        new.set('id',str(max(int(e.get('id')) for e in group)+1))
        for margin in new.findall('.//hh:margin',NS):
            for name,value in [('prev',before),('next',0),('left',left),('intent',indent)]:
                e=margin.find('hc:'+name,NS)
                if e is not None:e.set('value',str(value))
        for e in new.findall('.//hh:lineSpacing',NS):e.set('value','160')
        b=new.find('hh:breakSetting',NS)
        if b is not None:b.set('keepWithNext','1' if keep else '0')
        group.append(new);group.set('itemCnt',str(len(group)));p.set('paraPrIDRef',new.get('id'))
    old_table=section.find('.//hp:tbl',NS)
    title=text_of(old_table)
    original_title=remap(ET.fromstring(asset['title_table']))
    text_replace(original_title,{'{{title}}':title,'{{subtitle}}':a.subtitle})
    # Keep source geometry, bitmap decoration, margins and paragraph/character properties.
    for parent in section.iter():
        if old_table in list(parent):parent.remove(old_table);parent.append(original_title);break
    anchor=next(p for p in section if p.find('.//hp:tbl',NS) is original_title)
    attrs=remap(ET.Element('anchor',asset['title_anchor'])).attrib
    for key,value in attrs.items():anchor.set(key,value)
    page=section.find('.//hp:pagePr',NS)
    original_page=ET.fromstring(asset['page'])
    for parent in section.iter():
        if page in list(parent):i=list(parent).index(page);parent.remove(page);parent.insert(i,original_page);break
    anchor_index=list(section).index(anchor)
    for i,xml in enumerate(asset.get('title_spacers',[])):
        section.insert(anchor_index+1+i,remap(ET.fromstring(xml)))
    roman=['Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ','Ⅵ','Ⅶ','Ⅷ','Ⅸ','Ⅹ','Ⅺ','Ⅻ']
    section_no=0;sub_no=0;first_item=True
    for p in list(section):
        if p.tag!=q('hp','p') or p.find('.//hp:tbl',NS) is not None:continue
        text=text_of(p)
        if p.get('styleIDRef')=='2':
            section_no+=1;sub_no=0;first_item=True
            prototype=asset['section_paragraphs'][min(section_no-1,len(asset['section_paragraphs'])-1)]
            replacement=remap(ET.fromstring(prototype))
            text_replace(replacement,{'{{number}}':(roman[section_no-1] if section_no<=len(roman) else str(section_no))+'. ', '{{section}}':text})
            table=replacement.find('.//hp:tbl',NS);table.set('id',str(900000+section_no))
            index=list(section).index(p);section.remove(p);section.insert(index,replacement)
        elif p.get('styleIDRef')=='3':
            sub_no+=1
            first=p.find('.//hp:t',NS)
            if first is not None:first.text=re.sub(r'^\d+\.\s*',str(sub_no)+'. ',first.text or '')
            paragraph_format(p,before=0 if first_item else 900,keep=True);first_item=False
        elif text.strip():
            for t in p.findall('.//hp:t',NS):
                if t.text and t.text.startswith('BULLETCONTENTTOKEN '):t.text='○ '+t.text[len('BULLETCONTENTTOKEN '):]
            paragraph_format(p,before=300,left=1600,indent=-1300)
    if not section_no:raise ValueError('No sections found.')
    # Theme variants may recolor imported source resources; the canonical style retains source colors.
    replacements={old:profile[key] for old,key in [('#3057B9','title_color'),('#0000FF','section_color'),('#D6EAFE','section_fill')] if profile.get(key,old)!=old}
    for kind,mapping in maps.items():
        group=header.find('.//hh:'+kind,NS)
        for record in group:
            if record.get('id') not in mapping.values():continue
            for node in record.iter():
                for key,value in list(node.attrib.items()):
                    if value in replacements:node.set(key,replacements[value])
    package=ET.fromstring(parts['Contents/content.hpf']);manifest=package.find('opf:manifest',NS)
    for id,image in asset['images'].items():
        name='BinData/style_'+image['name'];parts[name]=base64.b64decode(image['base64'])
        ET.SubElement(manifest,q('opf','item'),{'id':'style_'+id,'href':name,'media-type':image['media_type'],'isEmbeded':'1'})
    parts['Contents/content.hpf']=ET.tostring(package,encoding='utf-8',xml_declaration=True)
    parts['Contents/header.xml']=ET.tostring(header,encoding='utf-8',xml_declaration=True)
    parts['Contents/section0.xml']=ET.tostring(section,encoding='utf-8',xml_declaration=True)
    parts['Preview/PrvText.txt']='\n'.join(text_of(p) for p in section).encode('utf-16')
    parts.pop('Preview/PrvImage.png',None)
    with zipfile.ZipFile(a.out,'x') as z:
        for name,data in parts.items():z.writestr(name,data,compress_type=zipfile.ZIP_STORED if name=='mimetype' else zipfile.ZIP_DEFLATED)
    print(json.dumps({'style':profile['id'],'sections':section_no,'design':'original-components','fonts':'source fonts preserved'}))
if __name__=='__main__':main()
