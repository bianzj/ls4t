"""Independent historical scalar-center, physical-unit and tiled-boundary checks."""
from pathlib import Path
import argparse
import ast
import hashlib
import inspect
import json
import warnings
import numpy as np
import produce_msg_ls4t as producer

HERE=Path(__file__).resolve().parent
SCALAR=Path('C:/work/ls4t-msg/cases/official/implementation/msg_lsct3.2-iter-site-cons-ig-center.py')
CACHE=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/parameter_search/input_cache.npz')
HC=6.62607015e-34
LIGHT=299792458.
KB=1.380649e-23
WAVELENGTH=10.5e-6

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def radiation(temperature):
    with np.errstate(all='ignore'):
        return (2*HC*LIGHT**2/WAVELENGTH**5)/(np.exp(HC*LIGHT/(WAVELENGTH*KB*np.asarray(temperature)))-1)*1e-6

def temperature(radiance):
    with np.errstate(all='ignore'):
        return np.where(radiance>0,HC*LIGHT/(WAVELENGTH*KB*np.log(1+2*HC*LIGHT**2*1e-6/(WAVELENGTH**5*np.asarray(radiance)))),np.nan)

def load_scalar():
    parsed=ast.parse(SCALAR.read_text(encoding='utf-8'))
    names={'hotspot_layer','solve_2x2_system_center','solve_constrained_vectorized2_center','solve_joint_center'}
    nodes=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert len(nodes)==len(names)
    namespace={'np':np}
    # Execute the unedited historical functions, without its I/O processing loop
    # or obsolete planck(10.5) units. Physical Planck is checked independently.
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SCALAR),'exec'),namespace)
    return namespace

def oracle(d,scalar):
    with np.errstate(all='ignore'):
        we,be=scalar['hotspot_layer'](d['lai'],.25,d['vza_e'],d['sza'],(d['saa']-d['vaa_e']+180)%360-180)
        wi,bi=scalar['hotspot_layer'](d['lai'],.25,d['vza_i'],d['sza'],(d['saa']-d['vaa_i']+180)%360-180)
        weights=np.stack([d['emis_s']*we,d['emis_s']*(be-we),d['emis_v']*(1-be),d['emis_s']*wi,d['emis_s']*(bi-wi),d['emis_v']*(1-bi)],-1)
        re=radiation(d['lst_e'])*weights[...,:3].sum(-1)
        ri=radiation(d['lst_i'])*weights[...,3:].sum(-1)
    good=np.isfinite(re)&np.isfinite(ri)&np.isfinite(weights).all(-1)
    good&=(d['sza']>=0)&(d['sza']<90)&(d['lai']>=0)&(d['lai']<=10)
    for key in ['vza_e','vza_i']:good&=(d[key]>=0)&(d[key]<90)
    for key in ['emis_s','emis_v']:good&=(d[key]>0)&(d[key]<=1)
    if 'land' in d:good&=(d['land']>0)&(d['land']<=17)
    n=int(good.sum());center_good=bool(good[2,2]);low_lai=bool(d['lai'][2,2]<.05)
    # Historical solve excludes NaN jointly. Normalize finite/physical masks
    # to that same common dual-view mask before feeding it the actual solver.
    re=np.where(good,re,np.nan);ri=np.where(good,ri,np.nan)
    weights=np.where(good[...,None],weights,np.nan)
    a,b,c,e,f,g=[weights[...,k] for k in range(6)]
    with np.errstate(all='ignore'):
        sun,_=scalar['solve_2x2_system_center'](re,ri,a,b+c,e,f+g)
        rre=re-a*sun;rri=ri-e*sun
        unconstrained_shade,unconstrained_canopy=scalar['solve_2x2_system_center'](rre,rri,b,c,f,g)
        # A scalar window can solve its neighbors even when its center is
        # missing. The rolling producer correctly rejects that center before
        # creating a prior; no constraint was applied there, so bit 16 is clear.
        bound=bool(center_good and n>=10 and abs(unconstrained_shade-unconstrained_canopy)>3)
        shade,canopy=scalar['solve_constrained_vectorized2_center'](rre,rri,b,c,f,g,sun,dif=3.)
        shade=min(shade,sun)
    valid_prior=center_good and n>=10 and not low_lai and np.isfinite([sun,shade,canopy]).all()
    expected=np.full(4,np.nan)
    if valid_prior:
        with np.errstate(all='ignore'):
            final=scalar['solve_joint_center'](re,ri,weights,np.array([sun,shade,canopy]),lmbda=1000.)
            fs,fh,fv=final
            gap=np.exp(-.5*d['lai'][2,2]/np.cos(np.radians(d['sza'][2,2])))
            expected=temperature(np.array([fs*gap+fh*(1-gap),fv,fs,fh]))
    valid=bool(np.isfinite(expected).all() and np.all((expected>=250)&(expected<=350)))
    if not valid:expected[:]=np.nan
    qa=int(not center_good)|(int(n<10)<<1)|(int(low_lai)<<2)
    qa|=int(not valid and center_good and n>=10 and not low_lai)<<3
    qa|=int(bound)<<4
    return expected,n,qa

def copy_case(d):return {k:np.asarray(v,dtype=np.float64).copy() for k,v in d.items()}

def variants(d,index):
    yield 'original',d
    if index%4:return
    for key in ['lst_e','lst_i','emis_s']:
        z=copy_case(d);z[key][0,0]=np.nan
        yield 'missing_neighbor_'+key,z
    z=copy_case(d);z['lst_e'][0,0]=np.nan;z['lst_i'][4,4]=np.nan
    yield 'distinct_dual_view_missing_neighbors',z
    z=copy_case(d);z['lst_i'][2,2]=np.nan
    yield 'missing_center',z
    z=copy_case(d);z['sza'][:]=95.
    yield 'night',z
    z=copy_case(d);z['lai'][2,2]=.049
    yield 'low_lai_center',z
    z=copy_case(d);z['emis_s'][0,1]=np.inf
    yield 'infinite_weight_neighbor',z
    for count in [9,10]:
        z=copy_case(d);keep=np.zeros(25,bool);keep[12]=True
        keep[np.array([i for i in range(25) if i!=12])[:count-1]]=True
        z['lst_e'].ravel()[~keep]=np.nan
        yield 'neighbor_threshold_'+str(count),z

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'verification.json')
    args=parser.parse_args()
    frozen_sha=sha(producer.__file__)
    expected={'hotspot':.25,'lambda':1000.,'delta_radiance':3.,'first_window':5,'second_window':5,'minimum_valid_neighbors':10,'minimum_LAI':.05,'wavelength_m':10.5e-6}
    assert all(producer.PROTOCOL[k]==value for k,value in expected.items())
    assert producer.PROTOCOL['residual_mode']=='center_constant_sunlit_over_entire_5x5'
    scalar=load_scalar()
    errors=[];invalid=0;cases=0;constraints=0;fixture=None;types={}
    with np.load(CACHE) as cached,warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        for index in range(len(cached['lai'])):
            data={key:values[0 if len(values)==1 else index].astype(np.float64).copy() for key,values in cached.items()}
            for label,d in variants(data,index):
                reference,neighbors,qa=oracle(d,scalar)
                actual,n,q=producer.retrieve(d)
                actual=actual[:,2,2]
                assert int(n[2,2])==neighbors,(index,label,'neighbor mask',int(n[2,2]),neighbors)
                assert int(q[2,2])==qa,(index,label,'QA',int(q[2,2]),qa)
                assert np.isfinite(actual).all()==np.isfinite(reference).all(),(index,label,actual,reference)
                np.testing.assert_allclose(actual,reference,rtol=0,atol=1e-7,equal_nan=True,err_msg=f'cache={index} case={label}')
                if np.isfinite(reference).all():
                    errors.append(float(np.max(np.abs(actual-reference))));fixture=copy_case(d)
                else:invalid+=1
                constraints+=bool(qa&16);cases+=1;types[label]=types.get(label,0)+1
    assert len(errors)>=250 and cases>=1500 and constraints>0
    # Every edge and several seams compare to explicit nearest-padded scalar
    # windows; this also records that edge replication counts repeated terms.
    mosaic={key:np.tile(value,(7,6)) for key,value in fixture.items()}
    result=producer.retrieve(mosaic);height,width=mosaic['lai'].shape
    padded={key:np.pad(value,2,mode='edge') for key,value in mosaic.items()}
    locations={(0,0),(0,width-1),(height-1,0),(height-1,width-1),(1,1),(2,2),(7,6),(8,7),(9,8),(height//2,width//2)}
    for y,x in locations:
        window={key:value[y:y+5,x:x+5] for key,value in padded.items()}
        reference,n,q=oracle(window,scalar)
        np.testing.assert_allclose(result[0][:,y,x],reference,rtol=0,atol=1e-7,equal_nan=True)
        assert int(result[1][y,x])==n and int(result[2][y,x])==q
    tiled=[np.full_like(array,np.nan) if i==0 else np.zeros_like(array) for i,array in enumerate(result)]
    for y in range(0,height,8):
        for x in range(0,width,7):
            end_y,end_x=min(height,y+8),min(width,x+7)
            lo_y,lo_x=max(0,y-2),max(0,x-2)
            hi_y,hi_x=min(height,end_y+2),min(width,end_x+2)
            crop_y,crop_x=slice(y-lo_y,end_y-lo_y),slice(x-lo_x,end_x-lo_x)
            local=producer.retrieve({key:value[lo_y:hi_y,lo_x:hi_x] for key,value in mosaic.items()})
            tiled[0][:,y:end_y,x:end_x]=local[0][:,crop_y,crop_x]
            tiled[1][y:end_y,x:end_x]=local[1][crop_y,crop_x]
            tiled[2][y:end_y,x:end_x]=local[2][crop_y,crop_x]
    np.testing.assert_allclose(tiled[0],result[0],rtol=0,atol=1e-7,equal_nan=True)
    assert np.array_equal(tiled[1],result[1]) and np.array_equal(tiled[2],result[2])
    signed=np.array([-32768,-15000,-8000,-1000,-1,0,1,1000,8000,12000],dtype=np.int16)
    expected_decode=signed.astype(float)/100+273.15
    expected_decode[(signed==0)|(signed==-8000)|(expected_decode<150)|(expected_decode>400)]=np.nan
    for raw in [signed,signed.view(np.uint16)]:
        np.testing.assert_allclose(producer.decode_lst(raw,nodata=0),expected_decode,rtol=0,atol=0,equal_nan=True)
    raw_lai=np.array([0,1,50,1000,10000,10001,65535],dtype=np.uint16)
    np.testing.assert_allclose(producer.decode_lai(raw_lai,nodata=0),[np.nan,.001,.05,1.,10.,np.nan,np.nan],rtol=0,atol=0,equal_nan=True)
    temperatures=np.array([250.,273.15,300.,350.])
    np.testing.assert_allclose(producer.planck(temperatures),radiation(temperatures),rtol=1e-13,atol=0)
    np.testing.assert_allclose(producer.inverse(radiation(temperatures)),temperatures,rtol=0,atol=1e-10)
    np.testing.assert_allclose(producer.inverse(producer.planck(temperatures)),temperatures,rtol=0,atol=1e-10)
    assert sha(producer.__file__)==frozen_sha,'Producer changed during verification; rerun final code.'
    report={'status':'passed','producer_sha256':frozen_sha,'protocol_hash':producer.PROTOCOL_HASH,'historical_scalar_sha256':sha(SCALAR),'real_cache_sha256':sha(CACHE),'real_cache_records':999,'scalar_cases':cases,'valid_scalar_cases':len(errors),'invalid_cases':invalid,'constraint_active_cases':constraints,'maximum_temperature_difference_K':max(errors),'case_types':types,'shared_mask_verified':True,'second_window_center_constant_verified':True,'center_constraint_and_joint_verified':True,'tile_halo_invariance':True,'edge_scalar_cases':len(locations),'boundary_rule':'Nearest replication, including repeated edge terms in valid_neighbors. No tile-seam padding enters the retained interior.','signed_uint16_int16_decode_verified':True,'zero_and_minus8000_nodata_verified':True,'night_missing_center_and_low_lai_verified':True,'physical_planck_verified':True,'B300_W_m2_sr_um':float(radiation(300.)),'ground_reference_filter':'None; production has no ground observation input or 10 K ground-error rejection.','limitations':['Verifies the numerical method and I/O decoding, not independent ground accuracy.','Declared-slot geometry and product-file schemas are audited separately.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
