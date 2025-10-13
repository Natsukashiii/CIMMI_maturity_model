import hashlib
import os
import pickle
from collections import defaultdict
from datetime import datetime
from scipy.stats import spearmanr, kruskal
import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from dotenv import load_dotenv

from src.python.entities.RateLimitException import RateLimitException
from src.python.extractor.Utilities import (add_joker, get_lowest_level,
                                            get_maturity_levels,
                                            get_report_per_level)
from src.python.results.AutomationReporter import (
    check_and_report_automations, parse_markdown_to_domain)

load_dotenv()
github_token = os.getenv("GITHUB_ISSUE_TOKEN")
headers = {
    "Authorization": f"token {github_token}",
}

with open("../data/rq1_java_repos.txt") as file:
    repos = [line.strip() for line in file if line.strip()]
with open("../data/rq1_python_repos.txt") as file:
    repos.extend([line.strip() for line in file if line.strip()])
with open("../output/automations_dict.pkl", "rb") as file:
    domains = parse_markdown_to_domain("../data/automations.md")
    report = check_and_report_automations(repos, domains, pickle.load(file))


def generate_subdomains_plot():
    with open("../data/results.pkl", "rb") as f:
        main_domains = pickle.load(f)

    data = []
    for main_domain in main_domains:
        for sub_domain in main_domain.child:
            data.append(
                {
                    "Domain": main_domain.name,
                    "Subdomain": sub_domain.name,
                    "Count": sub_domain.count,
                }
            )

    df = pd.DataFrame(data)
    total_count = 7376
    df["Percentage"] = (df["Count"] / total_count) * 100
    df = df.sort_values(by=["Domain", "Count"], ascending=[True, False])

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, y="Subdomain", x="Percentage", hue="Domain", orient="h")
    plt.xticks(rotation=45, ha="right", fontsize=16)
    plt.yticks(fontsize=16)
    plt.xlim(0, df["Percentage"].max() + 5)
    plt.legend(fontsize=16)  # You can change 12 to any size you
    plt.xlabel("Percentage (%)", fontsize=14)
    plt.ylabel("Subdomains", fontsize=14)
    plt.tight_layout()
    plt.savefig("../data/plots/percentage_graph.pdf")
    plt.clf()


def generate_tasks_plot():
    with open("../data/results.pkl", "rb") as f:
        main_domains = pickle.load(f)

    data = []
    for main_domain in main_domains:
        for sub_domain in main_domain.child:
            for task in sub_domain.child:
                data.append(
                    {
                        "Domain": main_domain.name,
                        "Subdomain": sub_domain.name,
                        "Task": task.name,
                        "Count": task.count,
                    }
                )

    df = pd.DataFrame(data)
    total_count = 7376
    df["Percentage"] = (df["Count"] / total_count) * 100
    df = df.sort_values(
        by=["Domain", "Subdomain", "Count"], ascending=[True, True, False]
    )

    domain_colors = {
        "Artifacts": "steelblue",
        "Code quality": "darkorange",
        "Collaboration": "forestgreen",
        "Development": "red",
    }

    plt.figure(figsize=(11, 10))  # Adjust size as needed

    palette = {}
    for domain, base_color in domain_colors.items():
        domain_subdomains = df[df["Domain"] == domain]["Subdomain"].unique()
        shades = sns.blend_palette(
            [sns.dark_palette(base_color, 3)[1], base_color],
            n_colors=len(domain_subdomains),
        )
        for subdomain, shade in zip(domain_subdomains, shades):
            palette[subdomain] = shade

    ax = sns.barplot(
        data=df,
        y="Task",
        x="Percentage",
        hue="Subdomain",
        palette=palette,
        orient="h",
        dodge=False,  # Important for having all bars in one line
    )

    # Find the positions where domains change
    y_tick_labels = ax.get_yticklabels()
    domain_boundaries = []
    current_domain = None
    for i, label in enumerate(y_tick_labels):
        task_name = label.get_text()
        task_domain = df[df["Task"] == task_name]["Domain"].iloc[0]
        if task_domain != current_domain:
            domain_boundaries.append(i - 0.5)
            current_domain = task_domain

    # Add horizontal lines between domains
    for boundary in domain_boundaries[1:]:  # Skip the first one
        ax.axhline(boundary, color="gray", linestyle="--", linewidth=0.5)

    # Add domain labels on the right side
    current_domain = None
    right_side = ax.get_xlim()[1] * 1.12  # Position right of the bars
    for i, label in enumerate(y_tick_labels):
        task_name = label.get_text()
        task_domain = df[df["Task"] == task_name]["Domain"].iloc[0]
        if task_domain != current_domain:
            # Position the label between the first and last task of the domain
            ax.text(
                right_side,
                i,
                task_domain,
                va="top",
                ha="right",
                fontweight="bold",
                color=domain_colors[task_domain],
            )
            current_domain = task_domain

    plt.yticks(rotation=0, ha="right", fontsize=10)
    plt.xticks(fontsize=10)
    plt.xlabel("Percentage (%)", fontsize=12)
    plt.ylabel("Tasks", fontsize=12)
    plt.xlim(0, df["Percentage"].max() * 1.2)
    plt.legend(title="Subdomain", loc=(0.68, 0.75))
    plt.tight_layout()
    plt.savefig("../data/plots/all_freqs.pdf")
    plt.clf()


def send_request(url: str, headers):
    filename_url = hashlib.sha256(url.encode()).hexdigest() + ".pkl"
    file_path = os.path.join("../requests", filename_url)
    old_filename_url = url.replace("/", "*") + ".pkl"
    old_file_path = os.path.join("../requests", old_filename_url)

    # Check if the file exists at the specified path
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    elif os.path.exists(old_file_path):
        with open(old_file_path, "rb") as f:
            return pickle.load(f)
    else:
        response = requests.get(url, headers=headers)
        if response.status_code == 403 or response.status_code == 429:
            raise RateLimitException(f"Rate limit exceeded on {url}")

        with open(file_path, "wb") as f:
            pickle.dump(response, f)
        return response


def fetch_commit_frequency(repo_full_name):
    # Fetch commits from the last year (adjust timeframe as needed)
    url = f"https://api.github.com/repos/{repo_full_name}/commits?since=2023-01-01T00:00:00Z"
    response = send_request(url, headers)

    if response.status_code != 200:
        print(f"Error fetching commits for {repo_full_name}: {response.status_code}")
        return None

    commits = response.json()
    commit_dates = [
        datetime.strptime(c["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
        for c in commits
        if c.get("commit")
    ]

    if not commit_dates:
        return 0  # No commits

    # Calculate commits per month (adjust to "weeks" if preferred)
    days_elapsed = (datetime.utcnow() - min(commit_dates)).days
    months_elapsed = max(days_elapsed / 30, 1)  # Avoid division by zero
    return len(commit_dates) / months_elapsed


def fetch_repo_info(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}"
    response = send_request(url, headers)

    if response.status_code != 200:
        print(f"Error fetching {repo_full_name}: {response.status_code}")
        return None
    commit_freq = fetch_commit_frequency(repo_full_name)
    data = response.json()

    created_at = data.get("created_at")
    if created_at:
        created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        age_years = (datetime.utcnow() - created_date).days / 365.25
    else:
        age_years = None

    return {
        "Stars": data.get("stargazers_count", 0),
        "Forks": data.get("forks_count", 0),
        "AgeYears": age_years,
        "CommitsPerMonth": commit_freq,
        "OpenIssues": data.get("open_issues_count", 0),
    }


def get_maturity_df():
    repo_scores = dict()
    for repo in repos:
        maturity_levels = get_maturity_levels(report[repo])
        joker_score = add_joker(get_report_per_level(report[repo]), maturity_levels)
        lowest = get_lowest_level(joker_score)
        if lowest == 0:
            repo_scores[repo] = "None"
        elif lowest == 1:
            repo_scores[repo] = "Basic"
        elif lowest == 2:
            repo_scores[repo] = "Intermediate"
        elif lowest == 3:
            repo_scores[repo] = "Advanced"

    records = []
    for repo, score in repo_scores.items():
        info = fetch_repo_info(repo)
        if info:
            records.append({"Repo": repo, "Maturity": score, **info})

    return pd.DataFrame(records).dropna()


def generate_violin_plots():
    df = get_maturity_df()
    maturity_order = ["None", "Basic", "Intermediate"]
    df["Maturity"] = pd.Categorical(
        df["Maturity"], categories=maturity_order, ordered=True
    )
    present_levels = df["Maturity"].unique().tolist()

    df["Maturity"] = pd.Categorical(
        df["Maturity"], categories=present_levels, ordered=True
    )

    plt.figure(figsize=(6, 5))
    sns.violinplot(data=df, x="Maturity", y="Stars")
    means = (
        df.groupby("Maturity")["Stars"]
        .median()
        .reindex(["None", "Basic", "Intermediate"])
    )
    plt.plot(
        means.index,
        means.values,
        marker="none",
        color="darkorange",
        linewidth=1,
        label="Median Trend",
    )
    plt.legend()
    plt.ylim(bottom=0, top=3000)  # optional: cap y-axis if needed
    plt.ylabel("Stars", fontsize=14)
    plt.xlabel("Maturity", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig("../data/plots/stars.pdf")
    plt.clf()
    print(means)

    plt.figure(figsize=(6, 5))
    sns.violinplot(data=df, x="Maturity", y="CommitsPerMonth")
    means = (
        df.groupby("Maturity")["CommitsPerMonth"]
        .median()
        .reindex(["None", "Basic", "Intermediate"])
    )
    plt.ylim(bottom=0)
    plt.plot(
        means.index,
        means.values,
        marker="none",
        color="darkorange",
        linewidth=1,
        label="Median Trend",
    )
    plt.legend()
    plt.ylabel("Commits per month", fontsize=14)
    plt.xlabel("Maturity", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig("../data/plots/commit_frequency.pdf")
    plt.clf()
    print(means)

    plt.figure(figsize=(6, 5))
    sns.violinplot(data=df, x="Maturity", y="Forks")
    means = (
        df.groupby("Maturity")["Forks"]
        .median()
        .reindex(["None", "Basic", "Intermediate"])
    )
    plt.plot(
        means.index,
        means.values,
        marker="none",
        color="darkorange",
        linewidth=1,
        label="Median Trend",
    )
    plt.legend()
    plt.ylim(bottom=0, top=900)  # Adjust y-axis as needed
    plt.ylabel("Forks", fontsize=14)
    plt.xlabel("Maturity", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig("../data/plots/forks.pdf")
    plt.clf()
    print(means)

    means = (
        df.groupby("Maturity")["OpenIssues"]
        .median()
        .reindex(["None", "Basic", "Intermediate"])
    )

    plt.figure(figsize=(6, 5))
    plt.plot(
        means.index,
        means.values,
        marker="none",
        color="darkorange",
        linewidth=1,
        label="Median trend",
    )
    plt.legend()
    sns.violinplot(data=df, x="Maturity", y="OpenIssues")
    plt.ylabel("Open issues", fontsize=14)
    plt.xlabel("Maturity", fontsize=14)
    plt.ylim(top=200)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(bottom=0)
    plt.tight_layout()
    plt.savefig("../data/plots/openissues.pdf")
    plt.clf()
    print(means)

    filtered_df = df[df["AgeYears"] <= 5]
    means = (
        filtered_df.groupby("Maturity")["AgeYears"]
        .median()
        .reindex(["None", "Basic", "Intermediate"])
    )

    plt.figure(figsize=(6, 5))
    plt.plot(
        means.index,
        means.values,
        marker="none",
        color="darkorange",
        linewidth=1,
        label="Median trend",
    )
    plt.legend()
    sns.violinplot(data=filtered_df, x="Maturity", y="AgeYears")
    plt.ylabel("Age (years)", fontsize=14)
    plt.xlabel("Maturity", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(bottom=0)
    plt.tight_layout()
    plt.savefig("../data/plots/age.pdf")
    plt.clf()
    print(means)

    # Kruskal
    def kruskal_attr(attribute):
        statistic, pvalue = kruskal(
            df[df["Maturity"] == "None"][attribute],
            df[df["Maturity"] == "Basic"][attribute],
            df[df["Maturity"] == "Intermediate"][attribute]
        )
        print(f"Kruskal-Wallis test for {attribute}: statistic={statistic:.3f}, p-value={pvalue:.4f}")

    for attr in df.columns[2:7]:
        kruskal_attr(attr)

def generate_top_bottom_plot():
    df = get_maturity_df()
    top_1_threshold = df["Stars"].quantile(0.99)
    bottom_10_threshold = df["Stars"].quantile(0.10)
    top_1_repos = df[df["Stars"] >= top_1_threshold]["Repo"]
    bottom_10_repos = df[df["Stars"] <= bottom_10_threshold]["Repo"]

    def filter_report_by_repos(report, repo_subset):
        return {repo: report[repo] for repo in repo_subset if repo in report}

    def parse_report_to_domains(filtered_report, all_domains):
        # Count (domain, subdomain) occurrences
        pair_counts = defaultdict(int)
        for repo in filtered_report.values():
            for domain in repo.values():
                for subdomain, tasks in domain.items():
                    if any(task == "Yes" for task in tasks.values()):
                        pair_counts[subdomain.name] += 1

        return pair_counts

    top_report = filter_report_by_repos(report, top_1_repos)
    bottom_report = filter_report_by_repos(report, bottom_10_repos)

    top_domains = parse_report_to_domains(top_report, domains)
    bottom_domains = parse_report_to_domains(bottom_report, domains)
    sub_to_domain = {}
    for domain in domains:
        for sub in domain.child:
            sub_to_domain[sub.name] = domain.name

    def subdomain_counts_to_df(
        subdomain_counts: dict, total_repos: int, sub_to_domain: dict
    ):
        df = pd.DataFrame(
            [
                {
                    "Subdomain": name,
                    "Count": count,
                    "Percentage": (count / total_repos) * 100,
                    "Domain": sub_to_domain.get(name, "Unknown"),
                }
                for name, count in subdomain_counts.items()
            ]
        )
        return df.sort_values(by=["Domain", "Subdomain"], ascending=[True, True])

    top_df = subdomain_counts_to_df(top_domains, len(top_1_repos), sub_to_domain)
    bottom_df = subdomain_counts_to_df(
        bottom_domains, len(bottom_10_repos), sub_to_domain
    )
    top_df["Group"] = "Top 1%"
    bottom_df["Group"] = "Bottom 10%"
    combined_df = pd.concat([top_df, bottom_df], ignore_index=True)
    custom_palette = {
        "Top 1%": "#E49C44",
        "Bottom 10%": "#74A2C7",
    }
    plt.figure(figsize=(12, 6))

    # Create a unique y-axis label combining Subdomain and Group
    combined_df["Subdomain_Group"] = combined_df.apply(
        lambda row: f"{row['Subdomain']} - {row['Group']}", axis=1
    )
    combined_df["Subdomain"] = combined_df["Subdomain"].astype(str)
    combined_df["Group"] = pd.Categorical(
        combined_df["Group"], categories=["Top 1%", "Bottom 10%"]
    )
    combined_df.sort_values(by=["Subdomain", "Group"], inplace=True)
    pivot_df = combined_df.pivot(
        index="Subdomain", columns="Group", values="Percentage"
    ).reset_index()
    melted_df = pivot_df.melt(
        id_vars="Subdomain",
        value_vars=["Top 1%", "Bottom 10%"],
        var_name="Group",
        value_name="Percentage",
    )

    sorted_order = pivot_df.sort_values(by="Top 1%", ascending=False)["Subdomain"]
    melted_df["Subdomain"] = pd.Categorical(
        melted_df["Subdomain"], categories=sorted_order, ordered=True
    )

    sns.barplot(
        data=melted_df,
        y="Subdomain",
        x="Percentage",
        hue="Group",
        palette=custom_palette,
        orient="h",
    )

    plt.legend(fontsize=14)  # You can change 12 to any size you
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xlim(0, 70)
    plt.xlabel("Percentage", fontsize=14)
    plt.ylabel("Subdomain", fontsize=14)
    plt.tight_layout()
    plt.savefig("../data/plots/top1vsbottom10.pdf")
    plt.clf()


if __name__ == "__main__":
    generate_tasks_plot()
    generate_subdomains_plot()
    generate_violin_plots()
    generate_top_bottom_plot()
