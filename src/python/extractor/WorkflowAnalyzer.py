import os
import pickle
from collections import defaultdict

import yaml

from src.python.entities.Action import Empty, Invalid, Metadata, Run, Uses
from src.python.extractor.Utilities import (AutomationClustering,
                                            print_analysis, process_commands)


class AutomationExtractor:

    def __init__(self, save_path):
        self.save_path = save_path
        self.automations_dict = defaultdict(dict)
        self.maven_dependencies_dict = defaultdict(list)
        self.maven_plugins_dict = defaultdict(list)
        self.exceptions = 0
        self.repos_dict = defaultdict(list)

    def add_automation(self, automation, repo, metadata):
        if repo not in self.automations_dict[automation]:
            self.automations_dict[automation][repo] = list()
        if repo not in self.repos_dict:
            self.repos_dict[repo] = list()
        self.repos_dict[repo].append(automation)
        self.automations_dict[automation][repo].append(metadata)

    def analyze_workflow(self, repo, file_path):
        file_name = file_path.split("\\")[-1]

        try:
            with open(file_path, "r", encoding="utf-8") as workflow_file:
                workflow = yaml.safe_load(workflow_file)
        except Exception:
            self.automations_dict[Invalid][repo] = list()
            self.automations_dict[Invalid][repo].append(None)
            self.exceptions += 1
            return

        if workflow is None:
            return
        for job_id, job in workflow.get("jobs", {}).items():
            steps = job.get("steps", [])
            if len(steps) > 0:
                job_name = job.get("name", None)
                for step in steps:
                    metadata = Metadata(
                        job_id,
                        job_name,
                        step.get("name", None),
                        file_name,
                        workflow.get("name", None),
                    )

                    if step.get("run") and step.get("shell", None) != "python":
                        if type(step["run"]) is bool:
                            continue
                        cmds = process_commands(step["run"])
                        automations = [Run(cmd) for cmd in cmds]
                        if len(automations) == 0:
                            automations = [Empty()]
                        for automation in automations:
                            self.add_automation(automation, repo, metadata)
                    elif step.get("uses"):
                        automation = Uses(step["uses"])
                        self.add_automation(automation, repo, metadata)
                    else:
                        self.add_automation(Empty(), repo, metadata)

    def analyze_all_files(
        self,
        python_dir="../data/rq1_python_repos.txt",
        java_dir="../data/rq1_java_repos.txt",
        specify_language=False,
    ):
        repos = []
        if python_dir:
            repos.extend(
                list(
                    map(
                        lambda j: (j, "python"),
                        open(os.path.join(python_dir), "r").readlines(),
                    )
                )
            )
        if java_dir:
            repos.extend(
                list(
                    map(
                        lambda j: (j, "java"),
                        open(os.path.join(java_dir), "r").readlines(),
                    )
                )
            )

        for repo, language in repos:
            if specify_language:
                path = os.path.join(self.save_path, language, repo.strip())
            else:
                path = os.path.join(self.save_path, repo.strip())

            for file in os.listdir(path):
                file_path = os.path.normpath(os.path.join(path, file))
                if os.path.isdir(file_path) or file_path.endswith("pom.xml"):
                    continue
                else:
                    self.analyze_workflow(repo.strip(), file_path)

        print(self.automations_dict[Invalid])
        return len(repos)


if __name__ == "__main__":
    automationsExtractor = AutomationExtractor("../output")
    total_repos = automationsExtractor.analyze_all_files(specify_language=True)
    print_analysis(automationsExtractor.automations_dict, total_repos)

    automation_clustering = AutomationClustering()
    automation_clustering.cluster_automations(automationsExtractor.automations_dict)
    automation_clustering.print_clusters()

    with open("../output/automations_dict.pkl", "wb") as dict_file:
        pickle.dump(automationsExtractor.repos_dict, dict_file)
