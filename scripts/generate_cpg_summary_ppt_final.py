# -*- coding: utf-8 -*-
"""Script to convert Word summary table into V10 PPT with corrected conclusion."""

import sys
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import pptx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx"])
    import pptx

try:
    import docx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    import docx

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pptx.enum.shapes

def estimate_row_height(row_data):
    col_limits = [25, 18, 45, 80, 18]
    max_lines = 1
    for idx, text in enumerate(row_data):
        limit = col_limits[idx]
        lines = 0
        for paragraph in text.split('\n'):
            if len(paragraph) == 0:
                lines += 1
            else:
                lines += (len(paragraph) // limit) + 1
        if lines > max_lines:
            max_lines = lines
    return (max_lines * 0.15) + 0.1

def create_ppt_from_docx(doc_path, ppt_path):
    logging.info(f"Reading document: {doc_path}")
    doc = docx.Document(doc_path)
    
    table = doc.tables[0]
    headers = [c.text for c in table.rows[0].cells]
    
    for i in range(len(headers)):
        h = headers[i].replace('\n', ' ')
        if "临床试验基本信息" in h:
            headers[i] = "临床试验基本信息"
        elif "核心参考文献" in h:
            headers[i] = "核心参考文献"
        else:
            headers[i] = h
    
    row_data = []
    for row in table.rows[1:]:
        row_data.append([c.text for c in row.cells])

    logging.info(f"Extracted {len(row_data)} rows of data.")

    slides_data = []
    current_chunk = []
    current_height = 0
    MAX_HEIGHT = 5.5 

    for row in row_data:
        h = estimate_row_height(row)
        if len(current_chunk) == 4 or (current_height + h > MAX_HEIGHT and len(current_chunk) >= 2):
            slides_data.append(current_chunk)
            current_chunk = [row]
            current_height = h
        else:
            current_chunk.append(row)
            current_height += h

    if current_chunk:
        if len(current_chunk) == 1 and len(slides_data) > 0 and len(slides_data[-1]) > 2:
            current_chunk.insert(0, slides_data[-1].pop())
        slides_data.append(current_chunk)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    DARK_RED = RGBColor(192, 0, 0)
    WHITE = RGBColor(255, 255, 255)
    BLACK = RGBColor(0, 0, 0)
    LIGHT_GRAY = RGBColor(245, 245, 245)
    HEADER_TEXT = RGBColor(255, 255, 255)
    LINK_BLUE = RGBColor(5, 99, 193)

    blank_layout = prs.slide_layouts[6]

    def format_cell(cell, text, size=8.5, bold=False, text_color=BLACK, bg_color=None, is_ref=False):
        cell.text = ""
        cell.margin_top = Pt(2)
        cell.margin_bottom = Pt(2)
        cell.margin_left = Pt(5)
        cell.margin_right = Pt(5)
        
        if bg_color:
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_color
            
        p = cell.text_frame.paragraphs[0]
        p.space_before = Pt(1)
        p.space_after = Pt(1)
        p.line_spacing = 1.0

        clean_text = text.replace('**', '')

        if not is_ref:
            run = p.add_run()
            run.text = clean_text
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = text_color
            run.font.name = 'Microsoft YaHei'
        else:
            pattern = re.compile(r'(PMID:\s*)(\d+)|(DOI:\s*)(10\.\S+)')
            last_idx = 0
            for match in pattern.finditer(clean_text):
                if match.start() > last_idx:
                    run = p.add_run()
                    run.text = clean_text[last_idx:match.start()]
                    run.font.size = Pt(size)
                    run.font.bold = bold
                    run.font.color.rgb = text_color
                    run.font.name = 'Microsoft YaHei'
                
                run = p.add_run()
                if match.group(1):
                    run.text = match.group(1) + match.group(2)
                    run.hyperlink.address = f'https://pubmed.ncbi.nlm.nih.gov/{match.group(2)}/'
                elif match.group(3):
                    run.text = match.group(3) + match.group(4)
                    run.hyperlink.address = f'https://doi.org/{match.group(4)}'
                
                run.font.size = Pt(size)
                run.font.bold = bold
                run.font.color.rgb = LINK_BLUE
                run.font.name = 'Microsoft YaHei'
                last_idx = match.end()
            
            if last_idx < len(clean_text):
                run = p.add_run()
                run.text = clean_text[last_idx:]
                run.font.size = Pt(size)
                run.font.bold = bold
                run.font.color.rgb = text_color
                run.font.name = 'Microsoft YaHei'

    # Title Slide
    title_slide = prs.slides.add_slide(blank_layout)
    rect = title_slide.shapes.add_shape(pptx.enum.shapes.MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.5))
    rect.fill.solid()
    rect.fill.fore_color.rgb = DARK_RED
    rect.line.color.rgb = DARK_RED
    
    title_box = title_slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11.333), Inches(2))
    tf = title_box.text_frame
    p = tf.add_paragraph()
    p.text = "CpG佐剂预防性疫苗\n核心临床试验与安全性数据汇总"
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(44)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = DARK_RED
    p.runs[0].font.name = 'Microsoft YaHei'
    
    col_widths = [Inches(1.8), Inches(1.3), Inches(3.2), Inches(5.6), Inches(1.3)]
    left_margin = Inches(0.1)
    top_margin = Inches(0.9)
    
    for chunk in slides_data:
        slide = prs.slides.add_slide(blank_layout)
        
        title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(0.05), Inches(12.33), Inches(0.6))
        tf = title_shape.text_frame
        tf.margin_top = 0
        tf.margin_bottom = 0
        p = tf.add_paragraph()
        p.text = "CpG佐剂预防性疫苗安全性汇总" 
        p.runs[0].font.size = Pt(26)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = DARK_RED
        p.runs[0].font.name = 'Microsoft YaHei'
        
        table_shape = slide.shapes.add_table(len(chunk) + 1, 5, left_margin, top_margin, sum(col_widths), Inches(1.0))
        tbl = table_shape.table
        tbl.rows[0].height = Inches(0.35)
        
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = w
            
        for c_idx, h_text in enumerate(headers):
            cell = tbl.cell(0, c_idx)
            format_cell(cell, h_text, size=11, bold=True, text_color=HEADER_TEXT, bg_color=DARK_RED)
            
        for r_idx, r_data in enumerate(chunk):
            bg_color = WHITE if r_idx % 2 == 0 else LIGHT_GRAY
            for c_idx, c_text in enumerate(r_data):
                cell = tbl.cell(r_idx + 1, c_idx)
                tbl.rows[r_idx + 1].height = Inches(0.5)
                is_ref_column = (c_idx == 4)
                format_cell(cell, c_text, size=8.5, bold=False, text_color=BLACK, bg_color=bg_color, is_ref=is_ref_column)

    # FINAL SUMMARY SLIDE
    summary_slide = prs.slides.add_slide(blank_layout)
    
    # Red header bar
    s_rect = summary_slide.shapes.add_shape(pptx.enum.shapes.MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.5))
    s_rect.fill.solid()
    s_rect.fill.fore_color.rgb = DARK_RED
    s_rect.line.color.rgb = DARK_RED
    
    # Slide Title
    s_title_shape = summary_slide.shapes.add_textbox(Inches(0.5), Inches(0.7), Inches(12.33), Inches(0.8))
    stf = s_title_shape.text_frame
    sp = stf.add_paragraph()
    sp.text = "【总体安全性总结】基于含CpG佐剂预防性疫苗的综合评价"
    sp.runs[0].font.size = Pt(28)
    sp.runs[0].font.bold = True
    sp.runs[0].font.color.rgb = DARK_RED
    sp.runs[0].font.name = 'Microsoft YaHei'

    # Content Box
    content_box = summary_slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.33), Inches(5.5))
    ctf = content_box.text_frame
    ctf.word_wrap = True
    
    paragraphs_data = [
        ("1. 优越的局部与全身耐受性 (Reactogenicity)", 
         "以注射部位疼痛（20%-40%左右）、红肿以及轻度至中度的疲劳、头痛和肌痛为最常见的非严重不良反应（ADR）。值得注意的是，相较于如 Shingrix 等使用强效脂质体佐剂系统的产品，CpG 1018 及联合方案在诱导高免疫原性的同时，极大幅度地降低了3级（严重）反应的发生率（例如Z-1018显著降低了中重度局部与全身不良反应）。"),
        
        ("2. 无明显自身免疫及严重不良事件 (SAE/AESI) 风险信号", 
         "包含 HEPLISAV-B 核心三期及大规模安全性监测，以及 SCB-2019 等新冠疫苗的三万人全球数据均证明：CpG佐剂预防性疫苗不会提升潜在免疫介导性疾病（如格林巴利综合征、类风湿性关节炎等）及心血管事件（如AMI）的基线发生率，发生率（常低于0.1%）与对照组高度相似，无疫苗归因性关联。"),
        
        ("3. 特征性免疫生理反应的安全可控性", 
         "部分疫苗（如 CYFENDUS 临床审评中）观察到了一过性的绝对淋巴细胞计数下降，FDA评估认定此为寡核苷酸佐剂特有的一过性免疫“归巢效应”（Homing Effect）。该反应迅速且可逆，无长期病理学意义，反而在细胞学层面佐证了佐剂的高效刺激机制。"),
        
        ("总结论：", 
         "CpG 1018 及其同类寡核苷酸佐剂通过高特异性激活 TLR-9 靶点，成功剥离了传统强效佐剂常伴随的“高反应原性”痛点。数万例严谨的大规模临床试验数据（Phase 1-3）的确证及 FDA 官方审评的背书，标志着其已成为业界高度成熟的下一代“高效、低毒”通用型人用疫苗佐剂平台。")
    ]
    
    for title_text, body_text in paragraphs_data:
        p_title = ctf.add_paragraph()
        p_title.text = title_text
        p_title.font.bold = True
        p_title.font.size = Pt(16)
        p_title.font.color.rgb = DARK_RED
        p_title.font.name = 'Microsoft YaHei'
        p_title.space_before = Pt(10)
        
        p_body = ctf.add_paragraph()
        p_body.text = body_text
        p_body.font.bold = False
        p_body.font.size = Pt(14)
        p_body.font.color.rgb = BLACK
        p_body.font.name = 'Microsoft YaHei'
        p_body.space_after = Pt(10)
        p_body.line_spacing = 1.3

    prs.save(ppt_path)
    logging.info(f"Successfully saved PPT to: {ppt_path}")

if __name__ == "__main__":
    import traceback
    try:
        doc_path = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\CpG_Vaccine_Safety_Summary-V10-20260820.docx"
        ppt_path = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\CpG_Vaccine_Safety_Summary_PPT-V10-20260820.pptx"
        create_ppt_from_docx(doc_path, ppt_path)
    except Exception as e:
        logging.error("An error occurred:")
        traceback.print_exc()
