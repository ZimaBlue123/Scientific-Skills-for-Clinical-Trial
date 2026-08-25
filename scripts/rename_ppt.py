import os

folder = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials"
old_name = "合并版-20260820_最终优化版.pptx"
new_name = "乙肝疫苗循证比较综述.pptx"

old_path = os.path.join(folder, old_name)
new_path = os.path.join(folder, new_name)

if os.path.exists(old_path):
    if os.path.exists(new_path):
        os.remove(new_path)
    os.rename(old_path, new_path)
    print(f"Renamed successfully to {new_name}")
else:
    print(f"Source file not found: {old_path}")
