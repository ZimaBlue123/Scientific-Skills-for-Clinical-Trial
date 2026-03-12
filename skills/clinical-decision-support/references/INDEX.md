# Clinical Decision Support — References Index

本文件是 `clinical-decision-support` 这个 skill 的参考资料索引。使用方式与入口说明请先看上一级目录的 `../SKILL.md`。

## Quick Start

This skill enables generation of three types of clinical documents:

1. **Individual Patient Treatment Plans** - Personalized protocols for specific patients
2. **Patient Cohort Analysis** - Biomarker-stratified group analyses with outcomes
3. **Treatment Recommendation Reports** - Evidence-based clinical guidelines

All documents are generated as compact, professional LaTeX/PDF files.

## References Included

- `patient_cohort_analysis.md`
- `treatment_recommendations.md`
- `clinical_decision_algorithms.md`
- `biomarker_classification.md`
- `outcome_analysis.md`
- `evidence_synthesis.md`

对应主题：

1. **Patient Cohort Analysis**：Stratification methods, biomarker correlations, statistical comparisons
2. **Treatment Recommendations**：Evidence grading, treatment sequencing, special populations
3. **Clinical Decision Algorithms**：Risk scores, decision trees, TikZ flowcharts
4. **Biomarker Classification**：Genomic alterations, molecular subtypes, companion diagnostics
5. **Outcome Analysis**：Survival methods, response criteria (RECIST), effect sizes
6. **Evidence Synthesis**：Guideline integration, systematic reviews, meta-analysis

## Example Use Cases

### Create a Patient Cohort Analysis
```
> Analyze a cohort of 45 NSCLC patients stratified by PD-L1 expression 
  (<1%, 1-49%, ≥50%) including ORR, PFS, and OS outcomes
```

### Generate Treatment Recommendations
```
> Create evidence-based treatment recommendations for HER2-positive 
  metastatic breast cancer with GRADE methodology
```

### Build Clinical Pathway
```
> Generate a clinical decision algorithm for acute chest pain 
  management with TIMI risk score
```

## Key Features

- **GRADE Methodology**: Evidence quality grading (High/Moderate/Low/Very Low)
- **Recommendation Strength**: Strong (Grade 1) vs Conditional (Grade 2)
- **Biomarker Integration**: Genomic, expression, and molecular subtype classification
- **Statistical Analysis**: Kaplan-Meier, Cox regression, log-rank tests
- **Guideline Concordance**: NCCN, ASCO, ESMO, AHA/ACC integration
- **Professional Output**: 0.5in margins, color-coded boxes, publication-ready

## Dependencies（运行脚本时）

Python scripts may require:
- `pandas`, `numpy`, `scipy`: Data analysis and statistics
- `lifelines`: Survival analysis (Kaplan-Meier, Cox regression)
- `matplotlib`: Visualization
- `pyyaml` (optional): YAML input for decision trees

Install with:
```bash
pip install pandas numpy scipy lifelines matplotlib pyyaml
```

## Templates Provided

1. **Cohort Analysis**: Demographics table, biomarker profile, outcomes, statistics, recommendations
2. **Treatment Recommendations**: Evidence review, GRADE-graded options, monitoring, decision algorithm
3. **Clinical Pathway**: TikZ flowchart with risk stratification and urgency-coded actions
4. **Biomarker Report**: Genomic profiling with tier-based actionability and therapy matching

## Scripts Included

1. **`generate_survival_analysis.py`**: Create Kaplan-Meier curves with hazard ratios
2. **`create_cohort_tables.py`**: Generate baseline, efficacy, and safety tables
3. **`build_decision_tree.py`**: Convert text/JSON to TikZ flowcharts
4. **`biomarker_classifier.py`**: Stratify patients by PD-L1, HER2, molecular subtypes
5. **`validate_cds_document.py`**: Quality checks for completeness and compliance

## Integration

Integrates with existing skills:
- **scientific-writing**: Citation management, statistical reporting
- **clinical-reports**: Medical terminology, HIPAA compliance
- **scientific-schematics**: TikZ flowcharts

## Version

Version 1.0 - Initial release
Created: November 2024
Last Updated: November 5, 2024

## Questions or Feedback

This skill was designed for pharmaceutical and clinical research professionals creating clinical decision support documents. For questions about usage or suggestions for improvements, contact the Scientific Writer development team.

