"""Relocate outputs while retaining the completed experiment's provenance.

No retrieval formulas or parameters are changed. Resume accepts the historical
protocol only with an exact, recorded set of relocated source hashes.
"""
from pathlib import Path
import ast,hashlib,json

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'
OLD='C:/BaiduSyncdisk/research/ls4t_msg/production_assessment'
NEW=(HERE.parent/'results/production_assessment').as_posix()

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def definitions(text):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

def main():
    assert json.loads((OUT/'progress.json').read_text())['status']=='completed'
    marker=OUT/'source_relocation.json'
    if marker.exists():
        m=json.loads(marker.read_text())
        assert all(sha(p)==h for p,h in m['relocated_source_sha256'].items())
        print('SOURCE_PATHS_ALREADY_RELOCATED');return
    protocol=json.loads((OUT/'protocol.json').read_text());snap=OUT/'source_snapshot';snap.mkdir(exist_ok=True)
    for path,h in protocol['source_sha256'].items():
        assert sha(path)==h,(path,'original source changed before relocation')
        (snap/Path(path).name).write_bytes(Path(path).read_bytes())
    changed=[];originals={}
    for p in HERE.glob('*.py'):
        if p.name==Path(__file__).name:continue
        text=p.read_text(encoding='utf8');updated=text.replace(OLD,NEW).replace(OLD.replace('/','\\'),NEW.replace('/','\\'))
        if p.name=='search_evo_parameters.py':
            updated=updated.replace("PAPER = Path('C:/BaiduSyncdisk/research/ls4t_msg')", "PAPER = ROOT/'cases/official/results'")
        if text!=updated:
            originals[p.name]=text
            p.write_text(updated,encoding='utf8');changed.append(str(p))
    runner=HERE/'run_station_full_2018_2024.py';text=runner.read_text(encoding='utf8')
    old="    if pp.exists():assert json.loads(pp.read_text())['protocol_hash']==ph,'Changed protocol: do not mix results'"
    new="""    if pp.exists():
        existing=json.loads(pp.read_text())
        if existing['protocol_hash']!=ph:
            relocation=json.loads((OUT/'source_relocation.json').read_text())
            assert existing['protocol_hash']==relocation['original_protocol_hash']
            assert protocol['source_sha256']==relocation['relocated_source_sha256'],'Changed source: do not mix results'
            core=lambda p:json.loads(json.dumps({k:v for k,v in p.items() if k not in ['source_sha256','protocol_hash']}))
            assert core(existing)==core(protocol),'Changed scientific protocol: do not mix results'
            atomic(OUT/'runtime_relocated_sources.json',{'source_sha256':protocol['source_sha256'],'output_root':str(OUT)})
            ph=existing['protocol_hash'];protocol=existing"""
    assert text.count(old)==1;text=text.replace(old,new);runner.write_text(text,encoding='utf8')
    for name,original in originals.items():
        before=definitions(original);after=definitions((HERE/name).read_text(encoding='utf8'))
        if name=='run_station_full_2018_2024.py':
            for n in ['worker','load','functions','sha','atomic']:assert before[n]==after[n],(name,n)
        if name=='search_evo_parameters.py':
            for n in before:assert before[n]==after[n],(name,n)
    mapping={'original_protocol_hash':protocol['protocol_hash'],'original_source_sha256':protocol['source_sha256'],
             'relocated_source_sha256':{p:sha(p) for p in protocol['source_sha256']},
             'unchanged_computation_AST':True,'source_snapshots':str(snap),'changed_path_sources':changed,
             'change':'Output/readback paths relocated to cases; runner permits exactly these hashes against unchanged historical scientific protocol.'}
    marker.write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf8')
    print('RELOCATED_PATH_SOURCES',len(changed))

if __name__=='__main__':main()
