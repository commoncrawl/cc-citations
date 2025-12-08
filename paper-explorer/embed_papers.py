#!/usr/bin/env python
import argparse
import json
import pandas as pd

import numpy as np
from sentence_transformers import SentenceTransformer
import umap


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path",
        default=None,
        type=str,
        help="Path to Excel sheet downloaded from EMNLP",
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

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_arguments()

    # read input data
    df = pd.read_json(args.input_path, lines=True, orient="records")

    # drop all entries with missing values
    df = df.dropna(subset=["abstract", "input_title", "venue", "authors"])

    # extract label information (from venue field)
    max_labels = 50
    labels = ["Other"] + list(
        df["venue"].value_counts(ascending=False).head(max_labels).index
    )

    # limit inputs (for debugging)
    if args.limit > 0:
        df = df.sample(n=args.limit).reindex()

    # load embedding model
    model = SentenceTransformer(args.model_name_or_path)

    # preprocessing (specific to SciNCL)
    sep_token = " [SEP] "

    title_abs = []
    for idx, row in df.iterrows():
        title_abs.append(row["input_title"] + sep_token + row.get("abstract", ""))

    print("Input papers:", len(title_abs))

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
    papers = []
    for idx, (_, row) in enumerate(df.iterrows()):
        # {"loc":[41.575330,13.102411], "title":"aquamarine"},
        try:
            label = labels.index(row["venue"])
        except ValueError:
            # other
            label = 0

        papers.append(
            {
                "loc": embeddings_2d[idx].tolist(),
                "openalex_id": row["openalex_id"],
                "title": row["input_title"],
                "authors": ", ".join(row["authors"]),
                "abstract": (row.get("abstract", "")),
                "venue": row["venue"],
                "label": label,
            }
        )

    print("labels: ", json.dumps(labels), len(labels))

    # save
    with open(args.json_output_path, "w") as f:
        json.dump(papers, f)

    with open(args.js_output_path, "w") as f:
        js = f"var data = {json.dumps(papers)};\n"
        js += f"var labels = {json.dumps(labels)};\n"

        f.write(js)

    print("Output saved to ", args.js_output_path)

    print("done")
