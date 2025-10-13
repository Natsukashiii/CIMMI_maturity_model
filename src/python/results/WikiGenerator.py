from src.python.results.AutomationReporter import parse_markdown_to_domain

if __name__ == "__main__":
    domains = parse_markdown_to_domain("../data/automations.md")
    md = "Welcome to the automations wiki! Find more details on each automation task on this page."
    for domain in domains:
        md += f"\n# {domain}"
        for subdomain in domain.child:
            md += f"\n## {subdomain}\n{subdomain.description}"
            ordered_tasks = sorted(subdomain.child, key=lambda task: task.level.value)
            for task in ordered_tasks:
                instances = "\n- ".join([str(instance) for instance in task.instances])
                md += (
                    f"\n### {task.name.split("[")[0]}\nMaturity level: *{task.level.name.capitalize()}*"
                    f"\n\nImplemented by {task.frequency}% of repositories on GitHub."
                    f"\n\nExamples that implement this task are: \n- {instances}"
                )
    with open("../data/wiki.md", "w+") as wiki:
        wiki.write(md)
