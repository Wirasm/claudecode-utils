# PRP: Dylan Release Branching Strategy Enhancement

## Goal

Enhance `dylan release` to support a proper branching strategy (develop → main) and add changelog management to `dylan pr`, enabling better team workflows and cleaner release processes.

## Why This Matters

### Current Problems
1. **Version Conflicts**: Direct merging to main causes version bumps on feature branches
2. **Messy History**: No clear separation between development and releases
3. **Manual Overhead**: Changelog updates are disconnected from PR workflow
4. **Team Friction**: Multiple developers stepping on each other's version changes

### Benefits of This Enhancement
1. **Clean Releases**: Version bumps only happen on develop → main
2. **Better Collaboration**: Teams can work without version conflicts
3. **Automated Workflow**: Changelog updates integrated into PR process
4. **Clear History**: Separation between integration (develop) and production (main)

## Context

The current `dylan release` command assumes direct merging to main branch, which doesn't work well for team workflows. We need to enhance it to support a proper branching strategy where:
- Features are developed on feature branches
- Features are merged to a `develop` branch for integration
- Releases are created from `develop` and merged to `main`

## Current Implementation

- `dylan release` only works on the current branch
- No awareness of branching strategies
- No automatic merging between branches
- `dylan pr` doesn't help with changelog management

## Requirements

### 1. Enhanced `dylan release` Command

Update the `dylan release` command to be branch-aware and project-agnostic:

```bash
# When run on ANY branch
dylan release --minor --tag

# Should:
1. Detect current branch
2. If on main: switch to develop (or configured release branch)
3. Create version bump and update changelog
4. Commit changes on develop
5. Merge develop → main
6. Tag the release on main
7. Push both branches and tags
```

#### Implementation Details

In `dylan/utility_library/dylan_release/dylan_release_runner.py`:

1. Make the prompt more intelligent about branch detection
2. Add project-agnostic branching strategy detection
3. Allow configuration through environment or config files

Example prompt additions:
```
INTELLIGENT BRANCH HANDLING:
1. Detect current branch: git symbolic-ref --short HEAD
2. If on 'main', check for common release branches:
   - develop
   - development
   - staging
   - release
3. If found, switch to release branch
4. If not found, ask user or use main directly

PROJECT-AGNOSTIC BRANCHING:
- Look for .branchingstrategy file
- Check for common patterns (develop, staging, etc.)
- Adapt workflow based on what's found
- Fall back to simple main-only workflow if needed

Example .branchingstrategy file:
release_branch: develop
production_branch: main
merge_strategy: direct
```

### 2. Default Behavior of `dylan review`

`dylan review` should maintain its current behavior regardless of branching strategy:
- Reviews changes in the specified branch
- Works the same on main, develop, or feature branches
- No special branching logic needed

### 3. Add `--changelog` Flag to `dylan pr`

Enhance `dylan pr` to optionally update the [Unreleased] section:

```bash
# Create PR and update changelog
dylan pr feature-branch --changelog

# Should:
1. Analyze commits in feature branch
2. Add entries to [Unreleased] section
3. Commit changelog update
4. Create/update PR
```

#### Implementation Details

In `dylan/utility_library/dylan_pr/dylan_pr_cli.py`:
- Add `changelog: bool = typer.Option(False, "--changelog", help="Update [Unreleased] section")`

In `dylan/utility_library/dylan_pr/dylan_pr_runner.py`:
- Update `generate_pr_prompt()` to include changelog instructions when flag is set

Example prompt additions:
```
CHANGELOG UPDATE (if --changelog flag):
1. Analyze commits: git log main..HEAD
2. Group by type (feat, fix, etc.)
3. Update CHANGELOG.md [Unreleased] section
4. Include in PR commits
```

### 3. Branching Strategy Documentation

Create documentation explaining the recommended workflow:

#### Recommended Branching Strategy

```
main (production releases)
├── develop (integration branch)
│   ├── feature/new-feature
│   ├── feature/another-feature
│   └── fix/bug-fix
```

#### Workflow

1. **Feature Development**
   ```bash
   git checkout develop
   git checkout -b feature/my-feature
   # ... work ...
   git commit -m "feat: add new feature"
   ```

2. **Create PR to develop**
   ```bash
   dylan pr --target develop --changelog
   # Updates [Unreleased] and creates PR
   ```

3. **Release from develop**
   ```bash
   git checkout develop
   git pull
   dylan release --minor --tag --merge-strategy direct
   # Creates release and merges to main
   ```

## Success Criteria

1. `dylan release` intelligently detects and adapts to project's branching strategy
2. When run from main, automatically switches to appropriate release branch
3. Works with multiple branching strategies (not just develop → main)
4. `dylan pr --changelog` updates [Unreleased] section
5. Fully backwards compatible with projects that only use main
6. Project-agnostic: adapts to different naming conventions

## Implementation Notes

- Keep changes minimal and focused
- Trust Claude Code to detect and adapt to branching strategies
- Use prompts to make Claude intelligent about branch detection
- Support configuration files but don't require them
- Test with multiple branching strategies:
  - main only
  - main + develop
  - main + staging + develop
  - custom branch names

## Example Usage

### Old Workflow (still supported)
```bash
# On main branch
dylan release --patch
```

### New Workflow
```bash
# On develop branch
dylan release --minor --merge-strategy pr
# Creates release, opens PR to main

# Or direct merge
dylan release --minor --merge-strategy direct
# Creates release, merges to main, tags
```

## Files to Modify

1. `dylan/utility_library/dylan_release/dylan_release_cli.py` - Add merge-strategy option
2. `dylan/utility_library/dylan_release/dylan_release_runner.py` - Add branch-aware logic
3. `dylan/utility_library/dylan_pr/dylan_pr_cli.py` - Add changelog flag
4. `dylan/utility_library/dylan_pr/dylan_pr_runner.py` - Add changelog logic
5. `README.md` - Document new branching strategy

## Testing

1. Test on repository with develop branch
2. Test on repository without develop branch (backwards compatibility)
3. Test all merge strategies
4. Test changelog generation in PR