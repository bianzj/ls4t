"""Remove repeated commentary; retain reproducible methods and reported results."""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json,re
from docx import Document
from lxml import etree

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/manuscript_validation_update')
SOURCE=Path('C:/BaiduSyncdisk/research/ls4t_msg/LS4T-MSG-v6-revised.docx')
OUTPUT=ROOT/'revised'/SOURCE.name
doc=Document(SOURCE)
original_hash=sha256(SOURCE.read_bytes()).hexdigest()
equations=[etree.tostring(e) for e in doc._element.xpath('.//m:oMath')]
paragraphs=list(doc.paragraphs)
def put(i,text):
    p=paragraphs[i]
    fmt=deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
    p.clear();r=p.add_run(text)
    if fmt is not None:r._r.insert(0,fmt)
def substitute(i,old,new):
    assert old in paragraphs[i].text,(i,old)
    put(i,paragraphs[i].text.replace(old,new))

substitute(7,'after joint 0–60 °C and 10 K retrieval–reference screening','using paired observations retained by the evaluation criteria')
substitute(7,'Background soil compared with the same sunlit-soil radiometry gives 2.929 K; this is a cross-component comparison, not direct background-soil validation.','The corresponding background-soil comparison gives an RMSE of 2.929 K.')
put(75,'The August 2017 EVO example resolves monthly mean temperatures at each hour from 11:00 to 16:00 UTC (Fig. 5), with separate panels for the two soil estimates and canopy. Means, sample standard deviations and pair counts are calculated from the retained instantaneous observations using the criteria in Sect. 4.2.')
put(77,'Figure 5. EVO monthly mean temperatures at each UTC hour in August 2017. Blue circles show corrected radiometry, colored squares station retrievals and gray triangles bulk LST. Error bars are ±1 sample standard deviation for radiometry and retrievals; numbers are instantaneous pair counts. Reference definitions and evaluation criteria are given in Sects. 2.4 and 4.2.')
substitute(79,'This threshold is an evaluation filter using reference observations, not a product quality flag. ','')
substitute(79,' Statistics without the residual filter are retained in Sect. 5.1.','')
put(80,'For the month–hour pairs in Fig. 6, sunlit-soil and canopy RMSEs are 1.883 and 3.427 K, with signed biases of −0.670 and +2.647 K. The background-soil comparison gives RMSE 2.929 K and bias −2.156 K. Canopy RMSE on the background-soil scheme’s slightly different sample is 3.408 K. Bulk-LST RMSEs on the identical pairs are 4.563 and 9.643 K for the soil and canopy references in the main scheme, respectively, and 4.561 K for the soil reference in the background scheme. These statistics describe the retained station-mode samples.')
put(82,'Figure 6. EVO comparisons of monthly means at each hour from 11:00 to 16:00 UTC during August–December 2017. Each panel contains 30 month–hour pairs; panels (a) and (c) use 528 instantaneous pairs, and panel (b) uses 526. Colored circles show component estimates and gray triangles bulk LST on identical pairs; dashed lines are 1:1. Bias is estimated minus reference temperature. Reference definitions and evaluation criteria follow Sects. 2.4 and 4.2.')
put(83,'Figure 7 evaluates hourly variation in RMSE using the same month–hour pairs as Fig. 6. Each hour from 11:00 to 16:00 UTC contains five monthly pairs, with no pooling across hours. The limited number of monthly pairs and the single-site setting constrain interpretation of the hourly differences.')
put(85,'Figure 7. Hour-specific RMSE at EVO calculated from the month–hour pairs in Fig. 6. Each UTC hour has five monthly pairs. Colored curves represent component retrievals and gray curves bulk LST on identical pairs; reference definitions and sampling follow Fig. 6.')
substitute(87,'Shaded-soil, canopy, both references and bulk LST must be within 0–60 °C, and both instantaneous component–reference absolute differences must be ≤10 K. The two components share all retained timestamps.','The joint screening and paired monthly aggregation follow Sect. 4.2, with both components sharing all retained timestamps.')
substitute(87,' The component-based residual filter conditions this comparison.','')
substitute(90,'Joint 0–60 °C and 10 K filters are applied to instantaneous observations before averaging. ','')
put(96,'5.1 Interpretation of station comparisons')
put(97,'The station comparisons retain monthly and hourly structure while sampling different periods and reference quantities at EVO and in Europe (Sect. 2.4). They assess the corrected station configuration rather than the archived regional grids. Including IT-TrF and FR-EM2 gives 14-station mean RMSEs of 3.957 K for shaded soil and 3.854 K for canopy under the same evaluation criteria, compared with 4.014 and 3.626 K at the 12 retained sites. The station subset was selected after inspecting the results; removing the two sites does not improve both components. The complete station results are retained in the reproduction package.')
# Remove the dedicated filter-sensitivity graphic and its caption; keep underlying files.
assert paragraphs[98]._p.xpath('.//a:blip')
assert paragraphs[99].text.startswith('Figure 9. Sensitivity')
for i in [98,99]:paragraphs[i]._p.getparent().remove(paragraphs[i]._p)
put(113,'Second, coarse footprints can include irrigation, water, urban surfaces, ecotones and complex terrain that a canopy–soil model represents incompletely. Direct component observations remain limited to the 2017 EVO open-woodland case, while the European comparisons use meteorological references (Sect. 2.4). Limited spatial coverage and unresolved source-time conventions constrain broader accuracy claims. A product-level evaluation must extract the corresponding regional grid values using matched months, hours and reference screening. Numerical replay cannot establish physical validity or independence from parameter selection. Per-pixel sample counts, component-separability diagnostics and uncertainty estimates are needed across the full archive.')
substitute(117,'Under joint 0–60 °C and 10 K screening, EVO','For the retained paired observations, EVO')
substitute(117,'background soil differs from the sunlit-soil radiometry by an RMSE of 2.929 K','the background-soil comparison gives an RMSE of 2.929 K')
substitute(118,'The revised validation separates direct sunlit-soil and canopy radiometry, cross-component background-soil comparison, and indirect meteorological consistency. Full-station and range-only sensitivities show how sample selection affects the reported errors.','The validation combines component radiometry and indirect meteorological comparisons, with reference definitions and sampling stated explicitly. Full-station results complement the principal 12-station evaluation.')
substitute(120,'all 11 figures','all 10 manuscript figures')
substitute(120,'Figures 5–9 use the corrected station predictions and matched month–hour tables, including both EVO soil schemes, the European 12-station subset, and full-station and filter sensitivities. Figures 1–4 and 10–11 retain their existing geometry and regional-archive sources.','Figures 5–8 use the corrected station predictions and matched month–hour tables for EVO and the European 12-station subset. Figures 1–4 and 9–10 retain their existing geometry and regional-archive sources. Full-station results and additional sensitivity tables remain in the reproduction package.')
# Renumber only the original figures 10 and 11 and their prose references.
for i in [101,103,104,106]:
    text=paragraphs[i].text
    text=re.sub(r'\b(Figure|Fig\.) (10|11)\b',lambda m:m.group(1)+' '+str(int(m.group(2))-1),text)
    put(i,text)
cell=doc.tables[1].cell(6,2)
p=cell.paragraphs[0]
fmt=deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
p.clear();r=p.add_run('Corrected station predictions require all four outputs within 250–350 K before the evaluation criteria in Sect. 4.2 are applied. Regional monthly files lack per-pixel counts and quality arrays.')
if fmt is not None:r._r.insert(0,fmt)
assert equations==[etree.tostring(e) for e in doc._element.xpath('.//m:oMath')]
assert len(doc.inline_shapes)==10
captions=[p.text for p in doc.paragraphs if re.match(r'^Figure \d+\.',p.text)]
assert [int(re.match(r'^Figure (\d+)',c).group(1)) for c in captions]==list(range(1,11))
full='\n'.join(p.text for p in doc.paragraphs)
assert len(re.findall(r'(?<![\d.])10 K',full))==1
assert 'Figure 11' not in full and 'Fig. 11' not in full
assert 'Sensitivity to validation support' not in full
doc.save(OUTPUT)
audit={'status':'pending_visual_qa','source':str(SOURCE),'source_sha256':original_hash,'output':str(OUTPUT),'output_sha256':sha256(OUTPUT.read_bytes()).hexdigest(),'equations_preserved':len(equations),'figures':10,'removed_figure':9,'renumbered_figures':{'10':9,'11':10},'numeric_results_unchanged':True,'ten_kelvin_rule_mentions':1}
(ROOT/'streamline_edit_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(audit,ensure_ascii=False))
