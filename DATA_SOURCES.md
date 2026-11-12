# Data sources and attribution

## O*NET 31.0

Original source: [O*NET 31.0 database](https://www.onetcenter.org/database.html), August 2026 release, U.S. Department of Labor, Employment and Training Administration (USDOL/ETA). Archived releases: https://www.onetcenter.org/db_releases.html.

This package includes information from the O*NET® 31.0 Database under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/). O*NET® is a trademark of USDOL/ETA. The study modifies the data through feature selection, normalization, aggregation, exposure recalculation, and clustering. USDOL/ETA has not approved, endorsed, or tested these modifications. The raw CSV bytes are unchanged after decompression. See the [database content license](https://www.onetcenter.org/license_db.html).

Exact included files: `occupation_data.csv`, `abilities.csv`, `essential_skills.csv`, `transferable_skills.csv`, `knowledge.csv`, `work_activities.csv`, `work_context.csv`, and `work_styles.csv`. Required variables and transformations are documented in `docs/METHODS.md`. Original file hashes are in `data/source_manifest.json`.

## AIOE application–Ability relationships

Original repository: https://github.com/AIOE-Data/AIOE

Original file: `Input/mturk_mapping_matrix.dta`

Pinned revision: `31c584b06d4c21c5ebd219e419ce3dec68fce6ec`

Download: https://raw.githubusercontent.com/AIOE-Data/AIOE/31c584b06d4c21c5ebd219e419ce3dec68fce6ec/Input/mturk_mapping_matrix.dta

The pinned matrix was downloaded and compared with the archived full-precision long-form matrix used by the study. Numeric values agreed to an absolute tolerance of 1e-15. The source file is included unchanged, and its SHA-256 is recorded in `data/source_manifest.json`.

The AIOE repository requests the following citation:

Felten E, Raj M, Seamans R. Occupational, industry, and geographic exposure to artificial intelligence: A novel dataset and its potential uses. Strategic Management Journal. 2021;42(12):2195–2217. https://doi.org/10.1002/smj.3286

The application-specific calculations use the original `language modeling` and `generating images` rows. They retain the historical relationship weights; only occupational Ability ratings are updated. This package does not claim to create a newly measured application–Ability matrix.

AIOE materials retain their original attribution and source terms. No new license over those third-party materials is granted by this package. The O*NET content license is not presented as a license for the AIOE matrix.

## Analysis code and derived files

The source code implements this study's transformations and analyses. No separate software license has been selected. Source-specific attribution remains applicable to the data and derived files. The manuscript and author contact details are not included in this reproducibility package.

Official source pages and the pinned AIOE file were checked on 2026-11-10. This date records package preparation, not the original study's data-access date.
