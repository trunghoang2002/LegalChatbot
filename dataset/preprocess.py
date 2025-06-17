import os
from docx import Document
import pandas as pd
import logging
from pathlib import Path
import sys
import win32com.client
import pythoncom
import shutil
import re
from typing import Generator, List, Dict, Any
import json

def is_running_in_notebook() -> bool:
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        return shell in ('ZMQInteractiveShell', 'TerminalInteractiveShell')
    except (ImportError, NameError):
        return False
    
# Thiết lập encoding mặc định cho toàn bộ chương trình
# if not is_running_in_notebook():
#     if sys.stdout.encoding != 'utf-8':
#         sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập logging với encoding UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def convert_doc_to_docx(doc_path):
    """Chuyển đổi file .doc sang .docx"""
    try:
        # Tạo đường dẫn cho file .docx
        docx_path = doc_path.replace('.doc', '.docx')
        
        # Nếu file .docx đã tồn tại, không cần chuyển đổi
        if os.path.exists(docx_path):
            return docx_path
            
        # Khởi tạo COM object
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        try:
            # Mở file .doc
            doc = word.Documents.Open(os.path.abspath(doc_path))
            # Lưu dưới dạng .docx
            doc.SaveAs2(os.path.abspath(docx_path), FileFormat=16)  # 16 là định dạng .docx
            doc.Close()
            return docx_path
        finally:
            word.Quit()
            pythoncom.CoUninitialize()
            
    except Exception as e:
        logging.error(f"Lỗi khi chuyển đổi file {doc_path}: {str(e)}")
        raise

def read_doc_file(file_path):
    """Đọc nội dung file .doc hoặc .docx"""
    try:
        # Kiểm tra file tồn tại
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
            
        # Kiểm tra định dạng file
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in ['.doc', '.docx']:
            raise ValueError(f"Định dạng file không được hỗ trợ: {file_extension}")
        
        # Nếu tên file dài hơn 70 ký tự, tạo bản sao với tên ngắn hơn
        if len(file_path) > 70:
            new_file_path = '-'.join(file_path.split('-')[:5]) + '.doc'
            if not os.path.exists(new_file_path):
                shutil.copy(file_path, new_file_path)
                file_path = new_file_path

        # Nếu là file .doc, chuyển đổi sang .docx
        if file_extension == '.doc':
            if not os.path.exists(file_path.replace('.doc', '.docx')):
                file_path = convert_doc_to_docx(file_path)
            else:
                file_path = file_path.replace('.doc', '.docx')
            
        # Đọc file
        doc = Document(file_path)
        text = ""
        
        # Đọc từng đoạn văn bản
        for para in doc.paragraphs:
            if para.text.strip():  # Chỉ thêm đoạn không rỗng
                text += para.text.strip() + "\n"
                
        if not text.strip():
            logging.warning(f"File {file_path} không chứa nội dung văn bản")
            
        return text.strip()
        
    except Exception as e:
        logging.error(f"Lỗi khi đọc file {file_path}: {str(e)}")
        raise

def convert_doc_to_txt(file_path):
    """Chuyển đổi file .doc hoặc .docx sang .txt"""
    try:
        # Tạo đường dẫn cho file .txt
        txt_path = file_path.replace('.doc', '.txt')

        # Nếu tên file dài hơn 100 ký tự, đổi tên ngắn hơn
        if len(txt_path) > 100:
            txt_path = '-'.join(txt_path.split('-')[:5]) + '.txt'
        
        # Nếu file .txt đã tồn tại, không cần chuyển đổi
        if os.path.exists(txt_path):
            return txt_path
        
        # Đọc nội dung file
        text = read_doc_file(file_path)

        # Lưu nội dung vào file .txt
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
    except Exception as e:
        logging.error(f"Lỗi khi chuyển đổi file {file_path}: {str(e)}")
        raise

def extract_law_name(text: str) -> str:
    """Trích xuất tên luật từ văn bản"""
    lines = text.splitlines()
    first_two_lines = ' '.join(lines[:2]).strip()
    law_pattern = r'\b(hiến pháp|luật|bộ luật)\s+[^\n.–;:]*'
    law_match = re.search(law_pattern, first_two_lines, flags=re.IGNORECASE)
    if law_match:
        return law_match.group(0).strip()
    return ""

def extract_law_metadata(file_path) -> dict:
    """Trích xuất metadata từ file văn bản"""
    metadata = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Các mẫu regex để trích xuất thông tin
    patterns = {
        "tieu_de": r"^(.*?)\s*$",
        "so_hieu": r"Số hiệu:\s*(.*)",
        "ngay_ban_hanh": r"Ngày ban hành:\s*(.*)",
        "nguoi_ky": r"Người ký:\s*(.*)",
        "so_cong_bao": r"Số công báo:\s*(.*)",
        "tinh_trang_hieu_luc": r"Tình trạng hiệu lực:\s*(.*)",
        "loai_van_ban": r"Loại văn bản:\s*(.*)",
        "noi_ban_hanh": r"Nơi ban hành:\s*(.*)",
        "ngay_cong_bao": r"Ngày công báo:\s*(.*)",
        "ngay_hieu_luc": r"Ngày hiệu lực:\s*(.*)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, flags=re.IGNORECASE | re.MULTILINE)
        metadata[key] = match.group(1).strip() if match else None

    return metadata

def extract_articles_with_parts(text: str) -> List[Dict[str, Any]]:
    """Trích xuất các điều luật kèm nội dung phân tách thành các phần nhỏ (văn bản, mục số, mục con) từ văn bản"""
    article_pattern = r'^(Đi.{1,2}u\s+\d+[.:]?[^\n]*)'
    matches = list(re.finditer(article_pattern, text, flags=re.IGNORECASE | re.MULTILINE))

    articles = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        article_header = match.group(1).strip()
        article_content = text[start:end].strip()

        # Tách tiêu đề
        article_index_match = re.match(r'^Đi.{1,2}u\s+(\d+)[.:]?[ \t\r\f\v]*(.*)', article_header, flags=re.IGNORECASE)
        if article_index_match:
            article_index = article_index_match.group(1)
            article_title = article_index_match.group(2).strip()

        # Phân tách nội dung bài viết thành các phần: text, item (1., 2.), subitems (a), b), ...)
        items = []
        lines = article_content.splitlines()
        current_item = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Mục chính: 1. 2. 3.
            item_match = re.match(r'^(\d+)\.\s+(.*)', line)
            if item_match:
                if current_item:
                    items.append(current_item)
                current_item = {
                    "type": "item",
                    "index": item_match.group(1),
                    "content": item_match.group(2).strip(),
                    "subitems": []
                }
                continue

            # Mục con: a) b) c) d) đ) e) ...
            subitem_match = re.match(r'^([a-zA-ZđĐ])\)\s+(.*)', line)
            if subitem_match and current_item:
                current_item["subitems"].append({
                    "index": subitem_match.group(1).lower(),
                    "content": subitem_match.group(2).strip()
                })
                continue

            # Nếu là dòng văn bản thông thường
            if current_item:
                # Gộp tiếp vào phần content của mục hiện tại
                if current_item.get("subitems"):
                    # Nếu có subitems → nối với subitem cuối
                    current_item["subitems"][-1]["content"] += " " + line
                else:
                    current_item["content"] += " " + line
            else:
                items.append({
                    "type": "text",
                    "content": line
                })

        # Thêm mục cuối nếu đang xử lý dở
        if current_item:
            items.append(current_item)

        articles.append({
            "type": "article",
            "index": article_index,
            "title": article_title,
            "items": items
        })

    return articles

def extract_sections_with_subsections(text: str) -> List[Dict[str, Any]]:
    """Trích xuất các mục kèm theo các tiểu mục từ văn bản"""
    section_pattern = r'^(?P<full>Mục\s+(?P<index>\d+)\.?\s*[:\-]?\s*(?P<title>[^\n]*))'
    subsection_pattern = r'^(?P<full>Tiểu\s+mục\s+(?P<index>\d+)\.?\s*[:\-]?\s*(?P<title>[^\n]*))'
    sections = []
    section_matches = list(re.finditer(section_pattern, text, flags=re.IGNORECASE | re.MULTILINE))

    for j, sec_match in enumerate(section_matches):
        section_index = sec_match.group('index').strip()
        section_title = sec_match.group('title').strip()
        sec_start = sec_match.end()
        sec_end = section_matches[j + 1].start() if j + 1 < len(section_matches) else len(text)
        section_text = text[sec_start:sec_end].strip()

        subsection_matches = list(re.finditer(subsection_pattern, section_text, flags=re.IGNORECASE | re.MULTILINE))

        if subsection_matches:
            subsections = []
            for k, sub_match in enumerate(subsection_matches):
                subsection_index = sub_match.group('index').strip()
                subsection_title = sub_match.group('title').strip()
                sub_start = sub_match.end()
                sub_end = subsection_matches[k + 1].start() if k + 1 < len(subsection_matches) else len(section_text)
                subsection_text = section_text[sub_start:sub_end].strip()

                articles = extract_articles_with_parts(subsection_text)
                subsections.append({
                    "type": "subsection",
                    "index": subsection_index,
                    "title": subsection_title,
                    "articles": articles
                })

            sections.append({
                "type": "section",
                "index": section_index,
                "title": section_title,
                "subsections": subsections
            })
        else:
            articles = extract_articles_with_parts(section_text)
            sections.append({
                "type": "section",
                "index": section_index,
                "title": section_title,
                "articles": articles
            })
    return sections

def extract_chapters_with_sections(text: str) -> List[Dict[str, Any]]:
    """Trích xuất các chương kèm theo các mục con từ văn bản"""
    chapter_pattern = r'^(?P<full>Chương\s+(?P<index>[IVXLCDM\d]+)\.?\s*[:\-]?\s*(?P<title>[^\n]*))'
    section_pattern = r'^(?P<full>Mục\s+(?P<index>\d+)\.?\s*[:\-]?\s*(?P<title>[^\n]*))'
    chapters = []
    chapter_matches = list(re.finditer(chapter_pattern, text, flags=re.IGNORECASE | re.MULTILINE))

    for i, chap_match in enumerate(chapter_matches):
        chapter_index = chap_match.group('index').strip()
        chapter_title = chap_match.group('title').strip()
        start_pos = chap_match.end()
        end_pos = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
        chapter_text = text[start_pos:end_pos].strip()

        section_matches = list(re.finditer(section_pattern, chapter_text, flags=re.IGNORECASE | re.MULTILINE))

        if section_matches:
            sections = extract_sections_with_subsections(chapter_text)
            chapters.append({
                "type" : "chapter",
                "index": chapter_index,
                "title": chapter_title,
                "sections": sections
            })
        else:
            articles = extract_articles_with_parts(chapter_text)
            chapters.append({
                "type" : "chapter",
                "index": chapter_index,
                "title": chapter_title,
                "articles": articles
            })

    return chapters

def extract_parts_with_chapters(text: str) -> List[Dict[str, Any]]:
    """Trích xuất các phần luật kèm theo các chương từ văn bản"""
    part_pattern = r'^(?P<full>(?P<index>Phần\s+thứ\s+[^\n\d]*)\n(?P<title>[^\n]*))'
    chapter_pattern = r'^(?P<full>Chương\s+(?P<index>[IVXLCDM\d]+)\.?\s*[:\-]?\s*(?P<title>[^\n]*))'

    parts = []
    part_matches = list(re.finditer(part_pattern, text, flags=re.IGNORECASE | re.MULTILINE))

    for i, match in enumerate(part_matches):
        part_index = match.group('index').strip()
        part_title = match.group('title').strip()
        start_pos = match.end()
        end_pos = part_matches[i + 1].start() if i + 1 < len(part_matches) else len(text)
        part_content = text[start_pos:end_pos].strip()

        chapter_matches = list(re.finditer(chapter_pattern, part_content, flags=re.IGNORECASE | re.MULTILINE))
        if chapter_matches:
            chapters = extract_chapters_with_sections(part_content)
            parts.append({
                "type": "part",
                "index": part_index,
                "title": part_title,
                "chapters": chapters
            })
        else:
            articles = extract_articles_with_parts(part_content)
            parts.append({
                "type": "part",
                "index": part_index,
                "title": part_title,
                "articles": articles
            })

    return parts

def extract_law_structure_and_metadata(text: str, metadata_file_path: str) -> Dict[str, Any]:
    """Trích xuất cấu trúc của luật từ văn bản"""
    law_name = extract_law_name(text)
    metadata = extract_law_metadata(metadata_file_path)

    part_pattern = r'^(?P<full>(?P<index>Phần\s+thứ\s+[^\n\d]*)\n(?P<title>[^\n]*))'
    part_matches = list(re.finditer(part_pattern, text, flags=re.IGNORECASE | re.MULTILINE))
    if part_matches:
        # Nếu có phần
        parts = extract_parts_with_chapters(text)
        return {
            "law_name": law_name,
            "metadata": metadata,
            "parts": parts
        }
    else:
        # Nếu không có phần, chỉ có chương và mục
        chapters = extract_chapters_with_sections(text)
        return {
            "law_name": law_name,
            "metadata": metadata,
            "chapters": chapters
        }

def process_documents(root_dir) -> tuple[list, list]:
    """Xử lý tất cả file .doc hoặc .docx trong thư mục"""
    processed_files = []
    failed_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(('.doc', '.docx')) and not file.startswith('~$'):
                file_path = os.path.join(root, file)
                metadata_file_path = file_path.split('.')[0] + '-metadata.txt'
                if not os.path.exists(metadata_file_path):
                    logging.warning(f"Không tìm thấy file metadata cho {file_path}")
                    failed_files.append(file_path)
                    continue

                if file_path.split(".")[0] in processed_files:
                    continue

                try:
                    logging.info(f"Đang xử lý file: {file_path}")
                    txt_path = file_path.split('.')[0] + '.txt'
                    if os.path.exists(txt_path):
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                    else:
                        text = read_doc_file(file_path)
                    
                    if not text.strip():
                        failed_files += 1
                        continue
                        
                    law_structure = extract_law_structure_and_metadata(text, metadata_file_path)
                    save_path = file_path.split('.')[0] + '.json'
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(law_structure, f, ensure_ascii=False, indent=4)

                    processed_files.append(file_path.split(".")[0])
                    logging.info(f"Đã xử lý thành công file: {file_path}")
                    
                except Exception as e:
                    failed_files.append(file_path)
                    logging.error(f"Lỗi khi xử lý file {file_path}: {str(e)}")
                    continue
    
    logging.info(f"Tổng số file đã xử lý của thư mục {root_dir}: {len(processed_files)}")
    logging.info(f"Tổng số file thất bại của thư mục {root_dir}: {len(failed_files)}")
    return processed_files, failed_files

def iterate_law_recursive(
    node: dict,
    level: str = "law",
    context: dict = None
) -> Generator[dict | Any, Any, None]:
    """Tạo generator để duyệt qua cấu trúc luật
    parts > chapters > sections > subsections > articles > items (text | item) > subitems"""
    if context is None:
        context = {
            "law": "",
            "part": ("", ""),
            "chapter": ("", ""),
            "section": ("", ""),
            "subsection": ("", ""),
            "article": ("", ""),
            "item": ("", ""),
            "subitem": ("", "")
        }

    # Xử lý cấp tiếp theo dựa trên thứ tự cấu trúc luật
    next_levels = {
        "law": ("parts", "part"),
        "part": ("chapters", "chapter"),
        "chapter": ("sections", "section"),
        "section": ("subsections", "subsection"),
        "subsection": ("articles", "article"),
        "article": ("items", "item"),
        "item": ("subitems", "subitem")
    }

    # print(f"Processing level: {level}")
    # Trường hợp đặc biệt: cấp item cần yield dữ liệu
    if level == "item":
        if node["type"] == "item":
            context["item"] = (node.get("index", ""), node.get("content", ""))
            if node["subitems"]:
                for sub in node["subitems"]:
                    context["subitem"] = (sub.get("index", ""), sub.get("content", ""))
                    yield dict(context)
            else:
                context["subitem"] = ("", "")
                yield dict(context)
        elif node["type"] == "text":
            context["item"] = ("", node.get("content", ""))
            context["subitem"] = ("", "")
            yield dict(context)
        return

    # Trường hợp cấp khác: lấy dữ liệu từ node
    if level == "law":
        context["law"] = node.get("law_name", "")
        # print(f"Law name: {context['law']}")
    else:
        context[level] = (node.get("index", ""), node.get("title", node.get("content", "")))
        # print(f"{level.capitalize()}: {context[level]}")

    # Truy xuất cấp con tiếp theo
    children_key, next_level = next_levels.get(level, (None, None))
    if children_key and next_level:
        children = node.get(children_key, [])
        for child in children:
            yield from iterate_law_recursive(child, next_level, context.copy())

    
    # # Trường hợp đặc biệt: cấp article cần yield dữ liệu
    # if level == "article" and node.get("items") == []:
    #     context["item"] = ("", "")
    #     context["subitem"] = ("", "")
    #     yield dict(context)
    
    # Trường hợp fallback nếu không có cấp giữa
    if level in ["chapter", "section"] and not node.get("sections" if level == "chapter" else "subsections"):
        articles = node.get("articles", [])
        for article in articles:
            yield from iterate_law_recursive(article, "article", context.copy())

    if level == "law" and not node.get("parts"):
        # Xử lý khi luật không có part, nhưng có chapter
        chapters = node.get("chapters", [])
        for chapter in chapters:
            yield from iterate_law_recursive(chapter, "chapter", context.copy())
    
    # bỏ qua trường hợp level == "part" and not node.get("chapters")
    # vì đây là ĐIỀU KHOẢN THI HÀNH không có ý nghĩa retrieval

def get_law_text(data, law_mapping=None):
    if law_mapping:
        text = law_mapping[data['law']] + '\n'
    else:
        text = data['law'] + '\n'
    if data['part'][0] and data['part'][1]:
        text += data['part'][0] + ' ' + data['part'][1]
    if data['chapter'][0] and data['chapter'][1]:
        text += '\nChương ' + data['chapter'][0] + ' ' + data['chapter'][1]
    if data['section'][0] and data['section'][1]:
        text += '\nMục ' + data['section'][0] + ' ' + data['section'][1]
    if data['subsection'][0] and data['subsection'][1]:
        text += '\nTiểu mục ' + data['subsection'][0] + ' ' + data['subsection'][1]
    if data['article'][0]:
        text += '\nĐiều ' + data['article'][0] + ' ' + data['article'][1]
    if data['item'][1]:
        text += '\n' + data['item'][1]
    if data['subitem'][0] and data['subitem'][1]:
        text += '\n' + data['subitem'][1]
    text = re.sub(r'[^\S\n]+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r'\n +', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()  # Remove leading and trailing spaces
    return text

def main():
    # Xử lý tất cả các thư mục
    # directories = ['HienPhap', 'LuatLaoDong', 'LuatDanSu', 'LuatHinhSu']
    directories = ['HienPhap', 'LuatLaoDong', 'LuatDanSu', 'LuatHinhSu']
    all_processed_files = []
    all_failed_files = []

    for directory in directories:
        logging.info(f"Đang xử lý thư mục {directory}...")
        processed_files, failed_files = process_documents(directory)
        all_processed_files.extend(processed_files)
        all_failed_files.extend(failed_files)

    logging.info(f"Tổng số file đã xử lý của tất cả thư mục: {len(all_processed_files)}")
    logging.info(f"Tổng số file thất bại của tất cả thư mục: {len(all_failed_files)}")

if __name__ == "__main__":
    main() 