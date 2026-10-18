from pathlib import Path
from docx import Document
from copy import deepcopy
import hashlib,json
root=Path(r'C:\work\ls4t-msg\cases\official\results\production_assessment\manuscript_validation_update')
source=Path(r'C:\BaiduSyncdisk\research\ls4t_msg\LS4T-MSG-v6-revised.docx')
doc=Document(source)
assert hashlib.sha256(source.read_bytes()).hexdigest()=='eb433191ca5f5b4ec62057fa3bfa58190fb2c3a5efb55c748e5a52d896111472'
title='LS4T-MSG: monthly mean hourly vegetation-canopy and background-soil temperatures over Europe and Africa during 2017–2025'
old='LS4T-MSG targets monthly vegetation-canopy and background-soil temperatures from paired Meteosat Second Generation observations at seven UTC hours (10:00–16:00) over Europe and Africa.'
new='LS4T-MSG describes hourly vegetation-canopy and background-soil temperatures as monthly means from paired Meteosat Second Generation observations over Europe and Africa. The retrieval targets daytime conditions with pronounced canopy–soil thermal contrast; the current sampling comprises seven nominal UTC hours (10:00–16:00).'
assert old in doc.paragraphs[7].text
for index,text in [(0,title),(7,doc.paragraphs[7].text.replace(old,new))]:
 p=doc.paragraphs[index];fmt=deepcopy(p.runs[0]._r.rPr)
 p.clear();r=p.add_run(text)
 if fmt is not None:r._r.insert(0,fmt)
doc.core_properties.title=title
doc.save(root/'revised'/source.name)
(root/'validation_analysis/title_revision.json').write_text(json.dumps({'title':title,'abstract_scope':new,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
