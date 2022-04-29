
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

# prepare: add CC annotations and ID
%.prepared.bib: %.bib
	perl -000 -lne '$$url="  url = {},\n"; $$url = "" if /\surl\s*=/; s@([}"]?),?\n\}$$@$$1,\n$$url  cc-author-affiliation = {},\n  cc-class = {},\n}@; print' $< | bibtool -f 'cc:%4p(author):%4d(year):%4T(title)' | perl -lpe 'do { s@\.ea:20@EtAl:20@; s@\.@@g } if /^@/' >$@

# some statistics about the citations
cc-annotations:
	perl -lne '$$h{$$1}++ if /^\s*(cc(?:-[a-z_0-9]+)+)\s*=/; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-classes:
	perl -lne 'if (s/^\s*cc-class\s*=\s*["{]// .. s/["}],?$$//) { $$classes .= $$_ } elsif (defined $$classes) { do { s@\s+@ @g; $$h{$$_}++ } for split /,\s*/, $$classes; $$classes = undef; }; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-derived-datasets:
	perl -lne 'if (s/^\s*cc-derived-dataset-(?:used|cited|about)\s*=\s*["{]// .. s/["}],?$$//) { $$datasets .= $$_ } elsif (defined $$datasets) {  $$h{$$_}++ for split /,\s*/, $$datasets; $$datasets = undef; } END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
count:
	grep -c '^@' bib/*.bib | perl -aF':' -lne 'print join("\t", $$F[1], $$F[0], @F[2..$$#F])' | sort -k2,2

clean:
	rm bib/*.formatted.bib


# Google Scholar Alerts
gscholar_alerts/extracted_citations.jsonl: gscholar_alerts/eml/
	python3 gscholar_alerts/parse_scholar_alert_eml.py $< | LC_ALL=C sort >$@

gscholar_alerts/citations.jsonl: gscholar_alerts/extracted_citations.jsonl
	jq -c 'select(.title != null and .authors != null) | del(.idx, .date, .data, .ref, .link)' $< >$@
