# Computational methods

## Sample and original records

Eight CSV files from the August 2026 O*NET 31.0 release are included as losslessly compressed files. The original bytes can be recovered with gzip. `data/source_manifest.json` lists both compressed and original SHA-256 hashes.

`occupation_data.csv` supplies official occupational titles. The seven rating files supply the following distinct features:

| Domain | Features | Scales selected | Used for clustering |
|---|---:|---|---|
| Abilities | 52 | IM, LV | No |
| Essential Skills | 10 | IM, LV | Yes |
| Transferable Skills | 25 | IM, LV | Yes |
| Knowledge | 33 | IM, LV | Yes |
| Work Activities | 41 | IM, LV | Yes |
| Work Context | 57 | CX or CT | Yes |
| Work Styles | 21 | WI | Yes |

IM is Importance (1–5), LV is Level (0–7), CX and CT are Work Context summary scales (1–5 and 1–3, respectively), and WI is Work Styles Impact (-3–3). CXP and CTP response distributions are not used as separate clustering inputs.

All 910 occupations with Ability ratings have 52 IM/LV pairs. Thirty-two lack all 21 WI values. Their other required rating domains are available. Complete cases across the seven domains yield 878 occupations. Missing numeric values are not imputed.

LV records marked `Not Relevant = Y` are set to zero before both feature and AIOE calculations. IM remains unchanged. Values marked `Recommend Suppress = Y` are retained. The flag does not become a missing value or an exclusion rule. Of the retained occupations, 649 have at least one flagged record among the clustering features; 652 have at least one when Abilities are included. A domain that does not supply a Recommend Suppress column has no such flag to apply. A flagged value can also have Not Relevant = Y; the LV zeroing rule still applies.

Exclusion rates use the number of AIOE-calculable occupations in each SOC major group as their denominator. Occupations, not workers, are counted. Source Date and Domain Source distributions are exported because one release does not imply one collection date.

## Feature construction and distance weights

For paired IM/LV clustering features, the representative value is

```text
Intensity_ij = ((IM_ij - 1) / 4) * (LV_ij / 7)
```

Here i is an occupation and j is a feature. CX, CT, and WI values are used directly. The original intermediate feature CSV was serialized to ten significant digits. The reconstruction deliberately repeats this step before standardization to reproduce that numerical input.

Each retained feature is then standardized across the 878 occupations:

```text
z_ij = (Intensity_ij - mean_j) / population_sd_j
```

The analogous operation applies to the raw CX/CT/WI values. `StandardScaler` uses `ddof=0`. Feature names, scaling constants, domain membership, and Element IDs are exported.

With p_d features in domain d, the fitted coordinate is

```text
y_ij = z_ij * sqrt(187 / (6 * p_d))
```

This equalizes the average total squared-distance contribution of the six domains. It does not equalize contributions for every occupation pair or remove within-domain correlations. The weighted matrix is not standardized again. The 52 Ability features are excluded from clustering, but other domains can remain conceptually and statistically related to Abilities.

## Clustering and interpretation

All fits use the weighted y matrix and the explicit settings in the README. Candidate k = 2–15 solutions use seed 42. At k = 2–9, seeds 0–19 are additionally fitted, each with ten starts. The 190 unordered pairs of these 20 partitions are compared by ARI. Seed 42 is not included in these 190 pairs.

The k = 4 reference fit is independently estimated. Archived k = 4 membership is used only to keep arbitrary display IDs consistent, using maximum-overlap one-to-one matching. Every alternative k = 4 run is then matched to the independently refitted reference by the same rule. AIOE values do not enter these matches. The matching algorithm is linear sum assignment on the negative membership-overlap matrix.

Displayed centroids are the mean pre-domain-weight z values, so individual features have comparable interpretation in standard-deviation units. All 187 are exported. The six largest centroid values are reported for each cluster. Representative occupations are the four nearest members to the centroid in the actual weighted y space. Exact titles and O*NET-SOC codes are retained.

Cluster labels describe the centroid profiles and representative occupations. The common 14-feature communication display is interpretive rather than a validated composite score. Other clusters may also involve communication. Naming and substantive selection are not automated by an AIOE threshold.

For initialization checks, the outputs include all assignments, top-ten centroid features, centroid-profile correlation, Jaccard membership overlap, cluster means and ranks, and differences between the two focal profiles. Correlations and overlaps describe correspondence; they do not prove identical semantic categories across runs.

PCA is fitted to y with the full SVD solver for a deterministic two-dimensional display. Clustering and separation metrics are computed in the original 187-dimensional space.

## Application–Ability weights and AIOE

The exact source is `Input/mturk_mapping_matrix.dta` from the AIOE repository. The pinned source URL and commit are recorded in `data/source_manifest.json` and `DATA_SOURCES.md`.

The matrix has 10 application rows and 52 Ability columns. `application_id` and `applications` are metadata columns, not weights. For each Ability a:

- General exposure uses the sum across the 10 application rows.
- Language modeling uses the row where `applications == 'language modeling'`.
- Image generation uses the row where `applications == 'generating images'`.

Full numeric precision from the Stata matrix is used. O*NET Element Names are lowercased, with spaces and hyphens removed, to match the Ability column names. Element IDs and original names are retained in the mapping table. The script checks 52 unique one-to-one matches and identical key sets.

The occupational Ability weight differs from the clustering Intensity formula:

```text
w_oa = (IM_oa / 5) * (LV_oa / 7)
raw_exposure_ot = sum_a(w_oa * relationship_ta) / sum_a(w_oa)
```

Here o is an occupation, a is one of the 52 Abilities, and t is the chosen application or application set. The denominator is checked to be positive. For general AIOE, `relationship_ta` is the sum over all ten applications.

Each exposure measure is standardized separately over all 910 calculable occupations:

```text
AIOE_ot = (raw_exposure_ot - reference_mean_t) / reference_sample_sd_t
```

The reference sample standard deviation uses `ddof=1`. These 910 reference occupations include the 32 excluded from clustering. All clusters are therefore compared on the same reference scale. Feature z-scores use 878 occupations and `ddof=0`; these are different standardizations.

The recalculation updates occupational Ability ratings, not the historical relationship matrix. The scores do not distinguish substitution from complementarity.

## Summaries and distributions

Each occupation receives equal weight in a cluster mean. Employment counts are not used. Q1, median, and Q3 use linear interpolation. Boxplot whiskers extend to the most extreme observations within 1.5 times the interquartile range. All observations, including points outside the whiskers, remain in descriptive calculations.

The focal difference is the mean for Interpersonal Support and Coordination minus the mean for Public-facing Service and Support. Its range across seeds is initialization variability rather than a confidence interval. No significance tests are performed.

## Reproduction checks

The pipeline checks source hashes, feature counts, uniqueness of source keys, complete-case sample size, Ability matching, exclusions and suppression counts, domain variance contributions, and exposure standardization. It then compares reconstructed features, exposure scores, the refitted k = 4 partition, and all candidate-k metrics against archived references. Verification failure stops the run.
