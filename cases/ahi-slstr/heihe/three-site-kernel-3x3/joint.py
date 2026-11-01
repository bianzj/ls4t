"""Joint two-SLSTR-view + one-AHI angular fit on matched 2 km supports.

Each footprint has an arbitrary thermal background; only angular coefficients
are shared. Native SLSTR correction precedes radiance aggregation. AHI IS a
calibration observation; only full-footprint leave-one-out results are validation.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import least_squares
from functions import radiance_mean


def window_mask(rows, cols, centre_row, centre_col):
    return (abs(np.asarray(rows)-centre_row)<=1)&(abs(np.asarray(cols)-centre_col)<=1)


def validate(data):
    required={'tn','to','ta','kn','ko','ka'}
    if set(data)!=required:raise ValueError('invalid joint input fields')
    if not all(np.isfinite(v).all() for v in data.values()):raise ValueError('inputs must be finite')
    n=len(data['ta']);p=data['ka'].shape[-1]
    if data['tn'].shape!=(n,4) or data['to'].shape!=(n,4) or data['kn'].shape!=(n,4,p) or data['ko'].shape!=(n,4,p) or data['ka'].shape!=(n,p):
        raise ValueError('invalid native/footprint array shapes')
    if p not in (1,2):raise ValueError('one or two angular coefficients required')
    for field in ('tn','to','ta'):
        if ((data[field]<220)|(data[field]>365)).any():raise ValueError('invalid input temperature range')


def correct(data, beta):
    native_n=data['tn']-data['kn']@beta;native_o=data['to']-data['ko']@beta
    if np.any(native_n<=0) or np.any(native_o<=0):raise ValueError('nonpositive trial native temperature')
    return np.column_stack([radiance_mean(native_n,axis=1),radiance_mean(native_o,axis=1),data['ta']-data['ka']@beta])


def residual(data,beta):
    n,o,a=correct(data,beta).T
    # Equivalent to eliminating one equal-weight mean per matched footprint.
    # One triplet contributes two contrasts, never four repeated AHI labels.
    return np.column_stack([(o-n)/np.sqrt(2),(a-(n+o)/2)/np.sqrt(1.5)]).ravel()


def scaled_condition(matrix):
    scale=np.linalg.norm(matrix,axis=0)
    if (scale<1e-12).any():raise ValueError('rank deficient kernel geometry')
    singular=np.linalg.svd(matrix/scale,compute_uv=False)
    if singular[-1]<=1e-12:raise ValueError('rank deficient kernel geometry')
    return float(singular[0]/singular[-1])


def fit_joint(data,max_condition=100.):
    data={k:np.asarray(v,float) for k,v in data.items()};validate(data)
    if len(data['ta'])<3:raise ValueError('at least three complete footprints required')
    kn,ko,ka=data['kn'].mean(axis=1),data['ko'].mean(axis=1),data['ka']
    x=np.stack([(ko-kn)/np.sqrt(2),(ka-(kn+ko)/2)/np.sqrt(1.5)],axis=1).reshape(-1,ka.shape[1])
    initial_condition=scaled_condition(x)
    if initial_condition>max_condition:raise ValueError(f'ill-conditioned initial geometry: {initial_condition:g}')
    tn,to=radiance_mean(data['tn'],axis=1),radiance_mean(data['to'],axis=1)
    y=np.column_stack([(to-tn)/np.sqrt(2),(data['ta']-(tn+to)/2)/np.sqrt(1.5)]).ravel()
    start=np.linalg.lstsq(x,y,rcond=None)[0]
    solution=least_squares(lambda b:residual(data,b),start,xtol=1e-12,ftol=1e-12,gtol=1e-12,x_scale='jac',max_nfev=500)
    if not solution.success:raise ValueError('joint optimization failed: '+solution.message)
    condition=scaled_condition(solution.jac)
    if condition>max_condition:raise ValueError(f'ill-conditioned joint fit: {condition:g}')
    return dict(coefficients=solution.x,condition=condition,footprints=len(tn),
                coarse_view_observations=3*len(tn),contrast_equations=2*len(tn),
                angular_parameters=len(solution.x),residual_degrees_of_freedom=2*len(tn)-len(solution.x),
                training_contrast_rmse_k=float(np.sqrt(np.mean(solution.fun**2))),
                initial_condition=initial_condition,success=True)


def subset(data,mask):
    return {k:v[mask] for k,v in data.items()}


def leave_one_out(data,max_condition=100.):
    fits=[]
    for i in range(len(data['ta'])):
        mask=np.arange(len(data['ta']))!=i
        fits.append(fit_joint(subset(data,mask),max_condition))
    return fits


def data_from_frame(frame,model='lsf_rl',width=1.):
    data={}
    for view in ('n','o'):
        data['t'+view]=frame[[f't_{view}_{j}' for j in range(4)]].to_numpy(float)
        native=[]
        for j in range(4):
            fields=[f'lsf_{view}_{j}']
            if model=='lsf_rl':fields.append(f'rl_{view}_w{width:g}_{j}')
            native.append(frame[fields].to_numpy(float))
        data['k'+view]=np.stack(native,axis=1)
    data['ta']=frame['t_a'].to_numpy(float)
    fields=['lsf_a']+([f'rl_a_w{width:g}'] if model=='lsf_rl' else [])
    data['ka']=frame[fields].to_numpy(float)
    return data


def correction_limits(data,beta,maximum=10.):
    raw=np.column_stack([radiance_mean(data['tn'],axis=1),radiance_mean(data['to'],axis=1),data['ta']])
    norms=correct(data,beta)
    maxima=np.column_stack([np.max(abs(data['kn']@beta),axis=1),np.max(abs(data['ko']@beta),axis=1),abs(data['ka']@beta)])
    accepted=np.isfinite(norms).all(axis=1)&(norms>=220).all(axis=1)&(norms<=365).all(axis=1)&(maxima<=maximum).all(axis=1)
    for field,kernel in [('tn','kn'),('to','ko')]:
        native=data[field]-data[kernel]@beta
        accepted&=np.isfinite(native).all(axis=1)&(native>=220).all(axis=1)&(native<=365).all(axis=1)
    return norms,norms-raw,maxima,accepted
