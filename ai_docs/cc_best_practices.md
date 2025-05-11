Claude Code: Best practices for agentic coding
Published Apr 18, 2025

Claude Code is a command line tool for agentic coding. This post covers tips and tricks that have proven effective for using Claude Code across various codebases, languages, and environments.

We recently released Claude Code, a command line tool for agentic coding. Developed as a research project, Claude Code gives Anthropic engineers and researchers a more native way to integrate Claude into their coding workflows.

Claude Code is intentionally low-level and unopinionated, providing close to raw model access without forcing specific workflows. This design philosophy creates a flexible, customizable, scriptable, and safe power tool. While powerful, this flexibility presents a learning curve for engineers new to agentic coding tools—at least until they develop their own best practices.

This post outlines general patterns that have proven effective, both for Anthropic's internal teams and for external engineers using Claude Code across various codebases, languages, and environments. Nothing in this list is set in stone nor universally applicable; consider these suggestions as starting points. We encourage you to experiment and find what works best for you!

Looking for more detailed information? Our comprehensive documentation at claude.ai/code covers all the features mentioned in this post and provides additional examples, implementation details, and advanced techniques.


1. Customize your setup
Claude Code is an agentic coding assistant that automatically pulls context into prompts. This context gathering consumes time and tokens, but you can optimize it through environment tuning.

a. Create CLAUDE.md files
CLAUDE.md is a special file that Claude automatically pulls into context when starting a conversation. This makes it an ideal place for documenting:

Common bash commands
Core files and utility functions
Code style guidelines
Testing instructions
Repository etiquette (e.g., branch naming, merge vs. rebase, etc.)
Developer environment setup (e.g., pyenv use, which compilers work)
Any unexpected behaviors or warnings particular to the project
Other information you want Claude to remember
There’s no required format for CLAUDE.md files. We recommend keeping them concise and human-readable. For example:

# Bash commands
- npm run build: Build the project
- npm run typecheck: Run the typechecker

# Code style
- Use ES modules (import/export) syntax, not CommonJS (require)
- Destructure imports when possible (eg. import { foo } from 'bar')

# Workflow
- Be sure to typecheck when you’re done making a series of code changes
- Prefer running single tests, and not the whole test suite, for performance

Copy
You can place CLAUDE.md files in several locations:

The root of your repo, or wherever you run claude from (the most common usage). Name it CLAUDE.md and check it into git so that you can share it across sessions and with your team (recommended), or name it CLAUDE.local.md and .gitignore it
Any parent of the directory where you run claude. This is most useful for monorepos, where you might run claude from root/foo, and have CLAUDE.md files in both root/CLAUDE.md and root/foo/CLAUDE.md. Both of these will be pulled into context automatically
Any child of the directory where you run claude. This is the inverse of the above, and in this case, Claude will pull in CLAUDE.md files on demand when you work with files in child directories
Your home folder (~/.claude/CLAUDE.md), which applies it to all your claude sessions
When you run the /init command, Claude will automatically generate a CLAUDE.md for you.

b. Tune your CLAUDE.md files
Your CLAUDE.md files become part of Claude’s prompts, so they should be refined like any frequently used prompt. A common mistake is adding extensive content without iterating on its effectiveness. Take time to experiment and determine what produces the best instruction following from the model.

You can add content to your CLAUDE.md manually or press the # key to give Claude an instruction that it will automatically incorporate into the relevant CLAUDE.md. Many engineers use # frequently to document commands, files, and style guidelines while coding, then include CLAUDE.md changes in commits so team members benefit as well.

At Anthropic, we occasionally run CLAUDE.md files through the prompt improver and often tune instructions (e.g. adding emphasis with "IMPORTANT" or "YOU MUST") to improve adherence.

Claude Code tool allowlist
c. Curate Claude's list of allowed tools
By default, Claude Code requests permission for any action that might modify your system: file writes, many bash commands, MCP tools, etc. We designed Claude Code with this deliberately conservative approach to prioritize safety. You can customize the allowlist to permit additional tools that you know are safe, or to allow potentially unsafe tools that are easy to undo (e.g., file editing, git commit).

There are four ways to manage allowed tools:

Select "Always allow" when prompted during a session.
Use the /allowed-tools command after starting Claude Code to add or remove tools from the allowlist. For example, you can add Edit to always allow file edits, Bash(git commit:*) to allow git commits, or mcp__puppeteer__puppeteer_navigate to allow navigating with the Puppeteer MCP server.
Manually edit your .claude/settings.json or ~/.claude.json (we recommend checking the former into source control to share with your team).
Use the --allowedTools CLI flag for session-specific permissions.
d. If using GitHub, install the gh CLI
Claude knows how to use the gh CLI to interact with GitHub for creating issues, opening pull requests, reading comments, and more. Without gh installed, Claude can still use the GitHub API or MCP server (if you have it installed).

2. Give Claude more tools
Claude has access to your shell environment, where you can build up sets of convenience scripts and functions for it just like you would for yourself. It can also leverage more complex tools through MCP and REST APIs.

a. Use Claude with bash tools
Claude Code inherits your bash environment, giving it access to all your tools. While Claude knows common utilities like unix tools and gh, it won't know about your custom bash tools without instructions:

Tell Claude the tool name with usage examples
Tell Claude to run --help to see tool documentation
Document frequently used tools in CLAUDE.md
b. Use Claude with MCP
Claude Code functions as both an MCP server and client. As a client, it can connect to any number of MCP servers to access their tools in three ways:

In project config (available when running Claude Code in that directory)
In global config (available in all projects)
In a checked-in .mcp.json file (available to anyone working in your codebase). For example, you can add Puppeteer and Sentry servers to your .mcp.json, so that every engineer working on your repo can use these out of the box.
When working with MCP, it can also be helpful to launch Claude with the --mcp-debug flag to help identify configuration issues.

c. Use custom slash commands
For repeated workflows—debugging loops, log analysis, etc.—store prompt templates in Markdown files within the .claude/commands folder. These become available through the slash commands menu when you type /. You can check these commands into git to make them available for the rest of your team.

Custom slash commands can include the special keyword $ARGUMENTS to pass parameters from command invocation.

For example, here’s a slash command that you could use to automatically pull and fix a Github issue:

Please analyze and fix the GitHub issue: $ARGUMENTS.

Follow these steps:

1. Use `gh issue view` to get the issue details
2. Understand the problem described in the issue
3. Search the codebase for relevant files
4. Implement the necessary changes to fix the issue
5. Write and run tests to verify the fix
6. Ensure code passes linting and type checking
7. Create a descriptive commit message
8. Push and create a PR

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.

Copy
Putting the above content into .claude/commands/fix-github-issue.md makes it available as the /project:fix-github-issue command in Claude Code. You could then for example use /project:fix-github-issue 1234 to have Claude fix issue #1234. Similarly, you can add your own personal commands to the ~/.claude/commands folder for commands you want available in all of your sessions.

3. Try common workflows
Claude Code doesn’t impose a specific workflow, giving you the flexibility to use it how you want. Within the space this flexibility affords, several successful patterns for effectively using Claude Code have emerged across our community of users:

a. Explore, plan, code, commit
This versatile workflow suits many problems:

Ask Claude to read relevant files, images, or URLs, providing either general pointers ("read the file that handles logging") or specific filenames ("read logging.py"), but explicitly tell it not to write any code just yet.
This is the part of the workflow where you should consider strong use of subagents, especially for complex problems. Telling Claude to use subagents to verify details or investigate particular questions it might have, especially early on in a conversation or task, tends to preserve context availability without much downside in terms of lost efficiency.
Ask Claude to make a plan for how to approach a specific problem. We recommend using the word "think" to trigger extended thinking mode, which gives Claude additional computation time to evaluate alternatives more thoroughly. These specific phrases are mapped directly to increasing levels of thinking budget in the system: "think" < "think hard" < "think harder" < "ultrathink." Each level allocates progressively more thinking budget for Claude to use.
If the results of this step seem reasonable, you can have Claude create a document or a GitHub issue with its plan so that you can reset to this spot if the implementation (step 3) isn’t what you want.
Ask Claude to implement its solution in code. This is also a good place to ask it to explicitly verify the reasonableness of its solution as it implements pieces of the solution.
Ask Claude to commit the result and create a pull request. If relevant, this is also a good time to have Claude update any READMEs or changelogs with an explanation of what it just did.
Steps #1-#2 are crucial—without them, Claude tends to jump straight to coding a solution. While sometimes that's what you want, asking Claude to research and plan first significantly improves performance for problems requiring deeper thinking upfront.

b. Write tests, commit; code, iterate, commit
This is an Anthropic-favorite workflow for changes that are easily verifiable with unit, integration, or end-to-end tests. Test-driven development (TDD) becomes even more powerful with agentic coding:

Ask Claude to write tests based on expected input/output pairs. Be explicit about the fact that you’re doing test-driven development so that it avoids creating mock implementations, even for functionality that doesn’t exist yet in the codebase.
Tell Claude to run the tests and confirm they fail. Explicitly telling it not to write any implementation code at this stage is often helpful.
Ask Claude to commit the tests when you’re satisfied with them.
Ask Claude to write code that passes the tests, instructing it not to modify the tests. Tell Claude to keep going until all tests pass. It will usually take a few iterations for Claude to write code, run the tests, adjust the code, and run the tests again.
At this stage, it can help to ask it to verify with independent subagents that the implementation isn’t overfitting to the tests
Ask Claude to commit the code once you’re satisfied with the changes.
Claude performs best when it has a clear target to iterate against—a visual mock, a test case, or another kind of output. By providing expected outputs like tests, Claude can make changes, evaluate results, and incrementally improve until it succeeds.

c. Write code, screenshot result, iterate
Similar to the testing workflow, you can provide Claude with visual targets:

Give Claude a way to take browser screenshots (e.g., with the Puppeteer MCP server, an iOS simulator MCP server, or manually copy / paste screenshots into Claude).
Give Claude a visual mock by copying / pasting or drag-dropping an image, or giving Claude the image file path.
Ask Claude to implement the design in code, take screenshots of the result, and iterate until its result matches the mock.
Ask Claude to commit when you're satisfied.
Like humans, Claude's outputs tend to improve significantly with iteration. While the first version might be good, after 2-3 iterations it will typically look much better. Give Claude the tools to see its outputs for best results.

Safe yolo mode
d. Safe YOLO mode
Instead of supervising Claude, you can use claude --dangerously-skip-permissions to bypass all permission checks and let Claude work uninterrupted until completion. This works well for workflows like fixing lint errors or generating boilerplate code.

Letting Claude run arbitrary commands is risky and can result in data loss, system corruption, or even data exfiltration (e.g., via prompt injection attacks). To minimize these risks, use --dangerously-skip-permissions in a container without internet access. You can follow this reference implementation using Docker Dev Containers.

e. Codebase Q&A
When onboarding to a new codebase, use Claude Code for learning and exploration. You can ask Claude the same sorts of questions you would ask another engineer on the project when pair programming. Claude can agentically search the codebase to answer general questions like:

How does logging work?
How do I make a new API endpoint?
What does async move { ... } do on line 134 of foo.rs?
What edge cases does CustomerOnboardingFlowImpl handle?
Why are we calling foo() instead of bar() on line 333?
What’s the equivalent of line 334 of baz.py in Java?
At Anthropic, using Claude Code in this way has become our core onboarding workflow, significantly improving ramp-up time and reducing load on other engineers. No special prompting is required! Simply ask questions, and Claude will explore the code to find answers.

Use Claude to interact with git
f. Use Claude to interact with git
Claude can effectively handle many git operations. Many Anthropic engineers use Claude for 90%+ of our git interactions:

Searching git history to answer questions like "What changes made it into v1.2.3?", "Who owns this particular feature?", or "Why was this API designed this way?" It helps to explicitly prompt Claude to look through git history to answer queries like these.
Writing commit messages. Claude will look at your changes and recent history automatically to compose a message taking all the relevant context into account
Handling complex git operations like reverting files, resolving rebase conflicts, and comparing and grafting patches
g. Use Claude to interact with GitHub
Claude Code can manage many GitHub interactions:

Creating pull requests: Claude understands the shorthand "pr" and will generate appropriate commit messages based on the diff and surrounding context.
Implementing one-shot resolutions for simple code review comments: just tell it to fix comments on your PR (optionally, give it more specific instructions) and push back to the PR branch when it's done.
Fixing failing builds or linter warnings
Categorizing and triaging open issues by asking Claude to loop over open GitHub issues
This eliminates the need to remember gh command line syntax while automating routine tasks.

h. Use Claude to work with Jupyter notebooks
Researchers and data scientists at Anthropic use Claude Code to read and write Jupyter notebooks. Claude can interpret outputs, including images, providing a fast way to explore and interact with data. There are no required prompts or workflows, but a workflow we recommend is to have Claude Code and a .ipynb file open side-by-side in VS Code.

You can also ask Claude to clean up or make aesthetic improvements to your Jupyter notebook before you show it to colleagues. Specifically telling it to make the notebook or its data visualizations “aesthetically pleasing” tends to help remind it that it’s optimizing for a human viewing experience.

4. Optimize your workflow
The suggestions below apply across all workflows:

a. Be specific in your instructions
Claude Code’s success rate improves significantly with more specific instructions, especially on first attempts. Giving clear directions upfront reduces the need for course corrections later.

For example:

Poor	Good
add tests for foo.py	write a new test case for foo.py, covering the edge case where the user is logged out. avoid mocks
why does ExecutionFactory have such a weird api?	look through ExecutionFactory's git history and summarize how its api came to be
add a calendar widget	look at how existing widgets are implemented on the home page to understand the patterns and specifically how code and interfaces are separated out. HotDogWidget.php is a good example to start with. then, follow the pattern to implement a new calendar widget that lets the user select a month and paginate forwards/backwards to pick a year. Build from scratch without libraries other than the ones already used in the rest of the codebase.
Claude can infer intent, but it can't read minds. Specificity leads to better alignment with expectations.

Give Claude images
b. Give Claude images
Claude excels with images and diagrams through several methods:

Paste screenshots (pro tip: hit cmd+ctrl+shift+4 in macOS to screenshot to clipboard and ctrl+v to paste. Note that this is not cmd+v like you would usually use to paste on mac and does not work remotely.)
Drag and drop images directly into the prompt input
Provide file paths for images
This is particularly useful when working with design mocks as reference points for UI development, and visual charts for analysis and debugging. If you are not adding visuals to context, it can still be helpful to be clear with Claude about how important it is for the result to be visually appealing.

Mention files you want Claude to look at or work on
c. Mention files you want Claude to look at or work on
Use tab-completion to quickly reference files or folders anywhere in your repository, helping Claude find or update the right resources.

Give Claude URLs
d. Give Claude URLs
Paste specific URLs alongside your prompts for Claude to fetch and read. To avoid permission prompts for the same domains (e.g., docs.foo.com), use /allowed-tools to add domains to your allowlist.

e. Course correct early and often
While auto-accept mode (shift+tab to toggle) lets Claude work autonomously, you'll typically get better results by being an active collaborator and guiding Claude's approach. You can get the best results by thoroughly explaining the task to Claude at the beginning, but you can also course correct Claude at any time.

These four tools help with course correction:

Ask Claude to make a plan before coding. Explicitly tell it not to code until you’ve confirmed its plan looks good.
Press Escape to interrupt Claude during any phase (thinking, tool calls, file edits), preserving context so you can redirect or expand instructions.
Double-tap Escape to jump back in history, edit a previous prompt, and explore a different direction. You can edit the prompt and repeat until you get the result you're looking for.
Ask Claude to undo changes, often in conjunction with option #2 to take a different approach.
Though Claude Code occasionally solves problems perfectly on the first attempt, using these correction tools generally produces better solutions faster.

f. Use /clear to keep context focused
During long sessions, Claude's context window can fill with irrelevant conversation, file contents, and commands. This can reduce performance and sometimes distract Claude. Use the /clear command frequently between tasks to reset the context window.

g. Use checklists and scratchpads for complex workflows
For large tasks with multiple steps or requiring exhaustive solutions—like code migrations, fixing numerous lint errors, or running complex build scripts—improve performance by having Claude use a Markdown file (or even a GitHub issue!) as a checklist and working scratchpad:

For example, to fix a large number of lint issues, you can do the following:

Tell Claude to run the lint command and write all resulting errors (with filenames and line numbers) to a Markdown checklist
Instruct Claude to address each issue one by one, fixing and verifying before checking it off and moving to the next
h. Pass data into Claude
Several methods exist for providing data to Claude:

Copy and paste directly into your prompt (most common approach)
Pipe into Claude Code (e.g., cat foo.txt | claude), particularly useful for logs, CSVs, and large data
Tell Claude to pull data via bash commands, MCP tools, or custom slash commands
Ask Claude to read files or fetch URLs (works for images too)
Most sessions involve a combination of these approaches. For example, you can pipe in a log file, then tell Claude to use a tool to pull in additional context to debug the logs.

5. Use headless mode to automate your infra
Claude Code includes headless mode for non-interactive contexts like CI, pre-commit hooks, build scripts, and automation. Use the -p flag with a prompt to enable headless mode, and --output-format stream-json for streaming JSON output.

Note that headless mode does not persist between sessions. You have to trigger it each session.

a. Use Claude for issue triage
Headless mode can power automations triggered by GitHub events, such as when a new issue is created in your repository. For example, the public Claude Code repository uses Claude to inspect new issues as they come in and assign appropriate labels.

b. Use Claude as a linter
Claude Code can provide subjective code reviews beyond what traditional linting tools detect, identifying issues like typos, stale comments, misleading function or variable names, and more.

6. Uplevel with multi-Claude workflows
Beyond standalone usage, some of the most powerful applications involve running multiple Claude instances in parallel:

a. Have one Claude write code; use another Claude to verify
A simple but effective approach is to have one Claude write code while another reviews or tests it. Similar to working with multiple engineers, sometimes having separate context is beneficial:

Use Claude to write code
Run /clear or start a second Claude in another terminal
Have the second Claude review the first Claude's work
Start another Claude (or /clear again) to read both the code and review feedback
Have this Claude edit the code based on the feedback
You can do something similar with tests: have one Claude write tests, then have another Claude write code to make the tests pass. You can even have your Claude instances communicate with each other by giving them separate working scratchpads and telling them which one to write to and which one to read from.

This separation often yields better results than having a single Claude handle everything.

b. Have multiple checkouts of your repo
Rather than waiting for Claude to complete each step, something many engineers at Anthropic do is:

Create 3-4 git checkouts in separate folders
Open each folder in separate terminal tabs
Start Claude in each folder with different tasks
Cycle through to check progress and approve/deny permission requests
c. Use git worktrees
This approach shines for multiple independent tasks, offering a lighter-weight alternative to multiple checkouts. Git worktrees allow you to check out multiple branches from the same repository into separate directories. Each worktree has its own working directory with isolated files, while sharing the same Git history and reflog.

Using git worktrees enables you to run multiple Claude sessions simultaneously on different parts of your project, each focused on its own independent task. For instance, you might have one Claude refactoring your authentication system while another builds a completely unrelated data visualization component. Since the tasks don't overlap, each Claude can work at full speed without waiting for the other's changes or dealing with merge conflicts:

Create worktrees: git worktree add ../project-feature-a feature-a
Launch Claude in each worktree: cd ../project-feature-a && claude
Create additional worktrees as needed (repeat steps 1-2 in new terminal tabs)
Some tips:

Use consistent naming conventions
Maintain one terminal tab per worktree
If you’re using iTerm2 on Mac, set up notifications for when Claude needs attention
Use separate IDE windows for different worktrees
Clean up when finished: git worktree remove ../project-feature-a
d. Use headless mode with a custom harness
claude -p (headless mode) integrates Claude Code programmatically into larger workflows while leveraging its built-in tools and system prompt. There are two primary patterns for using headless mode:

1. Fanning out handles large migrations or analyses (e.g., analyzing sentiment in hundreds of logs or analyzing thousands of CSVs):

Have Claude write a script to generate a task list. For example, generate a list of 2k files that need to be migrated from framework A to framework B.
Loop through tasks, calling Claude programmatically for each and giving it a task and a set of tools it can use. For example: claude -p “migrate foo.py from React to Vue. When you are done, you MUST return the string OK if you succeeded, or FAIL if the task failed.” --allowedTools Edit Bash(git commit:*)
Run the script several times and refine your prompt to get the desired outcome.
2. Pipelining integrates Claude into existing data/processing pipelines:

Call claude -p “<your prompt>” --json | your_command, where your_command is the next step of your processing pipeline
That’s it! JSON output (optional) can help provide structure for easier automated processing.
For both of these use cases, it can be helpful to use the --verbose flag for debugging the Claude invocation. We generally recommend turning verbose mode off in production for cleaner output.

What are your tips and best practices for working with Claude Code? Tag @AnthropicAI so we can see what you're building!


examples

Claude Code
Tutorials
Practical examples and patterns for effectively using Claude Code in your development workflow.

This guide provides step-by-step tutorials for common workflows with Claude Code. Each tutorial includes clear instructions, example commands, and best practices to help you get the most from Claude Code.

​
Table of contents
Resume previous conversations
Understand new codebases
Fix bugs efficiently
Refactor code
Work with tests
Create pull requests
Handle documentation
Work with images
Use extended thinking
Set up project memory
Set up Model Context Protocol (MCP)
Use Claude as a unix-style utility
Create custom slash commands
Run parallel Claude Code sessions with Git worktrees
​
Resume previous conversations
​
Continue your work seamlessly
When to use: You’ve been working on a task with Claude Code and need to continue where you left off in a later session.

Claude Code provides two options for resuming previous conversations:

--continue to automatically continue the most recent conversation
--resume to display a conversation picker
1
Continue the most recent conversation


claude --continue
This immediately resumes your most recent conversation without any prompts.

2
Continue in non-interactive mode


claude --continue --print "Continue with my task"
Use --print with --continue to resume the most recent conversation in non-interactive mode, perfect for scripts or automation.

3
Show conversation picker


claude --resume
This displays an interactive conversation selector showing:

Conversation start time
Initial prompt or conversation summary
Message count
Use arrow keys to navigate and press Enter to select a conversation.

How it works:

Conversation Storage: All conversations are automatically saved locally with their full message history
Message Deserialization: When resuming, the entire message history is restored to maintain context
Tool State: Tool usage and results from the previous conversation are preserved
Context Restoration: The conversation resumes with all previous context intact
Tips:

Conversation history is stored locally on your machine
Use --continue for quick access to your most recent conversation
Use --resume when you need to select a specific past conversation
When resuming, you’ll see the entire conversation history before continuing
The resumed conversation starts with the same model and configuration as the original
Examples:


# Continue most recent conversation
claude --continue

# Continue most recent conversation with a specific prompt
claude --continue --print "Show me our progress"

# Show conversation picker
claude --resume

# Continue most recent conversation in non-interactive mode
claude --continue --print "Run the tests again"
​
Understand new codebases
​
Get a quick codebase overview
When to use: You’ve just joined a new project and need to understand its structure quickly.

1
Navigate to the project root directory


cd /path/to/project 
2
Start Claude Code


claude 
3
Ask for a high-level overview


> give me an overview of this codebase 
4
Dive deeper into specific components


> explain the main architecture patterns used here 

> what are the key data models?

> how is authentication handled?
Tips:

Start with broad questions, then narrow down to specific areas
Ask about coding conventions and patterns used in the project
Request a glossary of project-specific terms
​
Find relevant code
When to use: You need to locate code related to a specific feature or functionality.

1
Ask Claude to find relevant files


> find the files that handle user authentication 
2
Get context on how components interact


> how do these authentication files work together? 
3
Understand the execution flow


> trace the login process from front-end to database 
Tips:

Be specific about what you’re looking for
Use domain language from the project
​
Fix bugs efficiently
​
Diagnose error messages
When to use: You’ve encountered an error message and need to find and fix its source.

1
Share the error with Claude


> I'm seeing an error when I run npm test 
2
Ask for fix recommendations


> suggest a few ways to fix the @ts-ignore in user.ts 
3
Apply the fix


> update user.ts to add the null check you suggested 
Tips:

Tell Claude the command to reproduce the issue and get a stack trace
Mention any steps to reproduce the error
Let Claude know if the error is intermittent or consistent
​
Refactor code
​
Modernize legacy code
When to use: You need to update old code to use modern patterns and practices.

1
Identify legacy code for refactoring


> find deprecated API usage in our codebase 
2
Get refactoring recommendations


> suggest how to refactor utils.js to use modern JavaScript features 
3
Apply the changes safely


> refactor utils.js to use ES2024 features while maintaining the same behavior 
4
Verify the refactoring


> run tests for the refactored code 
Tips:

Ask Claude to explain the benefits of the modern approach
Request that changes maintain backward compatibility when needed
Do refactoring in small, testable increments
​
Work with tests
​
Add test coverage
When to use: You need to add tests for uncovered code.

1
Identify untested code


> find functions in NotificationsService.swift that are not covered by tests 
2
Generate test scaffolding


> add tests for the notification service 
3
Add meaningful test cases


> add test cases for edge conditions in the notification service 
4
Run and verify tests


> run the new tests and fix any failures 
Tips:

Ask for tests that cover edge cases and error conditions
Request both unit and integration tests when appropriate
Have Claude explain the testing strategy
​
Create pull requests
​
Generate comprehensive PRs
When to use: You need to create a well-documented pull request for your changes.

1
Summarize your changes


> summarize the changes I've made to the authentication module 
2
Generate a PR with Claude


> create a pr 
3
Review and refine


> enhance the PR description with more context about the security improvements 
4
Add testing details


> add information about how these changes were tested 
Tips:

Ask Claude directly to make a PR for you
Review Claude’s generated PR before submitting
Ask Claude to highlight potential risks or considerations
​
Handle documentation
​
Generate code documentation
When to use: You need to add or update documentation for your code.

1
Identify undocumented code


> find functions without proper JSDoc comments in the auth module 
2
Generate documentation


> add JSDoc comments to the undocumented functions in auth.js 
3
Review and enhance


> improve the generated documentation with more context and examples 
4
Verify documentation


> check if the documentation follows our project standards 
Tips:

Specify the documentation style you want (JSDoc, docstrings, etc.)
Ask for examples in the documentation
Request documentation for public APIs, interfaces, and complex logic
​
Work with images
​
Analyze images and screenshots
When to use: You need to work with images in your codebase or get Claude’s help analyzing image content.

1
Add an image to the conversation

You can use any of these methods:

Drag and drop an image into the Claude Code window
Copy an image and paste it into the CLI with cmd+v (on Mac)
Provide an image path claude “Analyze this image: /path/to/your/image.png”
2
Ask Claude to analyze the image


> What does this image show? 
> Describe the UI elements in this screenshot 
> Are there any problematic elements in this diagram? 
3
Use images for context


> Here's a screenshot of the error. What's causing it? 
> This is our current database schema. How should we modify it for the new feature? 
4
Get code suggestions from visual content


> Generate CSS to match this design mockup 
> What HTML structure would recreate this component? 
Tips:

Use images when text descriptions would be unclear or cumbersome
Include screenshots of errors, UI designs, or diagrams for better context
You can work with multiple images in a conversation
Image analysis works with diagrams, screenshots, mockups, and more
​
Use extended thinking
​
Leverage Claude’s extended thinking for complex tasks
When to use: When working on complex architectural decisions, challenging bugs, or planning multi-step implementations that require deep reasoning.

1
Provide context and ask Claude to think


> I need to implement a new authentication system using OAuth2 for our API. Think deeply about the best approach for implementing this in our codebase. 
Claude will gather relevant information from your codebase and use extended thinking, which will be visible in the interface.

2
Refine the thinking with follow-up prompts


> think about potential security vulnerabilities in this approach 
> think harder about edge cases we should handle 
Tips to get the most value out of extended thinking:

Extended thinking is most valuable for complex tasks such as:

Planning complex architectural changes
Debugging intricate issues
Creating implementation plans for new features
Understanding complex codebases
Evaluating tradeoffs between different approaches
The way you prompt for thinking results in varying levels of thinking depth:

“think” triggers basic extended thinking
intensifying phrases such as “think more”, “think a lot”, “think harder”, or “think longer” triggers deeper thinking
For more extended thinking prompting tips, see Extended thinking tips.

Claude will display its thinking process as italic gray text above the response.

​
Set up project memory
​
Create an effective CLAUDE.md file
When to use: You want to set up a CLAUDE.md file to store important project information, conventions, and frequently used commands.

1
Bootstrap a CLAUDE.md for your codebase


> /init 
Tips:

Include frequently used commands (build, test, lint) to avoid repeated searches
Document code style preferences and naming conventions
Add important architectural patterns specific to your project
CLAUDE.md memories can be used for both instructions shared with your team and for your individual preferences. For more details, see Managing Claude’s memory.
​
Set up Model Context Protocol (MCP)
Model Context Protocol (MCP) is an open protocol that enables LLMs to access external tools and data sources. For more details, see the MCP documentation.

Use third party MCP servers at your own risk. Make sure you trust the MCP servers, and be especially careful when using MCP servers that talk to the internet, as these can expose you to prompt injection risk.

​
Configure MCP servers
When to use: You want to enhance Claude’s capabilities by connecting it to specialized tools and external servers using the Model Context Protocol.

1
Add an MCP Stdio Server


# Basic syntax
claude mcp add <name> <command> [args...]

# Example: Adding a local server
claude mcp add my-server -e API_KEY=123 -- /path/to/server arg1 arg2
2
Add an MCP SSE Server


# Basic syntax
claude mcp add --transport sse <name> <url>

# Example: Adding an SSE server
claude mcp add --transport sse sse-server https://example.com/sse-endpoint
3
Manage your MCP servers


# List all configured servers
claude mcp list

# Get details for a specific server
claude mcp get my-server

# Remove a server
claude mcp remove my-server
Tips:

Use the -s or --scope flag to specify where the configuration is stored:
local (default): Available only to you in the current project (was called project in older versions)
project: Shared with everyone in the project via .mcp.json file
user: Available to you across all projects (was called global in older versions)
Set environment variables with -e or --env flags (e.g., -e KEY=value)
Configure MCP server startup timeout using the MCP_TIMEOUT environment variable (e.g., MCP_TIMEOUT=10000 claude sets a 10-second timeout)
Check MCP server status any time using the /mcp command within Claude Code
MCP follows a client-server architecture where Claude Code (the client) can connect to multiple specialized servers
​
Understanding MCP server scopes
When to use: You want to understand how different MCP scopes work and how to share servers with your team.

1
Local-scoped MCP servers

The default scope (local) stores MCP server configurations in your project-specific user settings. These servers are only available to you while working in the current project.


# Add a local-scoped server (default)
claude mcp add my-private-server /path/to/server

# Explicitly specify local scope
claude mcp add my-private-server -s local /path/to/server
2
Project-scoped MCP servers (.mcp.json)

Project-scoped servers are stored in a .mcp.json file at the root of your project. This file should be checked into version control to share servers with your team.


# Add a project-scoped server
claude mcp add shared-server -s project /path/to/server
This creates or updates a .mcp.json file with the following structure:


{
  "mcpServers": {
    "shared-server": {
      "command": "/path/to/server",
      "args": [],
      "env": {}
    }
  }
}
3
User-scoped MCP servers

User-scoped servers are available to you across all projects on your machine, and are private to you.


# Add a user server
claude mcp add my-user-server -s user /path/to/server
Tips:

Local-scoped servers take precedence over project-scoped and user-scoped servers with the same name
Project-scoped servers (in .mcp.json) take precedence over user-scoped servers with the same name
Before using project-scoped servers from .mcp.json, Claude Code will prompt you to approve them for security
The .mcp.json file is intended to be checked into version control to share MCP servers with your team
Project-scoped servers make it easy to ensure everyone on your team has access to the same MCP tools
If you need to reset your choices for which project-scoped servers are enabled or disabled, use the claude mcp reset-project-choices command
​
Connect to a Postgres MCP server
When to use: You want to give Claude read-only access to a PostgreSQL database for querying and schema inspection.

1
Add the Postgres MCP server


claude mcp add postgres-server /path/to/postgres-mcp-server --connection-string "postgresql://user:pass@localhost:5432/mydb"
2
Query your database with Claude


# In your Claude session, you can ask about your database

> describe the schema of our users table
> what are the most recent orders in the system?
> show me the relationship between customers and invoices
Tips:

The Postgres MCP server provides read-only access for safety
Claude can help you explore database structure and run analytical queries
You can use this to quickly understand database schemas in unfamiliar projects
Make sure your connection string uses appropriate credentials with minimum required permissions
​
Add MCP servers from JSON configuration
When to use: You have a JSON configuration for a single MCP server that you want to add to Claude Code.

1
Add an MCP server from JSON


# Basic syntax
claude mcp add-json <name> '<json>'

# Example: Adding a stdio server with JSON configuration
claude mcp add-json weather-api '{"type":"stdio","command":"/path/to/weather-cli","args":["--api-key","abc123"],"env":{"CACHE_DIR":"/tmp"}}'
2
Verify the server was added


claude mcp get weather-api
Tips:

Make sure the JSON is properly escaped in your shell
The JSON must conform to the MCP server configuration schema
You can use -s global to add the server to your global configuration instead of the project-specific one
​
Import MCP servers from Claude Desktop
When to use: You have already configured MCP servers in Claude Desktop and want to use the same servers in Claude Code without manually reconfiguring them.

1
Import servers from Claude Desktop


# Basic syntax 
claude mcp add-from-claude-desktop 
2
Select which servers to import

After running the command, you’ll see an interactive dialog that allows you to select which servers you want to import.

3
Verify the servers were imported


claude mcp list 
Tips:

This feature only works on macOS and Windows Subsystem for Linux (WSL)
It reads the Claude Desktop configuration file from its standard location on those platforms
Use the -s global flag to add servers to your global configuration
Imported servers will have the same names as in Claude Desktop
If servers with the same names already exist, they will get a numerical suffix (e.g., server_1)
​
Use Claude Code as an MCP server
When to use: You want to use Claude Code itself as an MCP server that other applications can connect to, providing them with Claude’s tools and capabilities.

1
Start Claude as an MCP server


# Basic syntax
claude mcp serve
2
Connect from another application

You can connect to Claude Code MCP server from any MCP client, such as Claude Desktop. If you’re using Claude Desktop, you can add the Claude Code MCP server using this configuration:


{
  "command": "claude",
  "args": ["mcp", "serve"],
  "env": {}
}
Tips:

The server provides access to Claude’s tools like View, Edit, LS, etc.
In Claude Desktop, try asking Claude to read files in a directory, make edits, and more.
Note that this MCP server is simply exposing Claude Code’s tools to your MCP client, so your own client is responsible for implementing user confirmation for individual tool calls.
​
Use Claude as a unix-style utility
​
Add Claude to your verification process
When to use: You want to use Claude Code as a linter or code reviewer.

Steps:

1
Add Claude to your build script


// package.json
{
    ...
    "scripts": {
        ...
        "lint:claude": "claude -p 'you are a linter. please look at the changes vs. main and report any issues related to typos. report the filename and line number on one line, and a description of the issue on the second line. do not return any other text.'"
    }
}
​
Pipe in, pipe out
When to use: You want to pipe data into Claude, and get back data in a structured format.

1
Pipe data through Claude


cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt
​
Control output format
When to use: You need Claude’s output in a specific format, especially when integrating Claude Code into scripts or other tools.

1
Use text format (default)


cat data.txt | claude -p 'summarize this data' --output-format text > summary.txt
This outputs just Claude’s plain text response (default behavior).

2
Use JSON format


cat code.py | claude -p 'analyze this code for bugs' --output-format json > analysis.json
This outputs a JSON array of messages with metadata including cost and duration.

3
Use streaming JSON format


cat log.txt | claude -p 'parse this log file for errors' --output-format stream-json
This outputs a series of JSON objects in real-time as Claude processes the request. Each message is a valid JSON object, but the entire output is not valid JSON if concatenated.

Tips:

Use --output-format text for simple integrations where you just need Claude’s response
Use --output-format json when you need the full conversation log
Use --output-format stream-json for real-time output of each conversation turn
​
Create custom slash commands
Claude Code supports custom slash commands that you can create to quickly execute specific prompts or tasks.

​
Create project-specific commands
When to use: You want to create reusable slash commands for your project that all team members can use.

1
Create a commands directory in your project


mkdir -p .claude/commands
2
Create a Markdown file for each command


echo "Analyze the performance of this code and suggest three specific optimizations:" > .claude/commands/optimize.md 
3
Use your custom command in Claude Code


claude > /project:optimize 
Tips:

Command names are derived from the filename (e.g., optimize.md becomes /project:optimize)
You can organize commands in subdirectories (e.g., .claude/commands/frontend/component.md becomes /project:frontend:component)
Project commands are available to everyone who clones the repository
The Markdown file content becomes the prompt sent to Claude when the command is invoked
​
Add command arguments with $ARGUMENTS
When to use: You want to create flexible slash commands that can accept additional input from users.

1
Create a command file with the $ARGUMENTS placeholder


echo "Find and fix issue #$ARGUMENTS. Follow these steps: 1.
Understand the issue described in the ticket 2. Locate the relevant code in
our codebase 3. Implement a solution that addresses the root cause 4. Add
appropriate tests 5. Prepare a concise PR description" >
.claude/commands/fix-issue.md 
2
Use the command with an issue number


claude > /project:fix-issue 123 
This will replace $ARGUMENTS with “123” in the prompt.

Tips:

The $ARGUMENTS placeholder is replaced with any text that follows the command
You can position $ARGUMENTS anywhere in your command template
Other useful applications: generating test cases for specific functions, creating documentation for components, reviewing code in particular files, or translating content to specified languages
​
Create personal slash commands
When to use: You want to create personal slash commands that work across all your projects.

1
Create a commands directory in your home folder


mkdir -p ~/.claude/commands 
2
Create a Markdown file for each command


echo "Review this code for security vulnerabilities, focusing on:" >
~/.claude/commands/security-review.md 
3
Use your personal custom command


claude > /user:security-review 
Tips:

Personal commands are prefixed with /user: instead of /project:
Personal commands are only available to you and not shared with your team
Personal commands work across all your projects
You can use these for consistent workflows across different codebases
​
Run parallel Claude Code sessions with Git worktrees
​
Use worktrees for isolated coding environments
When to use: You need to work on multiple tasks simultaneously with complete code isolation between Claude Code instances.

1
Understand Git worktrees

Git worktrees allow you to check out multiple branches from the same repository into separate directories. Each worktree has its own working directory with isolated files, while sharing the same Git history. Learn more in the official Git worktree documentation.

2
Create a new worktree


# Create a new worktree with a new branch git worktree add
../project-feature-a feature-a # Or create a worktree with an existing
branch git worktree add ../project-bugfix bugfix-123 
This creates a new directory with a separate working copy of your repository.

3
Run Claude Code in each worktree


# Navigate to your worktree 
cd ../project-feature-a # Run Claude Code in this isolated environment claude 
4
In another terminal:


cd ../project-bugfix claude
5
Manage your worktrees


# List all worktrees git worktree list # Remove a worktree when done
git worktree remove ../project-feature-a 
Tips:

Each worktree has its own independent file state, making it perfect for parallel Claude Code sessions
Changes made in one worktree won’t affect others, preventing Claude instances from interfering with each other
All worktrees share the same Git history and remote connections
For long-running tasks, you can have Claude working in one worktree while you continue development in another
Use descriptive directory names to easily identify which task each worktree is for
Remember to initialize your development environment in each new worktree according to your project’s setup. Depending on your stack, this might include:
JavaScript projects: Running dependency installation (npm install, yarn)
Python projects: Setting up virtual environments or installing with package managers
Other languages: Following your project’s standard setup process
​
