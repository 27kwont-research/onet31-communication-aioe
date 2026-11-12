# Data dictionary

All analysis CSVs use UTF-8, a header row, and comma separation. Codes and Element IDs should be read as strings. Rows represent occupations, features, cluster summaries, source records, or fits as specified below. Seeds identify reproducible random-number initializations, not different samples.

## Source files

`data/raw/onet31/*.csv.gz` preserve original O*NET columns and bytes after decompression. Consult the [O*NET 31.0 CSV dictionary](https://www.onetcenter.org/dictionary/31.0/csv/) for source-level definitions. The most relevant columns are `O*NET-SOC Code`, `Element ID`, `Element Name`, `Scale ID`, `Data Value`, `Recommend Suppress`, `Not Relevant`, `Date`, and `Domain Source`. Availability of flag columns varies by domain.

`data/raw/aioe/mturk_mapping_matrix.dta` is the original 10-by-52 numeric relationship matrix plus two application identifier columns. `source_manifest.json` provides the fixed source revision and integrity hashes.

## Main outputs in results/

| File | Unit and purpose |
|---|---|
| `representative_features_187.csv` | 878 occupations, two identifier columns, and 187 representative feature columns before standardization |
| `standardized_z_187.csv` | Same rows/columns, feature-standardized values before domain weighting |
| `domain_weighted_input_187.csv` | Same rows/columns, actual K-means inputs after domain weighting |
| `feature_identifiers_239.csv` | All 239 feature definitions, including excluded Abilities |
| `feature_identifiers_187.csv` | Input features, IDs, domains, scales, pre-z means/SDs, and domain multipliers |
| `domain_weights.csv` | Six domain sizes and applied multipliers |
| `aioe_910.csv` | Calculable occupations, titles, denominator, weighted numerators, raw and standardized exposure scores |
| `aioe_reference_statistics.csv` | Three measures' raw means, sample SDs, reference n = 910, and ddof = 1 |
| `ability_mapping_52.csv` | Original Ability ID, original name, and normalized matrix key |
| `application_ability_weights_52.csv` | Each Ability's general, language-modeling, and image-generation relationship weights |
| `occupations_878_clusters_and_aioe.csv` | Retained occupations, primary cluster membership, and exposure values |
| `k_selection_k2_k15.csv` | Seed-42 inertia, silhouette, size range, and repeated-initialization ARI where evaluated |
| `assignments_k2_k15.csv` | Every occupation's seed-42 label for each candidate k |
| `pairwise_ari_k2_k9.csv` | 190 pairs per k, with seeds and ARI |
| `centroids_all_187.csv` | Each cluster's full ranked feature profile on both z and weighted scales |
| `top6_features.csv` | Six highest pre-weight centroid values per cluster |
| `nearest_10_occupations.csv` | Ten nearest members per cluster using weighted distance |
| `representative_occupations.csv` | Four nearest members per cluster, official titles and codes |
| `communication_features_14.csv` | Common interpretive feature set across all four clusters |
| `cluster_aioe_descriptives.csv` | Reference solution's means, ranks, SDs, medians, quartiles, minima, maxima, and n |
| `initialization_assignments_k4.csv` | Aligned membership for seed 42 and seeds 0–19 |
| `initialization_aioe_descriptives.csv` | All cluster exposure summaries for those 21 solutions |
| `initialization_profile_tracking.csv` | Membership overlap, profile correlation, and top-ten features across solutions |
| `initialization_mean_differences.csv` | Focal mean difference by measure and seed |
| `contrast_stability_summary.csv` | Minimum/maximum difference and positive-run count across seeds 0–19 only |
| `excluded_32_occupations.csv` | Exact excluded codes/titles, missing domain, and number of missing WI values |
| `exclusion_rates_by_soc.csv` | Available, excluded, retained, and exclusion percentage by SOC major group |
| `domain_coverage_and_flags.csv` | Required record counts, missingness and flags for retained occupations by domain |
| `recommend_suppress_records.csv` | All used source rows flagged Y, including those whose LV is zeroed by Not Relevant |
| `suppression_exclusion_counts.csv` | Hypothetical counts after excluding any flagged occupation; no restricted-sample clustering is performed |
| `source_rating_dates_and_provenance.csv` | Frequency of source Date and Domain Source values by domain |
| `worked_example_52_abilities.csv` | All components for occupation 25-2031.00 |
| `worked_example_scores.csv` | That occupation's numerators, denominator, raw scores, and standardized scores |
| `pca_coordinates.csv` | Weighted-input PCA coordinates and cluster IDs |
| `pca_variance.csv` | Explained variance ratios for PC1 and PC2 |
| `verification.json` | Numerical reproduction checks and software versions |

## Important fields

- `onet_soc_code`: Detailed O*NET-SOC identifier, preserving the decimal suffix.
- `title`: Official occupation title from the supplied release.
- `feature`: `Domain__Element ID__Element Name`. The two underscores delimit the three parts. Identical names in different domains remain distinct features.
- `cluster_id`: Arbitrary display ID, 0–3 for the interpreted k = 4 solution. It is not an ordinal score.
- `cluster_name`: Exploratory descriptive label; the ID mapping is defined in `src/run_analysis.py`.
- `centroid_z`: Cluster mean on the feature-standardized scale before domain weighting, with the 878 occupations as the reference.
- `centroid_weighted`: Cluster mean in the actual fitted coordinate system.
- `weighted_distance`: Euclidean distance to the fitted centroid using all 187 weighted coordinates.
- `aioe_z_detailed`, `lm_aioe_z_detailed`, `ig_aioe_z_detailed`: General, language-modeling, and image-generation z-scores against 910 occupations.
- `rank` in exposure summaries: Descending rank of the mean within the same exposure measure and fitted partition. Rank 1 is the highest. In centroid or representative tables, `rank` instead means position in the explicitly described feature/distance ordering.
- `mean_difference`: Cluster 3 mean minus cluster 0 mean in the same exposure measure.
- `jaccard_vs_seed42`: Membership intersection divided by membership union with the reference cluster.
- `centroid_correlation`: Pearson correlation of the 187-dimensional pre-weight centroid profile with its seed-42 counterpart.
- `seed`: 42 for the reference; 0–19 for the repeated-initialization analysis.

Blank ARI fields at k = 10–15 mean that repeated-initialization ARI was not calculated at those k values. They are not missing occupational measurements.

## Archived references

`data/reference/` contains prior numerical results used only for comparison and consistent display labels. The feature and exposure outputs are reconstructed from raw data, not copied from these files. The reference assignments do not train K-means. All inputs needed to run and verify the analysis are included.
