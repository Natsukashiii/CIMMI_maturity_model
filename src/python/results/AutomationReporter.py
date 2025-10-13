import json
import os
import pickle
import re
from collections import defaultdict

from src.python.entities.Action import Plugin, parse_action
from src.python.entities.Automation import (AutomationDomain,
                                            AutomationSubdomain, Task)


def parse_markdown_to_domain(
    markdown_file: str = "../data/automations.md",
) -> [AutomationDomain]:
    with open(markdown_file, "r") as f:
        lines = f.readlines()

    tlds = []
    for line in lines:
        line = line.strip()

        # Check for main headings (#) - e.g. Artifacts
        match_main = re.match(r"^# (.+)", line)
        if match_main:
            domain_name = match_main.group(1).strip()
            domain = AutomationDomain(domain_name)
            tlds.append(domain)
            counts = -1
            continue

        # Check for subheadings (##) - e.g. Artifact Creation, Release Management
        match_sub = re.match(r"^## (.+)", line)
        if match_sub:
            domain_name = match_sub.group(1).strip()
            domain = AutomationSubdomain(domain_name)
            tlds[-1].child.append(domain)  # Add as a child of the current domain
            counts += 1
            continue

        # Check for list items (-) - tasks under domains
        match_list = re.match(r"^- (.+)", line)
        if match_list:
            str_match = match_list.group(1).strip().split(";")
            task_name = str_match[0].strip()
            frequency = int(str_match[1].strip())
            level = str_match[2].strip()
            instances = [
                parse_action(instance.strip())
                for instance in str_match[3].split(",")
                if len(instance.strip()) > 0
            ]
            task = Task(task_name, instances, level, frequency)
            tlds[-1].child[counts].child.append(task)
            continue

        if not match_list and not match_sub and not match_main:
            domain.description = line
    return tlds


def check_and_report_automations(repos, domains, workflow_dict, print_unused=False):
    # Load the plugins JSON file
    with open("../data/plugins.json", "r") as file:
        plugins = json.load(file)

    unused_actions = {}
    report = defaultdict(dict)

    for repo in repos:
        repo = repo.strip()
        used_tasks = set()
        used_domains = set()
        used_subdomains = set()

        def check_instances(curr_task, curr_subdomain, curr_domain, to_check):
            if to_check in task.instances:
                unused_actions[curr_task.name].discard(to_check)  # Remove used actions

                if curr_task.name not in used_tasks:
                    used_tasks.add(curr_task.name)
                    curr_task += 1

                if curr_domain not in used_domains:
                    used_domains.add(curr_domain)
                    curr_domain += 1

                if curr_subdomain not in used_subdomains:
                    used_subdomains.add(curr_subdomain)
                    curr_subdomain += 1

        stack = [every for every in domains]

        while stack:
            current = stack.pop()

            # If the current element is a domain, print its name
            if isinstance(current, AutomationDomain):
                for child in reversed(current.child):
                    stack.append(child)
                domain = current
                report[repo][domain] = dict()

            elif isinstance(current, AutomationSubdomain):
                for child in reversed(current.child):
                    stack.append(child)
                subdomain = current
                report[repo][domain][subdomain] = dict()

            elif isinstance(current, Task):
                task = current
                if task.name not in unused_actions:
                    unused_actions[task.name] = set(task.instances)

                # Check for used actions in the workflow
                for used_action in workflow_dict.get(repo, []):
                    check_instances(task, subdomain, domain, used_action)

                # Check for used actions in plugins
                if repo in plugins:
                    for plugin in plugins[repo]:
                        plugin_object = Plugin(plugin)
                        check_instances(task, subdomain, domain, plugin_object)

                # Update the report
                report[repo][domain][subdomain][task] = (
                    "Yes"
                    if any(
                        instance in workflow_dict.get(repo, [])
                        or instance in [Plugin(p) for p in plugins.get(repo, [])]
                        for instance in task.instances
                    )
                    else "No"
                )

    if print_unused:
        for task_name, actions in unused_actions.items():
            if actions:  # If there are any unused actions
                print(
                    f"Task '{task_name}' has unused actions: {', '.join(str(action) for action in actions)}"
                )

    return report


def string_representation(current, number_of_repos):
    if isinstance(current, list):
        for task in current:
            string_representation(task, number_of_repos)
    elif isinstance(current, AutomationDomain):
        print(current.str(number_of_repos))
        string_representation(current.child, number_of_repos)
    elif isinstance(current, Task):
        print(current.str(number_of_repos))


if __name__ == "__main__":
    with open("../output/automations_dict.pkl", "rb") as dict_file:
        workflow_dict = pickle.load(dict_file)
    domains = parse_markdown_to_domain("../data/automations.md")

    # Open repository files
    python_repos = open(os.path.join("../data/rq1_python_repos.txt"), "r")
    java_repos = open(os.path.join("../data/rq1_java_repos.txt"), "r")
    repos = python_repos.readlines() + java_repos.readlines()

    number_of_repos = len(
        check_and_report_automations(repos, domains, workflow_dict, print_unused=True)
    )

    for domain in domains:
        string_representation(domain, number_of_repos)

    with open("../data/results.pkl", "wb") as file:
        pickle.dump(domains, file)
