import heapq
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

from src.python.entities.Automation import Level, Todo
from src.python.entities.RateLimitException import RateLimitException
from src.python.extractor.RepositoryDownloader import AutomationDownloader
from src.python.extractor.Utilities import (add_joker, download_files,
                                            get_average_level,
                                            get_lowest_level,
                                            get_maturity_levels,
                                            get_report_per_level)
from src.python.extractor.WorkflowAnalyzer import AutomationExtractor
from src.python.results.AutomationReporter import (
    check_and_report_automations, parse_markdown_to_domain)


def generate_radar_chart(repo, maturity_values, output_dir):
    values = [maturity_values[m].value for m in maturity_values.keys()]
    categories = ["Collaboration", "Code quality", "Development", "Artifacts"]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]  # Close the circle
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color="b", alpha=0.2)
    ax.plot(angles, values, color="b", linewidth=2)
    ax.set_yticks([0, 1, 2, 3])  # Adjust ticks to match maturity levels
    ax.set_yticklabels(["None", "Basic", "Intermediate", "Advanced"])  # Correct labels
    ax.yaxis.grid(True, linestyle="dashed", alpha=0.5)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    output_path = os.path.join(output_dir, f"{repo}_chart.pdf")
    plt.savefig(output_path, dpi=60, bbox_inches="tight")
    plt.close()


def get_link(name):
    return f"https://github.com/simchavos/automations/wiki/Automation-Thesis-Wiki#{name.replace(' ', '-')}"


def get_level_cell(domain, level, maturity_levels):
    if maturity_levels[domain] == level:
        return "‎ <br>✅ ***Completed this level!*** <br><br>"
    elif maturity_levels[domain] == Level.NONE and level == Level.BASIC:
        return "‎ <br>⚠️ ***Still working on this level!*** <br><br>"
    return ""


def get_tasks_cell(automations, domain, level):
    curr = ""
    for done in automations[domain][level]["Yes"]:
        curr += f"✔️ [{done.name}]({get_link(done.name)})<br>"
    for not_done in automations[domain][level]["No"]:
        curr += f"❌ [{not_done.name}]({get_link(not_done.name)})<br>"

    return curr


def generate_table(yes_no_table, repo_report, maturity_levels):
    first_row = repo_report.keys()

    header = "\n| Level of maturity | Basic | Intermediate | Advanced |\n"
    separator = "|--------------------|-------|-------------|----------|\n"
    rows = ""

    for domain in first_row:
        level_row = (
            f"| {domain} | "
            f"{get_level_cell(domain, Level.BASIC, maturity_levels)} | "
            f"{get_level_cell(domain, Level.INTERMEDIATE, maturity_levels)} | "
            f"{get_level_cell(domain, Level.ADVANCED, maturity_levels)} |\n"
        )
        row = (
            f"| | "
            f"{get_tasks_cell(yes_no_table, domain, Level.BASIC)} | "
            f"{get_tasks_cell(yes_no_table, domain, Level.INTERMEDIATE)} | "
            f"{get_tasks_cell(yes_no_table, domain, Level.ADVANCED)} |\n"
        )
        rows += level_row + row

    markdown_table = header + separator + rows
    return markdown_table


def get_todos(yes_no_table, maturity_levels, max_todos):
    sorted_domains = sorted(maturity_levels.items(), key=lambda x: x[1].value)
    todos = []

    for current_level in [Level.BASIC, Level.INTERMEDIATE, Level.ADVANCED]:
        for domain, maturity in sorted_domains:
            if (
                maturity.value < current_level.value
                and len(yes_no_table[domain][current_level]["No"]) > 0
            ):
                todos.append((domain, current_level))

    todos_pq = []
    for domain, level in todos:
        tasks = yes_no_table[domain][level]["No"]
        for task in tasks:
            heapq.heappush(todos_pq, Todo(level, task.frequency, task))

    md = (
        "\n# And now? Next steps!\nIt is not always clear which automation tasks should be prioritized. It is "
        "however important to balance your automation efforts, as a uniform level of maturity is most productive. "
        "I'm here to help! Below is a list of tasks that you can work on to help level up your maturity across "
        "the automation domains: \n\n "
    )

    for _ in range(max_todos):
        task = heapq.heappop(todos_pq)
        md += f"- Implement **[{task.task.name}]({get_link(task.task.name)});** implemented by {task.task.frequency}% of GitHub repositories\n"
    return md


def publish_github_issue(repository, title, body):
    """
    Publishes an issue to the specified GitHub repository.

    :param repository: The repository in the format 'owner/repository'.
    :param token: The GitHub personal access token for authentication.
    :param title: The title of the issue.
    :param body: The body/description of the issue.
    :raises RateLimitException: If a rate limit error is encountered.
    :raises Exception: For generic failures when creating an issue.
    """
    load_dotenv()
    github_token = os.getenv("GITHUB_ISSUE_TOKEN")

    url = f"https://api.github.com/repos/{repository}/issues"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"title": title, "body": body}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return response.json()
    elif (
        response.status_code == 403
        and "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == "0"
    ):
        raise RateLimitException("GitHub API rate limit exceeded.")
    else:
        print(
            f"Failed to create issue on {repository}: {response.status_code}, {response.text}"
        )


def generate_yes_no_table(repo_report):
    table = dict()
    for domain in repo_report.keys():
        table[domain] = dict()
        for level in [Level.BASIC, Level.INTERMEDIATE, Level.ADVANCED]:
            table[domain][level] = dict()
            table[domain][level]["Yes"] = list()
            table[domain][level]["No"] = list()
        for subdomain in repo_report[domain]:
            for task, completed in repo_report[domain][subdomain].items():
                table[domain][task.level][completed].append(task)

    return table


def generate_report(repo_report):
    repo_maturity_levels = get_maturity_levels(repo_report)
    table = generate_yes_no_table(repo_report)

    generate_radar_chart(repo, repo_maturity_levels, "../reports/output/")
    generated_table = generate_table(table, repo_report, repo_maturity_levels)
    generated_todos = get_todos(table, repo_maturity_levels, 2)

    content = (
        "I'm with the Software Engineering Research Group at the TU Delft, and I am investigating automations. "
        "I have looked at your repository and which GitHub workflows and Maven plugins you are using. I hope to "
        "provide you with some interesting insights about your repository! "
        "I'll give you a quick summary of what I found, and the automation tasks I recommend "
        "you to focus on next (:\n"
    )
    content += f"\n\n![Image](https://simchavos.com/assets/thesis/output/{repo}_chart.png)\n{generated_table}{generated_todos}"
    with open("../data/conclusion.md") as conclusion:
        return content + conclusion.read()


def statistics(average, least):
    with open("../data/issue_responses.csv") as issue_responses:
        df = pd.read_csv(issue_responses)
        closed_without_comment = [
            x.lower()
            for x in list(
                df[(df["Closed"] == 1) & (df["Commented"].fillna(0) == 0)].iloc[:, 0]
            )
        ]
        interested = [x.lower() for x in list(df[(df["Interested"] == 1)].iloc[:, 0])]
        all = [x.lower() for x in list(df.iloc[:, 0])]

        for name, category in [
            ("Closed without comment", closed_without_comment),
            ("Interested", interested),
            ("All", all),
        ]:
            lowest_sum = 0
            average_sum = 0

            for repository in category:
                if repository not in least or repository not in average:
                    print(repository)
                    continue

                lowest_sum += least[repository]
                average_sum += average[repository]

            print(
                f"{name}, lowest: {round(lowest_sum/len(category), 2)} or average: {round(average_sum/len(category), 2)}"
            )


if __name__ == "__main__":
    with open("../data/rq3_repos.txt") as file:
        repos = [line.strip() for line in file if line.strip()]

    download_files(repos, [AutomationDownloader("../reports/repositories")])
    automationsExtractor = AutomationExtractor("../reports/repositories")
    total_repos = automationsExtractor.analyze_all_files(
        python_dir="../data/empty.txt", java_dir="../data/rq3_repos.txt"
    )
    domains = parse_markdown_to_domain("../data/automations.md")
    report = check_and_report_automations(
        repos, domains, automationsExtractor.repos_dict
    )
    count = 0
    average_scores = dict()
    least_scores = dict()
    average_scores_joker = dict()
    least_scores_joker = dict()

    for repo in report:
        output_path = os.path.join("../reports/output", repo)
        os.makedirs(output_path, exist_ok=True)
        content = generate_report(report[repo])

        average_scores[repo.lower()] = get_average_level(
            get_maturity_levels(report[repo])
        )
        least_scores[repo.lower()] = get_lowest_level(get_maturity_levels(report[repo]))
        average_scores_joker[repo.lower()] = get_average_level(
            add_joker(
                get_report_per_level(report[repo]), get_maturity_levels(report[repo])
            )
        )
        least_scores_joker[repo.lower()] = get_lowest_level(
            add_joker(
                get_report_per_level(report[repo]), get_maturity_levels(report[repo])
            )
        )

        with open(f"{output_path}.md", "w+", encoding="utf-8") as file:
            file.write(content)

        # publish_github_issue(repo, "Automation analysis", content)

    print("Without joker:")
    statistics(average_scores, least_scores)
    print("With joker:")
    statistics(average_scores_joker, least_scores_joker)
