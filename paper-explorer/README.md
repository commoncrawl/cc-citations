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
```

## Topic detection with LDA

To assign topics to each paper, we run LDA on the titles and abstracts.

```bash
python classify_paper_topics.py --input_path=papers.json --topics_path=topics.json --paper_to_topic_path=paper_topics.json --n_topics=12 --n_words=20 --max_iter=100
```

Since LDA does not produce topic titles but keywords list we use an LLM to assign titles and colors (e.g., for Claude Code):

> Assign a `topic_title` to each topic in `topics.json` based on the provided keywords (LDA output) and assign colors such that the color reflects topic similarity. If no meaningful title can be assigned use "Other" as a topic title.

## JavaScript data

To load all results in a Web page, all pieces need to be converted into a Javascript file:

```bash
python create_papers_js.py
```

## View Web page

The resulting Web app is a single HTML file with Javascript and can be viewed in a browser.

```bash
cd hf_space

# from local FS
open index.html

# via local web server at http://localhost
python -m http.server 80
```

## Push to HF space

To deploy the web app to Hugginface, you can upload the relevant files as follows:

```bash
huggingface-cli upload commoncrawl/cc-citations ./hf_space --repo-type space --commit-message "Uploading paper explorer"
```

## References

- Embedding model: https://github.com/malteos/scincl
- Dimensionality reduction method: https://github.com/lmcinnes/umap
- Topic modeling: https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.LatentDirichletAllocation.html
