---
name: clinical-strict-extractor
description: A cognitive guardrail skill inspired by i-have-adhd. Enforces strict, filler-free, and deterministic formatting for AI agents during clinical data extraction or report generation.
metadata:
  version: "1.0.0"
---
# Clinical Strict Extractor (Cognitive Guardrail)

**STOP AND READ THIS CAREFULLY.**
When this skill is active, you MUST strictly adhere to the following behavioral and output constraints. This project involves processing highly sensitive clinical trial data (Protocols, DSURs, CSRs). "Conversational filler" and "AI slop" cause downstream Python parsing scripts to crash.

## CORE PRINCIPLES (Non-Negotiable)

1.  **NO CONVERSATIONAL FILLER:** 
    *   Do NOT start responses with "Here is the extracted data...", "I have updated the file...", "Certainly!", or "Great question."
    *   Do NOT end responses with "Let me know if you need anything else!", "Hope this helps!", or similar polite padding.
    *   **Action:** Your very first line must be the direct answer, the pure JSON, or the exact requested data snippet.

2.  **LEAD WITH THE NEXT ACTION:** 
    *   If a task is incomplete or requires a multi-step pipeline, the very first line of your response must state the current state and the immediate next step.

3.  **NUMBER MULTI-STEP TASKS:** 
    *   If you are proposing a plan or breaking down a complex clinical document review, you MUST use a numbered list of bounded, concrete actions. 
    *   *Bad:* "We will extract tables and then compare the adverse events."
    *   *Good:* "1. Extract tables from DSUR. 2. Diff Adverse Events against EDC data."

4.  **PURE DATA OUTPUT FOR SCRIPTS:**
    *   If you are asked to extract data (e.g., table structure, JSON, XML) intended for a script, **output ONLY the code block**. Any text outside the code block is strictly prohibited unless specifically requested for debugging.

5.  **CONCRETE ESTIMATES & METRICS:**
    *   When reporting issues found in clinical reports, use precise numbers. 
    *   *Bad:* "Found some missing definitions."
    *   *Good:* "Found 3 missing adverse event definitions in Section 4.2."

## TRIGGER CONDITIONS
Use this skill automatically whenever:
*   You are extracting structured data (Tables, JSON) from Clinical Trial Docs.
*   You are generating pipeline scripts.
*   You are running QA/QC (Quality Control) on generated clinical reports.


## Pre-flight Check

Before executing, the agent MUST:
1. Verify input file exists at the expected path
2. Clear any cached results from previous runs
3. Confirm required environment variables are set


## Post-execution Validation

After execution, the agent MUST:
1. Verify output file was created successfully
2. Run applicable validator (if available)
3. Report results in standardized Markdown table format
