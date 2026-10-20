"""Generate a social-media performance report from a post-level CSV export."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "platform",
    "post_date",
    "post_title",
    "impressions",
    "likes",
    "reposts",
    "comments",
    "clicks",
}
METRIC_COLUMNS = ["impressions", "likes", "reposts", "comments", "clicks"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a social-media performance report from a CSV export."
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to a CSV export.")
    parser.add_argument(
        "--output", default=Path("output"), type=Path, help="Folder for generated files."
    )
    parser.add_argument(
        "--top", default=5, type=int, help="Number of posts to include in the top-posts report."
    )
    return parser.parse_args()


def load_posts(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    posts = pd.read_csv(input_path)
    missing_columns = REQUIRED_COLUMNS.difference(posts.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"The input file is missing required columns: {missing}")

    posts["post_date"] = pd.to_datetime(posts["post_date"], errors="coerce")
    if posts["post_date"].isna().any():
        raise ValueError("Every post_date must use a valid date, for example 2026-09-02.")

    for column in METRIC_COLUMNS:
        posts[column] = pd.to_numeric(posts[column], errors="coerce")
        if posts[column].isna().any() or (posts[column] < 0).any():
            raise ValueError(f"{column} must contain non-negative numbers.")

    return posts


def calculate_metrics(posts: pd.DataFrame) -> pd.DataFrame:
    result = posts.copy()
    result["engagements"] = result[["likes", "reposts", "comments"]].sum(axis=1)
    result["engagement_rate"] = result["engagements"].div(result["impressions"]).fillna(0)
    result["click_through_rate"] = result["clicks"].div(result["impressions"]).fillna(0)
    return result


def create_summary(posts: pd.DataFrame) -> pd.DataFrame:
    summary = (
        posts.groupby("platform", as_index=False)
        .agg(
            posts=("post_title", "count"),
            impressions=("impressions", "sum"),
            engagements=("engagements", "sum"),
            clicks=("clicks", "sum"),
        )
        .sort_values("impressions", ascending=False)
    )
    summary["engagement_rate"] = summary["engagements"].div(summary["impressions"])
    summary["click_through_rate"] = summary["clicks"].div(summary["impressions"])
    return summary


def save_chart(summary: pd.DataFrame, output_path: Path) -> None:
    """Write a simple SVG chart so the project has no plotting dependency."""
    chart_data = summary.sort_values("engagement_rate", ascending=False)
    max_rate = max(chart_data["engagement_rate"].max(), 0.01)
    width, height, left, top, row_height = 760, 90 + len(chart_data) * 72, 185, 55, 72
    plot_width = 500
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="30" font-family="Arial, sans-serif" font-size="21" font-weight="bold" fill="#172B4D">Engagement rate by platform</text>',
    ]
    for index, row in enumerate(chart_data.itertuples(index=False)):
        y = top + index * row_height
        rate = row.engagement_rate * 100
        bar_width = (row.engagement_rate / max_rate) * plot_width
        elements.extend(
            [
                f'<text x="24" y="{y + 24}" font-family="Arial, sans-serif" font-size="16" fill="#1F2937">{escape(str(row.platform))}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="32" rx="4" fill="#1769AA"/>',
                f'<text x="{left + bar_width + 12:.1f}" y="{y + 23}" font-family="Arial, sans-serif" font-size="15" fill="#1F2937">{rate:.2f}%</text>',
            ]
        )
    elements.append("</svg>")
    output_path.write_text("\n".join(elements), encoding="utf-8")


def save_markdown_report(summary: pd.DataFrame, top_posts: pd.DataFrame, output_path: Path) -> None:
    best_post = top_posts.iloc[0]
    lines = [
        "# Social Media Performance Report",
        "",
        "## Platform summary",
        "",
        "| Platform | Posts | Impressions | Engagements | Engagement rate | Click-through rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.platform} | {row.posts} | {row.impressions:,} | {row.engagements:,} | "
            f"{row.engagement_rate:.2%} | {row.click_through_rate:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Best-performing post",
            "",
            f"**{best_post.post_title}** on {best_post.platform} had the highest engagement rate "
            f"at {best_post.engagement_rate:.2%}.",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_arguments()
    if args.top < 1:
        raise ValueError("--top must be at least 1.")

    posts = calculate_metrics(load_posts(args.input))
    summary = create_summary(posts)
    top_posts = posts.sort_values("engagement_rate", ascending=False).head(args.top)
    top_posts = top_posts[
        [
            "platform",
            "post_date",
            "post_title",
            "impressions",
            "engagements",
            "engagement_rate",
            "clicks",
            "click_through_rate",
        ]
    ]

    args.output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output / "monthly_summary.csv", index=False)
    top_posts.to_csv(args.output / "top_posts.csv", index=False)
    save_chart(summary, args.output / "engagement_by_platform.svg")
    save_markdown_report(summary, top_posts, args.output / "report.md")

    print(f"Created report files in: {args.output.resolve()}")


if __name__ == "__main__":
    main()
