

import markdown2
import os
import glob




def convert_md_to_html(md_file, output_dir=None):
    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # 转换为 HTML
    html_content = markdown2.markdown(markdown_content, extras=[
        'fenced-code-blocks', 'tables', 'header-ids'
    ])

    # 确定输出路径
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.basename(md_file).replace('.md', '.html')
        output_path = os.path.join(output_dir, base_name)
    else:
        output_path = md_file.replace('.md', '.html')

    # 写入 HTML 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Converted {md_file} to {output_path}")


# 使用示例
# 转换单个文件
convert_md_to_html('D:\独立站\成人用品计划.md')

# 转换目录中的所有 Markdown 文件
# md_files = glob.glob('')
# for md_file in md_files:
#     convert_md_to_html(md_file, 'html_output')

if __name__ == '__main__':
    convert_md_to_html("", "")