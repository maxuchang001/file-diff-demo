from diffPdfV2 import create_diff_report

def diffControl(file1_path, file2_path,file1_name,file2_name, ext):
    if ext.lower() == '.zip':
        # 压缩文件需先进行解压缩
        return 'no', 'zip 不支持的文件类型'
    else:
        # 其他文件类型直接调用 diffFile 函数
        return diffFile(file1_path, file2_path,file1_name,file2_name, ext)

def diffFile(file1_path, file2_path,file1_name,file2_name, ext):
    if ext.lower() == '.pdf':
        # 调用 diffPdfV2 模块进行比较
        diff_output_url = create_diff_report(file1_path, file2_path,file1_name,file2_name)
        return 'ok', diff_output_url
    elif ext.lower() == '.docx':
        # docx 文件需先转换为 pdf
        return 'no', 'docx 不支持的文件类型'
    elif ext.lower() == '.xlsx':
        # xlsx 文件需先转换为 pdf
        return 'no', 'xlsx 不支持的文件类型'
    elif ext.lower() == '.pptx':
        # pptx 文件需先转换为 pdf
        return 'no', 'pptx 不支持的文件类型'
    elif ext.lower() == '.txt':
        # txt 文件需先转换为 pdf
        return 'no', 'txt 不支持的文件类型'
    elif ext.lower() == '.csv':
        # csv 文件需先转换为 pdf
        return 'no', 'csv 不支持的文件类型'
    else:
        # 其他文件类型不支持
        return 'no', '不支持的文件类型'