# Browser form assist

The repository includes a local browser helper for application forms.

It can open a saved job URL and fill common fields when labels are recognizable.

It always stops for human review.

## Install

```bash
pip install -e .[browser]
playwright install chromium
```

## CV file

```bash
mkdir -p documents
cp /path/to/cv_chiara_segala.pdf documents/cv_chiara_segala.pdf
```

## Open the saved URL

```bash
job-agent open-link --job-id 12
```

## Run browser form assist

```bash
job-agent form-fill --job-id 12
```

Review all fields in the browser before continuing.

## Configure standard fields

Edit:

```text
configs/autofill_profile.yaml
```

Keep private data in local files and do not commit it.
