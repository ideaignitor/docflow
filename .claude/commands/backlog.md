# Process Backlog Item

Implement a backlog item and create a pull request for review.

## Arguments

- `$ARGUMENTS` - The backlog item ID (e.g., "1.1", "2.3", "4.5") or story title

## Workflow

1. **Read the backlog** from `backlog.md`
2. **Find the specified item** by ID or title match
3. **Find the corresponding GitHub issue** using the issue mapping below
4. **Create a feature branch** following naming convention:
   - `feature/{epic}-{story}-{short-description}`
   - Example: `feature/1-1-create-organization`
5. **Implement the story** based on acceptance criteria
6. **Run checks** before committing:
   - Frontend: `npm run typecheck && npm run lint`
   - Backend: `pytest` (if applicable)
7. **Commit changes** with conventional commit message
8. **Push branch** to origin (ideaignitor/docflow)
9. **Create PR** linking to the issue with `Closes #XX`
10. **After user merges PR**, close the issue with completion comment

## Issue Mapping (Backlog → GitHub Issue)

| Backlog ID | Story Title | GitHub Issue |
|------------|-------------|--------------|
| 1.1 | Create Organization | #8 (CLOSED) |
| 1.2 | Seed Default Roles | #9 (CLOSED) |
| 1.3 | Invite User by Email | #10 |
| 1.4 | Activate User via Magic Link | #11 |
| 1.5 | Assign Role to User | #12 |
| 2.1 | Create Employee Record | #13 |
| 2.2 | Update Employment Status | #14 |
| 2.3 | Link User to Employee | #15 |
| 4.1 | Enable Web Upload | #16 |
| 5.1 | Create Submission Record | #17 |
| 5.2 | Link Submission to Document | #18 |
| 5.3 | Handle Submission Failure | #19 |
| 6.1 | Create Document Shell | #20 |
| 6.2 | Create Document Version | #21 |
| 6.3/6.4 | Document Categories | #22 |
| 6.5 | Document Metadata | #23 |
| 7.1 | Review Queue | #24 |
| 7.2 | Approve Document | #25 |
| 7.3 | Reject Document | #26 |
| 10.1 | Audit Event Emitter | #27 |
| 10.2 | Audit Log Query | #28 |
| - | Entity Timeline Views | #29 |
| 8.1 | State-Based Retention | #30 |
| 8.2 | Retention Scheduling | #31 |
| 9.1 | Create Legal Hold | #32 |
| 9.2 | Apply Legal Hold | #33 |
| 9.3 | Release Legal Hold | #34 |
| - | Check Legal Hold Status | #35 |

## PR Format

```markdown
## Summary
[Brief description based on user story]

Closes #XX

## Backlog Item
**Epic**: [Epic Name]
**Story**: [Story ID] - [Story Title]
**Size**: [Size]

## User Story
**As** [role]
**I want** [capability]
**So that** [benefit]

## Acceptance Criteria
- [ ] AC 1
- [ ] AC 2
- [ ] AC 3

## Changes Made
- [List of changes]

## Testing
- [ ] Unit tests added
- [ ] Manual testing completed
- [ ] Acceptance criteria verified
```

## Important Rules

1. **One PR per backlog item** - Do not combine multiple stories
2. **Link to GitHub issue** - Use `Closes #XX` in PR body to auto-close on merge
3. **Wait for manual merge** - Never auto-merge; user reviews and merges each PR
4. **No AI attribution** - Do not include any Claude/AI references in commits or PRs
5. **Follow existing patterns** - Match code style in the codebase
6. **Security first** - This is HR compliance software; audit trails are critical

## Post-Merge Actions

After the user confirms the PR is merged:
1. Verify the issue was auto-closed (if `Closes #XX` was used)
2. If not auto-closed, manually close with: `gh issue close XX --repo ideaignitor/docflow --comment "Completed via PR #YY"`

## Usage

```
/backlog 1.3
/backlog "Invite User by Email"
/backlog 7.2
```

After the PR is created, wait for user to review and merge before proceeding to the next item.
