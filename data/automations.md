# Artifacts
## Artifact creation
Automations involved in compiling, packaging, and managing dependencies to generate an artifact.
- Code compilation; 14; basic; Runs 'mvn compile', org.apache.maven.plugins:maven-compiler-plugin, org.eclipse.tycho:tycho-compiler-plugin, org.eclipse.xtend:xtend-maven-plugin,Runs './gradlew build',Uses gradle/gradle-build-action
- Build tasks, resources and configuration; 13; intermediate; org.apache.maven.plugins:maven-resources-plugin, org.codehaus.mojo:build-helper-maven-plugin, org.eclipse.tycho:target-platform-configuration, org.apache.maven.plugins:maven-antrun-plugin,  org.honton.chas:exists-maven-plugin, org.apache.maven.plugins:maven-remote-resources-plugin
- Packaging; 27; intermediate; org.eclipse.tycho:tycho-packaging-plugin, org.apache.maven.plugins:maven-jar-plugin, org.springframework.boot:spring-boot-maven-plugin, org.eclipse.tycho:tycho-maven-plugin, org.apache.maven.plugins:maven-shade-plugin, org.apache.maven.plugins:maven-war-plugin,Runs './gradlew build',Runs 'python build',Runs 'poetry build',Runs 'mvn package',Uses gradle/gradle-build-action,Runs 'zip',Runs 'tar',Uses docker/metadata-action,Runs 'docker build', Uses docker/setup-buildx-action, Uses docker/setup-qemu-action,Runs 'docker run',Uses docker/build-push-action,Runs 'docker push'
- Dependency management of artifact; 15; basic; org.apache.maven.plugins:maven-dependency-plugin, org.eclipse.tycho:tycho-maven-plugin, org.codehaus.mojo:versions-maven-plugin,Runs 'npm install',org.apache.maven.plugins:maven-install-plugin,org.eclipse.tycho:tycho-p2-plugin
## Release management
Automations related to every aspect of the distribution of artifacts.
- Generate source and metadata artifacts; 7; advanced; org.apache.maven.plugins:maven-source-plugin, org.eclipse.tycho:tycho-source-plugin, org.apache.felix:maven-bundle-plugin, biz.aQute.bnd:bnd-maven-plugin
- Generate release notes; 1; advanced; Uses release-drafter/release-drafter
- Source control management; 4; advanced; io.github.git-commit-id:git-commit-id-maven-plugin, pl.project13.maven:git-commit-id-plugin, org.apache.maven.plugins:maven-scm-plugin,Runs 'git diff'
- Release tagging; 14; intermediate; org.apache.maven.plugins:maven-release-plugin, org.codehaus.mojo:buildnumber-maven-plugin,Uses actions/create-release
- Publish artifacts to a registry; 39; intermediate; Runs 'mvn deploy', org.apache.maven.plugins:maven-assembly-plugin, org.apache.maven.plugins:maven-deploy-plugin, org.sonatype.plugins:nexus-staging-maven-plugin,  org.apache.maven.plugins:maven-release-plugin,Uses softprops/action-gh-release, Runs 'twine upload', Uses actions/upload-artifact, Uses pypa/gh-action-pypi-publish,Runs 'poetry publish', Uses actions/create-release, Uses docker/build-push-action, Runs 'docker push'
# Development
## Pipeline
Automation workflows used in a runner for execution and optimization of CI/CD pipelines.
- Optimization; 14; advanced; Uses actions/cache, Uses actions/download-artifact,
- Build files configuration; 56; basic; Uses actions/checkout, Runs 'git checkout', org.apache.maven.plugins:maven-clean-plugin, Runs 'curl', Runs 'wget', Runs 'mvn clean', Runs 'git clone', org.commonjava.maven.plugins:directory-maven-plugin, Runs 'git fetch',
- Build environment configuration; 49; intermediate; Uses docker/setup-buildx-action, Uses docker/setup-qemu-action,Uses actions/github-script,Uses docker/login-action, Runs 'export', Runs 'source', Runs 'poetry run', Runs 'set',Uses conda-incubator/setup-miniconda,org.codehaus.mojo:flatten-maven-plugin,Uses actions/setup-python, Uses actions/setup-java, Uses actions/setup-node, Uses docker/setup-qemu-action
# Code quality
## Testing
- Run tests; 23; basic; org.apache.maven.plugins:maven-surefire-plugin, org.eclipse.tycho:tycho-surefire-plugin, org.apache.maven.plugins:maven-failsafe-plugin,Runs 'pytest',Runs 'python pytest',Runs 'make test',Runs 'mvn test',Runs './build/mvn test',Runs 'python unittest'
- Test coverage and validity; 9; intermediate; org.jacoco:jacoco-maven-plugin, org.codehaus.mojo:cobertura-maven-plugin,Runs 'coverage run',Runs 'tox'
- Generate test reports; 10; intermediate; Uses codecov/codecov-action,Runs 'coverage report',Runs 'coveralls', org.eluder.coveralls:coveralls-maven-plugin
## Linting
- Automatic code formatting; 10; intermediate; net.revelc.code.formatter:formatter-maven-plugin, net.revelc.code:impsort-maven-plugin,Runs 'flake8',Runs 'black',Runs 'ruff check',Uses psf/black,com.github.ekryd.sortpom:sortpom-maven-plugin
- Static code quality analysis; 5; intermediate; com.github.spotbugs:spotbugs-maven-plugin, org.apache.maven.plugins:maven-pmd-plugin, org.codehaus.mojo:findbugs-maven-plugin, org.sonarsource.scanner.maven:sonar-maven-plugin, org.codehaus.mojo:animal-sniffer-maven-plugin, org.gaul:modernizer-maven-plugin,Runs 'mypy',Runs 'pylint'
- Static code style analysis; 9; basic; com.diffplug.spotless:spotless-maven-plugin, org.apache.maven.plugins:maven-checkstyle-plugin,Runs 'flake8',Runs 'ruff check',Runs 'pylint'
- Verify packaging correctness; 6; advanced; org.basepom.maven:duplicate-finder-maven-plugin,Runs 'twine check',org.apache.maven.plugins:maven-enforcer-plugin
## Security and compliance
- Vulnerability scans; 6; advanced; Uses github/codeql-action/init, Uses github/codeql-action/analyze, Uses github/codeql-action/autobuild
- Sign artifacts; 3; advanced; org.apache.maven.plugins:maven-gpg-plugin
- License checks; 2; advanced; com.mycila:license-maven-plugin, org.apache.rat:apache-rat-plugin, org.codehaus.mojo:license-maven-plugin
# Collaboration
## Documentation
- Generate documentation from source code; 7; intermediate; org.apache.maven.plugins:maven-javadoc-plugin, org.apache.maven.plugins:maven-plugin-plugin
- Prepare or create documentation artifacts; 18; basic; org.apache.maven.plugins:maven-site-plugin, Uses actions/upload-pages-artifact,Runs 'make html',Uses actions/configure-pages,Runs 'sphinx-build', Runs 'mkdocs'
- Publish documentation; 5; advanced; org.apache.maven.plugins:maven-scm-publish-plugin,Uses actions/deploy-pages,Uses peaceiris/actions-gh-pages,Uses JamesIves/github-pages-deploy-action
## Social coding
- Pre-commit hooks; 4; advanced; Uses pre-commit/action, Runs 'pre-commit run'
- Issue or PR bots; 3; advanced; Uses actions/stale,Uses peter-evans/create-pull-request
- Bot commits; 6; intermediate; Runs 'git commit', Runs 'git push', Runs 'git add', Runs 'git config'
