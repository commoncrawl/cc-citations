import sys
import json
from collections import defaultdict
import csv


input_file = sys.argv[1]

with open(input_file, "r") as file:
    lines = file.readlines()

output_files = {}
counts = defaultdict(int)
for line in lines:
    data = json.loads(line)
    year = data["year"]
    if year not in output_files:
        output_files[year] = open(f"{year}.jsonl", "w")
    output_files[year].write(line)
    counts[year] += 1

for file in output_files.values():
    file.close()

with open('citations_counts.csv', mode='w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['year', 'count'])
    for year in sorted(counts):
        csvwriter.writerow([year, counts[year]])
