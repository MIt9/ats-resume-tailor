# Open-source репозиторії (MIt9 / github.com/MIt9)

> Джерело: `~/work/` + `~/work/git-promo/TASKS.md`, `TASKS-PHASE2.md`. Опис звірено з README + package.json / pyproject.toml 2026-10-09.
> Призначення: source of truth для резюме — копіпастити по 1 рядку в Summary / Side Projects, не переписувати.

## MCP-сервери

### mcp-comfy-ui-builder
- **GitHub:** https://github.com/MIt9/mcp-comfy-ui-builder
- **Що:** Керування ComfyUI з Claude / Cursor — 50+ MCP-тулів, без ручного редагування JSON.
- **Стек:** TypeScript, Node, WebSocket, knowledge base 62+ нод.
- **Install:** `npm install mcp-comfy-ui-builder` (npm 2.4.1), `server.json` + `mcpName` валідні.
- **Рядок для резюме:** `mcp-comfy-ui-builder — MCP server for ComfyUI (50+ tools, WebSocket real-time execution)`

### perplexity-pro-mcp (~/work/mcp-perplexity)
- **GitHub:** https://github.com/MIt9/perplexity-pro-mcp
- **Що:** Веб-пошук з Claude / Cursor через Perplexity AI Pro — deep search, follow-up питання, експорт тредів. Працює через cookie браузерної сесії, без окремого API-ключа.
- **Стек:** TypeScript, MCP SDK.
- **Install:** `npx perplexity-pro-mcp`, JSON-конфіг для Claude Desktop / Cursor.
- **Рядок для резюме:** `perplexity-pro-mcp — MCP server for Perplexity Pro deep search (no extra API key)`

### mcp-elevenreader
- **GitHub:** https://github.com/MIt9/mcp-elevenreader
- **Що:** TTS-читання документів з Claude / Cursor — завантаження EPUB/PDF, черга читання, контроль відтворення через ElevenLabs ElevenReader.
- **Стек:** Python, MCP.
- **Install:** `pip install mcp-elevenreader` (0.1.3).
- **Рядок для резюме:** `mcp-elevenreader — MCP server for ElevenReader TTS (queue + playback control)`

### mcp-book-lover
- **GitHub:** https://github.com/MIt9/mcp-book-lover
- **Що:** AI-бібліотекар — reading lists, прогрес, рецензії, цілі, рекомендації, пошук у 8 джерелах, конвертація форматів, синхронізація з ElevenReader. 35+ тулів.
- **Стек:** Python, MCP.
- **Install:** pip (0.1.8).
- **Рядок для резюме:** `mcp-book-lover — MCP book library manager (35+ tools, 8 sources, TTS sync)`

### workatastartup-mcp
- **GitHub:** https://github.com/MIt9/workatastartup-mcp
- **Що:** Пошук вакансій YC Work at a Startup з Claude / Cursor.
- **Стек:** Python, MCP.
- **Install:** pip (0.1.2).
- **Рядок для резюме:** `workatastartup-mcp — MCP server for YC startup jobs search`

### silpo-mcp (private / local)
- **GitHub:** https://github.com/MIt9/silpo-mcp
- **Що:** MCP-сервер для API Сільпо (каталог, кошик, замовлення). База для silpo-agent-cli.
- **Стек:** TypeScript, Express, Node ≥18.
- **Рядок для резюме:** не виносити як public; лише `MCP server for Silpo API (personal project)` якщо треба.

## CLI-утиліти

### laya-cli
- **GitHub:** https://github.com/MIt9/laya-cli
- **Що:** Typed decisions за 33ms без генерації і галюцинацій — `choice` / `score` / `noul` для людей і AI-агентів. Один load моделі, streaming batch mode.
- **Стек:** Python, Laya model.
- **Install:** `uvx / pipx laya-cli` (PyPI 0.2.4), `laya-cli predict --help`.
- **Рядок для резюме:** `laya-cli — typed decisions CLI (choice/score/noul, 33ms, batch mode)`

### kie-media-cli
- **GitHub:** https://github.com/MIt9/kie-media-cli
- **Що:** Генерація image / video / audio через KIE API (kie.ai) з терміналу або Claude / Cursor — unified `run`, live model registry, cost, history.
- **Стек:** TypeScript, Node.
- **Install:** npm 0.3.1.
- **Рядок для резюме:** `kie-media-cli — CLI for KIE API (image/video/audio generation)`

### hi3d-cli
- **GitHub:** https://github.com/MIt9/hi3d-cli
- **Що:** Генерація 3D-моделей з тексту або зображення однією командою — GLB / OBJ / STL / FBX / USDZ / 3MF, reliefs, split, multicolor.
- **Стек:** TypeScript, Node, Hi3D API (hitem3d.ai).
- **Install:** npm 0.1.25.
- **Рядок для резюме:** `hi3d-cli — text/image-to-3D CLI (6 formats, agent skill included)`

### pexels-cli (`px`)
- **GitHub:** https://github.com/MIt9/pexels-cli
- **Що:** Пошук і batch-скачування стокових фото / відео з Pexels з терміналу.
- **Стек:** Python, Pexels API.
- **Install:** `pip install pexels-cli` (PyPI 0.2.5, перейменовано з `pexels-ai-cli`).
- **Рядок для резюме:** `pexels-cli — Pexels API CLI (search + batch download)`

### gifboom
- **GitHub:** https://github.com/MIt9/gifboom
- **Що:** GIF з відео / послідовності зображень з терміналу — create, trim, compress, optimize.
- **Стек:** Python.
- **Install:** `pip install gifboom` (PyPI 0.1.5).
- **Рядок для резюме:** `gifboom — terminal GIF creator/optimizer`

### silpo-agent-cli
- **GitHub:** https://github.com/MIt9/silpo-agent-cli
- **Що:** Персональний CLI-обгортка над Silpo MCP — кошик / замовлення з терміналу та агента.
- **Стек:** Python.
- **Install:** PyPI є (0.3.1).
- **Рядок для резюме:** `silpo-agent-cli — personal CLI over Silpo MCP (cart/orders)`

### barcode-2-svg (legacy, 9★)
- **GitHub:** https://github.com/MIt9/barcode-2-svg
- **Що:** Server-side 1D-штрихкоди в SVG без canvas — Code39, Code128, EAN-13 тощо. Працює в Node і браузері.
- **Стек:** JavaScript, npm 0.4.1.
- **Рядок для резюме:** `barcode-2-svg — server-side barcode-to-SVG (9★, most starred legacy repo)`

### my-cli
- **Локально:** `~/work/my-cli` (0.3.2)
- **Що:** Multi-provider AI-асистент для терміналу — REPL, pipe mode, tools, sessions, presets, skills, MCP, sub-agents (Merlin, Ollama, LM Studio, OpenAI).
- **Рядок для резюме:** лише як `multi-provider terminal AI assistant (personal)` якщо релевантно.

## AI skills (skills.sh)

### hi3d-skills
- **GitHub:** https://github.com/MIt9/hi3d-skills
- **Що:** Офіційна колекція Agent Skills для генерації 3D через `hi3d-cli` — Claude Code, Cursor, Antigravity.
- **Install:** `npx -y skills add MIt9/hi3d-skills`.
- **Рядок для резюме:** `hi3d-skills — agent skills for text-to-3D via hi3d-cli`

### job-search-skills
- **GitHub:** https://github.com/MIt9/job-search-skills
- **Що:** 3 скіли для пошуку роботи — LinkedIn, резюме, job search. skills.sh-compatible, Claude Code.
- **Рядок для резюме:** `job-search-skills — AI skills for LinkedIn/resume/job search`

### building-with-laya-skill
- **GitHub:** https://github.com/MIt9/building-with-laya-skill
- **Що:** Скіл написання надійного AI decision-коду з Laya — Choice / Score / Noul, design питань, `laya-cli`, калібрування. Аналог `dbreunig/building-with-jev-skill`.
- **Install:** `npx -y skills add MIt9/building-with-laya-skill`.
- **Рядок для резюме:** `building-with-laya-skill — agent skill for Laya decision code`

## Контент-пайплайн (не публікувати окремо)

### img-to-post (0.8.0)
- **GitHub:** https://github.com/MIt9/img-to-post
- **Що:** Telegram-бот CLI — картинки → AI-пости, topic routing, черга, збереження в `posts/YYYY-MM-DD/`, anti-slop.
- **Рядок для резюме:** не виносити; лише в контексті `content automation (Telegram → AI posts)`.

### slop-to-post (0.1.0) / post-to-comment (0.2.0)
- **GitHub:** https://github.com/MIt9/slop-to-post, https://github.com/MIt9/post-to-comment
- **Що:** slop-to-post — детект AI-slop (Slop Score 0–100) + rewrite; post-to-comment — LinkedIn-коментарі без slop (3 варіанти, persona-aware). npm publish підготовлено (`--dry-run` ok), чекає `npm login`.
- **Рядок для резюме:** не виносити окремо; разом як `AI content cleanup tools`.

## Як використовувати в резюме

- **Side Projects (2–3 шт. макс):** `mcp-comfy-ui-builder` + `laya-cli` + один за вакансією (`mcp-book-lover` для Python, `hi3d-cli` для 3D/graphics, `workatastartup-mcp` для jobs/HR-tech).
- **Skills line:** `Custom MCP servers, CLIs, agent skills (public repos)` — деталі в `skills-inventory.md`.
- **Не додавати:** `img-to-post / slop-to-post / post-to-comment` (не опубліковані на npm), `silpo-mcp / silpo-sdk` (private/demo), `my-cli` (без публічного URL).
