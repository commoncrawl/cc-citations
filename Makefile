.PHONY: gscholar-bib

# consistent formatting
BIBCLEAN = bibclean  -max-width 120  -align-equals  -no-fix-names

# add a consistent citation key
BIBTOOLKEY = bibtool -f 'cc:%4p(author):%4d(year):%4T(title)'

BIBSRC = $(sort $(wildcard bib/cc*.bib))

# HF dataset repo settings
HF_REMOTE_BASE = git@hf.co:datasets/commoncrawl
LOCAL_REPO_BASEDIR = tmp/repos
TRACKED_FILES_BASEDIR = tmp/tracked_files
FILES_CITATIONS_ANNOTATED = tmp/commoncraw_annotated.csv
COMMIT_MSG=Automated update through cc-citations github repo


all: html/commoncrawl.html

tmp/commoncrawl.bib: $(BIBSRC)
	mkdir -p tmp
	$(BIBCLEAN) $(BIBSRC) >tmp/commoncrawl.bib

# HTML export
html/commoncrawl.html: tmp/commoncrawl.bib
	mkdir -p html; cd html; bibtex2html --charset utf-8 ../tmp/commoncrawl.bib

# CSV export for Hugging Face 🤗
tmp/commoncrawl_annotated.csv: tmp/commoncrawl.bib
	python3 export-csv.py $< >$@

# json annotated export for Hugging Face 🤗
# depends on gscholar_alerts/citations.jsonl but most people do not have the /eml/ subdirectory
gscholar-bib:
	mkdir -p tmp; cd tmp; python ../split-jsonl.py ../gscholar_alerts/citations.jsonl

# format .bib file
%.formatted.bib: %.bib
	$(BIBCLEAN) $< >$@

# prepare: add CC annotations and ID
%.prepared.bib: %.bib
	perl -000 -lne '$$url="  url = {},\n"; $$url = "" if /\surl\s*=/; s@([}"]?),?\n\}$$@$$1,\n$$url  cc-author-affiliation = {},\n  cc-class = {},\n}@; print' $< | $(BIBTOOLKEY) | perl -lpe 'do { s@\.ea:20@EtAl:20@; s@\.@@g } if /^@/' >$@

# some statistics about the citations
cc-annotations:
	perl -lne '$$h{$$1}++ if /^\s*(cc(?:-[a-z_0-9]+)+)\s*=/; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-classes:
	perl -lne 'if (s/^\s*cc-class\s*=\s*["{]// .. s/["}],?$$//) { $$classes .= $$_ } elsif (defined $$classes) { do { s@\s+@ @g; $$h{$$_}++ } for split /,\s*/, $$classes; $$classes = undef; }; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-author-affiliations:
	perl -lne 'if (s/^\s*cc-author-affiliation\s*=\s*["{]// .. s/["}],?$$//) { $$classes .= $$_ } elsif (defined $$classes) { do { s@\s+@ @g; $$h{$$_}++ } for split /;\s*/, $$classes; $$classes = undef; }; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
cc-derived-datasets:
	perl -lne 'if (s/^\s*cc-derived-dataset-(?:used|cited|about)\s*=\s*["{]// .. s/["}],?$$//) { $$datasets .= $$_ . ", " } elsif (defined $$datasets) {  $$h{$$_}++ for split /,\s*/, $$datasets; $$datasets = undef; } END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr
count:
	grep -c '^@' bib/*.bib | perl -aF':' -lne 'print join("\t", $$F[1], $$F[0], @F[2..$$#F])' | sort -k2,2
bibtex-fields:
	perl -lne '$$h{$$1}++ if /^\s*([A-Za-z_0-9-]+)\s*=\s*["{]/; END {print $$v, "\t", $$k while (($$k,$$v)=each %h)}' bib/*.bib | sort -k1,1nr

clean:
	rm bib/*.formatted.bib 


# Google Scholar Alerts
gscholar_alerts/extracted_citations.jsonl: gscholar_alerts/eml/
	python3 gscholar_alerts/parse_scholar_alert_eml.py $< | LC_ALL=C sort >$@

gscholar_alerts/citations.jsonl: gscholar_alerts/extracted_citations.jsonl
	jq -c 'select(.title != null and .authors != null) | del(.idx, .date, .data, .ref, .link)' $< >$@



# HF Dataset Repos Updating

# Since we dont know which years will exist in the jsonl,
# better to use a sentinel file to track their timestamp as well.
extract-citations.done: gscholar_alerts/citations.jsonl
	mkdir -p $(TRACKED_FILES_BASEDIR)/citations
	BASEDIR=$(TRACKED_FILES_BASEDIR)/citations ; \
	YEARS=$$(cat tmp/citations.jsonl | jq -r ."year" | sort | uniq) ; \
	for YEAR in $$YEARS; do \
		jq -c "select(."year" == \"$$YEAR\")" tmp/citations.jsonl > "$$BASEDIR/$$YEAR.jsonl"; \
	done
	touch $@

# TODO: Slightly inefficient now, if one .bib file has newer timestamp, redoes every year's .csv file.
#       However we know that git (HF) updates only files that really changed, so the inefficiency is only in this step.
#       Change?
# TODO: Do NOT push file 2024 for now, we get an error in export-csv.py for this, resulting in an empy file.
#       Correct this after bibtex code is corrected.
extract-citations-annotated.done: $(BIBSRC)
	mkdir -p $(TRACKED_FILES_BASEDIR)/citations-annotated
	BASEDIR=$(TRACKED_FILES_BASEDIR)/citations-annotated ; \
	for BIBFILE in $(BIBSRC); do \
		if [ `basename $$BIBFILE .bib` = "cc2024" ]; then \
			echo "Skipping $$BIBFILE" ; \
			continue ; \
		fi ; \
		OUTFILE=commoncrawl_citations_annotated_`basename $$BIBFILE .bib | sed 's/^cc//'`.csv; \
		echo "python3 export-csv.py $$BIBFILE > $$BASEDIR/$$OUTFILE"; \
		python3 export-csv.py $$BIBFILE > $$BASEDIR/$$OUTFILE; \
	done
	touch $@

$(LOCAL_REPO_BASEDIR)/%:
	git clone $(HF_REMOTE_BASE)/$* $@

hf-update: extract-citations.done extract-citations-annotated.done hf-citations-update.done hf-citations-annotated-update.done

hf-%-update.done: extract-%.done | $(LOCAL_REPO_BASEDIR)/%
	cd $(LOCAL_REPO_BASEDIR)/$*; git pull origin main || true
	cp $(TRACKED_FILES_BASEDIR)/$*/*.* $(LOCAL_REPO_BASEDIR)/$*
	cd $(LOCAL_REPO_BASEDIR)/$*; \
	git remote show origin; \
	git add --all; \
	if git diff --cached --quiet; then \
		echo "Nothing to commit. Skipping."; \
	else \
		git status --short; \
		echo; \
		read -p "Add and push these changes? [Y/n] " confirm; \
		if [ -z "$$confirm" ] || [ "$$confirm" = "Y" ] || [ "$$confirm" = "y" ]; then \
			git commit -m "$(COMMIT_MSG)"; \
			git push origin main || true; \
			touch $@; \
		else \
			git restore --staged .; \
			echo "Aborting commit."; \
		fi; \
	fi


hf-clean:
	rm -rf $(LOCAL_REPO_BASEDIR) $(TRACKED_FILES_BASEDIR) extract-*.done hf-*.done



.PHONY: hf-update
.PRECIOUS: $(LOCAL_REPO_BASEDIR)/%
