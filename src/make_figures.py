"""Create English-language, 300 dpi figures from regenerated analysis outputs."""
from __future__ import annotations
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLBACKEND','Agg')
os.environ.setdefault('MPLCONFIGDIR',str(ROOT / '.cache/matplotlib'))
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from run_analysis import NAMES, MEASURES

COLORS = ['#4477AA','#CCBB44','#777777','#EE7733']
LABELS = ['Public-facing Service\nand Support','STEM and Computing',
          'Physical and\nTechnical Work','Interpersonal Support\nand Coordination']
TITLES = ['General AIOE','Language modeling AIOE','Image generation AIOE']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,default=ROOT/'results')
    parser.add_argument('--output',type=Path,default=None)
    args = parser.parse_args()
    results = args.results
    output = args.output or results/'figures'
    output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'savefig.dpi':300})

    def save(fig,name):
        fig.savefig(output/name,dpi=300,facecolor='white')
        plt.close(fig)

    evaluation = pd.read_csv(results/'k_selection_k2_k15.csv')
    fig,axs = plt.subplots(3,1,figsize=(7,8),layout='constrained')
    for ax,field,title in zip(axs[:2],['inertia','silhouette'],['A. Inertia','B. Silhouette score']):
        ax.plot(evaluation.k,evaluation[field],'o-',color='#4477AA')
        ax.set(xlabel='Number of clusters (k)',ylabel=field.title(),title=title)
        ax.set_xticks(range(2,16))
    valid = evaluation.dropna(subset=['mean_ARI'])
    axs[2].plot(valid.k,valid.mean_ARI,'o-',label='Mean ARI')
    axs[2].plot(valid.k,valid.minimum_ARI,'s--',label='Minimum ARI')
    axs[2].set(xlabel='Number of clusters (k)',ylabel='Adjusted Rand index',title='C. Initialization stability')
    axs[2].legend()
    save(fig,'01_k_selection.png')

    pca = pd.read_csv(results/'pca_coordinates.csv')
    variance = pd.read_csv(results/'pca_variance.csv').explained_variance_ratio
    fig,ax = plt.subplots(figsize=(8,6),layout='constrained')
    for c in range(4):
        selected = pca.loc[pca.cluster_id.eq(c)]
        ax.scatter(selected.PC1,selected.PC2,s=18,alpha=.7,color=COLORS[c],label=NAMES[c])
        ax.scatter(selected.PC1.mean(),selected.PC2.mean(),marker='X',s=110,c='black',edgecolors='white')
    ax.set(xlabel='PC1',ylabel='PC2',title=f'Occupation profiles (k = 4)\nPC1 + PC2 explain {100*variance.sum():.2f}% of variance')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.12),ncol=1,frameon=False)
    save(fig,'02_pca_k4.png')

    profiles = pd.read_csv(results/'communication_features_14.csv')
    values = profiles[NAMES].to_numpy()
    fig,ax = plt.subplots(figsize=(10,8),layout='constrained')
    im = ax.imshow(values,cmap='RdBu_r',vmin=-1.5,vmax=1.5,aspect='auto')
    ax.set_xticks(range(4),LABELS,rotation=25,ha='right')
    ax.set_yticks(range(14),profiles.element_name)
    for i in range(14):
        for j in range(4):
            ax.text(j,i,f'{values[i,j]:.2f}',ha='center',va='center',fontsize=9,
                    color='white' if abs(values[i,j])>1 else 'black')
    for boundary in [3.5,11.5]:ax.axhline(boundary,color='black',linewidth=.8)
    ax.set_title('Communication-related feature profiles')
    fig.colorbar(im,ax=ax,label='Mean feature z-score before domain weighting',shrink=.65)
    save(fig,'03_communication_profiles.png')

    desc = pd.read_csv(results/'cluster_aioe_descriptives.csv')
    means = desc.pivot(index='cluster_id',columns='measure',values='mean')[MEASURES].to_numpy()
    fig,ax = plt.subplots(figsize=(8,5),layout='constrained')
    im = ax.imshow(means,cmap='RdBu_r',vmin=-1.3,vmax=1.3,aspect='auto')
    ax.set_xticks(range(3),['General','Language modeling','Image generation'])
    ax.set_yticks(range(4),[f'{label}\n(n = {int(desc.loc[desc.cluster_id.eq(c),"n"].iloc[0])})' for c,label in enumerate(LABELS)])
    for i in range(4):
        for j in range(3):
            ax.text(j,i,f'{means[i,j]:.3f}',ha='center',va='center',color='white' if abs(means[i,j])>.8 else 'black')
    ax.set_title('Mean occupational AI exposure by cluster')
    fig.colorbar(im,ax=ax,label='Mean AIOE z-score (910-occupation reference)')
    save(fig,'04_mean_aioe.png')

    occupations = pd.read_csv(results/'occupations_878_clusters_and_aioe.csv')
    fig,axs = plt.subplots(3,1,figsize=(8,8),layout='constrained')
    for j,(ax,measure) in enumerate(zip(axs,MEASURES)):
        values = [occupations.loc[occupations.cluster_id.eq(c),measure].to_numpy() for c in [0,3]]
        boxes = ax.boxplot(values,orientation='horizontal',patch_artist=True,
                           tick_labels=[LABELS[0],LABELS[3]],whis=1.5)
        for box,c in zip(boxes['boxes'],[0,3]):box.set_facecolor(COLORS[c]);box.set_alpha(.65)
        ax.axvline(0,color='gray',linestyle='--',linewidth=.8)
        ax.set(title=f'{chr(65+j)}. {TITLES[j]}',xlabel='Occupational AIOE z-score')
    save(fig,'05_exposure_distributions.png')

    differences = pd.read_csv(results/'initialization_mean_differences.csv')
    fig,axs = plt.subplots(3,1,figsize=(7,7),layout='constrained')
    for j,(ax,measure) in enumerate(zip(axs,MEASURES)):
        selected = differences.loc[differences.measure.eq(measure)]
        runs = selected.loc[selected.seed.ne(42)].sort_values('seed')
        ax.plot(runs.seed,runs.mean_difference,'o-',color=COLORS[3])
        ax.axhline(selected.loc[selected.seed.eq(42),'mean_difference'].iloc[0],linestyle='--',color='black',label='Reference (seed = 42)')
        ax.axhline(0,linewidth=.7,color='gray')
        ax.set(title=f'{chr(65+j)}. {TITLES[j]}',xlabel='Random seed',ylabel='Mean AIOE difference',ylim=(-.02,.8))
        ax.set_xticks(range(0,20,2))
        ax.legend(loc='lower right',fontsize=8)
    save(fig,'06_initialization_contrasts.png')
    print('Saved six 300 dpi figures.')


if __name__ == '__main__':
    main()
