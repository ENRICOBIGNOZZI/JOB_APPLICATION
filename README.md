# JOB_APPLICATION

Semi-automated job search, ranking, and application-preparation system.

The design is deliberate: this is **not** an auto-submit bot. It searches supported public job boards, scores roles, prepares application folders, opens saved links, assists with common form fields, and tracks status. Final review stays manual.

## Current default profile

The default profile in `configs/profile.yaml` is tuned for **Chiara Segala**: applied mathematics, numerical analysis, optimization/control, multi-agent and mean-field systems, kernel methods, uncertainty quantification, scientific computing, machine learning methods, and mathematical finance.

Default scoring now excludes postdoc/postdoctoral roles.

See also:

```text
docs/chiara_application_strategy.md
docs/source_sourcing_playbook.md
docs/local_runtime_setup.md
docs/browser_form_assist.md
```

## What it does

- Searches Greenhouse and Lever public job boards from configured companies.
- Crawls curated source pages from `configs/source_pages.csv`.
- Imports manual jobs from CSV for custom portals, LinkedIn exports, or jobs found by hand.
- Scores jobs using role match, location, seniority, thematic relevance, and negative filters.
- Groups ranked jobs by primary domain with `job-agent domains`.
- Opens the saved application link with `job-agent open-link`.
- Helps fill common application-form fields with `job-agent form-fill`.
- Explains score components with `job-agent explain`.
- Stores jobs and status history in SQLite.
- Generates one folder per application with:
  - `job_description.md`
  - `fit_review.md`
  - `cover_letter.md`
  - `contact_message.txt`
  - `application_notes.md`
  - `answers.md`
  - `checklist.md`
- Tracks statuses: `found`, `shortlisted`, `prepared`, `applied`, `rejected`, `interview`, `offer`, `ignored`.
- Exports ranked jobs to CSV.

## Current target areas

The default configuration is tuned for:

- research scientist / applied scientist roles
- numerical analysis and scientific computing
- optimization, optimal control, model predictive control, sparse/turnpike control
- multi-agent systems, mean-field models, multiscale models, collective dynamics
- kernel methods, large-scale approximation, surrogate modelling, machine learning methods
- uncertainty quantification and robust control
- mathematical finance, American option pricing, optimal stopping, conditional mean embeddings

Preferred regions in the default config:

- Paris / Île-de-France
- Ticino / Lugano / Bellinzona / Locarno / Mendrisio
- Zurich / Zürich
- Northern Italy / Milan / Turin
- Switzerland more broadly
- selected European research hubs

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

For browser form assist:

```bash
pip install -e .[browser]
playwright install chromium
```

## Local CV PDF

Compile or copy the CV PDF locally to:

```text
documents/cv_chiara_segala.pdf
```

This path is ignored by git. `job-agent doctor` checks whether the local file exists. See `docs/local_runtime_setup.md`.

## Configure

Edit:

```text
configs/profile.yaml
configs/targets.yaml
configs/source_pages.csv
configs/autofill_profile.yaml
```

`targets.yaml` controls role keywords, preferred locations, negative filters, thematic keyword groups, and score weights.

## Commands

```bash
job-agent init
job-agent search
job-agent crawl-pages
job-agent import-csv path/to/jobs.csv
job-agent rescore
job-agent rank --min-score 50
job-agent domains
job-agent show --job-id 1
job-agent open-link --job-id 1
job-agent form-fill --job-id 1
job-agent explain --job-id 1
job-agent shortlist --job-id 1
job-agent prepare --job-id 1
job-agent mark --job-id 1 --status applied --note "Submitted manually on company website"
job-agent status
job-agent export --out ranked_jobs.csv
job-agent doctor
```

## Typical workflow

```bash
job-agent doctor
job-agent search
job-agent crawl-pages
job-agent import-csv examples/manual_jobs_template.csv
job-agent rescore
job-agent rank --min-score 55
job-agent domains
job-agent show --job-id 12
job-agent explain --job-id 12
job-agent shortlist --job-id 12
job-agent prepare --job-id 12
job-agent open-link --job-id 12
job-agent form-fill --job-id 12
```

Then review the generated folder under:

```text
applications/<job-id>-<company>-<role>/
```

After manual final submission, update the tracker:

```bash
job-agent mark --job-id 12 --status applied --note "Submitted manually"
```

## CSV import format

Minimum columns:

```csv
company,title,location,url,description
```

Optional columns:

```csv
source,date_found,status,score
```

A template is available at:

```text
examples/manual_jobs_template.csv
```

## Safety rules

No LinkedIn automation. No CAPTCHA bypass. No credential handling. No blind submit. No fake answers. The browser helper only assists with recognizable fields and stops for human review.
