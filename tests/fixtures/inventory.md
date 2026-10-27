# Skills inventory (source of truth for tailoring)

Rule: a skill goes into a tailored resume only if it has an evidence line here. Never add a keyword that is not here — gaps go into the cover letter instead.
Status: `documented` = already in a profile resume or `info/`; `confirmed <date>` = user confirmed in chat with the detail shown; `NOT` = asked and not claimed (do not write it).
Updated 2026-10-09 after the skills interview.

## Frontend
| Skill | Status | Evidence / safe wording |
|---|---|---|
| React, Redux, TypeScript, GraphQL clients | documented | silpo.ua SPA 2018–present |
| Next.js | documented | resumes |
| Angular | documented + confirmed 2026-10-08 | 3+ years commercial; Angular Page Builder (SSR, 10+ widgets), React→Angular migration |
| CSS Modules, Stylus, Webpack, HTML5/CSS3 | documented | resumes |
| Tailwind CSS | confirmed 2026-10-09 | silpo.ua back-office; in 3 profiles' skills line |
| Storybook / design system | confirmed 2026-10-09 | silpo.ua, Angular project: used Storybook, updated and added components |
| NX monorepo | confirmed 2026-10-09 | Angular monorepo on silpo.ua; extended the NX configuration (user). Turborepo NOT confirmed |
| i18n (internationalisation) | confirmed 2026-10-09 | built-in Angular i18n, used in the silpo.ua Angular monorepo (user: "користувався" — used it, not owned the whole lifecycle). Crowdin / any translation management system NOT confirmed; do not claim "i18n lifecycle" or TMS integration |
| Next.js App Router | confirmed 2026-10-09 (personal projects only) | not in production work; write "Next.js (App Router in personal projects)" if claimed at all |
| Figma | confirmed 2026-10-09 | worked with Figma as a developer and set up / connected a Figma MCP server (user) |
| PWA / service worker (partial) | confirmed 2026-10-14 (limited) | silpo.ua: service worker serving a standalone offline page — list of supermarkets with filtering and a link to the map (user). Web app manifest / installability, push notifications, caching strategies, Workbox NOT confirmed. Write "service worker, offline page", never "PWA expertise" or "built a PWA" |
| Jest (unit tests) | confirmed 2026-10-09 | silpo.ua, unit tests for both Angular and React. Vitest NOT confirmed |
| Playwright E2E (visual regression) | confirmed 2026-10-09 | end-to-end tests to catch CSS/visual changes. Cypress is in resumes separately |
| Accessibility (WCAG, ARIA, screen-reader testing) | documented | `info/accessibility-silpo-collaboration.md` (audit 60→95/100, 3 months with screen-reader user) |
| Core Web Vitals / bundle optimisation | documented | LCP/FCP −40%, bundle −17% |
| Electron | documented (dated) | Bizerba scale app ~2017, first iteration |
| Web components with Lit | confirmed 2026-10-21 | user: "lit в проді на сільпо" — Lit web components in production on silpo.ua. Which components / scope not specified; ask before describing them. Stencil.js NOT confirmed |
| Zustand / Redux Toolkit / TanStack Query | NOT confirmed | do not claim |

## Backend / infra
| Skill | Status | Evidence / safe wording |
|---|---|---|
| Node.js, GraphQL, REST API design | documented | recipe-service, banners service, page-builder-service, 404-service |
| Express | confirmed 2026-10-09 | server APIs for MCP aggregators (own projects) |
| NestJS | confirmed 2026-10-09 | pet projects only — say "personal projects", not production |
| Docker / docker-compose | confirmed 2026-10-09 | silpo.ua: local development and production pipelines |
| RabbitMQ | confirmed 2026-10-09 | message-queue intermediary server exchanging messages with a closed (isolated) network so no ports are opened outward. Redis: personal projects only (2026-10-23). Kafka/SQS NOT confirmed |
| PostgreSQL (RDS) | documented | resumes |
| ORM: TypeORM (work), Prisma (personal) | confirmed 2026-10-21 | TypeORM in the silpo.ua Angular project; Prisma in a pet project only. Drizzle NOT confirmed |
| Role-based access (multi-role system) | confirmed 2026-10-21 | user: "RBAC була система мульти ролей". Project/scope not specified — write "worked with a multi-role access system", not "designed RBAC" |
| Payments via a Ukrainian payment processor | confirmed 2026-10-21 | gift certificates and event tickets on silpo.ua paid through a Ukrainian processing provider (provider not named). Stripe NOT confirmed |
| Multi-brand theming (Silpo + Fora) | confirmed 2026-10-21 | first versions of the site were one codebase for Fora and Silpo, styled only via CSS. This is multi-brand/theming, not tenant data isolation — say "one codebase served two retail brands (Silpo, Fora), themed via CSS", do not write "multi-tenant architecture" |
| SQL beyond ORM | confirmed 2026-10-09 | wrote queries against master data while debugging (debugging-level, not DBA/optimisation) |
| AWS (EKS, RDS, S3, CloudWatch) | documented, scope clarified 2026-10-12 | USER level only: worked with services running on the platform; did not provision or set up AWS infrastructure from scratch (DevOps did). Do NOT write "took part in EKS optimisation / RDS migration" — those `info/` pages are team/platform work, not his |
| CI/CD on Azure DevOps | confirmed 2026-10-12 | built the CI/CD himself (user) |
| CI/CD on GitLab | confirmed 2026-10-12 | extended the existing CI image (user); did not build the GitLab pipelines from scratch |
| Sentry | documented | resumes |
| Release practice | confirmed 2026-10-12 | finished tasks deployed every 2–3 days; some services deploy separately, so sometimes daily. Prod bug: if the cause is understood — quick fix (hotfix); if not — roll back to the previous release, reproduce on the test environment, ship a new release. When several services change, order matters (e.g. banners-service first, then api-gateway, then check on prod; QA env before prod) — user confirmed 2026-10-13. Moved silpo.ua frontend to GitLab as part of the team; extended the existing CI image (not built from scratch) |
| Spark/dbt/Airflow/Trino, MinIO/S3, Grafana, CloudWatch | documented (working familiarity) | `info/achievements-and-architecture.md` |
| FastAPI | confirmed 2026-10-21 (no detail) | user ticked FastAPI for the Sii check; work vs pet not specified — say "FastAPI (personal projects)" unless told otherwise. SQLAlchemy/Alembic and AWS Lambda NOT confirmed |
| MongoDB / DynamoDB / ElasticSearch | confirmed 2026-10-23 (personal projects only) | user: "використовував на пет проектах" for all three. Not production — list only under the "Personal projects" skills row, never in a work bullet |
| Kubernetes, Redis, Cloudflare | confirmed 2026-10-23 (personal projects only) | same answer. Work-side context stays as before: AWS EKS at user level; Cloudflare SEO redirects (documented). Do not write production K8s/Redis. Terraform/Helm still NOT confirmed |
| "Personal projects" skills row | applied 2026-10-23 | NestJS, Prisma, Redis, MongoDB, DynamoDB, Elasticsearch, Kubernetes, Cloudflare, WebSockets. Added to the general resume and to fullstack, ai-lead, FDE, platform-architect (frontend-dev has a shorter row) |
| Terraform / Helm / K8s manifests | NOT confirmed (Kubernetes in personal projects only, 2026-10-23) | do not claim production K8s, Terraform or Helm |
| GCP | NOT confirmed | AWS only |

## AI / LLM
| Skill | Status | Evidence / safe wording |
|---|---|---|
| Claude Code, Kiro, Gemini, Codex (assistants, daily) | documented | resumes (6+ months) |
| Custom MCP servers | documented | codebase memory/graph search, job pipeline; public mcp-book-lover, silpo-agent-cli; plus MCPs added to speed up team processes |
| MCP integrations with Jira and GitLab | confirmed 2026-10-21 | work project at TEMABIT, used by the team (user: "MCP до Jira і GitLab для команди, робочий проєкт"). Built vs configured not specified — write "set up MCP integrations with Jira and GitLab for the team", not "built" |
| LLM features for internal use at the company | confirmed 2026-10-21 | user: "ллм фічі для внутрішнього використання в компанії" + public CLIs in repos. Internal users only — write "LLM-based tools used internally at the company", never "shipped LLM features to customers/end users". Specific features not named yet; ask before describing one |
| Git worktree for agents; multiple AI agents in parallel | confirmed 2026-10-21 | user ticked both for the Anadea check. Safe wording: "run several AI agents in parallel in separate git worktrees" |
| Before/after eval measurement | NOT (asked 2026-10-21) | no prompt/model change measured on a fixed set — disclose as a gap |
| Skills and agents trained on the team's project base | confirmed 2026-10-09 | wrote skills/agents that work from project context for coding and for building the backlog; created and added MCPs |
| Own CLIs and AI-related side projects | confirmed 2026-10-09 | public repos (silpo-agent-cli etc.) |
| LLM-as-judge reviewer pass | confirmed 2026-10-09 | mandatory step in the application workflow (CLAUDE.md): a second model critiques AI-drafted resumes/letters against explicit criteria (fabricated claims, generic language, missed keyword matches, resume/letter inconsistencies) before they are presented as final |
| Verification of delegated AI-agent output | confirmed 2026-10-09 | rules for antigravity-worker: diff every change, rerun the tests, live smoke on real URLs; documented its failure modes (overclaiming reports, tests that only assert assigned variables, "wired" code never wired, stale snapshots) |
| Validation of a local classifier (Laya) for vacancy triage | confirmed 2026-10-09 | two passes against known postings (caught Ruby on Rails and Go backends; `genuinely_remote` stayed ~coin-flip so it is corroborating only); small sample, no saved labelled set |
| Structured output / "evals" as a framework | NOT confirmed | no golden set, no metrics over time, no re-run on prompt/model change — do not write "evals framework" or "evaluation pipeline". Safe keywords: LLM-as-judge, AI output verification, agent review |
| Generative-AI API integrations in public CLIs | confirmed 2026-10-09 | `kie-media-cli` (KIE API: image/video/audio generation, live model registry, cost, history; npm 0.3.1), `hi3d-cli` (Hi3D API text/image-to-3D, 6 formats, agent skill; npm 0.1.25), `mcp-comfy-ui-builder` (ComfyUI, 50+ MCP tools, WebSocket real-time execution; npm 2.4.1). Source: `info/open-source-repositories.md`, repos and packages verified public 2026-10-09 |
| Published packages (npm, PyPI) | confirmed 2026-10-09 | npm: mcp-comfy-ui-builder, kie-media-cli, hi3d-cli; PyPI: laya-cli 0.2.4, mcp-book-lover 0.1.8 and others listed in `info/open-source-repositories.md` (pexels-cli shows 0.1.0 on PyPI, the file says 0.2.5 — verify before quoting a version) |
| Agent skills published (skills.sh) | confirmed 2026-10-09 | hi3d-skills, job-search-skills, building-with-laya-skill |
| Direct text-LLM API (OpenAI/Anthropic) in own code | PARTIAL | `my-cli` multi-provider terminal assistant (OpenAI, Ollama, LM Studio, Merlin; skills, MCP, sub-agents) is local only, no public URL — say "personal", do not link. Public generative-media CLIs above are API integrations but not text-LLM calls: write "generative AI APIs", not "LLM API" |
| RAG / embeddings / vector DB | NOT confirmed | do not claim |

## Data / analytics / domains
| Skill | Status | Evidence / safe wording |
|---|---|---|
| E-commerce (catalog, cart, checkout, recipes, banners) | documented | silpo.ua |
| A/B testing | documented (Practices line) | resumes |
| Analytics counters and metrics monitoring | confirmed 2026-10-09 | silpo.ua: installed counters (analytics tags), monitored metrics, optimised execution. GA/GTM/pixel names not specified — write "analytics counters", not product names |
| SEO | documented + confirmed 2026-10-09 | `info/achievements-and-architecture.md`: Cloudflare redirects from old pages, SEO for dynamic pages (route list in Angular), sitemap/breadcrumbs, SSR Page Builder "for SEO and performance" |
| SSR | documented + confirmed 2026-10-09 | Angular Page Builder with SSR (silpo.ua); also personal projects and one iteration of the Fora store |
| Python | confirmed 2026-10-09 | courses + public repos only; NOT professional. But the public Python code is substantial and published on PyPI: laya-cli, mcp-book-lover, workatastartup-mcp, mcp-elevenreader, pexels-cli, gifboom, silpo-agent-cli. Safe wording: "Python (personal projects, PyPI packages)" |
| TypeScript / Node CLIs and MCP servers (public) | confirmed 2026-10-09 | mcp-comfy-ui-builder, kie-media-cli, hi3d-cli, perplexity-pro-mcp (GitHub language field shows JavaScript for the two CLIs, file says TypeScript — check before claiming TS for them) |

## Practices / languages / terms
| Item | Status | Evidence |
|---|---|---|
| ADR, mentoring 5+ to senior, hiring interviews, React Forum | documented | resumes |
| English B2, Ukrainian/Russian native | documented | resumes |
| B2B / ФОП contract | confirmed 2026-10-08 | MEDvidi form |
| Salary policy | see memory `project_salary-expectation` | verify current numbers |

## Candidate additions to resumes (applied 2026-10-23 together with the keyword-frequency pass over 434 postings)
- Frontend line: `Storybook`, `Jest`, `Playwright` (confirmed).
- Backend line: `Express`, `RabbitMQ`, `Docker` (confirmed; NestJS only as personal projects).
- Practices: `SEO`, `SSR`, analytics counters.
- Python: do not add as a skill; if added, "Python (personal projects, public repos)" only.
