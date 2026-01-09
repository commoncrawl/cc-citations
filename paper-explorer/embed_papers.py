#!/usr/bin/env python
"""Generate embedding based on cc-citation papers and get 2D representations.

Usage:

```bash
# Open Alex papers
python embed_papers.py --input_path=<path to OpenAlex JSONL> \
    --json_output_path=papers.json \
    --js_output_path=hf_space/papers.js \
    --model_name_or_path=malteos/scincl

# full papers
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
```
"""
import argparse
import json
import pandas as pd

import numpy as np
from sentence_transformers import SentenceTransformer
import umap


def get_js_content(papers, labels, colors=None) -> str:
    if colors is None:
        # default colors
        colors = [
            "#63b598",
            "#ce7d78",
            "#ea9e70",
            "#a48a9e",
            "#c6e1e8",
            "#648177",
            "#0d5ac1",
            "#f205e6",
            "#1c0365",
            "#14a9ad",
            "#4ca2f9",
            "#a4e43f",
            "#d298e2",
            "#6119d0",
            "#d2737d",
            "#c0a43c",
            "#f2510e",
            "#651be6",
            "#79806e",
            "#61da5e",
            "#cd2f00",
            "#9348af",
            "#01ac53",
            "#c5a4fb",
            "#996635",
            "#b11573",
            "#4bb473",
            "#75d89e",
            "#2f3f94",
            "#2f7b99",
            "#da967d",
            "#34891f",
            "#b0d87b",
            "#ca4751",
            "#7e50a8",
            "#c4d647",
            "#e0eeb8",
            "#11dec1",
            "#289812",
            "#566ca0",
            "#ffdbe1",
            "#2f1179",
        ]

    js = f"var colors = {json.dumps(colors)};\n"
    js += f"var data = {json.dumps(papers)};\n"
    js += f"var labels = {json.dumps(labels)};\n"

    return js


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path",
        default=None,
        type=str,
        help="Path to JSONL file containing paper metadata.",
    )
    parser.add_argument(
        "--json_output_path",
        default=None,
        type=str,
        help="Path to save output JSON file",
    )
    parser.add_argument(
        "--js_output_path", default=None, type=str, help="Path to save output JS file"
    )
    parser.add_argument(
        "--model_name_or_path",
        default="malteos/scincl",
        type=str,
        help="Model used for generating the paper embeddings",
    )
    parser.add_argument("--limit", default=0, type=int, help="Limit input samples")
    parser.add_argument("--batch_size", default=8, type=int, help="Limit input samples")
    parser.add_argument(
        "--title_field", default="input_title", help="Field containing the paper title"
    )
    parser.add_argument(
        "--abstract_field",
        default="abstract",
        help="Field containing the paper abstract",
    )
    parser.add_argument(
        "--id_field", default=None, help="Field containing the paper ID"
    )
    parser.add_argument(
        "--authors_field",
        default="authors",
        help="Field containing the paper authors",
    )
    parser.add_argument(
        "--venue_field", default=None, help="Field containing the paper venue"
    )
    parser.add_argument(
        "--url_field", default=None, help="Field containing the paper URL"
    )
    parser.add_argument(
        "--embedding_fields", nargs="+", required=True, help="Fields used as input to embedding model"
    )
    args = parser.parse_args()

    return args


def main():
    args = parse_arguments()

    title_field = args.title_field
    id_field = args.id_field
    abstract_field = args.abstract_field
    authors_field = args.authors_field
    venue_field = args.venue_field
    url_field = args.url_field

    embedding_fields = args.embedding_fields


    if len(embedding_fields) == 0:
        raise ValueError("No embedding fields set")
    elif len(embedding_fields) > 2:
        raise ValueError("Too many embedding fields set")

    print(f"Reading from {args.input_path}")

    # read input data
    df = pd.read_json(args.input_path, lines=True, orient="records")

    print(f"Input papers loaded: {len(df):,}")

    # drop all entries with missing values
    df = df.dropna(subset=[title_field, authors_field])

    # extract label information (from venue field)
    max_labels = 50
    labels = ["Other"]
    
    if venue_field is not None:
        labels += list(
        df[venue_field].value_counts(ascending=False).head(max_labels).index
    )

    # limit inputs (for debugging)
    if args.limit > 0:
        df = df.sample(n=args.limit).reindex()

    print("Loading embedding model")

    # load embedding model
    model = SentenceTransformer(args.model_name_or_path)

    # preprocessing (specific to SciNCL)
    sep_token = " [SEP] "

    title_abs = []
    for idx, row in df.iterrows():
        input_text = sep_token.join([row.get(f, "") or "" for f in embedding_fields])

        title_abs.append(input_text)

    print("Input papers:", len(title_abs))

    print("Generating embeddings")

    # Inference
    embeddings = model.encode(
        title_abs, batch_size=args.batch_size, show_progress_bar=True
    )

    # Convert to numpy
    embeddings = np.array(embeddings)

    print("Running umap")

    # maybe make smaller to focus on local structure, Sensible values are in the range 0.001 to 0.5,
    # metric='cosine' # correlation
    embeddings_2d = umap.UMAP(
        n_neighbors=10,  # 20,
        min_dist=0.05,  # 0.5,
        random_state=1,  # good = 1
    ).fit_transform(embeddings)

    # output
    label = 0
    papers = []
    for idx, (_, row) in enumerate(df.iterrows()):
        # {"loc":[41.575330,13.102411], "title":"aquamarine"},

        if venue_field is not None:
            try:
                label = labels.index(row[venue_field])
            except ValueError:
                # other
                label = 0

        paper = {
                "loc": embeddings_2d[idx].tolist(),
                "title": row[title_field],
                "authors": ", ".join(row[authors_field]),
                "abstract": row.get(abstract_field, ""),
                "label": label,
            }
        
        if id_field is not None:
            paper["id"] = row.get(id_field, None)
        
                
        if venue_field is not None:
            paper["venue"] = row.get(venue_field, None)

        if url_field is not None:
            paper["url"] = row[url_field]

            if isinstance(paper["url"], list):
                paper["url"] = paper["url"][0]

        if id_field == "openalex_id" and paper["url"] is None:
            paper["url"] = row[id_field]
        
        papers.append(
            paper
        )

    print("labels: ", json.dumps(labels), len(labels))

    # save
    with open(args.json_output_path, "w") as f:
        json.dump(papers, f)

    with open(args.js_output_path, "w") as f:
        f.write(get_js_content(papers=papers, labels=labels))

    print("Output saved to ", args.js_output_path)

    print("done")


if __name__ == "__main__":
    main()
