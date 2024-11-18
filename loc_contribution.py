import subprocess
from collections import defaultdict
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askdirectory

def browse_directory():
    """
    파일 탐색기를 열어 Git 저장소 경로를 선택.
    """
    root = Tk()
    root.withdraw()  # GUI 창 숨기기
    root.attributes('-topmost', True)  # 파일 탐색기가 맨 앞으로 오도록 설정
    selected_directory = askdirectory(title="Select Git Repository")
    if not selected_directory:
        print("No directory selected. Exiting.")
        exit(1)
    return selected_directory

def get_git_log(repo_path):
    """
    Git 로그에서 커밋별 통계 추출.
    """
    # Git 저장소 이동
    subprocess.run(["git", "-C", repo_path, "fetch"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # git log로 통계 추출
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "--numstat", "--pretty=format:'%an'"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'  # 인코딩 설정
    )
    if result.returncode != 0:
        print(f"Error running git log: {result.stderr}")
        return None
    return result.stdout

def parse_git_log(log_data, excluded_extensions=None):
    """
    Git 로그 데이터를 파싱해 사용자별 LOC 통계 계산.
    특정 파일 형식을 제외할 수 있음.
    """
    if excluded_extensions is None:
        excluded_extensions = []

    lines = log_data.split("\n")
    contributions = defaultdict(lambda: {"added": 0, "deleted": 0})
    current_author = None

    for line in lines:
        if line.startswith("'") and line.endswith("'"):
            current_author = line.strip("'")
        elif current_author and line:
            parts = line.split("\t")
            if len(parts) == 3:  # 추가/삭제/파일명 데이터
                filename = parts[2]
                if any(filename.endswith(ext) for ext in excluded_extensions):
                    continue  # 제외할 파일 형식이면 스킵
                try:
                    added = int(parts[0])
                    deleted = int(parts[1])
                    contributions[current_author]["added"] += added
                    contributions[current_author]["deleted"] += deleted
                except ValueError:
                    continue  # 이진 파일 등은 스킵

    return contributions

if __name__ == "__main__":
    print("Select the Git repository using the file browser...")
    repo_path = browse_directory()
    print(f"Selected repository: {repo_path}")
    print("Fetching Git log...")
    log_data = get_git_log(repo_path)
    if log_data is None:
        print("Failed to retrieve Git log.")
        exit(1)
    
    # 제외할 파일 확장자 리스트 설정
    excluded_extensions = ['.svg', '.png', '.jpg', '.gif', '.otf', '.ttf', '.woff2', '.json']
    print(f"Excluding files with extensions: {', '.join(excluded_extensions)}")

    print("Parsing contributions...")
    contributions = parse_git_log(log_data, excluded_extensions)
    print("Plotting contributions...")
    plot_contributions(contributions)

def plot_contributions(contributions):
    """
    사용자별 LOC 기여도를 시각화.
    """
    authors = contributions.keys()
    added_lines = [data["added"] for data in contributions.values()]
    deleted_lines = [data["deleted"] for data in contributions.values()]

    # 막대 그래프 출력
    plt.figure(figsize=(10, 6))
    bar_width = 0.35
    index = range(len(authors))

    plt.bar(index, added_lines, bar_width, label="Added Lines")
    plt.bar(index, deleted_lines, bar_width, bottom=added_lines, label="Deleted Lines")

    plt.xlabel("Authors")
    plt.ylabel("LOC")
    plt.title("Contributions by LOC")
    plt.xticks(index, authors, rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("Select the Git repository using the file browser...")
    repo_path = browse_directory()
    print(f"Selected repository: {repo_path}")
    print("Fetching Git log...")
    log_data = get_git_log(repo_path)
    if log_data is None:
        print("Failed to retrieve Git log.")
        exit(1)
    print("Parsing contributions...")
    contributions = parse_git_log(log_data)
    print("Plotting contributions...")
    plot_contributions(contributions)
