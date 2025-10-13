import unittest
from collections import defaultdict
from unittest.mock import mock_open, patch

from src.python.entities.Action import Invalid, Metadata, Run, Uses
from src.python.extractor.Utilities import create_jobs_dict, process_commands
from src.python.extractor.WorkflowAnalyzer import AutomationExtractor


class TestAutomationExtractor(unittest.TestCase):

    def setUp(self):
        self.save_path = "./test_output"
        self.extractor = AutomationExtractor(self.save_path)
        self.repo = "test_repo"
        self.file_path = "./test_workflow.yaml"
        self.file_content = """
        jobs:
          test_job:
            name: Test Job
            steps:
              - name: Checkout code
                uses: actions/checkout@v2
              - name: Run tests
                run: pytest
        """

    def test_add_automation(self):
        metadata = Metadata(
            "job_id", "job_name", "step_name", "file_name", "workflow_name"
        )
        automation = Run("pytest")
        self.extractor.add_automation(automation, self.repo, metadata)

        self.assertIn(automation, self.extractor.automations_dict)
        self.assertIn(self.repo, self.extractor.automations_dict[automation])
        self.assertEqual(
            self.extractor.automations_dict[automation][self.repo][0], metadata
        )

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""
        jobs:
          test_job:
            name: Test Job
            steps:
              - name: Checkout code
                uses: actions/checkout@v2
              - name: Run tests
                run: pytest
        """,
    )
    @patch("yaml.safe_load")
    def test_analyze_workflow(self, mock_safe_load, mock_open):
        mock_safe_load.return_value = {
            "jobs": {
                "test_job": {
                    "name": "Test Job",
                    "steps": [
                        {"name": "Checkout code", "uses": "actions/checkout@v2"},
                        {"name": "Run tests", "run": "pytest"},
                    ],
                }
            }
        }

        self.extractor.analyze_workflow(self.repo, self.file_path)

        self.assertIn(Uses("actions/checkout@v2"), self.extractor.automations_dict)
        self.assertIn(Run("pytest"), self.extractor.automations_dict)

    @patch("builtins.open", new_callable=mock_open, read_data="repo1\nrepo2\n")
    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("os.path.join", side_effect=lambda *args: "/".join(args))
    def test_analyze_all_files(self, mock_join, mock_isdir, mock_listdir, mock_open):
        mock_isdir.return_value = False
        mock_listdir.return_value = ["workflow1.yaml", "workflow2.yaml"]

        with patch.object(
            AutomationExtractor, "analyze_workflow"
        ) as mock_analyze_workflow:
            mock_analyze_workflow.return_value = None
            self.extractor.analyze_all_files()

            self.assertEqual(mock_analyze_workflow.call_count, 8)

    def test_analyze_workflow_invalid_file(self):
        with patch("builtins.open", side_effect=Exception):
            self.extractor.analyze_workflow(self.repo, self.file_path)

        self.assertIn(Invalid, self.extractor.automations_dict)
        self.assertEqual(self.extractor.automations_dict[Invalid][self.repo], [None])
        self.assertEqual(self.extractor.exceptions, 1)


class TestCreateJobsDict(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="jobs:\n  job1:\n    name: Job 1",
    )
    def test_create_jobs_dict(self, mock_open):
        result = create_jobs_dict("test_path.yaml")
        self.assertIn("job1", result)
        self.assertIsInstance(result["job1"], defaultdict)


class TestSplitting(unittest.TestCase):
    def test_remove_flags(self):
        cmds = "run: ./mvnw -B sonar:sonar"
        correct = ["run: ./mvnw sonar:sonar"]
        self.assertEqual(process_commands(cmds), correct)

    def test_combine_and_split_new_lines(self):
        cmds = """./mvnw \\
                    --quiet --batch-mode -DforceStdout=true test \\
                    | some-command /tmp/mvnw-project-version.out"""
        correct = {
            "mvn compile",
            "mvn test",
            "some-command /tmp/mvnw-project-version.out",
        }
        self.assertEqual(correct, set(process_commands(cmds)))

    def test_maven_cmds_skiptests(self):
        cmds = "mvn clean package -DskipTests"
        correct = {"mvn clean", "mvn package", "mvn compile"}
        self.assertEqual(correct, set(process_commands(cmds)))

    def test_maven_cmds_multiline(self):
        cmds = "mvn clean package -DskipTests"
        correct = {"mvn clean", "mvn package", "mvn compile"}
        self.assertEqual(correct, set(process_commands(cmds)))

    def test_maven_cmds_install(self):
        cmds = "mvn install"
        correct = {"mvn test", "mvn compile", "mvn install"}
        self.assertEqual(correct, set(process_commands(cmds)))

    def test_maven_cmds_verify(self):
        cmds = "mvn validate"
        correct = {"mvn validate"}
        self.assertEqual(correct, set(process_commands(cmds)))

    def test_newlines(self):
        cmds = """
        |
          export REVISION=$(</tmp/mvnw-project-version.out)
          export TAG="v$REVISION"
          git config user.name github-actions
          git config user.email github-actions@github.com
          git tag "$TAG"
          git push origin \"$TAG\""""
        correct = [
            "export",
            "export",
            "git config user.name github-actions",
            "git config user.email github-actions@github.com",
            'git tag "$TAG"',
            'git push origin "$TAG"',
        ]
        self.assertEqual(process_commands(cmds), correct)

    def test_remove_sudo_and_echo(self):
        cmds = """
            echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo some-command /etc/udev/rules.d/99-kvm4all.rules
            sudo udevadm control --reload-rules
            sudo udevadm trigger --name-match=kvm
            """
        correct = [
            "some-command /etc/udev/rules.d/99-kvm4all.rules",
            "udevadm control",
            "udevadm trigger",
        ]
        self.assertEqual(process_commands(cmds), correct)

    def test_special_cases(self):
        cmds = "poetry run mvn clean"
        correct = ["poetry run", "mvn clean"]
        self.assertEqual(correct, process_commands(cmds))
