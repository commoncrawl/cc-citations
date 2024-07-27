import csv
import re
import sys

from pybtex.database.input import bibtex

csv_out = sys.stdout
bibtex_in = sys.argv[1]

parser = bibtex.Parser()
bibdata = parser.parse_file(bibtex_in)

clean_pattern = re.compile('(?<!\\\\)[{}]')
unescape_pattern = re.compile('\\\\([{}%])')

csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
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
