from pathlib import Path
from copy import deepcopy
import hashlib,json
import pandas as pd
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(r'C:\work\ls4t-msg\cases\official\results\production_assessment\manuscript_validation_update')
SRC=Path(r'C:\BaiduSyncdisk\research\ls4t_msg\LS4T-MSG-v6-revised.docx')
A=ROOT/'validation_analysis'
d=Document(SRC);p=list(d.paragraphs)
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='74124183902fa9efda980ed8fc17f2799ab12e713fe8e38859c382f464ba8c65'
def change(i,text):
 assert not p[i]._p.xpath('.//m:oMath')
 fmt=deepcopy(p[i].runs[0]._r.rPr) if p[i].runs and p[i].runs[0]._r.rPr is not None else None
 p[i].clear();r=p[i].add_run(text)
 if fmt is not None:r._r.insert(0,fmt)
change(7,'Abstract. Satellite land surface temperature (LST) combines vegetation and soil contributions, limiting its interpretation over heterogeneous surfaces. LS4T-MSG targets monthly vegetation-canopy and background-soil temperatures from paired Meteosat Second Generation observations at seven UTC hours (10:00–16:00) over Europe and Africa. The documented archive covers August 2017–December 2025 on a nominal 0.03° grid, with inputs beginning on 3 August 2017. A constrained sequential neighborhood estimate supplies the target for a regularized joint adjustment of canopy, sunlit-soil and shaded-soil radiances. Background-soil temperature follows from soil-radiance aggregation and Planck inversion. This analysis evaluates the revised retrieval directly at stations, using 5 × 5 neighborhoods at both stages and monthly means calculated separately at 11:00–16:00 UTC. At Évora, sunlit-soil and canopy RMSEs are 1.883 and 3.427 K across 30 month–hour pairs during August–December 2017; the background-soil comparison gives 2.929 K. At 12 European stations during 2018–2024, equal-station mean RMSEs are 4.014 K for shaded soil against soil probes and 3.626 K for canopy against air temperature. Existing parameter experiments, complete 14-station results and retrospective temporal checks characterize sensitivity to configuration and sample support. These screened station comparisons support evaluation of the retrieval, but do not establish regional product accuracy. Regional illustrations are from the earlier processing version; validation of the replacement archive remains separate from the present station analysis.')
change(22,p[22].text.replace('The production input reader does not restore negative Celsius values stored as signed integers; Sect. 5.4 discusses the consequences.','The station input reader restores signed Celsius values in projected uint16 containers before conversion to kelvin and restricts solar and viewing zenith angles to 0–90° (excluding 90°). Projected zero remains missing because its original source mask is unavailable. Earlier regional processing differs from this configuration (Sect. 5.4).'))
change(29,p[29].text.replace('Probe depth and air-measurement height vary by source and are not replaced by surface radiometric temperatures.','The local evaluation packages do not specify TS_1 probe depths or TA measurement heights; neither reference is a surface component radiometric temperature.'))
change(36,p[36].text.replace('The regional configuration uses G = 0.5, a clumping index of 1, and a hotspot parameter of 0.2.','The evaluated configuration uses G = 0.5, a clumping index of 1, and a hotspot parameter of 0.25.'))
change(39,'Figure 3. Component-temperature retrieval workflow for the station evaluation. Both neighborhood stages use 5 × 5 input windows. The sequential constraints provide a target for the joint radiance adjustment (λ = 1000); the shaded-soil cap and solar-direction radiance aggregation follow the update. Table 2 states the evaluated configuration and separates it from earlier regional processing.')
change(47,p[47].text.replace('The regional retrieval fits both directional radiances over a 3 × 3 neighborhood','The evaluated retrieval fits both directional radiances over a 5 × 5 neighborhood'))
change(51,p[51].text.replace('In the regional retrieval','In the evaluated retrieval').replace('The regional setting is','The setting is').replace(', and canopy radiance above B₁₀.₅(350 K) is replaced by the shaded-soil estimate',''))
change(59,p[59].text.replace('The regional configuration uses λ = 100 without calibrating an absolute observation-error variance. The corrected station evaluation uses','An absolute observation-error variance is not calibrated. The station evaluation uses').replace('uses consistent physical Planck units and a common valid-input mask','uses consistent physical Planck units and a common valid-input mask including 0 ≤ solar and viewing zenith angles < 90°'))
change(60,'3.3 Product definition and archive provenance')
change(61,'A replacement regional production is being prepared separately; the file counts and regional summaries here describe the documented earlier archive, not a verified completion of that production. '+p[61].text.replace('LS4T-MSG contains 707 monthly files','The earlier LS4T-MSG archive contains 707 monthly files'))
change(63,'Here pₛ = exp[−0.5 LAI / cos(θₛ)] is the gap probability in the solar direction, where θₛ is the solar zenith angle. The weights describe ground illumination rather than a satellite reference view. Material emissivity cancels because the soil states share the same emissivity. Equation (8) combines radiances before converting to temperature; it is not an arithmetic temperature mean. For positive LAI and 0 ≤ θₛ < 90°, pₛ lies between 0 and 1. The station evaluation applies this daylight condition before retrieval. Missing endmembers are not replaced by one another. The earlier regional workflow lacked an explicit daylight gate, so its monthly fields are retained only as legacy illustrations pending replacement (Sect. 5.4).')
change(64,'The documented earlier archive uses the following file structure. '+p[64].text)
change(65,p[65].text.replace('None of the 707 monthly files','None of the 707 earlier monthly files')+' Station pair counts reported in Appendix A describe validation support only and cannot substitute for regional per-pixel counts.')
change(66,'Table 2. Configuration evaluated at stations and provenance of the earlier regional archive. The replacement regional archive requires its own configuration and output verification; station scores are not assigned to it.')
change(71,'4.1 Illustrative spatial patterns and station diurnal behavior')
change(72,p[72].text.replace('Figure 4 shows the native monthly','Figure 4 uses the earlier regional processing to illustrate native monthly')+' This example does not quantify the spatial behavior of the replacement archive.')
change(74,p[74].text.replace('Native monthly','Earlier regional processing: native monthly'))
change(79,p[79].text.replace('radiometry matched at identical UTC timestamps','radiometry matched at identical timestamps under the retained UTC convention')+' The source EVO CSV contains no timezone declaration; this time convention remains an assumption of the current matching.')
change(88,'All 14 European source files contain 30-min intervals, verified from TIMESTAMP_END minus TIMESTAMP_START. Matching uses the interval start, interpreted as UTC in the existing code, and the nearest record within ±30 min; it does not shift to interval centers. The local source packages do not declare the UTC offset, so absolute-time alignment remains unverified. The 10:00 product slot is excluded to use the same six-hour window at EVO and the European sites. The 12-site selection is assessed against all 14 sites in Sect. 5.1; actual retained years and sample counts are given in Table A1.')
change(97,p[97].text.replace('The complete station results are retained in the reproduction package.','Table A1 reports all 14 sites, including the two excluded sites. Pooling all retained month–hour pairs instead of averaging station RMSEs equally gives 4.032 K for shaded soil and 4.267 K for canopy at the 12 sites, demonstrating the influence of unequal support. Leaving out each of the 12 sites in turn gives equal-station mean RMSE ranges of 3.952–4.055 K and 3.492–3.818 K, respectively. These are descriptive stability ranges, not confidence intervals.'))
change(98,'5.2 Parameter sensitivity and illustrative interannual variability')
change(99,'The earlier regional archive is used solely for the sampling and variability illustrations in Figs. 9–10. '+p[99].text)
change(101,p[101].text.replace('Area-weighted monthly','Earlier regional processing: area-weighted monthly'))
change(104,p[104].text.replace('Exploratory conditional slopes','Earlier regional processing: exploratory conditional slopes'))
change(109,'The present analysis evaluates a revised station retrieval using existing input caches. Its main limits are component identifiability, physical and temporal reference comparability, uneven sample support and transfer to regional production. The ongoing replacement production is outside this station analysis; its completion and equivalence to the evaluated implementation have not been verified here.')
change(110,p[110].text.replace('Sensitivity to regularization strength and to perturbations in LST, LAI, emissivity, and geometry is needed to characterize this dependence.','The hotspot and window experiment characterizes selected configuration changes (Appendix A), but does not quantify uncertainty from LST, LAI, emissivity or geometry perturbations.'))
change(112,'The earlier regional archive used hotspot = 0.2, λ = 100 and sequential 3 × 3 and 5 × 5 windows. It also read projected signed LST values as unsigned and applied no explicit daylight mask. These defects are distinct from the revised station implementation, which restores signed values and applies the daylight gate. Source-mask recovery remains unresolved because the projected zero code conflates missing values with 0 °C. The cached IODC viewing geometry must also be verified against the acquisition-dependent geometry across the June 2022 transition. None of these remaining input-provenance checks can be replaced by numerical replay or by a fitted transition term. Figures 4, 9 and 10 therefore describe only the earlier archive and must be regenerated from verified replacement outputs before they support release-level interpretation.')
change(113,'Finally, the record begins partway through 2017, and monthly sampling follows joint clear-sky availability. Fixed UTC hours represent different local solar times across longitude. Regional evaluation requires acquisition-specific geometry, independent source masks, matched configuration hashes, complete per-pixel sampling layers and station extraction from the finished grids. Those checks are separate from the monthly station statistics presented here. No regional reconstruction or new retrieval experiment was performed for the present analysis; the added sensitivity results reuse existing predictions.')
change(115,p[115].text.replace('LS4T-MSG provides 707 monthly files','The documented earlier LS4T-MSG archive comprises 707 monthly files'))
change(116,'The contribution is a component-temperature record that retains time-of-day structure within each month, together with an explicit station-evaluation protocol. Parameter comparisons and sample-support analyses favor retaining the stated configuration as a benchmark, without establishing a unique optimum. Direct component radiometry remains limited to EVO, and the European comparisons provide indirect consistency evidence. The replacement regional archive requires validation against the finished grids, verified source-time conventions and acquisition-specific geometry before the station results can support release-level accuracy claims. The earlier regional illustrations do not establish climate trends.')
change(118,p[118].text.replace('The collection comprises 707','The documented earlier collection comprises 707').replace('Full-station results and additional sensitivity tables remain in the reproduction package.','Appendix A reports full-station support, retrospective temporal checks and hotspot/window sensitivity, with machine-readable tables and source hashes in the reproduction package.').replace('Figures 1–4 and 9–10 retain their existing geometry and regional-archive sources.','Figures 1–2 retain their geometry and input-data sources; Figure 3 presents the revised station workflow; Figures 4 and 9–10 use the earlier regional archive.'))
# Replace the configuration table with an unambiguous analysis-first contract.
rows=[
['Input pairing','Identical EURO/IODC timestamps; daily EURO LAI. Restore signed Celsius before kelvin conversion; LAI = raw/1000. Solar and viewing zenith: 0 ≤ angle < 90°.','Cached projected zero remains missing. Source masks and acquisition-dependent viewing geometry remain to be verified.'],
['Spatial support','Both stages: 5 × 5 station window; center output; at least 10 valid paired neighbors; center LAI ≥ 0.05.','No edge padding for station windows. Regional grid spacing is not the effective retrieval footprint.'],
['Radiance and weights','10.5 μm Planck radiance in W m⁻² sr⁻¹ μm⁻¹. G = 0.5; clumping index = 1; hotspot = 0.25.','Monochromatic and fixed canopy-structure approximations; no explicit SEVIRI spectral-response integration.'],
['Constraints and adjustment','δ = 3 W m⁻² sr⁻¹ μm⁻¹; λ = 1000; determinant threshold 10⁻⁸; post-update shaded-soil ≤ sunlit-soil radiance.','λ is a relative penalty. The common covariance scale cancels. A determinant threshold is not a condition-number test.'],
['Station output and aggregation','All four outputs finite and within 250–350 K; reference screening as Sect. 4.2. Month–hour pairs: 11–16 UTC, ≥3 instantaneous pairs; Europe: ≥3 groups per scored station.','Station monthly means use paired reference support and are not extractions of the regional monthly grids.'],
['Earlier regional archive','Hotspot = 0.2; λ = 100; stages 3 × 3 then 5 × 5. No explicit daylight gate; unsigned interpretation of signed LST. 707 monthly files, August 2017–December 2025.','Regional illustrations retain this earlier provenance. File completeness does not establish spatial completeness or validate the replacement production.'],
['Regional grid and output','EPSG:4326; 3333 × 2633 cells; origin (−18°,65°); spacing (0.030003798°,−0.030003000°). Monthly float32 temperatures scaled by 100; NaN missing.','Nominal 0.03° grid. The earlier monthly files lack per-pixel counts and quality arrays; replacement output metadata requires separate verification.']]
t=d.tables[1]
for r,vals in zip(t.rows[1:],rows):
 for c,v in zip(r.cells,vals):c.text=v
# Add analysis paragraphs before legacy variability.
def before(anchor,text):
 x=anchor.insert_paragraph_before(text);x.style=d.styles['Normal']
 if p[97]._p.pPr is not None:
  if x._p.pPr is not None:x._p.remove(x._p.pPr)
  x._p.insert(0,deepcopy(p[97]._p.pPr))
 return x
before(p[99],'The retained benchmark is hotspot = 0.25, λ = 1000, δ = 3 and 5 × 5 neighborhoods at both stages. The existing 16-configuration experiment varies hotspot (0.10, 0.20, 0.25 and 0.30) and both windows (3 × 3 or 5 × 5), holding λ and δ fixed. Table A3 recomputes its statistics for 11:00–16:00 UTC from existing month–hour pairs. Candidate-specific scores and paired common-support changes are both reported because changing windows or hotspot also changes sample retention. For example, hotspot = 0.30 with 5 × 5 then 3 × 3 windows gives 3.835/3.575 K on its own support, but on shared support its soil RMSE is 0.151 K above the benchmark while canopy RMSE is 0.045 K lower. The current evidence therefore does not establish a uniform improvement or justify changing the benchmark. Earlier λ and δ experiments used different soil-reference and screening definitions; they are not treated as optimization under the present protocol.')
before(p[99],'The 2018–2022 and 2023–2024 Europe comparisons and the early/late EVO periods in Table A2 are retrospective checks, since all periods had already been examined. Station eligibility is reapplied within each European period; nine sites qualify in each, with different site composition. These comparisons characterize observed temporal and sampling variability rather than independent prediction skill or a controlled temporal improvement. Additional independent sites and verified time metadata are needed before claiming transferable optimal parameters.')
# Append controlled tables before availability section.
anchor=p[117]
x=before(anchor,'Appendix A  Validation support and retrospective sensitivity')
x.paragraph_format.page_break_before=True;x.paragraph_format.keep_with_next=True
for rr in x.runs:rr.bold=True
def table(caption,headers,records,widths=None):
 cap=before(anchor,caption);cap.paragraph_format.keep_with_next=True
 if caption.startswith('Table A3.'):cap.paragraph_format.page_break_before=True
 tab=d.add_table(rows=1,cols=len(headers))
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'B0B0B0');borders.append(b)
 tab._tbl.tblPr.append(borders)
 for c,v in zip(tab.rows[0].cells,headers):c.text=v
 for vals in records:
  for c,v in zip(tab.add_row().cells,vals):c.text=str(v)
 for row in tab.rows:
  trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
  for cell in row.cells:
   for pp in cell.paragraphs:
    pp.paragraph_format.space_after=Pt(2);pp.paragraph_format.space_before=Pt(2)
    pp.paragraph_format.line_spacing=1
    for r in pp.runs:r.font.size=Pt(8)
 repeat=OxmlElement('w:tblHeader');tab.rows[0]._tr.get_or_add_trPr().append(repeat)
 if widths:
  tab.autofit=False
  for row in tab.rows:
   for c,w in zip(row.cells,widths):c.width=Inches(w)
 anchor._p.addprevious(tab._tbl)
 return tab
s=pd.read_csv(A/'all14_station_support.csv')
rec=[]
for x in s.itertuples():rec.append([x.site+(' *' if not x.retained else ''),x.years.replace('20','',1) if False else x.years.replace('201','1').replace('202','2'),x.months,x.groups,x.raw,f'{x.soil:.3f}',f'{x.canopy:.3f}'])
table('Table A1. Retained support and RMSE for all 14 European sites. Years use two digits (18 = 2018); months count distinct year–month combinations. An asterisk marks sites excluded from the principal 12-site subset. Soil and canopy share support. Counts describe paired station validation only.', ['Site','Years','Months','Groups','Raw pairs','Soil K','Canopy K'],rec,[.75,1.75,.5,.5,.65,.6,.65])
a=pd.read_csv(A/'temporal_assessment.csv');rec=[]
for (dom,per),g in a.groupby(['domain','period'],sort=False):
 def value(c):
  z=g[g.component==c];return '—' if z.empty else f'{z.rmse_equal.iloc[0]:.3f}'
 ss=g[g.component.isin(['soil','sunlit'])].iloc[0]
 label={'2017-08:12':'Aug–Dec 2017','2017-08:10':'Aug–Oct 2017','2017-11:12':'Nov–Dec 2017'}.get(per,per)
 rec.append([dom+' '+label,int(ss.sites),int(ss.groups),value('soil' if dom=='Europe12' else 'sunlit'),value('background'),value('canopy')])
table('Table A2. Retrospective temporal assessment of the fixed configuration. Europe values are equal-station mean RMSEs; EVO values are month–hour RMSEs. European sites need at least three groups in each period; compositions differ. All periods had previously been inspected. EVO background-soil support follows Sect. 4.2.', ['Domain and period','Sites','Groups','Soil K','Background K','Canopy K'],rec,[2.0,.45,.6,.75,.85,.75])
a=pd.read_csv(A/'hotspot_window_11_16.csv');rec=[]
models=sorted(a.model.unique(),key=lambda x:(float(x.split('_')[0][1:]),x))
for model in models:
 g=a[(a.period=='2018-2024')&(a.model==model)]
 own=g[g.support=='own_joint'].set_index('component'); common=g[g.support=='common_both10'].set_index('component')
 delta=lambda c: common.loc[c,'rmse']-common.loc[c,'baseline_rmse']
 rec.append([model.replace('h','').replace('_w',' / ').replace('_','–'),int(own.loc['soil','sites']),int(own.loc['soil','groups']),f"{own.loc['soil','rmse']:.3f}",f"{own.loc['canopy','rmse']:.3f}",f"{delta('soil'):+.3f}",f"{delta('canopy'):+.3f}"])
table('Table A3. Existing hotspot/window experiment summarized at 11–16 UTC for 2018–2024. The first column gives hotspot and first/second window width in pixels; λ = 1000 and δ = 3 throughout. Scores and counts use each candidate’s retained support. Δ is candidate minus benchmark RMSE on their shared instantaneous support, reaggregated to month–hour means; a negative value favors the candidate. Shared support differs between comparisons; complete counts and period-specific results accompany the analysis tables. These are retrospective comparisons, not independent selection tests.', ['h / windows','Sites','Groups','Soil K','Canopy K','Δsoil K','Δcanopy K'],rec,[1.2,.4,.6,.75,.8,.8,.85])
# Existing workflow image is replaced only if freshly drawn source exists.
fig=ROOT/'figures/figure03_station_workflow.png'
if fig.exists():
 x=p[38];x.clear();x.add_run().add_picture(str(fig),width=Inches(6.65));x.paragraph_format.keep_with_next=True
assert len(d._element.xpath('.//m:oMath'))==35
out=ROOT/'revised'/SRC.name;d.save(out)
audit={'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'staged_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'native_equations':35,'figures':len(d.inline_shapes),'tables':len(d.tables),'new_inversions':0,'regional_production_started':False,'external_pending':['source timezone metadata and sensor depths/heights','remote production configuration and completed output checks','corresponding author and CRediT','public final release and license']}
(A/'document_revision_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit,indent=2))
