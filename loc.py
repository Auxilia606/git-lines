import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
from datetime import datetime
import matplotlib.pyplot as plt

# Configure Matplotlib for Korean font
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False    # Fix minus sign issue with Korean

# Initialize variables
selected_directory = None
excluded_extensions = ['.svg', '.png', '.jpg', '.gif', '.otf', '.ttf', '.woff2', '.json']

# Function to browse directory
def browse_directory():
    global selected_directory
    selected_directory = filedialog.askdirectory()
    if selected_directory:
        dir_label.config(text=f"Selected Directory: {selected_directory}")

# Function to analyze cumulative LOC by unified accounts
def analyze_git_by_unified_account():
    if not selected_directory:
        messagebox.showerror("Error", "Please select a directory first.")
        return

    try:
        result = subprocess.check_output(
            ["git", "log", "--pretty='%aN|%ae|%cd'", "--numstat", "--date=iso"],
            cwd=selected_directory,
            text=True,
            encoding="utf-8",
            env={**os.environ, "LC_ALL": "C.UTF-8"}
        )
        cumulative_data = parse_git_log_by_unified_account(result)
        plot_cumulative_loc_by_account(cumulative_data)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to analyze Git repository: {e}")

# Function to parse Git log and unify accounts
def parse_git_log_by_unified_account(git_log):
    account_date_loc_data = {}
    account_mapping = {}  # Map email/nickname to unified account
    lines = git_log.splitlines()
    current_account = None
    current_date = None

    for line in lines:
        if "|" in line and line.startswith("'"):  # Author and date line
            parts = line.strip("'").split("|")
            nickname = parts[0].strip()
            email = parts[1].strip()
            current_date = datetime.strptime(parts[2].strip(), "%Y-%m-%d %H:%M:%S %z").date()

            # Determine unified account
            unified_account = account_mapping.get(nickname) or account_mapping.get(email)
            if not unified_account:
                unified_account = f"{nickname} ({email})"
                account_mapping[nickname] = unified_account
                account_mapping[email] = unified_account

            current_account = unified_account
            if current_account not in account_date_loc_data:
                account_date_loc_data[current_account] = {}
            if current_date not in account_date_loc_data[current_account]:
                account_date_loc_data[current_account][current_date] = 0
        elif current_account and current_date and "\t" in line:  # File change stats
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            file_name = parts[2]
            if any(file_name.endswith(ext) for ext in excluded_extensions):
                continue
            try:
                added = int(parts[0])
                deleted = int(parts[1])
                account_date_loc_data[current_account][current_date] += (added - deleted)
            except ValueError:
                pass

    # Compute cumulative LOC per unified account
    cumulative_data = {}
    for account, date_loc_data in account_date_loc_data.items():
        sorted_dates = sorted(date_loc_data.keys())
        cumulative_loc = 0
        cumulative_data[account] = {}
        for date in sorted_dates:
            cumulative_loc += date_loc_data[date]
            cumulative_data[account][date] = cumulative_loc

    return cumulative_data

# Function to plot cumulative LOC by unified accounts
def plot_cumulative_loc_by_account(cumulative_data):
    plt.figure(figsize=(12, 8))
    
    for account, date_loc in cumulative_data.items():
        dates = list(date_loc.keys())
        loc_values = list(date_loc.values())
        line, = plt.plot(dates, loc_values, marker='o', linestyle='-', label=account)
    
    plt.title("계정별 누적 LOC 변화", fontsize=14)
    plt.xlabel("날짜", fontsize=12)
    plt.ylabel("누적 LOC", fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title="계정", loc="upper left", fontsize=10)
    plt.tight_layout()
    plt.grid(True)
    plt.show()



# Initialize GUI
root = tk.Tk()
root.title("Git LOC Analyzer")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

browse_button = tk.Button(frame, text="Browse...", command=browse_directory)
browse_button.grid(row=0, column=0, padx=5, pady=5)

dir_label = tk.Label(frame, text="Selected Directory: None", anchor="w")
dir_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

account_loc_button = tk.Button(frame, text="계정별 누적 LOC 분석", command=analyze_git_by_unified_account)
account_loc_button.grid(row=1, column=0, columnspan=2, pady=10)

root.mainloop()
