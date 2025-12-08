# CC-Citations: Paper Explorer

A visual tool for exploring research papers citing Common Crawl.

## Setup

- Python 3.12

```bash
pip install -r requirements.txt
```

## Generate paper embeddings

The paper explorer requires 2D representations of the paper. To obtain those, we use the title and abtract of each paper to generate embeddings and then apply dimensionality reduction.

```bash
python embed_papers.py --input_path=<path to OpenAlex JSONL> \
    --json_output_path=papers.json \
    --js_output_path=hf_space/papers.js \
    --model_name_or_path=malteos/scincl
```

## View Web page

The resulting web app can be viewed a browser.

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