# Occupational Profiles and AI Exposure Using O*NET 31.0

This repository contains the data, analysis code, and reproducibility materials for the manuscript **“AI Occupational Exposure in Communication-Intensive Occupations: A K-Means Cluster Analysis Using O*NET 31.0.”**

The analysis uses 878 occupations and 187 occupational features. It excludes the 52 Abilities from clustering, balances the total contributions of six feature domains, and analyzes a four-cluster solution. General, language-modeling, and image-generation exposure scores are recalculated using O*NET 31.0 Ability ratings and the existing AIOE application–Ability relationship weights.

This package contains the domain-balanced analysis. The feature-standardized matrix is retained as an intermediate and as the scale for interpreting cluster profiles, not as a separate supplementary clustering analysis. Candidate values k = 2–15 are evaluated, but k = 4 is the substantive analysis.

## Quick start

Tested with Python 3.13.15 and the versions pinned in `requirements.txt`. The input files are included, so the analysis itself does not need a network connection.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/run_analysis.py --output results_reproduced
python src/make_figures.py --results results_reproduced
```

On Windows, activate the environment with `.venv\Scripts\activate` instead. Use `python` in place of `python3` if required by your installation.

`results/` contains the checked outputs supplied with this package. The commands above write to a separate directory. To regenerate the supplied output directory directly, omit the `--output` and `--results` arguments. The scripts locate inputs relative to their own location rather than the current working directory.

The analysis verifies source checksums, reconstructs features and AIOE from raw files, refits the candidate cluster solutions and repeated initializations, and checks the results against archived numerical references. It stops with an error if those checks fail. `verification.json` records the outcome and software versions. Small platform-dependent floating-point differences are allowed; arbitrary cluster IDs are aligned by occupational membership rather than exposure scores.

## Repository structure

```text
README.md
requirements.txt
DATA_SOURCES.md
src/
  run_analysis.py       Raw-data processing, exposure calculation, audits, clustering
  make_figures.py       English-language figures at 300 dpi
  verify_package.py    Package integrity checks
  build_manifest.py    Rebuild the file manifest after a deliberate update
docs/
  METHODS.md           Formulas, processing rules, and interpretation
  DATA_DICTIONARY.md   Output files and field definitions
  WORKED_EXAMPLE.md    One occupation's calculation using all 52 Abilities
data/
  raw/onet31/          Eight original CSV files, losslessly gzip-compressed
  raw/aioe/            Original application–Ability matrix in Stata format
  source_manifest.json Source hashes and pinned AIOE source URL
  reference/           Archived benchmarks for checking reproduction
results/               Regenerated CSV files and verification report
  figures/             Six PNG figures
```

## Analysis choices

- **Sample:** 910 occupations have calculable AIOE. Thirty-two lack all 21 Work Styles WI ratings. The complete-case clustering sample is 878 occupations.
- **Inputs:** Essential Skills (10), Transferable Skills (25), Knowledge (33), Work Activities (41), Work Context (57), and Work Styles (21).
- **Feature scores:** The four clustering domains with IM/LV pairs use `((IM - 1) / 4) * (LV / 7)`. Work Context uses CX or CT summary values. Work Styles uses WI.
- **Missingness and flags:** LV marked Not Relevant = Y is set to zero. Actual missing values are not imputed. Supplied values marked Recommend Suppress = Y are retained. Excluding every flagged occupation would leave 229 of the 878 clustering occupations.
- **Scaling:** Features are standardized across the 878 occupations using population standard deviations (`ddof=0`). Each standardized feature in domain d is then multiplied by `sqrt(187 / (6 * p_d))`, where `p_d` is the number of features in that domain. No further standardization follows.
- **K-means:** `init='k-means++'`, `n_init=10`, `max_iter=300`, `tol=0.0001`, `algorithm='lloyd'`, `random_state=42`. The explicitly chosen `n_init=10` should not be described as the library default.
- **Diagnostics:** Inertia and silhouette for k = 2–15. For k = 2–9, seeds 0–19 yield 20 fitted partitions and 190 pairwise ARIs per k. Each fit uses `n_init=10`.
- **Exposure:** Ability weights use `(IM / 5) * (LV / 7)`, which differs from the feature Intensity formula. Each of the three exposure measures is standardized separately against all 910 occupations using `ddof=1`.
- **Interpretation:** Cluster names are exploratory descriptions of centroid profiles and representative occupations. The 14 communication-related features are a common interpretive set, not a validated scale or a threshold classifier. AIOE is not used to fit or align clusters.

See [Methods](docs/METHODS.md) for exact formulas and [Data dictionary](docs/DATA_DICTIONARY.md) for output definitions.

## Main numerical checks

| Cluster | Occupations | General AIOE | Language modeling AIOE | Image generation AIOE |
|---|---:|---:|---:|---:|
| Public-facing Service and Support | 215 | 0.008 | 0.087 | -0.248 |
| STEM and Computing | 152 | 0.820 | 0.653 | 1.129 |
| Physical and Technical Work | 269 | -1.135 | -1.176 | -0.856 |
| Interpersonal Support and Coordination | 242 | 0.687 | 0.781 | 0.386 |

The k = 4 mean silhouette score is approximately 0.151679. Across the 20 alternative initializations, the mean pairwise ARI is 0.952770 and the minimum is 0.868029. The mean exposure of Interpersonal Support and Coordination exceeds that of Public-facing Service and Support in all 20 runs for each exposure measure. The differences range from 0.594–0.695 for general AIOE, 0.608–0.706 for language modeling, and 0.558–0.667 for image generation. These are initialization ranges, not confidence intervals.

k = 4 was selected by considering stability, separation, and interpretability together. It does not maximize every diagnostic. Individual occupational exposure distributions overlap.

## Sources and reuse

Source attribution, the pinned AIOE matrix revision, and source-specific terms are documented in [DATA_SOURCES.md](DATA_SOURCES.md). Original data attribution is retained. Derived files change the representation of the source data through selection, aggregation, normalization, and clustering. No endorsement by the original data providers is implied.

The package uses public occupational-level secondary data and contains no directly recruited participants. The exposure calculations update occupational Ability ratings while retaining historical application–Ability weights. They do not directly measure AI adoption, displacement, productivity, or the benefits of human–AI collaboration.

Source data retain their respective terms. A separate software license for the analysis code has not been selected.
