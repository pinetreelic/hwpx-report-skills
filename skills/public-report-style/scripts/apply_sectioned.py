#!/usr/bin/env python3
# Copyright 2026 Sawyer Lee. SPDX-License-Identifier: Apache-2.0
"""Apply section boxes to our freshly generated kordoc report, never an existing user file."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
      'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
      'hc': 'http://www.hancom.co.kr/hwpml/2011/core'}
for prefix, uri in NS.items(): ET.register_namespace(prefix, uri)
def q(prefix, name): return '{' + NS[prefix] + '}' + name

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source'); parser.add_argument('out')
    parser.add_argument('--profile', required=True); parser.add_argument('--subtitle', default='')
    a = parser.parse_args()
    if Path(a.out).exists(): parser.error('Refusing to overwrite output.')
    profile = json.loads(Path(a.profile).read_text(encoding='utf-8'))
    with zipfile.ZipFile(a.source) as z: parts = {n: z.read(n) for n in z.namelist()}
    header = ET.fromstring(parts['Contents/header.xml'])
    section = ET.fromstring(parts['Contents/section0.xml'])
    def clone_record(kind, original):
        group = header.find('.//hh:' + {'charPr':'charProperties','paraPr':'paraProperties','borderFill':'borderFills'}[kind], NS)
        if group is None: raise ValueError('Missing resource group: ' + kind)
        record = next(e for e in group if e.get('id') == str(original))
        record = deepcopy(record)
        record.set('id', str(max(int(e.get('id')) for e in group) + 1))
        group.append(record); group.set('itemCnt', str(len(group)))
        return record
    def char(original, size, color):
        c = clone_record('charPr', original); c.set('height', str(size)); c.set('textColor', color)
        return c.get('id')
    def para(original, before=0, after=0, left=0, indent=0, keep=False, align=None):
        p = clone_record('paraPr', original)
        for margin in p.findall('.//hh:margin', NS):
            for name, value in [('prev',before),('next',after),('left',left),('intent',indent)]:
                e=margin.find('hc:'+name,NS)
                if e is not None: e.set('value',str(value))
        for e in p.findall('.//hh:lineSpacing',NS): e.set('value','160')
        b=p.find('hh:breakSetting',NS)
        if b is not None:b.set('keepWithNext','1' if keep else '0');b.set('keepLines','1')
        if align:p.find('hh:align',NS).set('horizontal',align)
        return p.get('id')
    def text_of(p): return ''.join(e.text or '' for e in p.findall('.//hp:t',NS))
    def set_text(p,text,cref):
        for child in list(p):p.remove(child)
        run=ET.SubElement(p,q('hp','run'),{'charPrIDRef':str(cref)})
        ET.SubElement(run,q('hp','t')).text=text
    title_table=section.find('.//hp:tbl',NS)
    if title_table is None or title_table.get('rowCnt')!='3': raise ValueError('Unexpected title geometry.')
    title_cell=title_table.findall('hp:tr',NS)[1].find('hp:tc',NS)
    sub=title_cell.find('hp:subList',NS); title_p=sub.find('hp:p',NS)
    title=text_of(title_p); source_char=title_p.find('hp:run',NS).get('charPrIDRef')
    main_char=char(source_char,2400,profile['title_color']); small_char=char(source_char,1900,'#203A7B')
    center=para(title_p.get('paraPrIDRef'),align='CENTER')
    center_record=next(e for e in header.findall('.//hh:paraPr',NS) if e.get('id')==center)
    for e in center_record.findall('.//hh:lineSpacing',NS): e.set('value','130')
    set_text(title_p,title,main_char); title_p.set('paraPrIDRef',center)
    if a.subtitle:
        subtitle=deepcopy(title_p);set_text(subtitle,a.subtitle,small_char);sub.insert(0,subtitle)
    title_cell.find('hp:cellSz',NS).set('height','9600' if a.subtitle else '6803')
    title_table.find('hp:sz',NS).set('height',str((9600 if a.subtitle else 6803)+764))
    bf=clone_record('borderFill',title_cell.get('borderFillIDRef'))
    for child in list(bf):bf.remove(child)
    for name in ['leftBorder','rightBorder','topBorder','bottomBorder']:
        ET.SubElement(bf,q('hh',name),{'type':'DOUBLE_SLIM' if name in ['topBorder','bottomBorder'] else 'NONE',
            'width':'0.5 mm','color':profile['section_color']})
    brush=ET.SubElement(bf,q('hc','fillBrush'))
    gradient=ET.SubElement(brush,q('hc','gradation'),{'type':'LINEAR','angle':'0','centerX':'50','centerY':'50','step':'50','colorNum':'2','stepCenter':'50','alpha':'0'})
    for color in ['#FFFFFF',profile['section_fill']]:ET.SubElement(gradient,q('hc','color'),{'value':color})
    roman=['Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ','Ⅵ','Ⅶ','Ⅷ','Ⅸ','Ⅹ','Ⅺ','Ⅻ']
    section_no=0; sub_no=0; first_item=True
    for p in list(section):
        if p.tag!=q('hp','p') or p.find('.//hp:tbl',NS) is not None:continue
        text=text_of(p)
        if p.get('styleIDRef')=='2':
            section_no+=1;sub_no=0;first_item=True
            label=(roman[section_no-1] if section_no<=len(roman) else str(section_no))+'. '+text
            box=deepcopy(title_table)
            box.set('id',str(900000+section_no));box.set('rowCnt','1')
            for tr in list(box.findall('hp:tr',NS)):box.remove(tr)
            row=ET.SubElement(box,q('hp','tr'));cell=deepcopy(title_cell);row.append(cell)
            cell.set('borderFillIDRef',bf.get('id'))
            cell.find('hp:cellAddr',NS).set('rowAddr','0');cell.find('hp:cellSz',NS).set('height','3214')
            box.find('hp:sz',NS).set('height','3214')
            sl=cell.find('hp:subList',NS)
            for child in list(sl):sl.remove(child)
            cp=deepcopy(title_p);set_text(cp,label,char(source_char,1800,'#000000'))
            cp.set('paraPrIDRef',para(title_p.get('paraPrIDRef'),left=600,keep=True,align='LEFT'));sl.append(cp)
            original=p.get('paraPrIDRef');set_text(p,'',source_char)
            p.find('hp:run',NS).append(box)
            p.set('paraPrIDRef',para(original,before=1500,keep=True))
        elif p.get('styleIDRef')=='3':
            sub_no+=1
            text=re.sub(r'^\d+\.\s*','',text)
            c=p.find('hp:run',NS).get('charPrIDRef');set_text(p,str(sub_no)+'. '+text,c)
            p.set('paraPrIDRef',para(p.get('paraPrIDRef'),before=0 if first_item else 900,keep=True))
            first_item=False
        elif text.strip():
            if text.startswith('BULLETCONTENTTOKEN '):
                c=p.find('hp:run',NS).get('charPrIDRef')
                set_text(p,'○ '+text[len('BULLETCONTENTTOKEN '):],c)
            p.set('paraPrIDRef',para(p.get('paraPrIDRef'),before=300,left=1600,indent=-1300))
    if not section_no: raise ValueError('No sections found.')
    parts['Contents/header.xml']=ET.tostring(header,encoding='utf-8',xml_declaration=True)
    parts['Contents/section0.xml']=ET.tostring(section,encoding='utf-8',xml_declaration=True)
    # Refresh textual preview; do not retain stale thumbnails from an intermediate file.
    parts['Preview/PrvText.txt']='\n'.join(text_of(p) for p in section).encode('utf-16')
    parts.pop('Preview/PrvImage.png',None)
    with zipfile.ZipFile(a.out,'x') as z:
        for name,data in parts.items():z.writestr(name,data,compress_type=zipfile.ZIP_STORED if name=='mimetype' else zipfile.ZIP_DEFLATED)
    print(json.dumps({'style':profile['id'],'sections':section_no}))
if __name__=='__main__':main()
