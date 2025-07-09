.PHONY: gscholar-bib

# consistent formatting
BIBCLEAN = bibclean  -max-width 120  -align-equals  -no-fix-names

# add a consistent citation key
BIBTOOLKEY = bibtool -f 'cc:%4p(author):%4d(year):%4T(title)'

BIBSRC = $(sort $(wildcard bib/cc*.bib))

# HF dataset repo settings
HF_REMOTE_BASE = git@hf.co:datasets/commoncrawl
LOCAL_REPO_BASEDIR = ../tmp-repos
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
#
# Expected Flow:
# $ make hf-prepare   # Has to be run separately first.
# $ make hf-upload
# $ make hf-clean     # Optional but a good idea since we are filling in a folder outside pwd: ../tmp-repos

$(LOCAL_REPO_BASEDIR)/citations:
	mkdir -p $@
	git clone $(HF_REMOTE_BASE)/citations $@

hf-prepare.done: gscholar_alerts/citations.jsonl $(wildcard $(LOCAL_REPO_BASEDIR)/citations/*) | $(LOCAL_REPO_BASEDIR)/citations
	cd $(LOCAL_REPO_BASEDIR)/citations; git pull origin main || true
	BASEDIR=$(LOCAL_REPO_BASEDIR)/citations ; \
	YEARS=$$(cat tmp/citations.jsonl | jq -r ."year" | sort | uniq) ; \
	for YEAR in $$YEARS; do \
		jq -c "select(."year" == \"$$YEAR\")" tmp/citations.jsonl > "$$BASEDIR/$$YEAR.jsonl"; \
	done
	cd $(LOCAL_REPO_BASEDIR)/citations; \
	git remote show origin; \
	git add --all; \
	git status; \
	git restore --staged .
	touch $(CURDIR)/$@
	touch $(CURDIR)/hf-confirmed.done
	@echo;
	@echo "Do you like how this looks? If so, next run make hf-upload."

hf-confirmed.done: gscholar_alerts/citations.jsonl $(wildcard $(LOCAL_REPO_BASEDIR)/citations/*)
	$(error First run make hf-prepare to prepare and stage the files, then visually check staging status.)

hf-upload.done: hf-confirmed.done
	cd $(LOCAL_REPO_BASEDIR)/citations; \
	git add --all; \
	git commit -m "$(COMMIT_MSG)"; \
	git push origin main || true; \
	touch $(CURDIR)/$@; \

# Prepares file to commit to HF hub
hf-prepare: hf-prepare.done

# Makes the upload to HF hub
hf-upload: hf-upload.done

hf-clean:
	rm -rf $(LOCAL_REPO_BASEDIR) hf-prepare.done hf-confirmed.done hf-upload.done


.PHONY: hf-upload hf-prepare hf-clean
.PRECIOUS: $(LOCAL_REPO_BASEDIR)/%
