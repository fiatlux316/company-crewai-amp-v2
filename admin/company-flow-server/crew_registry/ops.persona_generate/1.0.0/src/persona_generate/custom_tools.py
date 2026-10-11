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
        resolved_path = None
        if len(md_file_path_or_content) < 255:
            candidate_paths = [
                Path(md_file_path_or_content),
                Path(os.getcwd()) / md_file_path_or_content,
                Path("./output") / Path(md_file_path_or_content).name,
                Path(__file__).parent.parent.parent / "output" / Path(md_file_path_or_content).name,
                Path("./output") / "{persona_name}.md",
                Path(__file__).parent.parent.parent / "output" / "{persona_name}.md",
            ]
            for cp in candidate_paths:
                if cp.exists() and cp.is_file():
                    resolved_path = cp
                    break

        if resolved_path:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                md_text = f.read()
        elif (md_file_path_or_content.strip().endswith(".md") or md_file_path_or_content.strip().startswith("./") or "/" in md_file_path_or_content) and "\n" not in md_file_path_or_content:
            return f"오류: 마크다운 파일 '{md_file_path_or_content}'을(를) 찾을 수 없습니다. 경로를 확인하세요."
        else:
            md_text = md_file_path_or_content

        # HTML로 파싱
        html_text = markdown.markdown(md_text, extensions=['tables'])

        # pandas로 html 내의 table 추출
        dfs = pd.read_html(io.StringIO(html_text))
        
        if not dfs:
            return f"결과: {md_file_path_or_content} 파일 내에서 변환할 표(Table)를 찾지 못했습니다."

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
                
        # deployed/output 폴더에도 복사 보장 (worker 아티팩트 수집 경로)
        try:
            deployed_output = Path(__file__).parent.parent.parent / "output" / Path(excel_file_path).name
            if deployed_output.resolve() != Path(excel_file_path).resolve():
                deployed_output.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(excel_file_path, deployed_output)
        except Exception:
            pass

        return f"성공: 마크다운 파일을 엑셀 파일로 변환 완료. (저장위치: {excel_file_path})"
        
    except ValueError:
        return "오류: pandas가 HTML에서 표를 추출하는 데 실패했습니다. 파일 포맷을 확인하세요."
    except Exception as e:
        return f"변환 중 알 수 없는 오류 발생: {str(e)}"