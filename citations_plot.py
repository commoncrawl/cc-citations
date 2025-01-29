#!/usr/bin/env python


# Usage: ./citations_plot.py [--transparent]
# This will output the CSV data to stdout, and will save an
# image file (.png) called cumulative_citations_[year].png
# optionally with a transparent background


import sys
import argparse
import json

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.font_manager import FontProperties
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--transparent', action='store_true', help='Save plot with transparent background')
parser.add_argument('--cumulative', action='store_true', help='Cumulative count of citations')
parser.add_argument('--interactive', action='store_true', help='Present the plot in interactive mode')
args = parser.parse_args()

# Non-interactive mode for matplotlib
if not args.interactive:
    matplotlib.use('Agg')

# These should be in the cwd, download from
# https://fonts.google.com/specimen/Libre+Franklin
font_regular_path = 'LibreFranklin-Regular.ttf'
font_medium_path = 'LibreFranklin-Medium.ttf'
font_italic_path = 'LibreFranklin-Italic.ttf'

regular_prop = FontProperties(fname=font_regular_path)
medium_prop = FontProperties(fname=font_medium_path)
italic_prop = FontProperties(fname=font_italic_path)

file_path = 'gscholar_alerts/citations.jsonl'
data = []

# Update each year
cutoff = 2025

with open(file_path, 'r') as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)

df['year'] = df['year'].astype(int)
df['count'] = 1

# Include this extra stuff that isn't in the JSON input file.
# Extra figures estimated from the number of results found on Google Scholar:
# https://scholar.google.de/scholar?q=commoncrawl&as_ylo=2015&as_yhi=2015

extra_data = pd.DataFrame({
    'year_count': [
        # (2011, 10),
        (2012, 30),
        (2013, 80),
        (2014, 173),
        (2015, 213)
    ]
})

extra_data[['year', 'count']] = pd.DataFrame(extra_data['year_count'].to_list(), index=extra_data.index)
extra_data = extra_data.drop(columns=['year_count'])

# Combine the JSON data and extra data
df = pd.concat([df, extra_data], ignore_index=True)
df_citations = df.groupby('year')['count'].sum().reset_index()
df_citations['cumulative_count'] = df_citations['count'].cumsum()

# Exclude anything from beyond the cutoff
df_citations = df_citations[df_citations['year'] < cutoff]

# Spit the CSV out
df_citations.to_csv(sys.stdout)

# Now plot it
plt.figure(figsize=(16, 9), facecolor='white')

plot_count = 'count'
plot_title = 'Plot of Common Crawl Citations'
filename   = 'citations_' + str(cutoff) + '.png'

if args.cumulative:
    plot_title += ' (Cumulative)'
    plot_count = 'cumulative_count'
    filename = 'cumulative_citations_' + str(cutoff) + '.png'


plt.plot(
    df_citations['year'],
    df_citations[plot_count],
    marker='o',
    linestyle='-',
    linewidth=2.5,
    markersize=8,
    color='#1f77b4'  # Our nice blue
)

plt.text(
    0.5, 1.05,
    plot_title + ' in Google Scholar until January ' + str(cutoff),
    fontsize=14,
    fontproperties=italic_prop,
    ha='center',
    transform=plt.gca().transAxes
)

plt.xlabel(
    'Year',
    fontsize=18,
    fontproperties=medium_prop,
    labelpad=15
)
plt.ylabel(
    'Count',
    fontsize=18,
    fontproperties=medium_prop,
    labelpad=15
)

plt.xticks(
    df_citations['year'],
    fontsize=14,
    fontproperties=regular_prop,
    rotation=30
)

# Wiggle room
buffer = df_citations[plot_count].max() * 0.05
plt.ylim(0, df_citations[plot_count].max() + buffer)

x_min = df_citations['year'].min()
x_max = df_citations['year'].max() + 0.1
plt.xlim(x_min, x_max)

ax = plt.gca()

ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

y_ticks = range(0, int(df_citations[plot_count].max() + buffer) + 1, 1000)
plt.yticks(
    y_ticks,
    fontsize=14,
    fontproperties=regular_prop
)

grey_colour = '#e6e6e6'

ax.spines['left'].set_color(grey_colour)
ax.spines['bottom'].set_color(grey_colour)
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# No bg grid
plt.grid(False)

# Transparency
plt.gcf().patch.set_alpha(0 if args.transparent else 1)

for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(regular_prop)

plt.tight_layout(pad=5)

plt.savefig(
    filename,
    transparent=args.transparent,
    dpi=300
)

if args.interactive:
    plt.show()

# You can ignore stderr messages about IMKClient and IMKInputSession
