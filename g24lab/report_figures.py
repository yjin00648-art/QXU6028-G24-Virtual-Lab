"""Regenerate the five report figure groups from current computed outputs.

No archived result, report number, private workspace or manual edit is used.
The full runner calls this after both regular and blind analyses finish.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from PIL import Image
from . import l1,l2,l3

REPO=Path(__file__).resolve().parents[1]


def generate(output_root: Path):
    output_root=Path(output_root)
    REPLAY=output_root/"regular"
    FIG=output_root/"report_figures"
    FIG.mkdir(parents=True,exist_ok=True)
    regular=json.loads((REPLAY/"results.json").read_text())
    blind=json.loads((output_root/"blind/results.json").read_text())
    if regular["pipeline_commit"]!=blind["pipeline_commit"]:
        raise ValueError("Report figure inputs must share one source commit.")
    params=json.loads((REPO/"L1/data/L1_params.json").read_text())
    trajectory=pd.read_csv(REPLAY/"L2_calculations.csv")
    sensitivity=pd.read_csv(REPLAY/"L3_eta_sensitivity.csv")
    noise=pd.read_csv(REPLAY/"L3_noise_maxima.csv").iloc[:,0].to_numpy()
    l2_validation=json.loads((REPLAY/"L2_validation.json").read_text())
    plt.rcParams.update({'font.family':'serif','font.serif':['Nimbus Roman'], 'font.size':12,
                         'axes.titlesize':12,'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':11,
                         'legend.fontsize':10.5,'mathtext.fontset':'stix','axes.spines.top':False,'axes.spines.right':False})
    blue, orange, teal = '#1f4e79', '#b45f2a', '#237d73'
    checks = {}
    # L1: direct evaluation of retained equations only, with no fitting.
    ef = np.linspace(0,0.26,161)
    nb = np.array([l1.n_band(x,params['T'],params['c']) for x in ef])
    nf = np.array([l1.n_fermi(x,params['T'],params['c']) for x in ef])
    op = params['EF_op_eV']
    c2,c4 = (l1.solve_crossing(v,params['T'],params['c']) for v in (2,4))
    assert np.isclose(l1.n_fermi(op,params['T'],params['c']),regular['L1']['n_fermi_op_cm2'],rtol=1e-10)
    checks['L1_operating_result_matches'] = True
    checks['C2_crossing_eV'],checks['C4_crossing_eV'] = c2,c4
    fig,axs=plt.subplots(1,2,figsize=(6.45,3.15),layout='constrained')
    axs[0].plot(ef,nb/1e12,color=blue,label=r'$n_B$')
    axs[0].plot(ef,nf/1e12,color=teal,label=r'$n_F$')
    axs[0].set(xlabel=r'$E_F$ (eV)',ylabel=r'Population ($10^{12}$ cm$^{-2}$)',title='(a) Carrier populations')
    axs[0].legend(frameon=False)
    axs[1].plot(ef,nb/nf,color=blue)
    for val,where in [(2,c2),(4,c4)]:
        axs[1].axhline(val,color='0.5',ls=':',lw=1)
        axs[1].plot(where,val,'o',color=orange,ms=4)
    axs[1].plot(op,regular['L1']['correction_factor'],'o',color=orange,ms=5)
    axs[1].annotate('Operating point',xy=(op,regular['L1']['correction_factor']),xytext=(0.017,5.6),fontsize=10.5,arrowprops={'arrowstyle':'-','color':orange})
    axs[1].set(xlabel=r'$E_F$ (eV)',ylabel=r'$C=n_B/n_F$',title='(b) Counting correction',ylim=(0.7,6.7))
    for ax in axs:ax.axvline(op,color=orange,ls='--',lw=1);ax.grid(alpha=.2)
    fig.savefig(FIG/'figure1.png',dpi=320);fig.savefig(FIG/'figure1.svg');plt.close(fig)

    data=pd.read_csv(REPO/'L2/data/L2_data.csv')
    means=l2.core.prepare_means(data)
    xy=l2.core.normalise_pairs(means.R_H_mean.to_numpy(),means.R_xx_mean.to_numpy())
    indices=means.measurement_index.to_numpy()
    fit_ef,hall,sheet=l2.build_curves(300.,np.array([0.,regular['L2']['Eg_kT']]))
    rms,j=l2.nearest(xy,hall[1],sheet[1])
    assigned=np.array(regular['L2']['EF_trajectory_eV'])
    np.testing.assert_allclose(fit_ef[j],assigned,rtol=0,atol=1e-14)
    np.testing.assert_allclose(trajectory.EF_assigned_eV,assigned,rtol=0,atol=1e-14)
    np.testing.assert_allclose(trajectory.R_H_mean,means.R_H_mean,rtol=1e-12,atol=1e-25)
    assert np.isclose(rms,l2_validation["selected_residual"],rtol=1e-10,atol=1e-12)
    checks.update(L2_assigned_trajectory_matches=True,L2_selected_RMS=rms,retained_EF_intervals_rows=len(trajectory))
    scan=pd.read_csv(REPLAY/'L2_gap_residual_sweep.csv')
    fig,axs=plt.subplots(2,2,figsize=(6.45,5.7),layout='constrained')
    ax=axs[0,0]
    ax.plot(hall[0],sheet[0],ls=':',color='0.5',label='Cone')
    ax.plot(hall[1],sheet[1],color=blue,label='Hard gap')
    ax.plot(xy[:,0],xy[:,1],ls='--',color=orange,lw=.8,alpha=.7)
    ax.scatter(xy[:,0],xy[:,1],s=13,color=orange,edgecolors='none',zorder=3,label='Repeat means')
    ax.set(xlabel=r'Normalised $R_H$',ylabel=r'Normalised $R_s$',title='(a) Joint curve fit')
    ax.legend(frameon=False,fontsize=9,loc='center',bbox_to_anchor=(.5,.55))
    for col,curves,title in [(0,hall,'(b) Signed Hall overlay'),(1,sheet,'(c) Resistance overlay')]:
        ax=axs[0,1] if col==0 else axs[1,0]
        ax.plot(fit_ef,curves[0],ls=':',color='0.5')
        ax.plot(fit_ef,curves[1],color=blue)
        ax.scatter(assigned,xy[:,col],s=11,color=orange)
        ax.set(xlabel=r'Assigned $E_F$ (eV)',ylabel=r'Normalised $R_H$' if col==0 else r'Normalised $R_s$',title=title)
        ax.axhline(0,color='0.65',lw=.6)
    ax=axs[1,1]
    overview=scan.loc[scan.grid=='global'].sort_values('Eg_kT')
    ax.plot(overview.Eg_kT,overview.rms_residual,color=blue,marker='.',ms=3)
    ax.axhline(.85*l2_validation["cone_residual"],color=teal,ls=':',lw=1,label='15% threshold')
    ax.plot(regular['L2']['Eg_kT'],rms,'*',color=orange,ms=9,label='Refined minimum')
    ax.set(xlabel=r'Gap $E_g/k_BT$',ylabel='Joint RMS residual',title='(d) Gap residual evidence')
    ax.legend(frameon=False,fontsize=9)
    for ax in axs.flat:ax.grid(alpha=.18)
    fig.savefig(FIG/'figure2.png',dpi=320);fig.savefig(FIG/'figure2.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.45,3.15),layout='constrained')
    ax.fill_between(indices,trajectory.EF_bootstrap_p16_eV,trajectory.EF_bootstrap_p84_eV,color='#9cc7df',alpha=.6,label='16th–84th percentile')
    ax.plot(indices,assigned,'o-',ms=3,color=blue,label='Central assignment')
    ax.axhline(0,color='0.3',lw=.7)
    ax.set(xlabel='Measurement index',ylabel=r'Assigned $E_F$ (eV)')
    ax.legend(frameon=False,fontsize=10.5,loc='upper left');ax.grid(alpha=.18)
    fig.savefig(FIG/'figure3.png',dpi=320);fig.savefig(FIG/'figure3.svg');plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(6.45,3.3),layout='constrained')
    norm=TwoSlopeNorm(vmin=-4.5,vcenter=0,vmax=4.5)
    for ax,result,title in zip(axs,[regular,blind],['(a) Regular clear fail','(b) Blind clear pass']):
        m=np.array(result['L3']['map']).reshape(10,10)*100
        image=ax.imshow(m,origin='lower',extent=(-3,3,-3,3),cmap='RdBu_r',norm=norm,interpolation='nearest')
        xx,yy=np.meshgrid(l3.COORDS,l3.COORDS)
        levels=[x for x in [-3,3] if m.min()<x<m.max()]
        if levels:ax.contour(xx,yy,m,levels=levels,colors='black',linestyles='--',linewidths=.7)
        for feature in result['L3']['features']:
            ax.plot(feature['x_probe_pitch'],feature['y_probe_pitch'],'o',ms=5,mfc='none',mec='black',mew=1)
        ax.set(xlabel='x (probe pitches)',ylabel='y (probe pitches)',title=title,xticks=[-2.7,0,2.7],yticks=[-2.7,0,2.7])
    bar=fig.colorbar(image,ax=list(axs),fraction=.038,pad=.025)
    bar.set_label('Relative deviation (%)',fontsize=11)
    fig.savefig(FIG/'figure4.png',dpi=320);fig.savefig(FIG/'figure4.svg');plt.close(fig)

    A=np.load(REPO/'L3/data/L3_A.npy')
    L=l3.gradient_matrix(10);P=l3.zero_mean_projector(100)
    eta=1e-2*np.linalg.norm(A,2)**2/np.linalg.norm(L,2)**2
    operator=l3.inverse_operator(A,L,P,eta)
    psf1,width1=l3.psf_result(A,operator,5,5);psf2,width2=l3.psf_result(A,operator,2,7)
    assert np.isclose(max(width1,width2),regular['L3']['resolution_probe_pitch'],rtol=1e-10)
    assert len(noise)==500 and np.isclose(np.percentile(noise,95),regular['L3']['detection_limit_fraction'],rtol=1e-10)
    np.testing.assert_allclose(pd.read_csv(REPLAY/'L3_map.csv',index_col=0).to_numpy().ravel(),regular['L3']['map'],rtol=1e-10,atol=1e-12)
    checks.update(L3_retained_map_matches=True,L3_noise_quantile_matches=True,L3_PSF_matches=True)
    fig,axs=plt.subplots(2,2,figsize=(6.45,5.9),layout='constrained')
    ax=axs[0,0]
    ax.plot(sensitivity.roughness_norm,sensitivity.residual_norm,'-',color='0.6',lw=1)
    for row,colour in zip(sensitivity.itertuples(),['#6a51a3','#237d73','#1f4e79','#b45f2a','#8c2d3e']):
        ax.plot(row.roughness_norm,row.residual_norm,'o',color=colour,ms=4,label=f'{row.eta_factor:g}')
    chosen=sensitivity.loc[sensitivity.eta_factor==1].iloc[0]
    ax.plot(chosen.roughness_norm,chosen.residual_norm,'*',color=orange,ms=10)
    ax.set(xlabel=r'Roughness $||Lm||_2$',ylabel=r'Residual $||Am-\bar d||_2$',title='(a) Sensitivity to eta')
    ax.legend(title=r'$\eta/\eta_0$',loc='upper right',frameon=False,fontsize=9,title_fontsize=10,labelspacing=.25)
    ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0));ax.grid(alpha=.18)
    for ax,psf,title in [(axs[0,1],psf1,'(b) Central PSF 1.444 pitches'),(axs[1,0],psf2,'(c) Off-centre PSF 1.303 pitches')]:
        im=ax.imshow(psf,origin='lower',extent=(-3,3,-3,3),cmap='RdBu_r',vmin=-.5,vmax=.5,interpolation='nearest')
        ax.set(xlabel='x (probe pitches)',ylabel='y (probe pitches)',title=title,xticks=[-2,0,2],yticks=[-2,0,2])
        fig.colorbar(im,ax=ax,fraction=.05,pad=.02,ticks=[-.5,0,.5])
    ax=axs[1,1]
    ax.hist(noise*1e6,bins=20,color=teal,edgecolor='white',linewidth=.4)
    ax.axvline(regular['L3']['detection_limit_fraction']*1e6,color=orange,ls='--',label=r'$\delta_{95}$')
    ax.set(xlabel=r'Noise maximum ($10^{-6}$)',ylabel='Count',title='(d) 500 noise-only maps')
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.18)
    fig.savefig(FIG/'figure5.png',dpi=320);fig.savefig(FIG/'figure5.svg');plt.close(fig)
    

    for number in range(1,6):
        with Image.open(FIG/f"figure{number}.png") as im:im.verify()
    checks.update(
        pipeline_commit=regular["pipeline_commit"],
        purpose="Recomputed figures for the English coursework report draft",
        figure_count=5,
        figure_panels={"1":"L1 n_B, n_F and correction factor", "2":"L2 joint fit, separate Hall/resistance overlays and residual search", "3":"L2 ordered Fermi trajectory and paired-resampling bands", "4":"Regular and blind maps on one percentage scale", "5":"L3 eta sensitivity, two PSFs and 500 noise maxima"},
        input_sha256={str(p.relative_to(output_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [REPLAY/"results.json",output_root/"blind/results.json",REPLAY/"L2_calculations.csv",REPLAY/"L3_eta_sensitivity.csv",REPLAY/"L3_noise_maxima.csv"]},
        output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FIG.iterdir()) if p.suffix in {".png",".svg"}},
    )
    (FIG/"validation.json").write_text(json.dumps(checks,indent=2)+"\n")
    print(json.dumps(checks,indent=2),flush=True)
    return checks


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root",type=Path,required=True)
    generate(parser.parse_args().output_root)
