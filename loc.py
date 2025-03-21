import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.dates import date2num, num2date
import numpy as np


plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

selected_directory = None
excluded_extensions = ['.svg', '.png', '.jpg', '.gif', '.otf', '.ttf', '.woff2', '.json']

def browse_directory():
    global selected_directory
    selected_directory = filedialog.askdirectory()
    if selected_directory:
        dir_label.config(text=f"Selected Directory: {selected_directory}")

def parse_git_log_by_unified_account(git_log):
    account_date_data = {}
    account_mapping = {}
    lines = git_log.splitlines()
    current_account = None
    current_date = None

    for line in lines:
        if "|" in line and line.startswith("'"):
            parts = line.strip("'").split("|")
            nickname = parts[0].strip()
            email = parts[1].strip()
            current_date = datetime.strptime(parts[2].strip(), "%Y-%m-%d %H:%M:%S %z").date()

            unified_account = account_mapping.get(nickname) or account_mapping.get(email)
            if not unified_account:
                unified_account = f"{nickname} ({email})"
                account_mapping[nickname] = unified_account
                account_mapping[email] = unified_account

            current_account = unified_account
            if current_account not in account_date_data:
                account_date_data[current_account] = {}
            if current_date not in account_date_data[current_account]:
                account_date_data[current_account][current_date] = {'added': 0, 'deleted': 0}
        elif current_account and current_date and "\t" in line:
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            file_name = parts[2]
            if any(file_name.endswith(ext) for ext in excluded_extensions):
                continue
            try:
                added = int(parts[0])
                deleted = int(parts[1])
                account_date_data[current_account][current_date]['added'] += added
                account_date_data[current_account][current_date]['deleted'] += deleted
            except ValueError:
                pass

    cumulative_data = {}
    for account, date_data in account_date_data.items():
        sorted_dates = sorted(date_data.keys())
        cumulative_loc = 0
        cumulative_data[account] = {}
        for date in sorted_dates:
            added = date_data[date]['added']
            deleted = date_data[date]['deleted']
            cumulative_loc += (added - deleted)
            cumulative_data[account][date] = cumulative_loc

    return cumulative_data, account_date_data

def plot_combined_line_with_bars(cumulative_data, account_date_data):
    import matplotlib.pyplot as plt
    from datetime import date

    all_dates = sorted({d for data in account_date_data.values() for d in data})
    date_nums = date2num(all_dates)
    bar_width = 1.0

    fig, ax = plt.subplots(figsize=(16, 8))

    for account, date_loc in cumulative_data.items():
        dates = sorted(date_loc.keys())
        loc_values = [date_loc[d] for d in dates]
        ax.plot(dates, loc_values, marker='o', label=account)

        added_list = []
        deleted_list = []
        x_list = []
        bottom_list = []

        for d in dates:
            added = account_date_data[account][d]['added']
            deleted = account_date_data[account][d]['deleted']
            cum_loc = date_loc[d]

            x = date2num(d)
            x_list.append(x)
            added_list.append(added)
            deleted_list.append(deleted)
            bottom_list.append(cum_loc)

        # 위로 막대 (추가)
        ax.bar(x_list, added_list, width=0.3, bottom=bottom_list,
               color='skyblue', alpha=0.6, label=f"{account} - 추가")

        # 아래로 막대 (삭제)
        ax.bar(x_list, [-v for v in deleted_list], width=0.3, bottom=bottom_list,
               color='salmon', alpha=0.6, label=f"{account} - 삭제")

    ax.set_title("계정별 누적 LOC + 추가/삭제 라인수", fontsize=14)
    ax.set_ylabel("라인 수")
    ax.set_xticks(date_nums)
    ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in all_dates], rotation=45, ha='right')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    ax.yaxis.set_major_formatter(mticker.ScalarFormatter(useMathText=False))
    ax.ticklabel_format(style='plain', axis='y')
    ax.yaxis.offsetText.set_visible(False)
    ax.grid(True)
    ax.legend(ncol=2, fontsize=9)
    ax.format_coord = lambda x, y: f"x={mdates.num2date(x).date()}, y={int(y):,}"

    plt.tight_layout()
    plt.show()

def analyze_combined_chart_single_axis():
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
        cumulative_data, account_date_data = parse_git_log_by_unified_account(result)
        plot_combined_line_with_bars(cumulative_data, account_date_data)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Git 분석 실패: {e}")

# GUI
root = tk.Tk()
root.title("Git LOC Analyzer")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

browse_button = tk.Button(frame, text="Browse...", command=browse_directory)
browse_button.grid(row=0, column=0, padx=5, pady=5)

dir_label = tk.Label(frame, text="Selected Directory: None", anchor="w")
dir_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

combined_chart_button = tk.Button(frame, text="한 차트에 누적 + 추가/삭제", command=analyze_combined_chart_single_axis)
combined_chart_button.grid(row=1, column=0, columnspan=2, pady=5)

root.mainloop()
