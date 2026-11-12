"""Reproduce the domain-balanced occupational clustering and exposure analysis."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from itertools import combinations
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('Abilities', 'abilities', 52, ['IM', 'LV']),
    ('Essential Skills', 'essential_skills', 10, ['IM', 'LV']),
    ('Transferable Skills', 'transferable_skills', 25, ['IM', 'LV']),
    ('Knowledge', 'knowledge', 33, ['IM', 'LV']),
    ('Work Activities', 'work_activities', 41, ['IM', 'LV']),
    ('Work Context', 'work_context', 57, ['CX', 'CT']),
    ('Work Styles', 'work_styles', 21, ['WI']),
]
NAMES = ['Public-facing Service and Support', 'STEM and Computing',
         'Physical and Technical Work', 'Interpersonal Support and Coordination']
MEASURES = ['aioe_z_detailed', 'lm_aioe_z_detailed', 'ig_aioe_z_detailed']
CORE_IDS = ['4.C.1.a.4', '4.C.1.b.1.f', '4.A.4.a.8', '2.C.1.e',
            '2.A.1.b', '2.A.1.d', '2.B.1.a', '2.B.1.b', '2.B.1.c',
            '2.B.1.d', '2.B.1.e', '4.A.4.a.4', '2.B.1.f', '4.A.4.a.5']
SOC_NAMES = dict(zip(
    ['11','13','15','17','19','21','23','25','27','29','31','33','35','37','39','41','43','45','47','49','51','53'],
    ['Management','Business and Financial Operations','Computer and Mathematical',
     'Architecture and Engineering','Life, Physical, and Social Science',
     'Community and Social Service','Legal','Educational Instruction and Library',
     'Arts, Design, Entertainment, Sports, and Media','Healthcare Practitioners and Technical',
     'Healthcare Support','Protective Service','Food Preparation and Serving Related',
     'Building and Grounds Cleaning and Maintenance','Personal Care and Service',
     'Sales and Related','Office and Administrative Support','Farming, Fishing, and Forestry',
     'Construction and Extraction','Installation, Maintenance, and Repair',
     'Production','Transportation and Material Moving']))


def save(frame, output, name):
    frame.to_csv(output / (name + '.csv'), index=False, float_format='%.15g')


def verify_sources():
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    for item in manifest['files']:
        path = ROOT / item['path']
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError(f'Source checksum mismatch: {item["path"]}')
        raw = gzip.decompress(content) if path.suffix == '.gz' else content
        if hashlib.sha256(raw).hexdigest() != item['uncompressed_sha256']:
            raise ValueError(f'Uncompressed checksum mismatch: {item["path"]}')


def load_sources():
    titles = pd.read_csv(ROOT / 'data/raw/onet31/occupation_data.csv.gz').set_index('O*NET-SOC Code')['Title']
    raw = {}
    for domain, filename, count, scales in SPECS:
        frame = pd.read_csv(ROOT / f'data/raw/onet31/{filename}.csv.gz')
        frame = frame.loc[frame['Scale ID'].isin(scales)].copy()
        assert frame['Element ID'].nunique() == count
        assert not frame.duplicated(['O*NET-SOC Code', 'Element ID', 'Scale ID']).any()
        raw[domain] = frame
    return titles, raw


def prepare_features(raw, titles, output):
    matrices, metadata = [], []
    for domain, _, count, scales in SPECS:
        frame = raw[domain].copy()
        if 'LV' in scales:
            nr = frame['Scale ID'].eq('LV') & frame['Not Relevant'].eq('Y')
            frame.loc[nr, 'Data Value'] = 0.0
            paired = frame.pivot(index=['O*NET-SOC Code', 'Element ID', 'Element Name'],
                                 columns='Scale ID', values='Data Value').reset_index()
            paired['value'] = (paired.IM - 1) / 4 * (paired.LV / 7)
            scale_description = 'IM/LV'
        else:
            paired = frame.rename(columns={'Data Value': 'value'})
            scale_description = '/'.join(scales)
        wide = paired.pivot(index='O*NET-SOC Code', columns=['Element ID', 'Element Name'], values='value')
        wide = wide.sort_index(axis=1)
        wide.columns = [f'{domain}__{element}__{name}' for element, name in wide.columns]
        matrices.append(wide)
        for column in wide.columns:
            _, element, name = column.split('__', 2)
            metadata.append(dict(feature=column, domain=domain, element_id=element,
                                 element_name=name, scales=scale_description,
                                 used_in_clustering=domain != 'Abilities'))
    all_features = pd.concat(matrices, axis=1).sort_index()
    complete = all_features.dropna()
    assert complete.shape == (878, 239)
    metadata = pd.DataFrame(metadata)
    save(metadata, output, 'feature_identifiers_239')
    selected = metadata.loc[metadata.used_in_clustering].copy()
    # The original intermediate CSV used ten significant digits. Preserve this
    # documented serialization step before standardization for exact replication.
    features = complete[selected.feature].map(lambda value: float(format(value, '.10g')))
    identifiers = pd.DataFrame({'onet_soc_code': features.index,
                                'title': titles.reindex(features.index).values})
    features = features.reset_index(drop=True)
    save(pd.concat([identifiers, features], axis=1), output, 'representative_features_187')
    counts = selected.groupby('domain').size()
    multipliers = np.sqrt(187 / (6 * selected.domain.map(counts).to_numpy()))
    scaler = StandardScaler()
    z = scaler.fit_transform(features)
    y = z * multipliers
    assert np.isfinite(y).all()
    for domain in counts.index:
        mask = selected.domain.eq(domain).to_numpy()
        assert np.isclose(y[:, mask].var(axis=0, ddof=0).sum(), 187 / 6)
    selected['mean_before_z'] = scaler.mean_
    selected['sd_before_z_ddof0'] = scaler.scale_
    selected['domain_multiplier'] = multipliers
    save(selected, output, 'feature_identifiers_187')
    save(pd.DataFrame({'domain': counts.index, 'feature_count': counts.values,
                       'multiplier': np.sqrt(187 / (6 * counts.values))}), output, 'domain_weights')
    for name, values in [('standardized_z_187', z), ('domain_weighted_input_187', y)]:
        save(pd.concat([identifiers, pd.DataFrame(values, columns=features.columns)], axis=1), output, name)
    return identifiers, selected, features, z, y


def calculate_exposure(raw, titles, output):
    matrix = pd.read_stata(ROOT / 'data/raw/aioe/mturk_mapping_matrix.dta')
    columns = [column for column in matrix if column not in ['application_id', 'applications']]
    assert len(matrix) == 10 and len(columns) == 52
    weights = pd.DataFrame({'ability_key': columns, 'general_ai_weight': matrix[columns].sum().values})
    for application, name in [('language modeling', 'language_modeling_weight'),
                              ('generating images', 'image_generation_weight')]:
        chosen = matrix.loc[matrix.applications.eq(application), columns]
        assert len(chosen) == 1
        weights[name] = chosen.iloc[0].values
    frame = raw['Abilities'].copy()
    nr = frame['Scale ID'].eq('LV') & frame['Not Relevant'].eq('Y')
    frame.loc[nr, 'Data Value'] = 0.0
    wide = frame.pivot(index=['O*NET-SOC Code','Element ID','Element Name'],
                       columns='Scale ID', values='Data Value').reset_index()
    assert len(wide) == 910 * 52 and wide[['IM','LV']].notna().all().all()
    wide['ability_key'] = wide['Element Name'].str.lower().str.replace(r'[ -]', '', regex=True)
    mapping = wide[['Element ID','Element Name','ability_key']].drop_duplicates()
    assert len(mapping) == 52 and mapping.ability_key.is_unique
    assert set(mapping.ability_key) == set(weights.ability_key)
    save(mapping.sort_values('Element ID'), output, 'ability_mapping_52')
    save(weights, output, 'application_ability_weights_52')
    wide = wide.merge(weights, on='ability_key', validate='many_to_one')
    wide['occupation_ability_weight'] = wide.IM / 5 * (wide.LV / 7)
    prefixes = ['aioe', 'lm_aioe', 'ig_aioe']
    for prefix, weight in zip(prefixes, ['general_ai_weight','language_modeling_weight','image_generation_weight']):
        wide[prefix + '_numerator_contribution'] = wide.occupation_ability_weight * wide[weight]
    grouped = wide.groupby('O*NET-SOC Code', sort=True)
    scores = grouped.occupation_ability_weight.sum().to_frame('denominator')
    assert (scores.denominator > 0).all()
    reference = []
    for prefix in prefixes:
        scores[prefix + '_numerator'] = grouped[prefix + '_numerator_contribution'].sum()
        values = scores[prefix + '_numerator'] / scores.denominator
        scores[prefix + '_raw'] = values
        mean, sd = values.mean(), values.std(ddof=1)
        scores[prefix + '_z_detailed'] = (values - mean) / sd
        reference.append(dict(measure=prefix, n=910, mean_raw=mean, sd_raw=sd, ddof=1))
    scores = scores.rename_axis('onet_soc_code').reset_index()
    scores.insert(1, 'title', scores.onet_soc_code.map(titles))
    save(scores, output, 'aioe_910')
    save(pd.DataFrame(reference), output, 'aioe_reference_statistics')
    example = '25-2031.00'
    save(wide.loc[wide['O*NET-SOC Code'].eq(example)], output, 'worked_example_52_abilities')
    save(scores.loc[scores.onet_soc_code.eq(example)], output, 'worked_example_scores')
    return scores


def audit_sample(raw, titles, identifiers, scores, output):
    retained = set(identifiers.onet_soc_code)
    excluded = scores.loc[~scores.onet_soc_code.isin(retained), ['onet_soc_code','title']].copy()
    assert len(excluded) == 32
    reasons = {code: [] for code in excluded.onet_soc_code}
    flags, date_rows, coverage_rows = [], [], []
    for domain, _, count, scales in SPECS:
        frame = raw[domain]
        expected = frame[['Element ID','Scale ID']].drop_duplicates()
        assert len(expected) == count * (2 if 'LV' in scales else 1)
        for code in excluded.onet_soc_code:
            rows = frame.loc[frame['O*NET-SOC Code'].eq(code)]
            if len(rows) != len(expected) or rows['Data Value'].isna().any():
                reasons[code].append(domain)
        used = frame.loc[frame['O*NET-SOC Code'].isin(retained)]
        assert len(used) == len(retained) * len(expected)
        assert used['Data Value'].notna().all()
        suppressed = used.get('Recommend Suppress', pd.Series('', index=used.index)).eq('Y')
        nr = used['Not Relevant'].eq('Y') & used['Scale ID'].eq('LV') if 'Not Relevant' in used else pd.Series(False,index=used.index)
        flagged = used.loc[suppressed].copy()
        flagged.insert(0,'domain',domain)
        flags.append(flagged)
        coverage_rows.append(dict(domain=domain, required_records_per_occupation=len(expected),
                                  retained_records=len(used), missing_values=int(used['Data Value'].isna().sum()),
                                  suppressed_records=int(suppressed.sum()),
                                  suppressed_occupations=used.loc[suppressed,'O*NET-SOC Code'].nunique(),
                                  not_relevant_lv_records=int(nr.sum())))
        for field in ['Date','Domain Source']:
            if field in used:
                for value, n in used[field].fillna('<missing>').value_counts().items():
                    date_rows.append(dict(domain=domain, field=field, value=value, records=int(n)))
    assert all(value == ['Work Styles'] for value in reasons.values())
    excluded['missing_domain'] = excluded.onet_soc_code.map(lambda code: '; '.join(reasons[code]))
    excluded['missing_wi_values'] = 21
    save(excluded, output, 'excluded_32_occupations')
    audit = scores[['onet_soc_code']].assign(excluded=lambda d: ~d.onet_soc_code.isin(retained))
    audit['soc_major_group'] = audit.onet_soc_code.str[:2]
    counts = audit.groupby('soc_major_group').agg(aioe_available=('onet_soc_code','size'),excluded=('excluded','sum')).reset_index()
    counts['retained'] = counts.aioe_available - counts.excluded
    counts['excluded_percent'] = 100 * counts.excluded / counts.aioe_available
    counts['major_group_name'] = counts.soc_major_group.map(SOC_NAMES)
    save(counts, output, 'exclusion_rates_by_soc')
    flags = pd.concat(flags, ignore_index=True)
    save(flags, output, 'recommend_suppress_records')
    clustering_flagged = flags.loc[flags.domain.ne('Abilities'),'O*NET-SOC Code'].nunique()
    all_flagged = flags['O*NET-SOC Code'].nunique()
    assert clustering_flagged == 649 and all_flagged == 652
    save(pd.DataFrame([dict(scope='Clustering features',flagged=clustering_flagged,remaining=878-clustering_flagged),
                       dict(scope='Including Abilities',flagged=all_flagged,remaining=878-all_flagged)]),
         output,'suppression_exclusion_counts')
    save(pd.DataFrame(coverage_rows), output,'domain_coverage_and_flags')
    save(pd.DataFrame(date_rows), output,'source_rating_dates_and_provenance')


def align(reference, candidate, k):
    """Align arbitrary labels by maximum membership overlap, without exposure data."""
    table = np.zeros((k,k),dtype=int)
    np.add.at(table, (reference,candidate), 1)
    rows, columns = linear_sum_assignment(-table)
    mapping = dict(zip(columns,rows))
    return np.array([mapping[label] for label in candidate])


def fit(y, k, seed):
    return KMeans(n_clusters=k, init='k-means++', n_init=10, max_iter=300,
                  tol=0.0001, algorithm='lloyd', random_state=seed).fit(y)


def clustering(identifiers, features, z, y, scores, output):
    # Archived membership fixes display IDs only; fitting does not use these labels.
    reference = pd.read_csv(ROOT / 'data/reference/k4_assignments.csv').set_index('onet_soc_code').loc[identifiers.onet_soc_code].cluster_id.to_numpy()
    metrics, assignments, all_runs, pairs = [], identifiers.copy(), {}, []
    for k in range(2,16):
        model = fit(y,k,42)
        labels = model.labels_
        if k == 4:
            labels = align(reference,labels,k)
            assert adjusted_rand_score(reference,labels) > 0.999999
        assignments[f'cluster_k{k}'] = labels
        sizes = np.bincount(labels)
        row = dict(k=k,inertia=model.inertia_,silhouette=silhouette_score(y,labels),
                   smallest_cluster=int(sizes.min()),largest_cluster=int(sizes.max()))
        if k <= 9:
            runs = {seed: align(labels,fit(y,k,seed).labels_,k) for seed in range(20)}
            values = []
            for a,b in combinations(range(20),2):
                value = adjusted_rand_score(runs[a],runs[b])
                values.append(value)
                pairs.append(dict(k=k,seed_a=a,seed_b=b,ari=value))
            row.update(mean_ARI=float(np.mean(values)),minimum_ARI=float(np.min(values)))
            all_runs[k] = runs
        metrics.append(row)
        print(f'Completed k={k}',flush=True)
    evaluation = pd.DataFrame(metrics)
    save(evaluation,output,'k_selection_k2_k15')
    save(pd.DataFrame(pairs),output,'pairwise_ari_k2_k9')
    save(assignments,output,'assignments_k2_k15')
    labels = assignments.cluster_k4.to_numpy()
    joined = identifiers.merge(scores.drop(columns='title'),on='onet_soc_code',validate='one_to_one')
    joined['cluster_id'] = labels
    joined['cluster_name'] = [NAMES[c] for c in labels]
    save(joined,output,'occupations_878_clusters_and_aioe')
    a = joined[MEASURES].to_numpy()
    centers, representatives = [], []
    for c in range(4):
        center = z[labels==c].mean(axis=0)
        rank = np.argsort(-center)
        for r,j in enumerate(rank,1):
            entry = features.iloc[j]
            centers.append(dict(cluster_id=c,cluster_name=NAMES[c],rank=r,feature=entry.feature,
                                domain=entry.domain,element_id=entry.element_id,element_name=entry.element_name,
                                centroid_z=center[j],centroid_weighted=y[labels==c,j].mean()))
        indices = np.flatnonzero(labels==c)
        distances = np.linalg.norm(y[indices]-y[indices].mean(axis=0),axis=1)
        for r,t in enumerate(np.argsort(distances)[:10],1):
            representatives.append(dict(cluster_id=c,cluster_name=NAMES[c],rank=r,
                                        onet_soc_code=identifiers.iloc[indices[t]].onet_soc_code,
                                        title=identifiers.iloc[indices[t]].title,weighted_distance=distances[t]))
    centers = pd.DataFrame(centers)
    save(centers,output,'centroids_all_187')
    save(centers.loc[centers['rank']<=6],output,'top6_features')
    save(pd.DataFrame(representatives),output,'nearest_10_occupations')
    save(pd.DataFrame(representatives).query('rank<=4'),output,'representative_occupations')
    communication = centers.loc[centers.element_id.isin(CORE_IDS)].pivot(index=['element_id','element_name'],columns='cluster_name',values='centroid_z').reset_index()
    communication['display_order'] = communication.element_id.map(dict(zip(CORE_IDS,range(14))))
    save(communication.sort_values('display_order'),output,'communication_features_14')
    run_labels, descriptions, tracking, contrasts = [], [], [], []
    for seed, lab in {42:labels, **all_runs[4]}.items():
        run_labels.append(identifiers.assign(seed=seed,cluster_id=lab))
        means = np.array([a[lab==c].mean(axis=0) for c in range(4)])
        ranks = pd.DataFrame(means).rank(ascending=False,method='min').to_numpy()
        for c in range(4):
            ix, ref = lab==c, labels==c
            center = z[ix].mean(axis=0)
            top = np.argsort(-center)[:10]
            tracking.append(dict(seed=seed,cluster_id=c,cluster_name=NAMES[c],n=int(ix.sum()),
                                 jaccard_vs_seed42=float((ix&ref).sum()/(ix|ref).sum()),
                                 centroid_correlation=float(np.corrcoef(center,z[ref].mean(axis=0))[0,1]),
                                 top10_features='; '.join(features.iloc[top].element_name)))
            for j,m in enumerate(MEASURES):
                values = a[ix,j]
                q1,median,q3 = np.quantile(values,[.25,.5,.75],method='linear')
                descriptions.append(dict(seed=seed,cluster_id=c,cluster_name=NAMES[c],n=int(ix.sum()),
                                         measure=m,mean=means[c,j],rank=int(ranks[c,j]),median=median,
                                         q1=q1,q3=q3,sd=values.std(ddof=1),minimum=values.min(),maximum=values.max()))
        for j,m in enumerate(MEASURES):
            contrasts.append(dict(seed=seed,measure=m,mean_difference=means[3,j]-means[0,j]))
    desc = pd.DataFrame(descriptions)
    save(desc,output,'initialization_aioe_descriptives')
    save(desc.query('seed==42'),output,'cluster_aioe_descriptives')
    save(pd.concat(run_labels,ignore_index=True),output,'initialization_assignments_k4')
    save(pd.DataFrame(tracking),output,'initialization_profile_tracking')
    contrast = pd.DataFrame(contrasts)
    save(contrast,output,'initialization_mean_differences')
    summary = contrast.query('seed!=42').groupby('measure').agg(minimum=('mean_difference','min'),maximum=('mean_difference','max'),positive_runs=('mean_difference',lambda v:int((v>0).sum()))).reset_index()
    assert (summary.positive_runs == 20).all()
    save(summary,output,'contrast_stability_summary')
    pca = PCA(n_components=2,svd_solver='full')
    points = pca.fit_transform(y)
    save(identifiers.assign(cluster_id=labels,PC1=points[:,0],PC2=points[:,1]),output,'pca_coordinates')
    save(pd.DataFrame({'component':['PC1','PC2'],'explained_variance_ratio':pca.explained_variance_ratio_}),output,'pca_variance')
    return evaluation


def verify_results(identifiers, feature_values, scores, metrics):
    archived = pd.read_csv(ROOT / 'data/reference/representative_features_187.csv')
    assert identifiers.onet_soc_code.tolist() == archived.onet_soc_code.tolist()
    feature_error = float(np.max(np.abs(feature_values.to_numpy()-archived.iloc[:,2:].to_numpy())))
    assert feature_error < 1e-12
    expected = pd.read_csv(ROOT / 'data/reference/aioe_910.csv').set_index('onet_soc_code')
    actual = scores.set_index('onet_soc_code').loc[expected.index,MEASURES]
    aioe_error = float(np.max(np.abs(actual.to_numpy()-expected[MEASURES].to_numpy())))
    assert aioe_error < 1e-10
    benchmark = pd.read_csv(ROOT / 'data/reference/k_selection.csv').set_index('k')
    for field in ['inertia','silhouette','mean_ARI','minimum_ARI']:
        want = benchmark.loc[metrics.k,field].to_numpy()
        got = metrics[field].to_numpy()
        assert np.allclose(want,got,rtol=1e-6,atol=1e-8,equal_nan=True), field
    return dict(raw_checksums_verified=True,n_occupations=878,n_features=187,aioe_reference_n=910,
                maximum_feature_error=feature_error,maximum_aioe_error=aioe_error,
                archived_k4_partition_reproduced=True,candidate_k_metrics_reproduced=True,
                numpy_version=np.__version__,pandas_version=pd.__version__,
                scipy_version=scipy.__version__,sklearn_version=sklearn.__version__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results',help='Destination for regenerated results.')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    verify_sources()
    titles,raw = load_sources()
    identifiers,features,feature_values,z,y = prepare_features(raw,titles,output)
    scores = calculate_exposure(raw,titles,output)
    audit_sample(raw,titles,identifiers,scores,output)
    with threadpool_limits(limits=1):
        metrics = clustering(identifiers,features,z,y,scores,output)
    report = verify_results(identifiers,feature_values,scores,metrics)
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Source audits, exposure calculations, and clustering reproduction passed.',flush=True)


if __name__ == '__main__':
    main()
