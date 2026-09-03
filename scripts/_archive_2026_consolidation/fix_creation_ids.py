# -*- coding: utf-8 -*-
"""
修复 deepcopy 导致的 a16:creationId GUID 重复：
为新增 6 页（slide64-69）中所有 shape 的 a16:creationId 重新生成唯一 GUID。
采用重写整个 zip 的方式避免 zipfile append 导致的重复条目。
"""
import zipfile, os, uuid, shutil
from lxml import etree

SRC = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\TVAX-009项目3期临床试验启动前沟通交流ppt-20260903（临床部分-新增糖尿病亚组）.pptx"
OUT = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\TVAX-009项目3期临床试验启动前沟通交流ppt-20260903（临床部分-新增糖尿病亚组）-fixed.pptx"

A16_NS = 'http://schemas.microsoft.com/office/drawing/2014/main'

def new_guid():
    return '{' + str(uuid.uuid4()).upper() + '}'

# 读取源 zip 所有条目
src_zf = zipfile.ZipFile(SRC, 'r')
items = []
modified = []
for info in src_zf.infolist():
    data = src_zf.read(info.filename)
    if info.filename.startswith('ppt/slides/slide') and info.filename.endswith('.xml'):
        # 仅修改 slide64-69
        name = os.path.basename(info.filename)
        try:
            n = int(name.replace('slide', '').replace('.xml', ''))
        except ValueError:
            n = 0
        if 64 <= n <= 69:
            tree = etree.fromstring(data)
            count = 0
            for cid in tree.iter(f'{{{A16_NS}}}creationId'):
                cid.set('id', new_guid())
                count += 1
            data = etree.tostring(tree, xml_declaration=True, standalone=True, encoding='UTF-8')
            modified.append((info.filename, count))
    items.append((info, data))
src_zf.close()

# 写入新 zip
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as out_zf:
    for info, data in items:
        out_zf.writestr(info, data)

print('modified:', modified)
print('saved:', OUT)
