from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json
from docx import Document
from docx.shared import Inches
from lxml import etree

root=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/manuscript_validation_update')
source=Path('C:/BaiduSyncdisk/research/ls4t_msg/LS4T-MSG-v6-revised.docx')
doc=Document(source)
equations=[etree.tostring(e) for e in doc._element.xpath('.//m:oMath')]
p=next(p for p in doc.paragraphs if p.text.startswith('Figure 8.'))
old='Labels give station–month–hour group counts. '
assert old in p.text
text=p.text.replace(old,'')
fmt=deepcopy(p.runs[0]._r.rPr)
p.clear();run=p.add_run(text)
if fmt is not None:run._r.insert(0,fmt)
shape=doc.inline_shapes[7]
rid=shape._inline.xpath('.//a:blip')[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
doc.part.related_parts[rid]._blob=(root/'figures/figure08_europe12.png').read_bytes()
assert equations==[etree.tostring(e) for e in doc._element.xpath('.//m:oMath')]
output=root/'revised'/source.name
doc.save(output)
audit={'source_sha256':sha256(source.read_bytes()).hexdigest(),'output_sha256':sha256(output.read_bytes()).hexdigest(),'change':'Remove n labels in figure 8 and corresponding caption sentence','status':'pending_visual_qa'}
(root/'figure8_label_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in (root/'qa').glob('page-??.png')}
(root/'qa/before_figure8_hashes.json').write_text(json.dumps(hashes),encoding='utf8')
print(json.dumps(audit))
