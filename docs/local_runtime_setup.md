# Local runtime setup

This repository should not store private files or local runtime secrets.

## CV PDF

The profile points to:

```text
documents/cv_chiara_segala.pdf
```

Keep the PDF local. It is ignored by git through `.gitignore`.

Suggested local setup:

```bash
mkdir -p documents
cp /path/to/cv_chiara_segala.pdf documents/cv_chiara_segala.pdf
```

The TeX source can be compiled locally with:

```bash
pdflatex cv_chiara_segala.tex
pdflatex cv_chiara_segala.tex
mkdir -p documents
cp cv_chiara_segala.pdf documents/cv_chiara_segala.pdf
```

## Local notification workflow

Do not commit local credentials or tokens.

Recommended policy:

- keep local runtime variables in a local file such as `.env.local`
- never commit `.env.local`
- keep notification sending disabled by default
- send only explicit test notifications before enabling regular use
- rotate any exposed local credential immediately

Minimal local variables:

```bash
JOB_AGENT_SEND_NOTIFICATIONS=0
JOB_AGENT_NOTIFY_TO=chiara.segala@usi.ch
JOB_AGENT_NOTIFY_FROM=your_local_sender
```

The current safe workflow is manual:

1. Run `job-agent prepare --job-id <ID>`.
2. Review the generated application folder.
3. Send the final message manually after review.

Automated sending should only be added with mocked tests and local-only configuration.
