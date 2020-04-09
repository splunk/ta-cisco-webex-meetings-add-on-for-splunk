# FDSE CI/CD Pipeline
This repository aims providing templates to easily setup the team CI/CD pipeline and satisfy best practices in your own projects.

## Features
These files will:
* kick off CI/CD pipeline that packages the app and runs through app inspect
> Make sure to check app inspect failures in logs even if the pipeline is green / passed 
* eventually deploy the app on S3 for download

## Getting Started
### Usage
* Add these files to your app folder before git tracking (`git add -A`)

### Alternative Usage
* Automatically create your own repository based on this template via [fdsegit](https://gitlab.com/splunk-fdse/other/fdsegit), internal tool meant to ease your life

### Deploy 
**You should only deploy when it passes app inspect and not before**

Deploy stage will only run on `git tag`. Follow semantic versioning explained below when tagging the code.

Example:
* `git tag -a v1.2.0 -m "my version 1.2.0"`
* `git push origin v1.2.0`

#### Semantic Versioning
Every version is formatted as `MAJOR.MINOR.PATCH` and each part changes according to the following rules.
We increment:
* `MAJOR` when breaking backward compatibility,
* `MINOR` when adding a new feature which doesn't break compatibility,
* `PATCH` when fixing a bug without breaking compatibility

## Notes
### Git Comments Messages
`git commit` message convention that helps us reading fast. In comments messages use verbs recommended in Table below.

| **Verb** | **Description**                                       |
|----------|-------------------------------------------------------|
| Add      | Create a capability such as feature, test, dependency |
| Cut      | Remove a capability such as feature, test, dependency |
| Fix      | Fix an issue (bug, typo, accident, misstatement, etc) |
| Bump     | Increase the version of something (e.g. dependency)   |
| Make     | Change the build process, or tooling, or infra        |
| Start    | Begin doing something (e.g. create a feature flag)    |
| Stop     | End doing something (e.g. remove a feature flag)      |
| Refactor | A code change that MUST be refactoring only           |
| Reformat | Refactor of formatting (e.g. omit whitespace)         |
| Optimize | Refactor of performance (e.g. speed up code)          |
| Document | Refactor of documentation (e.g. help files)           |

## References
* [git tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
* [GitLab CI/CD](https://docs.gitlab.com/ee/ci/)

