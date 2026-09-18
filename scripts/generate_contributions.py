import json
import os
import urllib.request
from datetime import datetime

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER") or os.environ.get("USERNAME")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = "profile/contributions.svg"

if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required")

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            color
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode()
request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-profile-readme"
    },
    method="POST",
)

with urllib.request.urlopen(request) as response:
    result = json.load(response)

if result.get("errors"):
    raise SystemExit(json.dumps(result["errors"]))

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
days = [day for week in weeks for day in week["contributionDays"]]

cell = 13
gap = 3
left = 38
top = 28
width = left + len(weeks) * (cell + gap) + 12
height = top + 7 * (cell + gap) + 30

month_positions = []
seen = set()
for wi, week in enumerate(weeks):
    first_date = week["contributionDays"][0]["date"]
    dt = datetime.strptime(first_date, "%Y-%m-%d")
    label = dt.strftime("%b")
    key = f"{dt.year}-{dt.month}"
    if key not in seen and dt.day <= 7:
        month_positions.append((wi, label))
        seen.add(key)

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" rx="10" fill="#0d1117"/>',
    '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}</style>',
    f'<text x="0" y="15" fill="#8b949e" font-size="11">{calendar["totalContributions"]} contributions in the last year</text>'
]

for wi, label in month_positions:
    x = left + wi * (cell + gap)
    svg.append(f'<text x="{x}" y="25" fill="#8b949e" font-size="10">{label}</text>')

for row, label in [(0, "Mon"), (2, "Wed"), (4, "Fri")]:
    y = top + row * (cell + gap) + 10
    svg.append(f'<text x="0" y="{y}" fill="#8b949e" font-size="9">{label}</text>')

for wi, week in enumerate(weeks):
    for di, day in enumerate(week["contributionDays"]):
        x = left + wi * (cell + gap)
        y = top + di * (cell + gap)
        color = day["color"]
        svg.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{color}">'
            f'<title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>'
        )

svg.append("</svg>")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
