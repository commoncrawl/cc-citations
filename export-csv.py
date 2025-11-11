''' Exports annotated .bib files to one big csv.

    Optional flag --explode outputs multiple rows per paper,
      so that every row has one value per key.
      This behavior is currently **hard-coded only over keywords and cc-class**
      fields, which hold multiple values.

      - It adds three new fields to the csv:
         - bib_id as unique identifier, to match papers over multiple lines
         - an aggregate field cc-topic that combines values from cc-class
           and keyword fields (both of which can include multiple values)
         - a field cc-og-key that holds which original field cc-topic value
           came from, options: keyword or cc-class

      - Accordingly, it removes fields keyword and cc-class, which are instead
          aggregated into cc-topic field.

      - Since it is aimed towards manual excel analysis, for readability:
          - It uses YYYY format for post_date, rather than YYYY0101Z00:00:00 format
          - It drops cc_project_category field, which has a set value "papers"

    Usage: python export-csv.py --bib bibfile [--explode]
'''
import argparse
import csv
import re
import sys

from pybtex.database.input import bibtex

csv_out = sys.stdout
parser = argparse.ArgumentParser(description="Converts .bib file to csv")
parser.add_argument("--bib", type=str, help="Path to the input bibfile")
parser.add_argument("--explode", action="store_true", help="Output multiple lines per paper, one row per key-value.")
args = parser.parse_args()

parser = bibtex.Parser()
bibdata = parser.parse_file(args.bib)

clean_pattern = re.compile('(?<!\\\\)[{}]')
unescape_pattern = re.compile('\\\\([{}%])')

csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)

if args.explode==False:
    column_names = [
        # old website csv
        "cc_project_author",
        "post_title",
        "cc_project_url",
        "cc_project_category",  # always 'papers'
        "post_date",
        # full csv
        "keywords",
        "abstract",
        "cc_author_affiliation",  # removed from cc_project_author
        "cc_class",
        "cc_snippet",
        "cc_dataset_used",
        "cc_derived_dataset_about",
        "cc_derived_dataset_used",
        "cc_derived_dataset_cited",
    ]
else:
    # change header for enabling multi-line per paper:
    #   - introduce bib_id as unique identifier
    #   - introduce new columns: cc-topic and cc-og-key
    #   - remove og columns: keywords and cc_class
    column_names = [
        "bib_id",
        "cc_project_author",
        "post_title",
        "cc_project_url",
        "post_date",
        "cc-og-key",
        "cc-topic",
        "abstract",
        "cc_author_affiliation",  # removed from cc_project_author
        "cc_snippet",
        "cc_dataset_used",
        "cc_derived_dataset_about",
        "cc_derived_dataset_used",
        "cc_derived_dataset_cited",
    ]
csvwriter.writerow(column_names)

for bib_id in bibdata.entries:
    entry = bibdata.entries[bib_id]
    b = entry.fields
    authorstr = ''
    url = ''

    # try to fill all required fields
    authors = entry.persons['author']
    for author in authors:
        if authorstr != '':
            authorstr += ','
        if author.bibtex_first_names:
            if authorstr != '':
                authorstr += ' '
            authorstr += ' '.join(author.bibtex_first_names)
        if author.prelast_names:
            if authorstr != '':
                authorstr += ' '
            authorstr += ' '.join(author.prelast_names)
        if authorstr != '':
            authorstr += ' '
        authorstr += ' '.join(author.last_names)
    for f in ['URL', 'pdf', 'doi']:
        if f in b:
            url = b[f]
            break

    year = b.get('year')
    title = b.get('title')
    keywords = b.get('keywords')
    abstract = b.get('abstract')
    cc_author_affiliation = b.get('cc-author-affiliation')
    cc_class = b.get('cc-class')
    cc_snippet = b.get('cc-snippet')
    cc_dataset_used = b.get('cc-dataset-used')
    cc_derived_dataset_about = b.get('cc-derived-dataset-about')
    cc_derived_dataset_used = b.get('cc-derived-dataset-used')
    cc_derived_dataset_cited = b.get('cc-derived-dataset-cited')

    if authorstr == '':
        sys.stderr.write("No author: {} - {}\n".format(bib_id))
        continue
    if title is None:
        sys.stderr.write("No title: {}\n".format(bib_id))
        continue
    if year is None:
        sys.stderr.write("No year: {}\n".format(bib_id))
        continue
    if url == '':
        sys.stderr.write("No URL: {}\n".format(bib_id))

    if 'cc-author-affiliation' in b:
        authorstr += ' &ndash; '
        authorstr += b['cc-author-affiliation']
    else:
        sys.stderr.write("No affiliation: {}\n".format(bib_id))

    title = re.sub(clean_pattern, '', title)
    title = re.sub(unescape_pattern, '\1', title)

    if args.explode==False: # one csv line per paper
        row = [
            authorstr, title, url, 'papers', '{}0101Z00:00:00'.format(year),
            keywords,
            abstract,
            cc_author_affiliation,
            cc_class,
            cc_snippet,
            cc_dataset_used,
            cc_derived_dataset_about,
            cc_derived_dataset_used,
            cc_derived_dataset_cited,
        ]
        csvwriter.writerow(row)

    else:
        row_template = [
            bib_id,
            authorstr, title, url, year,
            "{CC_OG_FIELD}", # placeholder
            "{CC_TOPIC}",    # placeholder
            abstract,
            cc_author_affiliation,
            cc_snippet,
            cc_dataset_used,
            cc_derived_dataset_about,
            cc_derived_dataset_used,
            cc_derived_dataset_cited,
        ]

        idx_cc_og_field = row_template.index("{CC_OG_FIELD}")
        idx_cc_topic = row_template.index("{CC_TOPIC}")

        if keywords:
            print(keywords)
            for keyword in keywords.split(','):
                row = row_template.copy()
                row[idx_cc_og_field], row[idx_cc_topic] = "keyword", keyword.strip()
                csvwriter.writerow(row)
        if cc_class:
            for cc_class_instance in cc_class.split(','):
                row = row_template.copy()
                row[idx_cc_og_field], row[idx_cc_topic] = "cc_class", cc_class_instance.strip()
                csvwriter.writerow(row)
        if not keywords and not cc_class: # dump single line with both fields empty
            row = row_template.copy()
            row[idx_cc_og_field], row[idx_cc_topic] = "", ""
            csvwriter.writerow(row)



