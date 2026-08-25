import pandas as pd
import pdfplumber

pdf_path = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\006 1期 免疫持久性结果-中检院-20260825.pdf"
excel_path = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\006 1期分组.xlsx"

# 1. Read Excel Group Mapping
df_group = pd.read_excel(excel_path)
# Excel has 'GROUPID', '组别', '组别.1'
# Let's create a mapping dictionary from GROUPID (int) to Group info
group_mapping = {}
for _, row in df_group.iterrows():
    try:
        group_id = int(row["GROUPID"])
        group_mapping[group_id] = f"{row['组别']} - {row['组别.1']}"
    except:
        pass

print("Sample group mappings:")
for k in list(group_mapping.keys())[:5]:
    print(k, group_mapping[k])


# 2. Extract PDF Data
def extract_tables_from_pages(pages):
    extracted_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pages:
            page = pdf.pages[p]
            tables = page.extract_tables()
            for table in tables:
                for row in table[1:]:  # Skip header
                    if len(row) == 4:
                        id1, val1, id2, val2 = row
                        if id1 and str(id1).strip() and str(id1).strip() != "/":
                            extracted_data.append(
                                {
                                    "样本编号": str(id1).strip(),
                                    "结果": str(val1).strip(),
                                }
                            )
                        if id2 and str(id2).strip() and str(id2).strip() != "/":
                            extracted_data.append(
                                {
                                    "样本编号": str(id2).strip(),
                                    "结果": str(val2).strip(),
                                }
                            )
    return extracted_data


# Page 2-3 (index 2, 3) are gE, Page 4-5 are VZV ELISA, Page 6-7 are VZV FAMA
# Let's map it based on the text to be safe
gE_data = extract_tables_from_pages([2, 3])
vzv_elisa_data = extract_tables_from_pages([4, 5])
vzv_fama_data = extract_tables_from_pages([6, 7])

print(f"Extracted gE: {len(gE_data)} records")
print(f"Extracted VZV ELISA: {len(vzv_elisa_data)} records")
print(f"Extracted VZV FAMA: {len(vzv_fama_data)} records")

# 3. Combine Data
for item in gE_data:
    item["检测项目"] = "记忆抗体 (gE)"
for item in vzv_elisa_data:
    item["检测项目"] = "VZV抗体 (ELISA)"
for item in vzv_fama_data:
    item["检测项目"] = "VZV抗体 (FAMA)"

all_data = gE_data + vzv_elisa_data + vzv_fama_data
df_all = pd.DataFrame(all_data)


# Extract Middle ID
def get_middle_id(sample_id):
    # format: V10-0001-送检1
    parts = str(sample_id).split("-")
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except:
            return None
    return None


df_all["MiddleID"] = df_all["样本编号"].apply(get_middle_id)

# Map Group
df_all["组别"] = df_all["MiddleID"].map(group_mapping)

print("Combined DataFrame head:")
print(df_all.head())
print("Combined DataFrame tail:")
print(df_all.tail())
print("Missing groups:", df_all["组别"].isna().sum())

# Save to Excel
output_path = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\汇总_原始数据.xlsx"
df_all[["样本编号", "检测项目", "结果", "组别"]].to_excel(output_path, index=False)
print(f"Saved to {output_path}")
