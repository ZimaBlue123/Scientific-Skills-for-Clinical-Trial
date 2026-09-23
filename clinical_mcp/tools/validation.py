from ..schemas import VALIDATE_PPTX, RUN_SKILL_VALIDATION, DEDUPE_SKILLS
from ..session import load_script_module

def _handle_validate_pptx(args: dict) -> dict:
    module = load_script_module("pptx_validator")
    if hasattr(module, "validate_pptx"):
        return {"result": module.validate_pptx(args["file_path"])}
    return {"error": "validate_pptx not implemented in scripts"}

def _handle_run_skill_validation(args: dict) -> dict:
    module = load_script_module("skill_validator")
    if hasattr(module, "validate_skills"):
        return {"result": module.validate_skills(args["registry_path"])}
    return {"error": "validate_skills not implemented in scripts"}

def _handle_dedupe_skills(args: dict) -> dict:
    module = load_script_module("skill_deduper")
    if hasattr(module, "dedupe_skills"):
        return {"result": module.dedupe_skills(args["registry_path"])}
    return {"error": "dedupe_skills not implemented in scripts"}

VALIDATION_TOOLS = [
    {
        "name": "validate_pptx",
        "description": "Check PPTX for overflow",
        "inputSchema": VALIDATE_PPTX,
        "_handler": _handle_validate_pptx,
    },
    {
        "name": "run_skill_validation",
        "description": "Validate skills registry",
        "inputSchema": RUN_SKILL_VALIDATION,
        "_handler": _handle_run_skill_validation,
    },
    {
        "name": "dedupe_skills",
        "description": "Detect duplicate skills",
        "inputSchema": DEDUPE_SKILLS,
        "_handler": _handle_dedupe_skills,
    },
]
