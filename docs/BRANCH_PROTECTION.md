# Branch Protection Configuration

## Overview

This repository has branch protection rules configured to ensure code quality and prevent accidental changes to critical branches.

## Protected Branches

### Main Branch (`main`)

The main branch is protected with the following rules:

#### Pull Request Requirements
- **Required Approving Reviews**: At least 1 approving review is required before merging
- **Dismiss Stale Reviews**: Pull request approvals are automatically dismissed when new commits are pushed
- **Allowed Merge Methods**: Merge commits, squash merging, and rebase merging are all permitted

#### Branch Protection Rules
- **Prevent Force Pushes**: Force pushes to the main branch are not allowed (non-fast-forward rule)
- **Prevent Deletion**: The main branch cannot be deleted
- **Direct Commits**: Direct commits to main are blocked; all changes must go through pull requests

## Rationale

Branch protection rules provide several benefits:

1. **Code Quality**: Requiring pull request reviews ensures that all code changes are reviewed before merging
2. **Collaboration**: The PR workflow encourages discussion and knowledge sharing among team members
3. **Safety**: Preventing force pushes and deletions protects the repository history
4. **Auditability**: All changes are traceable through pull requests

## Configuration Details

The branch protection is configured using GitHub Repository Rulesets (modern approach). The ruleset ID is `15683117`.

### Viewing the Configuration

You can view the current ruleset configuration using the GitHub CLI:

```bash
gh api repos/chipoto69/herodash/rulesets/15683117
```

Or view it in the GitHub web interface at:
https://github.com/chipoto69/HeroDash/rules/15683117

### Modifying the Configuration

To modify the branch protection rules, you need admin access to the repository. Use the GitHub web interface or the GitHub API:

```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  repos/chipoto69/herodash/rulesets/15683117 \
  --input ruleset.json
```

## Best Practices

When working with protected branches:

1. **Create Feature Branches**: Always create a new branch for your work
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Push Your Changes**: Push your feature branch to the remote repository
   ```bash
   git push -u origin feature/your-feature-name
   ```

3. **Open a Pull Request**: Create a pull request through GitHub's web interface or CLI
   ```bash
   gh pr create --base main --head feature/your-feature-name
   ```

4. **Request Reviews**: Tag team members for review or wait for automated reviewers

5. **Address Feedback**: Make any requested changes and push updates to your branch

6. **Merge**: Once approved, merge your pull request using your preferred merge method

## Troubleshooting

### "Push declined due to repository rule violations"

This error occurs when you try to push directly to the main branch. Solution: Create a feature branch and open a pull request instead.

### "Pull request requires approving reviews before merging"

Your PR needs at least one approval. Request a review from a team member or add additional reviewers.

## Further Reading

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Repository Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
