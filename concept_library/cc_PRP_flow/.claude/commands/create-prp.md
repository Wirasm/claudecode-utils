I want you to help me draft a new PRP based on the PRP structure in the PRPs/ directory.

PRP name: $ARGUMENTS

## Research Phase

I'll first conduct thorough research to understand the required context:

1. **Explore documentation** - I'll check if the user has added any relevant documentation in the ai_docs/ directory
2. **Analyze existing PRPs** - I'll examine the structure and patterns in existing PRPs, especially base_template_v1
3. **Explore codebase** - I'll identify relevant files that should be referenced in the PRP
4. **Web search if needed** - For any external libraries or concepts mentioned that require additional context

## Initial Information Gathering

Let me check:
1. Existing code structure
2. Similar features or patterns in the codebase
3. Documentation in ai_docs/ directory
4. Any external resources needed for context

## PRP Structure

I'll craft a comprehensive PRP with these sections:

```markdown
## Goal
A clear, concise statement of what this PRP aims to achieve

## Why
- Business justification explaining why this change is needed
- Who will benefit from this implementation
- The value this feature brings to the project
- How it integrates with or enhances existing functionality

## What
- Detailed explanation of the feature or change to be implemented
- Core functionality
- Key components
- User/system interactions
- Scope boundaries

## Endpoints/APIs to Implement
If applicable, list of API endpoints or interfaces to be created/modified

## Current Directory Structure
Tree-like representation of the current relevant directory structure

## Proposed Directory Structure
Tree-like representation showing new files and directories to be created

## Files to Reference
List of existing files that should be used as references, with explanations

## Files to Implement (concept)
Detailed descriptions of files to be created or modified, with sample code

## Implementation Notes
Specific guidance, patterns to follow, and technical considerations

## Validation Gates
Specific criteria that must be met for implementation to be considered complete
- Testing requirements
- Performance metrics
- Compatibility requirements
- Explicit test commands to run
- Expected outcomes

## Implementation Checkpoints/Testing
Step-by-step checkpoints for implementation and testing

## Other Considerations
- Security concerns
- Performance implications
- Scalability factors
- Backward compatibility
- Future extensibility
- Dependencies
- Potential risks or limitations
```

## Best Practices I'll Follow

1. **CONTEXT IS KING** - I'll provide comprehensive context by referencing:
   - Specific files in the codebase
   - Documentation from ai_docs/
   - Relevant URLs for external libraries
   - Example implementations

2. **Clear implementation patterns** - I'll clearly define HOW the feature should be implemented, not just WHAT

3. **Validation gates** - I'll include specific commands to verify the implementation works correctly

4. **Deterministic checks** - I'll ensure validation can be objectively measured

***REMEMBER: A PRP is a PRD + curated codebase intelligence + agent/runbook—the minimum viable packet an AI needs to ship production-ready code on the first pass.***