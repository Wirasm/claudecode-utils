name: "Base PRP Template"
description: |

## Purpose of this Template

This document provides a standardized Product Requirement Prompt (PRP) template for implementing new features or making significant changes to any codebase. PRPs serve as comprehensive specifications that provide AI coding assistants with sufficient context to implement a feature correctly.

## How to Use This Template

1. Copy this template to create a new PRP
2. Replace the placeholders with your specific implementation details
3. Include sufficient context for each section, referencing existing code paths
4. Be explicit about implementation patterns to follow
5. Include examples where helpful
6. Reference any external documentation, resources, or code patterns
7. Fill out all sections, using "N/A" only when a section truly doesn't apply

---

## Goal

[Concise statement of what this PRP aims to achieve]

## Why

- [Business justification explaining why this change is needed]
- [Who will benefit from this implementation]
- [The value this feature brings to the project]
- [How it integrates with or enhances existing functionality]

## What

[Detailed explanation of the feature or change to be implemented, including:]

- [Core functionality]
- [Key components]
- [User/system interactions]
- [Scope boundaries]

## Endpoints/APIs to Implement

[If applicable, list the API endpoints or interfaces to be created/modified:]

Example:
<Name> – [METHOD] /path – one-line purpose

- Params (typed)
- Success response shape
- Failure response shape

Example:
**[Endpoint Name]**

- [HTTP Method] [Path]
- [Brief description]
- [Key parameters]
- [Response format]

Example:
**[Endpoint Name]**

- [HTTP Method] [Path]
- [Brief description]
- [Key parameters]
- [Response format]

## Current Directory Structure

```
[Provide a tree-like representation of the current relevant directory structure]
├── [directory]
│   ├── [file]
│   └── [subdirectory]
│       ├── [file]
│       └── [file]
```

## Proposed Directory Structure

```
[Provide a tree-like representation of the proposed directory structure with new files]
├── [directory]
│   ├── [existing file]
│   ├── [new file]
│   └── [subdirectory]
│       ├── [existing file]
│       ├── [new file] Specify file content when appropriate
│       └── [new file] Specify file content when appropriate
```

## Files to Reference

- [File path 1] (read_only) [Brief description of how this file should be used as reference]
- [File path 2] (read_only) [Brief description of its relevance]
- [Documentation URL] (read_only) [Brief description of documentation]
- [Example file path] (read_only) [Explanation of the pattern to follow]

## Files to Implement (concept)

### [Component Category 1]

1. `[file_path]` - [Brief description]

```[language]
[Sample code or structure illustrating the implementation concept]
```

2. `[file_path]` - [Brief description]

```[language]
[Sample code or structure illustrating the implementation concept]
```

### [Component Category 2]

1. `[file_path]` - [Brief description]

```[language]
[Sample code or structure illustrating the implementation concept]
```

## Implementation Notes

### [Topic 1]

- [Detailed implementation guidance]
- [Technical considerations]
- [Design patterns to follow]
- [Edge cases to handle]

### [Topic 2]

- [Detailed implementation guidance]
- [Technical considerations]
- [Design patterns to follow]
- [Edge cases to handle]

## Validation Gates

- [Specific criteria that must be met for implementation to be considered complete]
- [Testing requirements]
- [Performance metrics]
- [Compatibility requirements]
- [Explicit test commands to run]
- [Expected outcomes]

## Implementation Checkpoints/Testing

### 1. [Checkpoint Name]

- [Steps to implement this checkpoint]
- [Testing approach]
- [Expected results]
- [Command to verify: `example test command`]

### 2. [Checkpoint Name]

- [Steps to implement this checkpoint]
- [Testing approach]
- [Expected results]
- [Command to verify: `example test command`]

## Other Considerations

- [Security concerns]
- [Performance implications]
- [Scalability factors]
- [Backward compatibility]
- [Future extensibility]
- [Dependencies]
- [Potential risks or limitations]

---

## Template Usage Examples

### For Server Endpoints

- Goal: "Implement REST API endpoints for user authentication"
- Files to Reference: "src/auth/existing_auth_service.js for auth logic patterns"
- Validation Gates: "All endpoints must include proper error handling with appropriate HTTP status codes"

### For UI Components

- Goal: "Create a reusable dropdown component with support for search and multi-select"
- Files to Reference: "src/components/Button.jsx for styling conventions"
- Implementation Notes: "Component must be accessible and keyboard navigable"

### For Database Schema Changes

- Goal: "Add support for storing user preferences"
- Files to Reference: "database/migrations/20230101_create_users.sql for migration patterns"
- Validation Gates: "Migration must be reversible with a corresponding down migration"

### For Refactoring

- Goal: "Refactor authentication service to use dependency injection"
- Files to Reference: "src/services/payment_service.js for DI pattern examples"
- Other Considerations: "Must maintain backward compatibility with existing service interfaces"
