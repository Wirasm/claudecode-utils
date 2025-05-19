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

After code review and approval, merge your feature branch into `develop`.

---

(WIP) below

### 4. Release Process

When you're ready to create a release from `develop` to `main`, use the dylan release command:

```bash
git checkout develop
git pull  # ensure you have the latest changes
dylan release --minor --tag
```

This will:

1. Create a version bump and update the changelog
2. Commit changes on develop
3. Merge develop → main
4. Tag the release on main
5. Push both branches and tags

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
