# Process Backlog Item

Implement a backlog item and create a pull request for review.

## Arguments

- `$ARGUMENTS` - The backlog item ID (e.g., "1.1", "2.3", "4.5") or story title

## Workflow

1. **Read the backlog** from `backlog.md`
2. **Find the specified item** by ID or title match
3. **Create a feature branch** following naming convention:
   - `feature/{epic}-{story}-{short-description}`
   - Example: `feature/1-1-create-organization`
4. **Implement the story** based on acceptance criteria
5. **Run checks** before committing:
   - Frontend: `npm run typecheck && npm run lint`
   - Backend: `pytest` (if applicable)
6. **Commit changes** with conventional commit message
7. **Push branch** to origin (ideaignitor/docflow)
8. **Create PR** for manual review and merge

## PR Format

```markdown
## Summary
[Brief description based on user story]

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
2. **Wait for manual merge** - Never auto-merge; user reviews and merges each PR
3. **No AI attribution** - Do not include any Claude/AI references in commits or PRs
4. **Follow existing patterns** - Match code style in the codebase
5. **Security first** - This is HR compliance software; audit trails are critical

## Usage

```
/backlog 1.1
/backlog "Create Organization"
/backlog 7.2
```

After the PR is created, wait for user to review and merge before proceeding to the next item.
