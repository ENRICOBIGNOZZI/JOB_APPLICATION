# Source sourcing playbook

The search stack has three layers.

## 1. API boards

Use first:

```bash
job-agent search
```

This covers configured Greenhouse and Lever boards.

## 2. Curated source pages

Use next:

```bash
job-agent crawl-pages
```

The curated pages are stored in:

```text
configs/source_pages.csv
```

Current priority sources:

- ETH Zurich
- EPFL
- USI
- CSCS
- Inria
- CNRS
- CEA
- Google Careers / Google DeepMind
- IBM Research Zurich

The crawler is intentionally simple. It works best on static pages with regular links. Dynamic sites may still require manual CSV import.

## 3. Manual CSV import

Use for LinkedIn, Workday, company portals, academic pages, and jobs discovered by hand:

```bash
job-agent import-csv examples/manual_jobs_template.csv
job-agent rescore
job-agent rank --min-score 50
job-agent domains
```

Minimum CSV fields:

```csv
company,title,location,url,description
```

## Manual target expansion

Good additional targets for Chiara:

- ETH AI Center
- ETH D-MATH / Seminar for Applied Mathematics
- EPFL IC / SB / STI research groups
- Inria teams around Palaiseau, Saclay, Paris, Grenoble, Rennes
- CSCS Lugano
- IBM Research Zurich
- industrial research groups in optimization, control, simulation, robotics, scientific computing
- computational modelling roles in life-science companies, only when modelling/computation is central
- quant research groups focused on mathematical finance, numerical methods, options, stochastic modelling, or kernel methods

Avoid spending time on roles dominated by sales, product ownership, regulatory paperwork, or experimental lab work.
