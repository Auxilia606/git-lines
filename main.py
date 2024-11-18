import os
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Git 저장소 경로 설정
repo_path = "C:/Users/auxil/Documents/portal-frontend"
contributions = defaultdict(int)

# 제외할 파일 확장자 목록
# 이미지, 폰트, json 등 RAW데이터는 제외하기
excluded_extensions = {".jpg", ".svg", '.png', '.otf', '.ttf', '.woff2', '.json'}

def is_git_repository(path):
    return os.path.isdir(os.path.join(path, ".git"))

def get_all_files(repo_path):
    result = subprocess.run(["git", "ls-files"], cwd=repo_path, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", check=True)
    all_files = result.stdout.splitlines()
    
    # 특정 확장자를 제외한 파일 목록 생성
    filtered_files = [file for file in all_files if not any(file.endswith(ext) for ext in excluded_extensions)]
    return filtered_files

def analyze_file(file_path):
    try:
        result = subprocess.run(["git", "blame", "--line-porcelain", file_path],
                                cwd=repo_path, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", check=True)
        lines = result.stdout.splitlines()
        
        local_contributions = defaultdict(int)
        for line in lines:
            if line.startswith("author "):
                author = line.split("author ", 1)[1].strip()
                local_contributions[author] += 1

        return local_contributions
    except subprocess.CalledProcessError:
        print(f"Error analyzing file: {file_path}")
        return {}

def analyze_repo(repo_path):
    if not is_git_repository(repo_path):
        print(f"Error: {repo_path} is not a valid Git repository.")
        return

    files = get_all_files(repo_path)

    # 진행 바 설정
    with tqdm(total=len(files), desc="Analyzing files", unit="file") as progress_bar:
        # 병렬로 분석
        with ThreadPoolExecutor() as executor:
            for local_contributions in executor.map(analyze_file, files):
                # 각 파일의 기여도 누적
                for author, count in local_contributions.items():
                    contributions[author] += count
                
                # 진행 바 업데이트
                progress_bar.update(1)

    # 최종 결과 출력
    print("\nFinal contributions:")
    for author, line_count in contributions.items():
        print(f"{author}: {line_count} lines")

if __name__ == "__main__":
    analyze_repo(repo_path)
