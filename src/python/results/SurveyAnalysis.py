from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.cluster import KMeans

with open("../data/survey.csv") as f:
    df = pd.read_csv(f)
    code_quality = dict()
    artifacts = dict()
    collaboration = dict()
    development = dict()

    for column in df.columns:
        if column.startswith("Q6"):
            code_quality[df[column][0]] = df[column][2:].tolist()
        elif column.startswith("Q7"):
            collaboration[df[column][0]] = df[column][2:].tolist()
        elif column.startswith("Q8"):
            artifacts[df[column][0]] = df[column][2:].tolist()
        elif column.startswith("Q9"):
            development[df[column][0]] = df[column][2:].tolist()


def convert_scores_to_numeric(scores):
    score_mapping = {"Basic": 1, "Intermediate": 2, "Advanced": 3}
    numeric_scores = [score_mapping[score] for score in scores]
    return numeric_scores


def calculate_mean_scores(task_dict):
    mean_scores = {}
    for task, scores in task_dict.items():
        numeric_scores = convert_scores_to_numeric(scores)
        mean_scores[task] = np.mean(numeric_scores)
    return mean_scores


def calculate_weighted_average(task_dict):
    weighted_scores = {}
    for task, scores in task_dict.items():
        numeric_scores = convert_scores_to_numeric(scores)
        weighted_scores[task] = np.mean(numeric_scores)
    return weighted_scores


def perform_kmeans_clustering(mean_scores, domain_name):
    mean_scores_array = np.array(list(mean_scores.values()))

    k = 3  # Number of clusters
    kmeans = KMeans(n_clusters=k, random_state=0).fit(mean_scores_array.reshape(-1, 1))

    cluster_centers = kmeans.cluster_centers_
    labels = kmeans.labels_
    sorted_centers = np.argsort(cluster_centers.flatten())
    level_mapping = {
        sorted_centers[0]: "Basic",
        sorted_centers[1]: "Intermediate",
        sorted_centers[2]: "Advanced",
    }

    task_levels = {
        task: level_mapping[label] for task, label in zip(mean_scores.keys(), labels)
    }
    markers = ["o", "s", "^"]  # Circle, Square, Triangle
    cluster_markers = [markers[label] for label in labels]

    plt.figure(figsize=(10, 2), constrained_layout=True)
    xmin, xmax = min(mean_scores_array) - 0.1, max(mean_scores_array) + 0.1
    sorted_centers = np.sort(cluster_centers.flatten())

    boundaries = [
        xmin,
        (sorted_centers[0] + sorted_centers[1]) / 2,
        (sorted_centers[1] + sorted_centers[2]) / 2,
        xmax,
    ]

    plt.axvspan(
        boundaries[0], boundaries[1], color="lightblue", alpha=0.3, label="Basic"
    )
    plt.axvspan(
        boundaries[1], boundaries[2], color="khaki", alpha=0.3, label="Intermediate"
    )
    plt.axvspan(
        boundaries[2], boundaries[3], color="lightgreen", alpha=0.3, label="Advanced"
    )

    for score, marker, label in zip(mean_scores_array, cluster_markers, labels):
        plt.scatter(
            score, 0, c=plt.cm.viridis(label / k), marker=marker, s=100, edgecolors="k"
        )

    plt.scatter(
        cluster_centers,
        np.zeros_like(cluster_centers),
        c="red",
        marker="x",
        s=200,
        label="Cluster Centers",
    )
    plt.xlabel("Mean maturity score of task")
    plt.yticks([])  # Hide y-axis
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()
    plt.savefig(f"../data/plots/{domain_name.replace(" ", "")}.pdf")
    plt.clf()
    return task_levels


def calculate_wilcoxon(responses):
    mapping = {
        "Strongly agree": 5,
        "Somewhat agree": 4,
        "Neither agree or disagree": 3,
        "Somewhat disagree": 2,
        "Strongly disagree": 1,
    }
    numeric_responses = [mapping[response] for response in responses]
    stat, p = wilcoxon([x - 3 for x in numeric_responses])
    print(f"Wilcoxon test statistic: {stat}, p-value: {p}")


def statistics_education(column):
    education_map = {
        "Bachelor's degree": "Bachelor",
        "Master's degree": "Master",
        "Doctoral degree": "PhD",
        "I haven't graduated yet but am a student in a related field": "None (student)",
        "Other formal education or training (e.g. apprenticeship)": "Other",
    }
    column = column.replace(education_map)
    education_counts = column.value_counts(dropna=True)
    plt.figure(figsize=(6, 4))

    wedges, texts, autotexts = plt.pie(
        education_counts,
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.85,  # Distance of % labels from center
        labeldistance=1.1,  # Leader line length
    )

    plt.legend(
        wedges,
        education_counts.index,
        title="Education Levels",
        loc="center left",
        bbox_to_anchor=(0.9, 0.5),
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(10)

    plt.tight_layout()
    plt.show()


def statistics_years_industry(column):
    num = pd.to_numeric(column, errors="coerce")
    median_experience = num.dropna().median()
    print(f"Median years of experience: {median_experience}")

    bins = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, float("inf")]
    labels = [
        "0–1",
        "2–3",
        "4–5",
        "6–7",
        "8–9",
        "10–11",
        "12–13",
        "14–15",
        "16–17",
        "18–19",
        "20+",
    ]

    df["Experience_Binned"] = pd.cut(num, bins=bins, labels=labels, right=False)
    experience_counts = df["Experience_Binned"].value_counts().sort_index()

    plt.figure(figsize=(6, 5))
    experience_counts.plot(kind="bar")
    plt.xticks(rotation=45)
    plt.xlabel("Years of Experience", fontsize=14)
    plt.ylabel("Number of Respondents", fontsize=14)
    plt.tight_layout()
    plt.show()


def statistics_technologies_used(column):
    def map_other(item_list):
        return [
            "Other" if v == "another type of CI/CD or build automation" else v
            for v in item_list
        ]

    all_choices = column.dropna().apply(
        lambda x: [item.strip().replace("I've used ", "") for item in x.split(",")]
    )

    all_choices = all_choices.apply(map_other)
    choice_counts = Counter([choice for sublist in all_choices for choice in sublist])
    total = sum(choice_counts.values())
    choice_series = pd.Series({k: (v / total) * 100 for k, v in choice_counts.items()})
    choice_series = choice_series.sort_values(ascending=False).round(1)

    plt.figure(figsize=(5, 6))
    choice_series.plot(kind="bar")
    plt.ylabel("Percentage", fontsize=14)
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.tight_layout()
    plt.show()


def print_levels(domain_name, name_levels):
    print(f"\n{domain_name} Levels:")
    for task, level in sorted(
        name_levels.items(),
        key=lambda x: ["Basic", "Intermediate", "Advanced"].index(x[1]),
    ):
        name = task.split("-")[1].split("(")[0]
        print(f"{name}: {level}")


# Calculate weighted average scores for each category
code_quality_means = calculate_weighted_average(code_quality)
collaboration_means = calculate_weighted_average(collaboration)
artifacts_means = calculate_weighted_average(artifacts)
development_means = calculate_weighted_average(development)

# Perform k-means clustering for each category and assign levels
code_quality_levels = perform_kmeans_clustering(code_quality_means, "Code Quality")
collaboration_levels = perform_kmeans_clustering(collaboration_means, "Collaboration")
artifacts_levels = perform_kmeans_clustering(artifacts_means, "Artifacts")
development_levels = perform_kmeans_clustering(development_means, "Development")

for domain_name, levels in [
    ("Code Quality", code_quality_levels),
    ("Collaboration", collaboration_levels),
    ("Artifacts", artifacts_levels),
    ("Development", development_levels),
]:
    print_levels(domain_name, levels)

calculate_wilcoxon(df["Q10_1"][2:])
calculate_wilcoxon(df["Q11_1"][2:])

statistics_education(df["Q2"][2:])
statistics_years_industry(df["Q3"][2:])
statistics_technologies_used(df["Q4"][2:])
