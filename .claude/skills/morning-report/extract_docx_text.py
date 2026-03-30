import sys
import zipfile
import xml.etree.ElementTree as ET

local_path = sys.argv[1]

ns = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

with zipfile.ZipFile(local_path) as z:
    rels = {}
    with z.open('word/_rels/document.xml.rels') as f:
        for rel in ET.parse(f).getroot():
            if rel.get('Type', '').endswith('/hyperlink'):
                rels[rel.get('Id')] = rel.get('Target', '')
    with z.open('word/document.xml') as f:
        body = ET.parse(f).getroot().find('.//w:body', ns)
    for para in body.findall('.//w:p', ns):
        parts = []
        for elem in para:
            tag = elem.tag.split('}')[-1]
            if tag == 'r':
                t = elem.find('w:t', ns)
                if t is not None and t.text:
                    parts.append(t.text)
            elif tag == 'hyperlink':
                rid = elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', '')
                text = ''.join(t.text or '' for t in elem.findall('.//w:t', ns))
                if text:
                    parts.append(text)
        line = ''.join(parts).strip()
        if line:
            print(line)
