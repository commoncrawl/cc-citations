#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import jsonlines
import sys
import argparse

# Usage:
# ./plot-data.py                                                \
#     --title "Common Crawl Google Scholar Citations per Year"  \
#     --groupby "year"                                          \
#     --xlabel "Year"                                           \
#     --ylabel "N Citations"                                    \
#     --output "citations-by-year.png"                          \
#     --format "jsonl"                                          \
#     < data.jsonl

# Alternatively for CSV data as input:
# ./plot-data.py                                                \
#     --title "Common Crawl Google Scholar Citations per Year"  \
#     --groupby "year"                                          \
#     --xlabel "Year"                                           \
#     --ylabel "N Citations"                                    \
#     --output "citations-by-year.png"                          \
#     --format "csv"                                            \
#     --transparent                                             \
#     < data.csv

parser = argparse.ArgumentParser()
parser.add_argument('--title', default='Graph Title')
parser.add_argument('--xlabel', default='X Label')
parser.add_argument('--ylabel', default='Y Label')
parser.add_argument('--output', default='output.png')
parser.add_argument('--groupby', default='year')
parser.add_argument('--transparent', action='store_true', help='Save plot with transparent background')
parser.add_argument('--format', choices=['jsonl', 'csv'], default='jsonl', help='input data format')

args = parser.parse_args()

outputfile = args.output
ccblue = '#3287c5'

if args.format == 'jsonl':
    data = []
    with jsonlines.Reader(sys.stdin) as reader:
        for obj in reader:
            data.append(obj)
    df = pd.DataFrame(data)

elif args.format == 'csv':
    df = pd.read_csv(sys.stdin)

# # debug: verify df structure
# print("DataFrame columns:", df.columns)
# print("DataFrame head:\n", df.head())

plt.figure(figsize=(20, 12))
bars = plt.bar(df['year'].astype(str), df['count'], color=ccblue)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom', ha='center')

plt.title(args.title)
plt.xlabel(args.xlabel)
plt.ylabel(args.ylabel)
plt.xticks()
plt.grid(False)

ax = plt.gca()
ax.patch.set_alpha(0)
plt.gcf().patch.set_alpha(0 if args.transparent else 1)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.tick_params(left=False, bottom=False)

plt.savefig(outputfile, transparent=args.transparent, dpi=320, bbox_inches='tight')

print(f"Total rows: {len(df)}")
print(f"Plot saved to {outputfile}")
