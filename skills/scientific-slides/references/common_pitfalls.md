# Common Pitfalls to Avoid

Content, design, and timing mistakes, with the corrections for each.

## Common Pitfalls to Avoid

### Content Mistakes

**Dry, Boring Presentations** (CRITICAL TO AVOID):
- Problem: Text-heavy slides with no visual interest, missing research context
- Signs: All bullet points, no images, default templates, no citations
- Solution: 
  - Use research-lookup to find 8-15 papers for credible context
  - Add high-quality visuals to EVERY slide (figures, photos, diagrams, icons)
  - Choose modern color palette reflecting your topic
  - Vary slide layouts (not all bullet lists)
  - Tell a story with visuals, use text sparingly

**Too Much Content**:
- Problem: Trying to include everything from paper
- Solution: Focus on 1-2 key findings for short talks, show visually

**Too Much Text**:
- Problem: Full paragraphs on slides, dense bullet points, reading verbatim
- Solution: 3-4 bullets with 4-6 words each, let visuals carry the message

**Missing Research Context**:
- Problem: No citations, claims without support, unclear positioning
- Solution: Use research-lookup to find papers, cite 3-5 in intro, 3-5 in discussion

**Poor Narrative**:
- Problem: Jumping between topics, no clear story, no flow
- Solution: Follow story arc, use visual transitions, maintain thread

**Rushing Through Results**:
- Problem: Brief methods, brief results, long discussion
- Solution: Spend 40-50% of time on results, show data visually

### Design Mistakes

**Generic, Default Appearance**:
- Problem: Using default PowerPoint/Beamer themes without customization, looks dated
- Solution: Choose modern color palette, customize fonts/layouts, add visual personality

**Text-Heavy, Visual-Poor**:
- Problem: All bullet point slides, no images or graphics, boring to look at
- Solution: Add figures, photos, diagrams, icons to EVERY slide, make visually interesting

**Small Fonts**:
- Problem: Body text <18pt, unreadable from back, looks unprofessional
- Solution: 24-28pt for body (not just 18pt minimum), 36-44pt for titles

**Low Contrast**:
- Problem: Light text on light background, poor visibility, hard to read
- Solution: High contrast (7:1 preferred, not just 4.5:1 minimum), test with contrast checker

**Cluttered Slides**:
- Problem: Too many elements, no white space, overwhelming
- Solution: One idea per slide, 40-50% white space, generous spacing

**Inconsistent Formatting**:
- Problem: Different fonts, colors, layouts slide-to-slide, looks amateurish
- Solution: Use master slides, maintain design system, professional consistency

**Missing Visual Hierarchy**:
- Problem: Everything same size and color, no emphasis, unclear focus
- Solution: Size differences (titles large, body medium), color for emphasis, clear focal point

### Timing Mistakes

**Not Practicing**:
- Problem: First time through is during presentation
- Solution: Practice minimum 3 times with timer

**No Time Checkpoints**:
- Problem: Don't realize running behind until too late
- Solution: Set 3-4 checkpoints, monitor throughout

**Going Over Time**:
- Problem: Extremely unprofessional, cuts into Q&A
- Solution: Practice to exact time, prepare Plan B (slides to skip)

**Skipping Conclusions**:
- Problem: Running out of time, rush through or skip ending
- Solution: Never skip conclusions, cut earlier content instead

### Anti-AI-Slop Visual Restraint (Floor / Reflex / Finish)

Adapted from Hallmark and Impeccable deterministic design gates to prevent generic AI-generated slide bloat:

- **Floor (Hard Block — P0)**:
  - Never ship unreplaced placeholders (`TODO`, `TBD`, `FIXME`, `Lorem ipsum`, `[待补充]`).
  - Never allow body/table text `< 9 pt` or text-to-background contrast `< 3.0:1` (aim for `>= 4.5:1`).
  - Never flatten editable scientific charts (e.g., GraphPad Prism OLE objects) into static screenshots when native editability is required.
- **Reflex (AI Template Tell — P1/P2)**:
  - **No purple-to-blue / neon gradient defaults**: Stick to clean white/off-white surfaces + 1 restrained brand color + 1 semantic accent.
  - **No uppercase eyebrow pills on every slide**: Avoid repeating `RESEARCH OVERVIEW` / `KEY FINDINGS` badges above titles; use assertion-based slide titles directly.
  - **No single-word colored headline gimmicks**: Keep slide titles in one consistent high-contrast color.
  - **No cards-nested-in-cards**: Replace multi-layered rounded boxes and icon tiles with structured comparison tables or clean whitespace/hairline dividers.
  - **Font discipline**: Keep `<= 3` font families per slide (ideally 1–2).
- **Finish (Craft — P3)**:
  - Remove empty decorative AutoShape frames and run `scripts/pipeline/validate/pptx_slop_detector.py` before delivery.
