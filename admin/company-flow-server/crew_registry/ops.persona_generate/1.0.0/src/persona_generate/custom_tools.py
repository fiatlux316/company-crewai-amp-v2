import os
import re
import io
from pathlib import Path
from typing import Optional
import pandas as pd
import markdown
from crewai.tools import tool

@tool("markdown_to_excel_converter")
def markdown_to_excel_tool(md_file_path_or_content: str, excel_file_path: Optional[str] = None) -> str:
    """
    마크다운 파일 경로 또는 마크다운 표 텍스트 전체를 읽어서 엑셀(.xlsx) 파일로 변환하고 저장하는 도구입니다.
    md_file_path_or_content: 원본 마크다운 파일의 경로(예: './output/crew_spec.md') 또는 변환할 마크다운 텍스트 전체
    excel_file_path: 저장할 엑셀 파일의 경로(예: './output/crew_spec.xlsx'). None인 경우 dfs 또는 마크다운 상단의 crew_name을 찾아 자동으로 설정합니다.
    """
    try:
        # 파일 경로인 경우 파일 읽기, 아니면 텍스트 자체로 간주
        if len(md_file_path_or_content) < 255 and os.path.exists(md_file_path_or_content):
            with open(md_file_path_or_content, 'r', encoding='utf-8') as f:
                md_text = f.read()
        else:
            md_text = md_file_path_or_content

        # HTML로 파싱
        html_text = markdown.markdown(md_text, extensions=['tables'])

        # pandas로 html 내의 table 추출
        dfs = pd.read_html(io.StringIO(html_text))
        
        if not dfs:
            return f"결과: {md_file_path_or_content} 파일 내에서 변환할 표(Table)를 찾지 못했습니다."

        # # excel_file_path가 None(또는 미지정)인 경우 dfs 상단 또는 마크다운에서 crew_name 추출
        # if excel_file_path is None or str(excel_file_path).strip().lower() in ("", "none"):
        #     crew_name = None

        #     # 1. md_text 본문 상단에서 탐색
        #     if md_text:
        #         m = re.search(r"[`'\"]?crew_name[`'\"]?\s*[:=]\s*[`'\"]?([a-zA-Z0-9_\-\.]+)[`'\"]?", md_text, re.IGNORECASE)
        #         if m:
        #             crew_name = m.group(1).strip()

        #     # 2. dfs(DataFrame) 내에서 crew_name : xxxxx 탐색
        #     if not crew_name and dfs:
        #         for df in dfs:
        #             # 1-1. 컬럼명에서 탐색 (예: 'crew_name : xxxxx' 또는 'crew_name')
        #             for col in df.columns:
        #                 col_str = str(col).strip()
        #                 m = re.search(r"crew_name\s*[:=]\s*([^\s,'\"]+)", col_str, re.IGNORECASE)
        #                 if m:
        #                     crew_name = m.group(1).strip()
        #                     break
        #                 if col_str.lower() == "crew_name":
        #                     series = df[col].dropna()
        #                     if not series.empty:
        #                         val = str(series.iloc[0]).strip()
        #                         if ":" in val:
        #                             val = val.split(":", 1)[1].strip()
        #                         crew_name = val.strip("'\" ")
        #                         break
        #             if crew_name:
        #                 break

        #             # 1-2. 상단 행(row) 및 셀 값에서 탐색 (예: 'crew_name : xxxxx' 또는 'crew_name' 셀)
        #             for _, row in df.head(5).iterrows():
        #                 vals = [str(v).strip() for v in row.values if pd.notna(v)]
        #                 for i, cell in enumerate(vals):
        #                     m = re.search(r"crew_name\s*[:=]\s*([^\s,'\"]+)", cell, re.IGNORECASE)
        #                     if m:
        #                         crew_name = m.group(1).strip()
        #                         break
        #                     if cell.lower() == "crew_name" and i + 1 < len(vals):
        #                         crew_name = vals[i + 1].strip("'\" ")
        #                         break
        #                 if crew_name:
        #                     break
        #             if crew_name:
        #                 break

        #     # 3. crew_name을 파일명으로 하는 excel_file_path 설정
        #     target_name = crew_name or "crew_spec"
        #     if not target_name.endswith(".xlsx"):
        #         target_name = f"{target_name}.xlsx"

        #     base_dir = os.path.dirname(md_file_path_or_content) if (
        #         isinstance(md_file_path_or_content, str)
        #         and len(md_file_path_or_content) < 255
        #         and os.path.exists(md_file_path_or_content)
        #     ) else "./output"
        #     base_dir = base_dir or "./output"

        #     if os.path.dirname(target_name):
        #         excel_file_path = target_name
        #     else:
        #         excel_file_path = os.path.join(base_dir, target_name)

        # 디렉토리 확인 및 생성
        target_dir = os.path.dirname(excel_file_path) or '.'
        os.makedirs(target_dir, exist_ok=True)
        
        # 기존 xlsx 파일들 모두 삭제 (이전 실행 잔여 파일 정리 후 본작업 진행)
        cleanup_dirs = set()
        if target_dir not in ('.', '', '/'):
            cleanup_dirs.add(os.path.abspath(target_dir))
        if os.path.isdir("./output"):
            cleanup_dirs.add(os.path.abspath("./output"))
        if os.path.isdir("output"):
            cleanup_dirs.add(os.path.abspath("output"))

        for c_dir in cleanup_dirs:
            if os.path.exists(c_dir):
                for p in Path(c_dir).rglob("*.xlsx"):
                    if p.is_file():
                        try:
                            p.unlink()
                        except Exception:
                            pass

        if os.path.exists(excel_file_path):
            try:
                os.remove(excel_file_path)
            except Exception:
                pass

        # 엑셀로 저장
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
            for i, df in enumerate(dfs):
                sheet_name = f'Sheet{i+1}'
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        return f"성공: 마크다운 파일을 엑셀 파일로 변환 완료. (저장위치: {excel_file_path})"
        
    except ValueError:
        return "오류: pandas가 HTML에서 표를 추출하는 데 실패했습니다. 파일 포맷을 확인하세요."
    except Exception as e:
        return f"변환 중 알 수 없는 오류 발생: {str(e)}"
