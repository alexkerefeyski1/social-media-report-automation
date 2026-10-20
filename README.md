# Social Media Report Automation

A Python automation that turns a CSV export of social-media post metrics into a simple monthly report.

It calculates engagement totals and rates, identifies the best-performing posts, creates platform-level summaries, and saves a chart that can be used in a report or presentation.

## Why I built it

I previously tracked monthly LinkedIn and X post performance manually. This project shows how that repetitive reporting task can be automated with Python.

## Skills demonstrated

- Python scripting and command-line arguments
- Data cleaning with pandas
- Metric calculation and ranking
- CSV report generation
- Data visualization with a portable SVG chart

## Input format

The input CSV must contain these columns:

`platform, post_date, post_title, impressions, likes, reposts, comments, clicks`

The included `data/sample_posts.csv` uses fictional data. Replace it with an export from a reporting tool that follows the same column names.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/generate_report.py --input data/sample_posts.csv --output output
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Generated files

- `monthly_summary.csv` - performance by platform
- `top_posts.csv` - top posts ranked by engagement rate
- `engagement_by_platform.svg` - bar chart of engagement rate by platform
- `report.md` - short written report for quick review

## CV or LinkedIn description

Built a Python reporting automation that processes social-media post exports, calculates engagement metrics, identifies top-performing content, and generates CSV summaries and visual reports.

## Next improvements

- Accept native LinkedIn or X export formats through column mapping
- Add an Excel workbook export
- Schedule the report to run monthly
- Send the completed report by email or upload it to a shared folder
