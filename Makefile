
# consistent formatting
BIBCLEAN = bibclean  -max-width 120  -align-equals  -no-fix-names

# add a consistent citation key
BIBTOOLKEY = bibtool -f 'cc:%4p(author):%4d(year):%4T(title)'

BIBSRC = $(sort $(wildcard bib/cc*.bib))

all: html/commoncrawl.html

tmp/commoncrawl.bib: $(BIBSRC)
	mkdir -p tmp
	$(BIBCLEAN) $(BIBSRC) >tmp/commoncrawl.bib

# HTML export
html/commoncrawl.html: tmp/commoncrawl.bib
	mkdir -p html; cd html; bibtex2html --charset utf-8 ../tmp/commoncrawl.bib

# CSV export to import papers into wordpress
tmp/commoncrawl_site_wp.csv: tmp/commoncrawl.bib
	python3 export-csv.py $< >$@

# format .bib file
%.formatted.bib: %.bib
	$(BIBCLEAN) $< >$@

# some statistics about the citations
cc-annotations:
	perl -lne '$$h{$$1}++ if /^\s*(cc(?:-[a-z_0-9]+)+)\s*=/; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-classes:
	perl -lne 'next unless s/^\s*cc-class\s*=\s*//; s/^["{]//; s/["}],?$$//; $$h{$$_}++ for split /,\s*/; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-derived-dataset-used:
	perl -lne 'next unless s/^\s*cc-derived-dataset-used\s*=\s*//; s/^["{]//; s/["}],?$$//; $$h{$$_}++ for split /,\s*/; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr

