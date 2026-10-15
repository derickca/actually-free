# AGENTS.md — actually-free

Rules for anyone working in this repository. General working rules are in the home AGENTS.md.

## Build rules

- generate.py owns the built files: `assets/styles.css`, `assets/app.js`, `index.html`, `app/*.html` and `data/apps.json` are all generated. Never edit a built file directly. Make the change in generate.py, then regenerate.
- data/apps.json is assembled from the seed files. Edit `~/workspace/certifiable-apps/apps-seed.json` and the in-repo mirror `data/apps-seed.json` (the two copies are kept identical), plus `data/windows-seed.json` for Windows records. Then run generate.py, validate and commit everything, including the regenerated apps.json.
- Taxonomy drift is checked with `tools/taxonomy_check.py`, run by hand when the catalogue is edited. There is no scheduled taxonomy check.
