---
name: custom-pubmed-cli-search
description: Search PubMed using the project's custom CLI tool to fetch clinical trial literature.
---
# Custom PubMed CLI Search

This skill instructs the AI agent on how to seamlessly use the project's internal `scripts/pubmed_search_tool.py` to perform medical literature searches.

## Usage

When the user asks you to find clinical trials or literature for a specific topic (e.g. Norovirus, Varicella vaccine safety), follow these steps:

1. **Formulate the Query**: Create a valid PubMed query string. For example: `"Varicella Vaccine"[tiab] AND safety[tiab]`.
2. **Execute the Search**: Use the CLI tool to fetch the results.
   ```bash
   python scripts/pubmed_search_tool.py --query "<YOUR_QUERY>" --out ".workbuddy/audit/search_results.json"
   ```
   *(You can also use `--mindate YYYY/MM/DD` and `--maxdate YYYY/MM/DD` if a specific time window is needed).*
3. **Analyze**: Read the generated `.workbuddy/audit/search_results.json` file using your file reading tools, and provide a structured summary of the PMIDs, authors, and findings to the user.
