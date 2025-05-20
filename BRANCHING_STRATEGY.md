# Branching Strategy Guide

This repository follows a develop → main branching strategy, where:

- `main` is the production branch containing stable releases
- `develop` is the integration branch where features are merged
- Feature branches are created from `develop` for work in progress

## Workflow

### 1. Feature Development

Start by creating a feature branch from `develop`:

```bash
git checkout develop
git pull  # ensure you have the latest changes
git checkout -b feature/my-feature
```

Work on your feature, making commits (we have a git hook that automatically creates commit messages)

you enver have to add commit messages manually

```bash
git commit
```

---

(WIP) below

### 2. Creating Pull Requests

When your feature is ready, create a pull request to the `develop` branch using the dylan PR tool:

```bash
dylan pr --target develop --changelog
```

This will:

- Create a PR from your feature branch to `develop`
- Update the [Unreleased] section of the CHANGELOG.md file
- Add appropriate labels and reviewers

### 3. Code Review and Merge

After creating a PR, the following steps should be followed:

1. **Code Review**: Request reviews from team members
2. **Address Feedback**: Make necessary changes based on review feedback
3. **CI/CD Checks**: Ensure all automated tests and checks pass
4. **Approval**: Get approval from required reviewers
5. **Merge**: Merge the feature branch into `develop` using the GitHub UI or command line:

```bash
git checkout develop
git merge --no-ff feature/my-feature
git push origin develop
```

The `--no-ff` flag creates a merge commit even if a fast-forward merge is possible, which helps maintain a clear history of feature integrations.

### 4. Release Process

When you're ready to create a release from `develop` to `main`, follow these steps:

```bash
# 1. Create a release branch from develop
git checkout develop
git pull  # ensure you have the latest changes
git checkout -b release/x.y.z  # where x.y.z is the new version number

# 2. Update version and changelog
# Edit pyproject.toml and CHANGELOG.md

# 3. Commit and push the release branch
git add pyproject.toml CHANGELOG.md
git commit -m "build(release): bump version to x.y.z"
git push -u origin release/x.y.z

# 4. Create a PR from the release branch to main
# Merge the PR after review

# 5. After the PR is merged, sync develop with main
git checkout develop
git merge main
git push origin develop
```

Alternatively, you can use the dylan release command which automates this process:

```bash
dylan release --patch  # for patch releases
# or
dylan release --minor  # for minor releases
# or
dylan release --major  # for major releases
```

## Branch Naming Conventions

- Feature branches: `feature/descriptive-name`
- Bug fix branches: `fix/issue-description`
- Documentation branches: `docs/what-is-changing`
- Refactoring branches: `refactor/what-is-changing`

## Configuration

The branching strategy is configured in the `.branchingstrategy` file:

```
release_branch: develop
production_branch: main
merge_strategy: direct
```

This configuration is used by the dylan tools to understand how to handle branches during release and PR processes.
