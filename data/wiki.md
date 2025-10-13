Welcome to the automations wiki! Find more details on each automation task on this page.
# Artifacts
## Artifact creation
Automations involved in compiling, packaging, and managing dependencies to generate an artifact.
### Code compilation
Maturity level: *Basic*

Implemented by 14% of repositories on GitHub.

Examples that implement this task are: 
- Runs "mvn compile"
- Plugin org.apache.maven.plugins:maven-compiler-plugin
- Plugin org.eclipse.tycho:tycho-compiler-plugin
- Plugin org.eclipse.xtend:xtend-maven-plugin
- Runs "./gradlew build"
- Uses gradle/gradle-build-action
### Dependency management of artifact
Maturity level: *Basic*

Implemented by 15% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-dependency-plugin
- Plugin org.eclipse.tycho:tycho-maven-plugin
- Plugin org.codehaus.mojo:versions-maven-plugin
- Runs "npm install"
- Plugin org.apache.maven.plugins:maven-install-plugin
- Plugin org.eclipse.tycho:tycho-p2-plugin
### Build tasks, resources and configuration
Maturity level: *Intermediate*

Implemented by 13% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-resources-plugin
- Plugin org.codehaus.mojo:build-helper-maven-plugin
- Plugin org.eclipse.tycho:target-platform-configuration
- Plugin org.apache.maven.plugins:maven-antrun-plugin
- Plugin org.honton.chas:exists-maven-plugin
- Plugin org.apache.maven.plugins:maven-remote-resources-plugin
### Packaging
Maturity level: *Intermediate*

Implemented by 27% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.eclipse.tycho:tycho-packaging-plugin
- Plugin org.apache.maven.plugins:maven-jar-plugin
- Plugin org.springframework.boot:spring-boot-maven-plugin
- Plugin org.eclipse.tycho:tycho-maven-plugin
- Plugin org.apache.maven.plugins:maven-shade-plugin
- Plugin org.apache.maven.plugins:maven-war-plugin
- Runs "./gradlew build"
- Runs "python build"
- Runs "poetry build"
- Runs "mvn package"
- Uses gradle/gradle-build-action
- Runs "zip"
- Runs "tar"
- Uses docker/metadata-action
- Runs "docker build"
- Uses docker/setup-buildx-action
- Uses docker/setup-qemu-action
- Runs "docker run"
- Uses docker/build-push-action
- Runs "docker push"
## Release management
Automations related to every aspect of the distribution of artifacts.
### Release tagging
Maturity level: *Intermediate*

Implemented by 14% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-release-plugin
- Plugin org.codehaus.mojo:buildnumber-maven-plugin
- Uses actions/create-release
### Publish artifacts to a registry
Maturity level: *Intermediate*

Implemented by 39% of repositories on GitHub.

Examples that implement this task are: 
- Runs "mvn deploy"
- Plugin org.apache.maven.plugins:maven-assembly-plugin
- Plugin org.apache.maven.plugins:maven-deploy-plugin
- Plugin org.sonatype.plugins:nexus-staging-maven-plugin
- Plugin org.apache.maven.plugins:maven-release-plugin
- Uses softprops/action-gh-release
- Runs "twine upload"
- Uses actions/upload-artifact
- Uses pypa/gh-action-pypi-publish
- Runs "poetry publish"
- Uses actions/create-release
- Uses docker/build-push-action
- Runs "docker push"
### Generate source and metadata artifacts
Maturity level: *Advanced*

Implemented by 7% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-source-plugin
- Plugin org.eclipse.tycho:tycho-source-plugin
- Plugin org.apache.felix:maven-bundle-plugin
- Plugin biz.aQute.bnd:bnd-maven-plugin
### Generate release notes
Maturity level: *Advanced*

Implemented by 1% of repositories on GitHub.

Examples that implement this task are: 
- Uses release-drafter/release-drafter
### Source control management
Maturity level: *Advanced*

Implemented by 4% of repositories on GitHub.

Examples that implement this task are: 
- Plugin io.github.git-commit-id:git-commit-id-maven-plugin
- Plugin pl.project13.maven:git-commit-id-plugin
- Plugin org.apache.maven.plugins:maven-scm-plugin
- Runs "git diff"
# Development
## Pipeline
Automation workflows used in a runner for execution and optimization of CI/CD pipelines.
### Build files configuration
Maturity level: *Basic*

Implemented by 56% of repositories on GitHub.

Examples that implement this task are: 
- Uses actions/checkout
- Runs "git checkout"
- Plugin org.apache.maven.plugins:maven-clean-plugin
- Runs "curl"
- Runs "wget"
- Runs "mvn clean"
- Runs "git clone"
- Plugin org.commonjava.maven.plugins:directory-maven-plugin
- Runs "git fetch"
### Build environment configuration
Maturity level: *Intermediate*

Implemented by 49% of repositories on GitHub.

Examples that implement this task are: 
- Uses docker/setup-buildx-action
- Uses docker/setup-qemu-action
- Uses actions/github-script
- Uses docker/login-action
- Runs "export"
- Runs "source"
- Runs "poetry run"
- Runs "set"
- Uses conda-incubator/setup-miniconda
- Plugin org.codehaus.mojo:flatten-maven-plugin
- Uses actions/setup-python
- Uses actions/setup-java
- Uses actions/setup-node
- Uses docker/setup-qemu-action
### Optimization
Maturity level: *Advanced*

Implemented by 14% of repositories on GitHub.

Examples that implement this task are: 
- Uses actions/cache
- Uses actions/download-artifact
# Code quality
## Testing

### Run tests
Maturity level: *Basic*

Implemented by 23% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-surefire-plugin
- Plugin org.eclipse.tycho:tycho-surefire-plugin
- Plugin org.apache.maven.plugins:maven-failsafe-plugin
- Runs "pytest"
- Runs "python pytest"
- Runs "make test"
- Runs "mvn test"
- Runs "./build/mvn"
- Runs "python unittest"
### Test coverage and validity
Maturity level: *Intermediate*

Implemented by 9% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.jacoco:jacoco-maven-plugin
- Plugin org.codehaus.mojo:cobertura-maven-plugin
- Runs "coverage run"
- Runs "tox"
### Generate test reports
Maturity level: *Intermediate*

Implemented by 10% of repositories on GitHub.

Examples that implement this task are: 
- Uses codecov/codecov-action
- Runs "coverage report"
- Runs "coveralls"
- Plugin org.eluder.coveralls:coveralls-maven-plugin
## Linting

### Static code style analysis
Maturity level: *Basic*

Implemented by 9% of repositories on GitHub.

Examples that implement this task are: 
- Plugin com.diffplug.spotless:spotless-maven-plugin
- Plugin org.apache.maven.plugins:maven-checkstyle-plugin
- Runs "flake8"
- Runs "ruff check"
- Runs "pylint"
### Automatic code formatting
Maturity level: *Intermediate*

Implemented by 10% of repositories on GitHub.

Examples that implement this task are: 
- Plugin net.revelc.code.formatter:formatter-maven-plugin
- Plugin net.revelc.code:impsort-maven-plugin
- Runs "flake8"
- Runs "black"
- Runs "ruff check"
- Uses psf/black
- Plugin com.github.ekryd.sortpom:sortpom-maven-plugin
### Static code quality analysis
Maturity level: *Intermediate*

Implemented by 5% of repositories on GitHub.

Examples that implement this task are: 
- Plugin com.github.spotbugs:spotbugs-maven-plugin
- Plugin org.apache.maven.plugins:maven-pmd-plugin
- Plugin org.codehaus.mojo:findbugs-maven-plugin
- Plugin org.sonarsource.scanner.maven:sonar-maven-plugin
- Plugin org.codehaus.mojo:animal-sniffer-maven-plugin
- Plugin org.gaul:modernizer-maven-plugin
- Runs "mypy"
- Runs "pylint"
### Verify packaging correctness
Maturity level: *Advanced*

Implemented by 6% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.basepom.maven:duplicate-finder-maven-plugin
- Runs "twine check"
- Plugin org.apache.maven.plugins:maven-enforcer-plugin
## Security and compliance

### Vulnerability scans
Maturity level: *Advanced*

Implemented by 6% of repositories on GitHub.

Examples that implement this task are: 
- Uses github/codeql-action/init
- Uses github/codeql-action/analyze
- Uses github/codeql-action/autobuild
### Sign artifacts
Maturity level: *Advanced*

Implemented by 3% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-gpg-plugin
### License checks
Maturity level: *Advanced*

Implemented by 2% of repositories on GitHub.

Examples that implement this task are: 
- Plugin com.mycila:license-maven-plugin
- Plugin org.apache.rat:apache-rat-plugin
- Plugin org.codehaus.mojo:license-maven-plugin
# Collaboration
## Documentation

### Prepare or create documentation artifacts
Maturity level: *Basic*

Implemented by 18% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-site-plugin
- Uses actions/upload-pages-artifact
- Runs "make html"
- Uses actions/configure-pages
- Runs "sphinx-build"
- Runs "mkdocs"
### Generate documentation from source code
Maturity level: *Intermediate*

Implemented by 7% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-javadoc-plugin
- Plugin org.apache.maven.plugins:maven-plugin-plugin
### Publish documentation
Maturity level: *Advanced*

Implemented by 5% of repositories on GitHub.

Examples that implement this task are: 
- Plugin org.apache.maven.plugins:maven-scm-publish-plugin
- Uses actions/deploy-pages
- Uses peaceiris/actions-gh-pages
- Uses JamesIves/github-pages-deploy-action
## Social coding

### Bot commits
Maturity level: *Intermediate*

Implemented by 6% of repositories on GitHub.

Examples that implement this task are: 
- Runs "git commit"
- Runs "git push"
- Runs "git add"
- Runs "git config"
### Pre-commit hooks
Maturity level: *Advanced*

Implemented by 4% of repositories on GitHub.

Examples that implement this task are: 
- Uses pre-commit/action
- Runs "pre-commit run"
### Issue or PR bots
Maturity level: *Advanced*

Implemented by 3% of repositories on GitHub.

Examples that implement this task are: 
- Uses actions/stale
- Uses peter-evans/create-pull-request