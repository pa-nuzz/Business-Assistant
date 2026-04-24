---
auto_execution_mode: 0
description: Auto-activate relevant skills based on user request keywords and context.
---
# Skill Auto-Activation Workflow


When the user makes a request, analyze the intent and **automatically** suggest or apply the most relevant skill(s).

## Step 1: Intent Analysis
Read the user's request and identify keywords matching these categories:

| Keywords | Activate Skills |
|---|---|
| design, UI, UX, landing page, color, font, style, component, theme, layout, hero section, dashboard, form | ui-ux-pro-max, ui-design, ui-audit |
| animation, motion, transition, spring, gesture, drag, scroll, fade | ui-animation |
| debug, bug, fix, error, broken, crash, investigate, trace | systematic-debugging |
| test, testing, TDD, spec, coverage, unit test, integration test | test-driven-development |
| architecture, structure, folder, setup, scaffold, organize, monorepo, backend, frontend boundary | define-architecture, scaffold-nextjs, scaffold-cli |
| review, PR, code review, quality check, audit, examine | review-pr, caveman-review, ui-audit, requesting-code-review |
| write, blog, article, documentation, README, tutorial, how-to, guide | blog-post, docs-writing, readme-creator, copywriting |
| copy, marketing, CTA, landing page text, product description, email, headline | copywriting |
| SEO, meta tag, sitemap, structured data, canonical, performance | optimise-seo |
| presentation, slides, deck, pitch, investor | presentation-creator |
| plan, strategy, roadmap, milestone, task breakdown, todo, checklist | writing-plans, executing-plans, verification-before-completion |
| brainstorm, ideate, explore, alternatives, solutions, ideas | brainstorming |
| git, worktree, branch, commit, merge, rebase | using-git-worktrees, linear-worktree, caveman-commit |
| subagent, delegate, parallel, concurrent, multi-agent | dispatching-parallel-agents, subagent-driven-development |
| typography, font, spacing, line-height, letter-spacing, font-family | typography-audit |
| mindmap, diagram, visualize, flowchart, concept map | mermaid-mind-map |
| SaaS, tenant, multi-tenant, white-label, subdomain, custom domain | multi-tenant-architecture |

## Step 2: Apply Skills
1. **Activate** the identified skills by referencing them by name in your thinking process.
2. **Load** the SKILL.md content for any skill you reference.
3. **Apply** the skill's methodology, rules, and workflows to the user's request.
4. **Cross-reference** multiple skills if the task spans categories (e.g., a landing page needs ui-ux-pro-max + copywriting + optimise-seo).

## Step 3: Always-On Verification
Before completing ANY task:
1. Run **verification-before-completion** checklist
2. Verify all requirements are met
3. Verify no TODOs or placeholders remain
4. Verify tests pass (if applicable)
5. Verify documentation is updated (if applicable)

## Step 4: Best Practices Always Apply
Regardless of which skill is active, always follow:
- 01-coding-standards.md rules
- Security, accessibility, performance, and git hygiene standards
- Error handling and input validation