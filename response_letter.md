# Response to Reviewers

**Manuscript:** "Limited Structural Reliability in Public Educational Prediction Benchmarks: A Four-Dimension Audit of Seven Datasets"
**Submission ID:** fbf130b1-76af-4698-aa61-7b55e8721359
**Authors:** Yan Ma, Lizhuo Zhang

---

## Reviewer 3 — Comments Refer to a Different Manuscript

We note that Reviewer 3's comments pertain to a manuscript on Moroccan secondary-school outcome prediction using CatBoost with SHAP/LIME explainability, which does not correspond to our submission.

---

## Reviewer 1

### Comment 1 — Threshold Justification
> The manuscript relies on several predefined thresholds... The authors should provide stronger theoretical or empirical justification...

**Response:** We agree that additional empirical justification strengthens the presentation. Our Supplementary Figure S3 (threshold-sensitivity analysis) already demonstrates that the main conclusions remain stable when each threshold is varied across a ±20% range. We have expanded the Methods section (Section 2.2) to cite this figure explicitly and discuss the rationale:

> "The threshold values are empirically motivated starting points rather than universal normative cutoffs. Supplementary Figure S3 shows that the main conclusions are robust to threshold variation within ±20% of each adopted value, indicating that the reported profiles are not artifacts of borderline cutoff choices."

### Comment 2 — Metadata Adequacy Assessment
> The decision process for metadata adequacy appears to rely primarily on linear-model group-holdout performance. The authors should better justify this choice...

**Response:** We have expanded the justification:

> "The linear model is used as the primary reference for the metadata-adequacy judgment because it is the least forgiving detector of group-sensitive leakage: an unregularized linear fit maximizes the contrast between within-group and cross-group signal. Regularized or ensemble models that recover under group holdout (e.g., ridge and ensemble models on Entrance Exam) indicate that the metadata-adequacy failure is partly remediable through modeling choices, but the audit protocol is designed to flag the structural risk inherent in the benchmark rather than to certify whether some model in the hyperparameter space can compensate for it. Using the best-performing model for the pass/fail judgment would create a perverse incentive: datasets with missing grouping metadata could be claimed as 'passing' simply by deploying a model complex enough to overfit group-specific noise."

### Comment 3 — Interpretation of Group-Holdout Results
> ...such degradation may also reflect distribution shift or out-of-distribution prediction challenges. The discussion should acknowledge these alternative explanations more explicitly.

**Response:** We have moved the diagnostic discussion from Section 5 (Discussion) to Section 4.1 (Results) where group-holdout numbers are first reported, and expanded it:

> "Group-holdout R² collapse does not uniquely diagnose confounding; it may also reflect legitimate distributional shift when held-out groups differ systematically from the training groups. To distinguish these cases, we recommend the following diagnostic sequence (see also Section 5). When all model types collapse (as with UCI Student and Higher Ed), comparing group-level feature distributions can reveal whether large distributional gaps point toward cross-context heterogeneity rather than leakage. When only unregularized linear models collapse while ridge or ensemble models recover (as with Entrance Exam), overfitting on high-dimensional features is the more parsimonious explanation."

### Comment 4 — Regression-Based Formulation
> ...the manuscript would benefit from a stronger theoretical justification for this choice...

**Response:** Added in Section 2.4:

> "Evaluating all seven datasets under a common regression framing ensures cross-dataset comparability of the audit metrics (MAE, R², Pearson r). For binary and ordinal datasets, we map targets to equally spaced integers and verify in a dedicated sensitivity analysis (Section 4.4, Table 4) that the audit profiles are robust to classification-appropriate metrics. We acknowledge that integer mapping imposes an equal-interval assumption on ordinal scales; this is a pragmatic choice for cross-task comparability rather than a psychometric claim."

### Comment 5 — Uncertainty Quantification
> Confidence intervals or comparable uncertainty measures are not consistently reported.

**Response:** We have added a new supplementary analysis reporting across-group standard deviations for all group-holdout R² estimates (Supplementary Table S4). The main text now reports:

> "For UCI Student, the linear-model group-holdout $R^2$ carries a standard deviation of 0.154 across its 2 eligible schools (range: $-0.206$ to $0.012$), confirming uniform rather than group-specific collapse. For OULAD, the across-cohort SD is 0.166 across 22 cohorts (range: $0.041$ to $0.654$), consistent with positive---though variable---cross-group generalization. For Higher Ed (4 eligible courses), the large SD of 7.37 (range: $-18.65$ to $-0.975$) reflects the high heterogeneity of collapse severity across courses."

This analysis was implemented in a dedicated supplementary script (`scripts/supplementary_revision_analyses.py`) that reads per-group statistics directly from the main pipeline output.

### Comment 6 — Limited Dataset Coverage
> The authors should further moderate claims regarding the general characteristics of educational prediction benchmarks...

**Response:** We have revised all broad generalizations throughout the manuscript. Specifically:
- "educational prediction benchmarks" → "the seven audited benchmarks" where only our datasets are discussed
- Added explicit caveat: "As an exploratory analysis of seven datasets, these findings should not be over-generalized to the full population of educational prediction benchmarks"
- Cross-dataset structural pattern analysis (Section 4.3) explicitly labeled as "exploratory"

### Comment 7 — Theoretical Foundation of the Audit Framework
> ...discussing why other potentially relevant dimensions, such as fairness, robustness, explainability, missing data quality, or representativeness, were not included.

**Response:** Added in Limitations (Section 5):

> "The four dimensions selected for this audit target pre-modeling statistical reliability rather than post-modeling properties such as fairness, algorithmic robustness, or explainability. These omitted dimensions are complementary rather than competing: Model Cards (Mitchell et al., 2019) and Datasheets for Datasets (Gebru et al., 2021) provide frameworks for documenting representativeness and intended use, while fairness and explainability audits operate at the model level rather than the dataset level. We regard the four-dimension audit as a minimal necessary check before stronger modeling claims are made, not as a comprehensive quality certification."

### Comment 8 — Language and Interpretation
> Some statements imply causal relationships...

**Response:** We have revised the manuscript throughout to adopt cautious language. Key substitutions:
- "causes" → "is associated with"
- "demonstrates" → "indicates" / "is consistent with"
- "structural fragility" → introduced only after presenting train-test gap evidence (new Analysis 2) that distinguishes overfitting from cross-group collapse

A complete list of language revisions is available on request.

---

## Reviewer 2

### Comment 1 — EDA-Driven Data Adequacy Assessment
> ...the authors should show whether the observed fragility persists after appropriate EDA-informed checks...

**Response:** We have added a systematic EDA summary for all seven datasets as Supplementary Table S2, covering: sample size, feature dimensionality, class/target distribution, missing values (none in any of the seven releases), group size distribution, and pairwise feature correlation summaries. The key observation is that the datasets that fail the audit do not show distinctive EDA red flags (e.g., extreme imbalance or redundant features) that would pre-emptively disqualify them—the fragility is only revealed through the four-dimension audit.

### Comment 2 — Overfitting vs. Structural Fragility
> ...the authors should more explicitly separate overfitting effects from structural benchmark fragility.

**Response:** We have added a dedicated train-test R² gap analysis (Supplementary Table S3, new Section 4.1). The results show that on UCI Student, the linear model's mean train-test gap is 0.138 (train R² = 0.353, test R² = 0.214), compared to an iid-to-group-holdout collapse of 0.262 to −0.097. On OULAD, both the train-test gap (0.014) and the iid-to-group gap (0.061) remain small. On Higher Ed, the train-test gap is larger (0.507) and the group-holdout collapse is catastrophic (−8.79), indicating that overfitting and cross-group fragility are jointly present. This contrast confirms that the group-holdout failures are not attributable to ordinary overfitting alone—models generalize adequately to iid held-out samples but fail specifically on unseen institutional groups.

### Comment 3 — Data Leakage Risks
> The authors should explicitly report how such risks were checked and controlled for each dataset...

**Response:** We thank the reviewer for this important observation. Following this suggestion, we identified that group-identifier columns in three datasets (UCI Student, xAPI-Edu, Entrance Exam) caused zero-variance predictors in the training partition under leave-one-group-out holdout, producing inflated group-holdout R² estimates. After correcting this, xAPI-Edu's linear group-holdout R² updated from −2.03 to +0.484 (reclassified from Mostly Passing to Strong) and UCI Student and Entrance Exam were corrected from −25.36 and −3.32 to −0.097 and −0.060 respectively. An additional leakage-prevention measure was applied during the revision process: for datasets in which group membership was encoded as one-hot features in the original feature matrix (UCI Student, xAPI-Edu, Entrance Exam), group-identifier columns were excluded from the feature matrix prior to leave-one-group-out training to avoid zero-variance predictors in the training partition. This correction primarily affected xAPI-Edu, whose apparent linear-model collapse (previously reported as group-holdout R² = −2.03) was entirely attributable to zero-variance topic indicators in the training partition. After correction, xAPI-Edu achieves linear group-holdout R² = 0.484, passes the metadata-adequacy threshold, and is reclassified from Mostly Passing (3/4) to Strong (4/4). This reclassification is itself informative: it demonstrates that the audit framework can distinguish genuine cross-group fragility from numerical artifacts introduced by group-collinear feature encoding. The group-column fix and its consequences are documented in Section 2.4 (Methods) and reflected across all revised tables, figures, and the Discussion.

> "The following leakage-prevention measures were applied uniformly: (i) all standardization (Z-score) parameters were fitted exclusively on the training partition of each split and applied to the corresponding test partition; (ii) one-hot encoding was fitted on the full dataset but applies only to categorical variables with fixed levels, introducing no lookahead from the test set; (iii) for each dataset, we verified the absence of duplicate or near-duplicate rows (none found); (iv) the UCI Student adapter excludes G1 and G2 (intermediate-term assessments that post-date G3) to prevent target-proxy leakage; (v) for OULAD, assessment scores are treated as features but we confirm that all rows in a given split are temporally coherent within the same course-presentation cohort."

### Comment 4 — Explanation-Level Consistency
> A supporting explainability analysis... would help determine whether the observed predictive signal is explanation-consistent.

**Response:** We have added a feature-attribution stability analysis (Supplementary Tables S5–S6, new Section 4.5). For UCI Student, Higher Ed, and OULAD, we track linear-model standardized coefficients and Random Forest feature importances across 100 repeated splits. On OULAD, the top-10 features show zero sign flips with SD ≤ 0.008, indicating consistent directional relationships. On UCI Student, one of the top-10 features (f23) shows a 1% sign-flip rate with larger SD (up to 0.114), and RF importance CVs range from 0.08 to 0.21, reflecting greater uncertainty about feature rankings. On Higher Ed, the pattern is most pronounced: coefficient SDs reach 0.126 (f28, f0), and RF importance CVs range from 0.18 to 0.36.

### Comment 5 — Reporting Consistency
> The baseline-gap criterion is defined using ΔMAE and beat rate, whereas some visualizations present baseline-related evidence using R²...

**Response:** We have aligned all figure captions, table headers, and threshold references with the operational definitions in Table 1 (now Table 5 after renumbering). Specifically:
- Figure 2 caption now explicitly states: "Beat rate uses ΔMAE; the normalized score shown is 1−I/(1+I) for the linear model"
- All supplementary references checked for consistency with Methods

### Comment 6 — Tone
> Terms such as "structural fragility" and "algorithm-invariant failure" may be too strong...

**Response:** Revised throughout. Key changes:
- "algorithm-invariant failure" → "persistent across model families" (for UCI Student, Higher Ed)
- "structural fragility" → used only after the new train-test gap analysis (Comment 2 above) provides evidence distinguishing it from ordinary overfitting
- "fragile" is retained as a categorical profile label (defined in Section 2.1) but contextualized with the specific failure dimensions

### Comment 7 — Discussion of Prior Work
> ...the Discussion does not sufficiently compare the present findings with prior empirical results...

**Response:** We have added a new paragraph in Section 5 (Discussion) explicitly situating our findings:

> "The present findings extend prior work on benchmark reliability in several directions. Bouthillier et al. (2021) demonstrated that random-seed variation can inflate apparent method differences in image classification; our audit operationalizes this concern for educational prediction through the instability ratio I, showing that the same phenomenon carries more severe consequences in smaller, more nested educational benchmarks. Northcutt et al. (2021) showed that label errors degrade benchmark validity in vision datasets; we find that in educational prediction, group-level confounding and missing provenance metadata impose constraints comparable to or exceeding those of label quality. The results are also consistent with the broader data documentation literature (Gebru et al., 2021; Sambasivan et al., 2021), which identifies upstream quality failures—here, the absence of grouping metadata—as downstream benchmark threats. The contribution of the present study lies not in identifying these concerns for the first time, but in integrating them into a unified four-dimension pre-modeling audit protocol tailored to educational prediction datasets and demonstrating, across seven public releases, that their combined effect is to render most of these benchmarks structurally unreliable for strong benchmark claims."

---

We thank both reviewers for their constructive feedback, which substantially improved the manuscript.

---

## Revision Summary

| Change | Location |
|--------|----------|
| Reviewer 3 note | Cover letter |
| Threshold justification expanded | Section 2.2 + cite Fig S3 |
| Metadata adequacy rationale | Section 2.4 |
| Distribution shift caveat | Section 4.1 |
| Regression framing justification | Section 2.4 |
| Group-column zero-variance fix (new) | Section 2.4, all tables/figures |
| Group-holdout uncertainty (new analysis) | Supp. Table S4, Section 4.1 |
| Dataset coverage caveats | Throughout |
| Four-dimension boundary discussion | Limitations |
| Language softening | Throughout |
| EDA summary (new analysis) | Supp. Table S2 |
| Train-test gap (new analysis) | Supp. Table S3, Section 4.1 |
| Data leakage controls | Section 2.4 |
| Feature-attribution stability (new analysis) | Supp. Tables S5–S6, Section 4.5 |
| Reporting consistency | All figures/tables |
| Prior work comparison | Section 5 |
