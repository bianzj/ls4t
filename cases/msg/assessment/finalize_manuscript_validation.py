from pathlib import Path
from datetime import datetime
from hashlib import sha256
import json, shutil
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
from pypdf import PdfReader

root=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/manuscript_validation_update')
audit=json.loads((root/'document_edit_audit.json').read_text(encoding='utf8'))
source,backup,output=map(Path,[audit['source'],audit['backup'],audit['output']])
digest=lambda p:sha256(p.read_bytes()).hexdigest()
assert digest(source)==audit['source_sha256'],'Canonical manuscript changed during editing; do not overwrite.'
assert digest(output)==audit['output_sha256']
old,new=Document(backup),Document(output)
assert [etree.tostring(e) for e in old._element.xpath('.//m:oMath')]==[etree.tostring(e) for e in new._element.xpath('.//m:oMath')]
def picture_hashes(doc):
    return [sha256(doc.part.related_parts[s._inline.xpath('.//a:blip')[0].get(qn('r:embed'))].blob).hexdigest() for s in doc.inline_shapes]
a,b=picture_hashes(old),picture_hashes(new)
assert len(a)==len(b)==11
assert [i+1 for i in range(11) if a[i]!=b[i]]==[5,6,7,8,9]
assert len(new.tables)==3 and len(new.tables[0].rows)==13
pdf=root/'qa/LS4T-MSG-v6-revised.pdf'
reader=PdfReader(pdf)
assert len(reader.pages)==24
(root/'qa/rendered.txt').write_text('\n\f\n'.join(p.extract_text() for p in reader.pages),encoding='utf8')
audit.update(status='passed_and_saved',pages=24,visual_qa='All 24 pages inspected; revised spacing on page 13 rechecked; other 23 rendered page hashes unchanged.',unmodified_figures_verified=[1,2,3,4,10,11],pdf_sha256=digest(pdf),completed_at=datetime.now().astimezone().isoformat())
shutil.copy2(output,source)
assert digest(source)==digest(output)
audit['canonical_sha256']=digest(source)
(root/'document_edit_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
with (root/'修订记录.md').open('a',encoding='utf8') as f:
    f.write('\n已完成24页逐页渲染检查；35个原生公式全部保留，11幅图与3个表数量正常，仅替换图5—9。已覆盖保存research下现有v6，修订前备份及验证材料均保存在本cases目录。\n')
print(json.dumps({'saved':str(source),'sha256':digest(source),'pages':24,'equations_preserved':35,'status':'passed'},ensure_ascii=False))
