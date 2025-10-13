import os
import re
from collections import Counter, defaultdict
from pprint import pprint

import bashlex
import yaml
from bashlex.errors import ParsingError

from src.python.entities.Action import Run, flatten
from src.python.entities.Automation import Level
from src.python.entities.RateLimitException import RateLimitException

mvn_dict = dict()
mvn_dict["mvn test"] = {"mvn compile"}
mvn_dict["mvn package"] = {"mvn compile", "mvn test"}
mvn_dict["mvn integration-test"] = {"mvn compile", "mvn test", "mvn package"}
mvn_dict["mvn verify"] = {"mvn compile", "mvn test"}
mvn_dict["mvn install"] = {"mvn compile", "mvn test"}
mvn_dict["mvn deploy"] = {"mvn compile", "mvn test"}


def print_debug_file(jobs_dict, save_path):
    with open(os.path.join(save_path, "debug.txt"), "w", encoding="utf-8") as f:

        # Convert all defaultdicts to regular dicts
        def convert_dict(d):
            if isinstance(d, defaultdict):
                return {str(key.name) + ":" + str(value) for (key, value) in d.items()}
            elif isinstance(d, dict):
                return {k: convert_dict(v) for k, v in d.items()}
            return d

        def custom_pprint(data, stream):
            for key, value in data.items():
                pprint({key: value}, stream=stream)
                stream.write("\n\n")

        # Convert the entire structure
        regular_dict = convert_dict(jobs_dict)
        custom_pprint(regular_dict, f)


def print_analysis(automations_dict, number_of_repos):
    sorted_automations = sorted(
        automations_dict.items(), key=lambda item: len(item[1]), reverse=True
    )
    print("\n\nACTIONS")

    for automation, repo_dict in sorted_automations:
        if len(repo_dict) > 1:
            print(f"{automation} [{len(repo_dict)}/{number_of_repos}]")


def print_dep_plugs_analysis(dep_dict, number_of_poms):
    sorted_deps = sorted(dep_dict.items(), key=lambda item: len(item[1]), reverse=True)

    for dep, repos in sorted_deps:
        print(f"{dep} [{len(repos)}/{number_of_poms}]")


def download_files(repos, downloaders):
    pom_files = workflows = 0
    total_pom_files = total_workflows = 0
    no_automation_repos = set()
    no_poms = set()
    # Run the download function
    for repo in repos:
        try:
            for downloader in downloaders:
                pom_files, workflows = downloader.download_files(repo.strip())
                if pom_files == 0:
                    no_poms.add(repo.strip())
        except RateLimitException as e:
            print(e)
            break

        print(f", poms: {pom_files}, workflows: {workflows}")

        if pom_files + workflows == 0:
            no_automation_repos.add(repo)

        total_workflows += workflows
        total_pom_files += pom_files
    print(
        f"\nNumber of requests: {downloader.num_requests}, remaining rate limit: {downloader.rate_limit_remaining}/{downloader.rate_limit_total}."
    )
    print(
        f"\nTotal repositories: {len(repos)}, total pom files {total_pom_files}, total workflows {total_workflows}"
    )
    return no_poms


class AutomationClustering:
    def __init__(self):
        self.automations_clustered = defaultdict(list)

    def cluster_automations(self, automations_dict):
        # Iterate through all the automations in the automations_dict
        for automation, repos in automations_dict.items():
            if type(automation) is Run:
                first_words = tuple(automation.get_cmd().split()[:1])

                # Add the automation to the appropriate cluster based on the first three words
                for i in range(len(repos)):
                    self.automations_clustered[first_words].append(automation)

    def print_clusters(self):
        sorted_clusters = sorted(
            self.automations_clustered.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )

        for cluster, automations in sorted_clusters:
            if len(automations) > 14:
                if automations[0].prefix:
                    continue
                print(f"\nCluster based on {cluster}:")
                sorted_automations = sorted(
                    automations, key=lambda item: item.run, reverse=True
                )
                for automation in sorted_automations:
                    print(f"  - {automation}")


def extract_logical_commands(node, result=None):
    """
    Extract logical commands (e.g., 'mvn test', 'grep test') from a PipelineNode.
    This function skips operators like '|' and directly collects full commands.
    """
    if result is None:
        result = []

    if node.kind == "command":
        command = " ".join(part.word for part in node.parts if hasattr(part, "word"))
        result.append(command)

    if hasattr(node, "parts"):
        for part in node.parts:
            extract_logical_commands(part, result)

    return result


def clean_command(command: str) -> str:
    for prefix in ["sudo ", "xargs ", "call ", "until "]:
        if command.startswith(prefix):
            command = command[len(prefix) :]

    if command.endswith(";"):
        command = command[:-1]

    cleaned_tokens = []

    for token in command.split():
        if "-DskipTests" in token or not (
            token.startswith("-") or token.startswith("$") or "=" in token
        ):
            cleaned_tokens.append(token)

    return " ".join(cleaned_tokens)


def split_special_cases(cmd):
    special_cases = [("poetry run", None)]
    for prefix, number in special_cases:
        len_tokens = len(prefix.split())
        if cmd.split()[:len_tokens] == prefix.split():
            if number:
                return [prefix, clean_command(cmd.split()[len_tokens:number])]
            else:
                return [prefix, clean_command(flatten(cmd.split()[len_tokens:]))]
    if (
        cmd.startswith("mvn")
        or cmd.startswith("./mvnw")
        or cmd.startswith("./build/mvn")
    ):
        no_tests = False
        if "-DskipTests" in cmd:
            no_tests = True
            cmd = cmd.replace("-DskipTests", "")
        mvn_cmds = ["mvn " + x for x in cmd.split()[1:]]
        aggregated_cmds = set()
        for mvn_cmd in mvn_cmds:
            aggregated_cmds.add(mvn_cmd)
            aggregated_cmds = aggregated_cmds.union(mvn_dict.get(mvn_cmd, set()))
        if no_tests and "mvn test" in aggregated_cmds:
            aggregated_cmds.remove("mvn test")
        return list(aggregated_cmds)

    return [cmd]


def process_commands(run):
    try:
        no_comments = "\n".join(
            line for line in run.splitlines() if not line.strip().startswith("#")
        )
        if no_comments == "":
            return []
        cmds = [
            cmd
            for parsed in bashlex.parse(no_comments)
            for cmd in extract_logical_commands(parsed)
        ]
    except (NotImplementedError, ParsingError, AssertionError, TypeError):
        cmds = re.split(r"(?<!\\)(?:\s*&&\s*|\s*\|\s*|\n)", run.strip())
        cmds = [
            re.sub(r"\\\s*", "", cmd.strip()) for cmd in cmds if len(cmd.strip()) > 0
        ]

    filtered_run = []

    for command in cmds:
        for split_command in split_special_cases(clean_command(command)):
            if not (
                len(split_command) == 0
                or split_command.startswith("#")
                or any(
                    split_command.strip().split()[0] == prefix
                    for prefix in [
                        "cd",
                        "echo",
                        "ls",
                        "mkdir",
                        "rm",
                        "chmod",
                        "grep",
                        "rm",
                        "touch",
                        "[",
                        "[[",
                        "elif",
                        "sleep",
                        "printf",
                        "(echo",
                        ">&2 echo",
                        "${{",
                        "if",
                        "mv",
                        "cat",
                        "tr",
                        "for",
                        "true",
                        '"${{',
                        "exit",
                        "head",
                        "cut",
                        "tail",
                        "wc",
                        "which",
                        "-",
                        "unset",
                        "pwd",
                        "then",
                        "EOF",
                        "while",
                        "case",
                        "for",
                        "import",
                        ")",
                        "sed",
                        "cp",
                        "tee",
                        "find",
                    ]
                )
                or any(
                    forbidden_cmd == split_command
                    for forbidden_cmd in ["", "fi", "else", "done", "do", "}", "{"]
                )
            ):
                filtered_run.append(split_command)
    return filtered_run


def create_jobs_dict(file_path):
    with open(file_path, "r", encoding="utf-8") as workflow_file:
        workflow = yaml.safe_load(workflow_file)

    jobs = {}

    for job_name, job in workflow.get("jobs", {}).items():
        jobs[job_name] = defaultdict(int)
    return jobs


def remove_repos_without_maven():
    remove = [
        "movingblocks/gestalt",
        "gnembon/carpetmod112",
        "emilyy-dev/bypass-resource-pack",
        "openmf/fineract-client",
        "Theta-Dev/ConstructionWand",
        "GoogleCloudPlatform/dataflow-vision-analytics",
        "link4real/plushie-mod",
        "manifold-systems/manifold",
        "cloudburstmc/nbt",
        "jpenilla/squaremap-addons",
        "WebCuratorTool/webcurator",
        "adsuyi/adsuyisdkdemo-android",
        "Intelehealth/Intelehealth-FHW-MobileApp",
        "keyfactor/ejbca-ce",
        "serceman/jnr-fuse",
        "replay-framework/replay",
        "mangopay/mangopay2-java-sdk",
        "3arthqu4ke/pingbypass",
        "the-aether-team/the-aether",
        "sufficientlysecure/calendar-import-export",
        "generalbytescom/batm_public",
        "Lucreeper74/Create-Metallurgy",
        "sakurakoi/dglabunlocker",
        "thelimeglass/skellett",
        "glitchfiend/terrablender",
        "microservice-canvas/microservice-canvas-tools",
        "rwth-acis/las2peer",
        "apache/openwhisk-runtime-java",
        "misionthi/nbttooltips",
        "jerolba/jfleet",
        "odnoklassniki/one-nio",
        "19misterx98/seedcrackerx",
        "imagekit-developer/imagekit-java",
        "Layers-of-Railways/CreateNumismatics",
        "jwplayer/jwplayer-sdk-android-demo",
        "brightcoveos/android-player-samples",
        "iexecblockchaincomputing/iexec-common",
        "DAMcraft/MeteorServerSeeker",
        "etiennestuder/teamcity-build-scan-plugin",
        "DolphFlynn/jwt-editor",
        "whatsapp/stickers",
        "applovin/applovin-max-sdk-android",
        "eb-wilson/singularity",
        "redis-field-engineering/redis-kafka-connect",
        "slack-samples/bolt-java-starter-template",
        "terraformersmc/cinderscapes",
        "ssanner/rddlsim",
        "mybigday/react-native-external-display",
        "xHookman/IGexperiments",
        "ome/omero-ms-zarr",
        "shinoow/abyssalcraft",
        "apache/mnemonic",
        "gradle/develocity-testing-annotations",
        "longi94/javasteam",
        "WebFuzzing/EMB",
        "bekoeppel/droidplane",
        "opencubicchunks/cubicchunks",
        "crowdin/crowdin-cli",
        "maandree/ponypipe",
        "web3j/web3j",
        "happycao/lingxi-android",
        "micronaut-projects/micronaut-kafka",
        "chaychan/bottombarlayout",
        "HMCL-dev/HMCL-Update",
        "Nxer/Twist-Space-Technology-Mod",
        "domaframework/doma",
        "xiaojieonly/ehviewer_cn_sxj",
        "adkandari/react-native-mock-location-detector",
        "ILikePlayingGames/FancyWarpMenu",
        "ihmcrobotics/mecano",
        "mzcretin/autoupdateproject",
        "SecUSo/privacy-friendly-dice-game",
        "darkkronicle/advancedchatcore",
        "neuronrobotics/java-bowler",
        "CSneko/More_end_rod",
        "magmamaintained/Magma-1.12.2",
        "tinymodularthings/ic2classic",
        "vonovak/react-native-add-calendar-event",
        "etomica/etomica",
        "getodk/javarosa",
        "OpenLiberty/liberty-tools-eclipse",
        "xm-online/xm-commons",
        "yukuku/androidbible",
        "kgu-clab/clab-platforms-server",
        "open-telemetry/semantic-conventions-java",
        "TT432/eyelib",
        "cvette/intellij-neos",
        "bowser0000/skyblockmod",
        "newrelic/newrelic-jfr-core",
        "Red-Studio-Ragnarok/Fancier-Block-Particles",
        "reportportal/agent-java-junit",
        "eclipse-jkube/jkube",
        "oraxen/oraxen",
        "epam/cloud-pipeline",
        "viktorholk/push-notifications-api",
        "barsifedron/candid-cqrs",
        "err0-io/err0agent",
        "alphajiang/hyena",
        "wisp-forest/gadget",
        "codingsoo/REST_Go",
        "minecraftmoddevelopmentmods/extra-golems",
        "treasure-data/td-android-sdk",
        "amitshekhariitbhu/fast-android-networking",
        "crazy-marvin/vacationdays",
        "banasiak/coinflip",
        "dzikoysk/cdn",
        "sundrio/sundrio",
        "Stirling-Tools/Stirling-PDF",
        "heiher/sockstun",
        "legacymoddingmc/unimixins",
        "apache/felix-atomos",
        "gtnewhorizons/minetweaker-gregtech-5-addon",
        "globox1997/dehydration",
        "oliexdev/openscale",
        "googlecloudplatform/mqtt-cloud-pubsub-connector",
        "pcorless/icepdf",
        "evmodder/dropheads",
        "mth/yeti",
        "braintree/android-card-form",
        "arakelian/java-jq",
    ]
    with open("../data/rq3_repos.txt", "r", encoding="utf-8") as infile:
        repos = [line.strip() for line in infile if line.strip()]

    filtered_repos = [repo for repo in repos if repo not in remove]

    with open("../data/filtered_sampled_repos.txt", "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(filtered_repos))


if __name__ == "__main__":
    remove_repos_without_maven()


def get_report_per_level(repo_report):
    level_dict = dict()
    for domain, subdomains in repo_report.items():
        level_dict[domain] = dict()

        for subdomain_dict in subdomains.values():
            for task, status in subdomain_dict.items():
                if task.level not in level_dict[domain]:
                    level_dict[domain][task.level] = []
                level_dict[domain][task.level].append((task, status))
    return level_dict


def get_maturity_levels(repo_report):
    maturity_levels = dict()

    for domain, subdomains in repo_report.items():
        domain_tasks = []
        tasks_completed = {}

        for subdomain_dict in subdomains.values():
            for task, status in subdomain_dict.items():
                domain_tasks.append(task)
                tasks_completed[task] = status

        total_count = Counter(task.level for task in domain_tasks)
        completed_count = Counter(
            task.level for task in domain_tasks if tasks_completed[task] == "Yes"
        )
        levels = [Level.BASIC, Level.INTERMEDIATE, Level.ADVANCED]
        maturity_levels[domain] = Level.NONE

        for level in levels:
            if 0 < total_count[level] == completed_count[level]:
                maturity_levels[domain] = level
            else:
                break
    return maturity_levels


def add_joker(repo_report, maturity_levels):
    next_level = {
        Level.NONE: Level.BASIC,
        Level.BASIC: Level.INTERMEDIATE,
        Level.INTERMEDIATE: Level.ADVANCED,
    }
    domain_to_place_joker = min(maturity_levels, key=lambda k: maturity_levels[k].value)
    highest_completed_domains = 0
    lowest_level = min(maturity_levels.values(), key=lambda v: v.value)

    for domain, domain_level in maturity_levels.items():
        if domain_level == lowest_level and lowest_level != Level.ADVANCED:
            current_completed_domains = 0
            level_to_check = next_level[lowest_level]
            while level_to_check != Level.ADVANCED and all(
                x[1] == "Yes" for x in repo_report[domain][next_level[level_to_check]]
            ):
                current_completed_domains += 1
                level_to_check = next_level[level_to_check]
            if current_completed_domains > highest_completed_domains:
                domain_to_place_joker = domain
                highest_completed_domains = current_completed_domains

    new_level = maturity_levels[domain_to_place_joker]
    for _ in range(highest_completed_domains + 1):
        new_level = next_level[new_level]
    maturity_levels[domain_to_place_joker] = new_level

    return maturity_levels


def get_lowest_level(maturity_levels: [Level]):
    lowest = 4
    for level in maturity_levels.values():
        lowest = min(lowest, level.value)
    return lowest


def get_average_level(maturity_levels: [Level]):
    return sum([x.value for x in maturity_levels.values()]) / len(maturity_levels)
