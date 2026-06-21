# Claude Usage

Claude can use this project as an external CLI tool.

Recommended workflow:

1. Run scan mode.
2. Read JSON output.
3. Summarize what will change.
4. Ask the user for confirmation.
5. Run apply mode only for confirmed targets.
6. Run scan mode again to verify.

Example prompts for Claude:

```text
Use the traditionalize CLI in this repository. First scan C:\\Work\\Docs for Simplified Chinese in filenames and Word/Excel/PowerPoint contents. Do not modify files until I confirm.
```

Example commands:

```bash
traditionalize --root "C:\\Work\\Docs" --targets names,office --mode scan --json
traditionalize --root "C:\\Work\\Docs" --targets names,office --mode apply --json
```

Claude should avoid broad apply operations unless the user explicitly confirms the scan report.
