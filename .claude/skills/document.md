# /document — Workflow Documentation Generator

## Description
Creates a standardised `.md` documentation file in the `docs/` folder. Accepts content from multiple sources: inline text in the message, references to existing files, or free-form thoughts and decisions about work already done. Combines everything into a structured document following the standard template.

## Trigger
Invoked when the user runs `/document` or asks to "document", "write docs for", or "create documentation for" a step, notebook, or workflow.

## Arguments
`/document <filename> [--title "Title"]`

- `<filename>` — the output filename (without `.md`). Must include the notebook number (e.g. `notebook_1_sales_dq`, `nb01_data_ingestion`). Written to `docs/<filename>.md`.
- `[--title "Title"]` — optional explicit title. If omitted, infer from the filename and context.

## Content Input Modes

The skill accepts content from three sources within the same message. Parse and route each accordingly:

1. **File references** — any path ending in `.md`, `.py`, `.ipynb`, `.sql`, or `.txt` → read the file and extract relevant context.
2. **Inline content** — free-form text or bullet points provided directly in the message → use as the primary content body.
3. **Thoughts & decisions** — sentences starting with "I decided...", "The reason...", "My assumption...", "I chose...", or similar → route to the **Key Decisions** or **Working Assumptions** section.

## Instructions

Follow these steps precisely when this skill is invoked:

---

### Step 1 — Parse arguments and content

Extract:
- `filename` from the command args (strip `.md` if present). Resolve the output path as `docs/<filename>.md` relative to the project root.
- `title` from `--title` if provided; otherwise derive it from `filename` by replacing underscores/hyphens with spaces and title-casing. Keep the notebook number prefix visible in the title (e.g. `Notebook 1 — Sales Data Quality`).
- `notebook_number` — extract from the filename. Look for patterns like `notebook_1`, `nb01`, `pipeline_3`, etc. If not found, leave blank.
- All referenced file paths and inline content from the rest of the message.

---

### Step 2 — Read referenced files

For every file path found in the message:
- Read the file using the Read tool.
- Extract: purpose, key steps, any comments or docstrings that reveal intent, column/variable names, and any explicit TODO or NOTE markers.
- Do NOT dump raw file content into the doc — synthesise it into prose and bullets.

---

### Step 3 — Check for naming standards

Before writing, check if the user has specified a naming standard for headings in this message or in prior context. If yes, apply it to the section headings. If no naming standard is given, use the **Default Template** below exactly as written.

---

### Step 4 — Build the document

Compose the `.md` file using the template below. Fill every section with synthesised content from Steps 1–3. Sections with no available content should show a short placeholder line (e.g. `_To be completed._`) rather than being omitted — this preserves the standard structure for future updates.

---

#### Default Template

```markdown
# [Notebook <N>] <Title>

**Date:** <YYYY-MM-DD>
**Pipeline:** Notebook <N> — <Short one-line description>
**Output file:** `docs/<filename>.md`

---

## Overview

<2–4 sentences describing what this notebook/step does, what dataset or inputs it operates on, and what outputs it produces.>

---

## Working Assumptions

<Bullet list of assumptions made about the data, business logic, or environment. Each assumption should be a single, testable statement.>

- <Assumption 1>
- <Assumption 2>

---

## Workflow Structure

<Numbered list of the high-level steps performed. Reference cell numbers or function names where relevant.>

1. <Step 1>
2. <Step 2>

---

## Key Decisions

<Bullet list of non-obvious design or implementation decisions and the rationale behind each. Focus on the WHY.>

- **<Decision>:** <Rationale>

---

## Notes / Additional Context

<Any extra context, caveats, references to external docs, or follow-up items.>
```

---

### Step 5 — Write the file

Use the Write tool to write the completed document to `docs/<filename>.md`.

- If the `docs/` directory does not exist, create it first using Bash: `mkdir -p docs`.
- Always write to the path `docs/<filename>.md` (relative to project root).
- Never overwrite an existing file without confirming with the user first. If the file exists, ask: "A file at `docs/<filename>.md` already exists. Overwrite, append, or cancel?"

---

### Step 6 — Report to the user

After writing, tell the user:
- The path of the created file: `docs/<filename>.md`
- Which sections were fully populated vs. left as placeholders
- If any referenced files could not be read, name them explicitly
- Remind them: "Run `/document` again with the same filename and new content to update any placeholder sections."
