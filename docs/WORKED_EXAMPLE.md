# Worked calculation for one occupation

Occupation: **Secondary School Teachers, Except Special and Career/Technical Education** (`25-2031.00`).

This example uses all 52 Abilities. The accompanying `results/worked_example_52_abilities.csv` lists the original IDs and names, IM, effective LV after the Not Relevant rule, the three application weights, occupational Ability weights, and numerator contributions. The application weights are unchanged from the source matrix.

For each Ability, `w = (IM / 5) * (LV / 7)`. The common denominator is the sum of these 52 weights. The clustering Intensity formula is not used here.

Common denominator: **8.921291428571**.

| Measure | Weighted numerator | Raw exposure | Reference mean | Reference sample SD | Final z-score |
|---|---:|---:|---:|---:|---:|
| General | 58.944026292069 | 6.607118124546 | 6.090005328958 | 0.452611639430 | 1.142508832162 |
| Language modeling | 6.209899042633 | 0.696076245502 | 0.595670253703 | 0.085291501491 | 1.177209804549 |
| Image generation | 5.195813597070 | 0.582405993423 | 0.558644921937 | 0.026063415807 | 0.911663753585 |

Each raw exposure equals its weighted numerator divided by the common denominator. Each z-score then equals `(raw exposure - reference mean) / reference sample SD`. The reference is all 910 calculable occupations, with `ddof=1`. Displayed numbers are rounded; the pipeline uses full numerical precision.

## Illustrative Ability rows

The following rows illustrate the components. The totals above use all 52 rows, not just this excerpt.

| Ability | IM | Effective LV | Occupational weight | General relationship weight | General numerator contribution |
|---|---:|---:|---:|---:|---:|
| Oral Comprehension | 4.00 | 4.00 | 0.457142857143 | 6.661454009092 | 3.045236118442 |
| Written Comprehension | 4.00 | 4.00 | 0.457142857143 | 6.422261332089 | 2.935890894669 |
| Oral Expression | 4.12 | 4.88 | 0.574445714286 | 6.356647097907 | 3.651548682619 |
| Written Expression | 4.00 | 4.00 | 0.457142857143 | 6.238470030497 | 2.851872013941 |
| Fluency of Ideas | 3.50 | 3.25 | 0.325000000000 | 6.138950253182 | 1.995158832284 |

To check the example independently, sum each numerator-contribution column and the occupational-weight column in the 52-row CSV. Divide, then standardize using `results/aioe_reference_statistics.csv`.
