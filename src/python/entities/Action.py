class Metadata:
    def __init__(self, job_id, job_name, step_name, workflow_id, workflow_name):
        self.job_id = job_id
        self.job_name = job_name
        self.step_name = step_name
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name

    def __str__(self):
        return (
            f'Workflow {self.workflow_id}:{self.workflow_name or ""} -> Job {self.job_id}{self.job_name or ""} -> '
            f'Step {self.step_name or ""}'
        )


def parse_action(action: str):
    if action.startswith("Uses "):
        return Uses(flatten(action.split()[1:]))
    elif action.startswith("Runs "):
        return Run(flatten(action.replace("'", "").split()[1:]))
    else:
        return Plugin(action)


class Action:
    def __init__(self):
        pass

    def str2(self):
        pass


class Run(Action):
    def __init__(self, run):
        super().__init__()
        self.prefixes = [
            ("python3", 2),
            ("python", 2),
            ("git", 2),
            ("mvn", 2),
            (".", 2),
            ("docker", 2),
            ("make", 2),
            ("./gradlew", 2),
            ("poetry", 2),
            ("bash", 2),
            ("conda", 2),
            ("gh", 2),
            ("coverage", 2),
            ("twine", 2),
            ("brew", 2),
            ("ruff", 2),
            ("npm", 2),
            ("pre-commit", 2),
            ("/usr/bin/python3", 2),
            ("npm run", 3),
            ("./mvnw", 2),
            ("python3", 2),
        ]
        self.run = flatten(run.split()[:4])
        prefixed_run = None
        self.prefix = None
        for prefix, number in self.prefixes:
            len_prefix = len(prefix.split())
            if flatten(self.run.split()[:len_prefix]) == prefix:
                prefixed_run = flatten(self.run.split()[:number])
                self.prefix = prefix
        if prefixed_run:
            self.run = prefixed_run
        else:
            self.run = self.run.split()[0]

    def get_cmd(self):
        return self.run

    def __str__(self):
        return f'Runs "{self.run}"'

    def __hash__(self):
        return hash(self.run)

    def str2(self):
        return self.run

    def __eq__(self, other):
        return isinstance(other, Run) and self.run == other.run


def flatten(to_flatten):
    output = ""
    for item in to_flatten:
        output += item + " "
    return output.strip()


class Uses(Action):
    def __init__(self, uses):
        super().__init__()
        if uses:
            index = uses.rfind("@")
            self.uses = uses[:index] if index != -1 else uses
        else:
            self.uses = ""

    def __hash__(self):
        return hash(self.uses)

    def __eq__(self, other):
        return isinstance(other, Uses) and self.uses == other.uses

    def __str__(self):
        return f"Uses {self.uses}"

    def str2(self):
        return self.uses


class Empty(Action):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Empty action"

    def __hash__(self):
        return hash("Empty")

    def __eq__(self, other):
        return isinstance(other, Empty)

    def str2(self):
        pass


class Invalid(Action):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Invalid file"

    def __hash__(self):
        return hash("Invalid")

    def __eq__(self, other):
        return isinstance(other, Empty)

    def str2(self):
        pass


class Plugin(Action):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def __str__(self):
        return f"Plugin {self.plugin}"

    def __hash__(self):
        return hash(self.plugin)

    def __eq__(self, other):
        return isinstance(other, Plugin) and self.plugin == other.plugin

    def str2(self):
        return self.plugin
