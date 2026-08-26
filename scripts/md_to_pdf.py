import sys

from markdown_pdf import MarkdownPdf, Section


def convert_md_to_pdf(md_path, pdf_path):
    try:
        with open(md_path, encoding="utf-8") as f:
            md_content = f.read()

        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(md_content))
        pdf.save(pdf_path)
        print(f"Successfully converted {md_path} to {pdf_path}")
    except Exception as e:
        print(f"Error converting to PDF: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        convert_md_to_pdf(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python md_to_pdf.py <input.md> <output.pdf>")
