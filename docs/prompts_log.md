# Prompts log (AI tools used to build HarvestRadar)

Course requirement: every significant prompt given to an AI tool, with the tool, the date, the purpose,
the prompt (or an excerpt) and what was kept.

| # | Date | Tool | Purpose | Prompt (excerpt) | What was kept |
|---|---|---|---|---|---|
| 1 | 2026-11-15 | Claude Code (Anthropic), cloud session | Read the app guidelines and ask questions | "Lis, poses des questions si nécessaire. Ton but est de coder l'app" + `HarvestRadar_app_guidelines.md` | Questions on the missing repository, storyboard and video brief |
| 2 | 2026-11-15 | Claude Code | Build the whole project from the specification | "Aucun code n'a été créé, les seuls éléments sont le premier fichier et ces deux fichiers. Il faut que tu crées l'app HarvestRadar de A à Z" + `SPEC.md`, `docs/app_guidelines.md`, storyboard v3 (PDF) | The repository: pipeline (`src/harvestradar/`), app, email export, tests, scripts, docs. Every source and number was then checked against the downloaded data (see `data/manifest.json`). |
| 3 | 2026-11-15 | Qwen2.5-1.5B-Instruct (Hugging Face, local) | Write the weekly note from a fact sheet with slots | System prompt: `src/harvestradar/report/prompts/weekly_note_system.md`; user prompt built by `user_prompt()` in `src/harvestradar/report/weekly_note.py` (fact sheet with `{SLOTS}`, a style example, "no digits, copy the {SLOTS}") | Notes that pass the three checks (numbers, context, claims). Failed attempts are logged in `notes.parquet` (`failures`), and after 2 retries the deterministic template is used and tagged. |

## Notes on prompt design (weekly note)

- First version: the fact sheet was a bullet list. The 1.5B model copied the bullets and typed the ONI season
  digits. Changed to prose plus a slot for the ONI period.
- Second version: a style example with invented facts ("the window opens next month") leaked into the output.
  The example was rewritten with slots only, the fact sheet now gives the next window explicitly, and the
  claims check rejects unsupported timing ("next month", "next week") and windows said to be open when none is.
| 4 | 2026-11-15 | Claude Code | Data access decision | "Remplis-le pour moi" (answer to: fill in the MapSPAM Dataverse guestbook with the account e-mail and ESSEC Business School) | MapSPAM 2020 rasters downloaded through the Dataverse API after the guestbook response. |
| 5 | 2026-11-15 | Claude Code | Scope reminder from the user | "A quelle étape es-tu sur le codage de l'application ? Ton rôle est uniquement ceci." | Work narrowed to finishing and delivering the app. |
| 6 | 2026-11-16 | Claude Code | Third round of feedback | "toujours ces problèmes de design dans daily note. Image 2 c'est pas pro les ticks et croix, pourquoi image 3 c'est pas corrélé ? ajoute un outil de pricing par rapport au risque de climat qui donne la fair value mise à jour automatiquement aux nouvelles données. Aussi ajouter si possible un Claude gratuit dedans qui aide au trading de commodités" | Daily note layout fixed, verdict tags instead of ticks and crosses, measured index-price correlations shown in the app, climate fair value (`signal/fair_value.py`) with a pricing tool, Ask Claude tab in the web edition. |
| 7 | 2026-11-16 | Claude (viewer's own plan, via the published page) | In-app trading assistant | Standing instructions `RULES` in `web/app.js` (figures only from the snapshot, flag missing data, trade ideas as scenarios with invalidation and risks, not personalised advice, no em dashes) + `claudeContext()` (the page's data) + the conversation | Answers shown in the Ask Claude tab; nothing stored by the page. |
| 8 | 2026-11-16 | Claude Code | Assistant and delivery choices | "Ajoute ChatGPT au lieu de Claude. GitHub Actions ok. Garder la note quotidienne au lieu du mail" + "fais ceci" (publish the weather history and models so the daily update can run) | The in-page Claude chat replaced by "Ask ChatGPT" links (question and page figures pre-written, `web/app.js` `gptPrompt`, `src/harvestradar/app/chatgpt.py`); email view and download removed from the app (CLI export kept); data snapshot published for the daily workflow. |
| 9 | 2026-11-16 | Claude Code | Keep the answers in the page | "quand on clique ça ouvre ChatGPT, alors qu'il faudrait juste que la question s'envoie direct dans le panneau" + choice "Modèle gratuit dans le navigateur" + "les flèches ne sont pas pro" | In-page assistant: Qwen2.5-1.5B-Instruct run in the browser with WebLLM 0.2.87 (instructions `RULES` + `contextText()` in `web/app.js`), the local Qwen in Streamlit (`src/harvestradar/app/assistant.py`); ChatGPT link only as fallback; all arrows removed. |
