# CC-Citations: Paper Explorer

A visual tool for exploring research papers citing Common Crawl based on embedding similarity. The tool is deployed as a [Huggingface space](https://huggingface.co/spaces/commoncrawl/cc-citations). This folder contains all code for generating paper embeddings, topic modeling, and the Web app.

## Setup

- Python 3.12 (recommended)

```bash
# install dependencies via pip
pip install -r requirements.txt
```

## Generate paper embeddings

The paper explorer requires 2D representations of the paper embeddings. To obtain those, we use the title and abtract of each paper to generate embeddings and then apply dimensionality reduction.

```bash
python embed_papers.py --input_path=<path to OpenAlex JSONL> \
    --json_output_path=papers.json \
    --js_output_path=hf_space/papers.js \
    --model_name_or_path=malteos/scincl

python embed_papers.py --input_path=../gscholar_alerts/citations.jsonl \
    --json_output_path=papers_full.json \
    --js_output_path=papers_full.js \
    --model_name_or_path=malteos/scincl \
    --batch_size=12 \
    --title_field=title \
    --url_field=url \
    --authors_field=authors \
    --abstract_field=snippet \
    --embedding_fields title

python embed_papers.py --input_path=./merged_citations.jsonl \
    --json_output_path=papers_merged.json \
    --js_output_path=papers_merged.js \
    --model_name_or_path=malteos/scincl \
    --batch_size=12 \
    --title_field=title \
    --url_field=url \
    --authors_field=authors \
    --abstract_field=abstract \
    --id_field=openalex_id \
    --embedding_fields title abstract

```

## Topic detection with LDA

To assign topics to each paper, we run LDA on the titles and abstracts.

```bash
python classify_paper_topics.py \
    --input_path=papers.json \
    --topics_path=topics.json \
    --paper_to_topic_path=paper_topics.json \
    --n_topics=12 --n_words=20 --max_iter=100 --use_abstracts

python classify_paper_topics.py \
    --input_path=papers_full.json \
    --topics_path=topics_full.json \
    --paper_to_topic_path=paper_topics_full.json \
    --n_topics=30 --n_words=20 --max_iter=100


python classify_paper_topics.py \
    --input_path=papers_merged.json \
    --topics_path=topics_merged.json \
    --paper_to_topic_path=paper_topics_merged.json \
    --n_topics=50 --n_words=20 --max_iter=100  --use_abstracts
```

Since LDA does not produce topic titles but keywords list we use an LLM to assign titles and colors (e.g., for Claude Code):

> Assign a `topic_title` to each topic in `topics.json` based on the provided keywords (LDA output) and assign colors such that the color reflects topic similarity. If no meaningful title can be assigned use "Other" as a topic title.

Or use a CLI command:

```bash
claude --permission-mode acceptEdits --allowedTools Read,Edit,Glob -p "In the file topics_full.json, assign a `topic_title` field to each topic in JSON list of topics based provided keywords (LDA output) and assign colors such that the color reflects topic similarity. If no meaningful title can be assigned use "Other" as a topic title." 

claude --permission-mode acceptEdits --allowedTools Read,Edit,Glob -p "In the file topics_merged.json, assign a 'topic_title' field to each topic in JSON list of topics based provided keywords (LDA output) and assign colors such that the color reflects topic similarity. If no meaningful title can be assigned use "Other" as a topic title." 

claude --permission-mode acceptEdits --allowedTools Read,Edit,Glob -p "The file topics_merged.json holds a list of many topics with titles and keywords (LDA output). Group these topics into a 15 meaningful main topics. Assign a new field 'main_topic_title' to each topic. If certain topics cannot be meanigfully grouped, assign them the 'Other' main topic title. Save the output into a new file with the '_grouped' suffix."

```

## JavaScript data

To load all results in a Web page, all pieces need to be converted into a Javascript file:

```bash
python create_papers_js.py \
  --papers papers_full.json \
  --topics topics_full.json \
  --paper-topics paper_topics_full.json \
  --output hf_space/papers.js


python create_papers_js.py \
  --papers papers_merged.json \
  --topics topics_merged.json \
  --paper-topics paper_topics_merged.json \
  --output hf_space/papers.js

```

## View Web page

The resulting Web app is a single HTML file with Javascript and can be viewed in a browser.

```bash
cd hf_space

# from local FS
open hf_space/index.html

# via local web server at http://localhost
python -m http.server 80
```

## Push to HF space

To deploy the web app to Hugginface, you can upload the relevant files as follows:

```bash
huggingface-cli upload commoncrawl/cc-citations ./hf_space --repo-type space --commit-message "Uploading paper explorer"

huggingface-cli upload malteos/some-tests ./hf_space --repo-type space --commit-message "Uploading paper explorer"
```

## References

- Embedding model: https://github.com/malteos/scincl
- Dimensionality reduction method: https://github.com/lmcinnes/umap
- Topic modeling: https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.LatentDirichletAllocation.html
