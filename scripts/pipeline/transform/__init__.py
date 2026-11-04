"""Transform stage: embeddings, RAG, statistical recomputation and data reshaping."""

from .clinical_rag import ClinicalDocumentIndex
from .immunogenicity_stats import (
    GeoMeanResult,
    GroupComparison,
    ProportionResult,
    compare_log_means,
    compare_proportions,
    fmt_ci,
    fmt_p,
    fmt_rate,
    geomean,
    power_gmc_ni,
    power_rate_ni_fm,
    proportion,
    rate_difference_ci,
    sample_size_gmc_ni,
    sample_size_rate_ni_fm,
    sample_size_rate_ni_wald,
)
from .quantile_definitions import quantile, quartiles, scan_definitions
from .rate_ci_methods import DIFF_METHODS, clopper_pearson_ci, scan_diff_methods, wilson_ci

__all__ = [
    "ClinicalDocumentIndex",
    "ProportionResult",
    "GeoMeanResult",
    "GroupComparison",
    "proportion",
    "geomean",
    "rate_difference_ci",
    "compare_proportions",
    "compare_log_means",
    "fmt_rate",
    "fmt_ci",
    "fmt_p",
    "sample_size_rate_ni_wald",
    "power_rate_ni_fm",
    "sample_size_rate_ni_fm",
    "sample_size_gmc_ni",
    "power_gmc_ni",
    "quantile",
    "quartiles",
    "scan_definitions",
    "DIFF_METHODS",
    "clopper_pearson_ci",
    "scan_diff_methods",
    "wilson_ci",
]
