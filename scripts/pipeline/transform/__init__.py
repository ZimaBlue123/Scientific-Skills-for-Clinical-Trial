"""Transform stage: embeddings, RAG, statistical recomputation and data reshaping."""

from .clinical_rag import ClinicalDocumentIndex
from .quantile_definitions import quantile, quartiles, scan_definitions
from .rate_ci_methods import DIFF_METHODS, clopper_pearson_ci, scan_diff_methods, wilson_ci

__all__ = [
    "ClinicalDocumentIndex",
    "quantile",
    "quartiles",
    "scan_definitions",
    "DIFF_METHODS",
    "clopper_pearson_ci",
    "scan_diff_methods",
    "wilson_ci",
]
