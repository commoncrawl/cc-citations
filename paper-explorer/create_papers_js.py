#!/usr/bin/env python
"""Create papers.js file with topic labels and colors.

This script combines:
- papers.json (with embeddings and paper data)
- topics.json (with topic titles, keywords, colors)
- paper_topics.json (mapping paper idx to topic idx)

Output:
- papers.js (JavaScript file for visualization)
"""

import argparse
import json
from collections import Counter


def get_js_content(papers, labels, colors=None) -> str:
    """Generate JavaScript content for visualization.

    Args:
        papers: List of paper dictionaries with loc, title, etc.
        labels: List of label names (topic titles)
        colors: List of color codes (hex colors for each topic)

    Returns:
        JavaScript code as string
    """
    if colors is None:
        # default colors
        colors = [
            "#63b598", "#ce7d78", "#ea9e70", "#a48a9e", "#c6e1e8", "#648177", "#0d5ac1",
            "#f205e6", "#1c0365", "#14a9ad", "#4ca2f9", "#a4e43f", "#d298e2", "#6119d0",
            "#d2737d", "#c0a43c", "#f2510e", "#651be6", "#79806e", "#61da5e", "#cd2f00",
            "#9348af", "#01ac53", "#c5a4fb", "#996635", "#b11573", "#4bb473", "#75d89e",
            "#2f3f94", "#2f7b99", "#da967d", "#34891f", "#b0d87b", "#ca4751", "#7e50a8",
            "#c4d647", "#e0eeb8", "#11dec1", "#289812", "#566ca0", "#ffdbe1", "#2f1179",
        ]

    js = f"var colors = {json.dumps(colors)};\n"
    js += f"var data = {json.dumps(papers)};\n"
    js += f"var labels = {json.dumps(labels)};\n"

    return js


def main():
    parser = argparse.ArgumentParser(
        description='Create papers.js file with topic labels and colors'
    )
    parser.add_argument(
        '--papers',
        type=str,
        default='paper-explorer/papers.json',
        help='Path to papers JSON file (default: paper-explorer/papers.json)'
    )
    parser.add_argument(
        '--topics',
        type=str,
        default='paper-explorer/topics.json',
        help='Path to topics JSON file (default: paper-explorer/topics.json)'
    )
    parser.add_argument(
        '--paper-topics',
        type=str,
        default='paper-explorer/paper_topics.json',
        help='Path to paper-topics mapping JSON file (default: paper-explorer/paper_topics.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='paper-explorer/papers.js',
        help='Output JavaScript file path (default: paper-explorer/papers.js)'
    )

    args = parser.parse_args()

    # Load papers with embeddings
    print(f"Loading papers from {args.papers}...")
    with open(args.papers, 'r') as f:
        papers = json.load(f)

    print(f"Loaded {len(papers)} papers")

    # Load topics
    print(f"Loading topics from {args.topics}...")
    with open(args.topics, 'r') as f:
        topics = json.load(f)

    print(f"Loaded {len(topics)} topics")

    # Load paper-to-topic mapping
    print(f"Loading paper-topics mapping from {args.paper_topics}...")
    with open(args.paper_topics, 'r') as f:
        paper_topics = json.load(f)

    print(f"Loaded {len(paper_topics)} paper-topic mappings")

    title_field = "topic_title"

    # Merge topics with the same title
    print("\nMerging topics with duplicate titles...")
    title_to_topic_indices = {}  # Map from title to list of original topic indices
    title_to_merged_data = {}    # Map from title to merged topic data

    for topic_idx_str, topic_data in topics.items():
        topic_idx = int(topic_idx_str)
        title = topic_data[title_field]

        if title not in title_to_topic_indices:
            title_to_topic_indices[title] = []
            # Keep the first occurrence's data (color, etc.)
            title_to_merged_data[title] = topic_data.copy()

        title_to_topic_indices[title].append(topic_idx)

    print(f"Found {len(title_to_merged_data)} unique topic titles from {len(topics)} original topics")

    # Create mapping from old topic index to title (for paper-topic remapping)
    old_topic_idx_to_title = {}
    for title, indices in title_to_topic_indices.items():
        for idx in indices:
            old_topic_idx_to_title[idx] = title
        if len(indices) > 1:
            print(f"  Merging {len(indices)} topics with title '{title}': {indices}")

    # Update paper_topics mapping to use merged topics
    # Map from old topic idx to title, which represents the merged topic
    merged_paper_topics = {}
    for paper_idx_str, old_topic_idx in paper_topics.items():
        if old_topic_idx in old_topic_idx_to_title:
            merged_paper_topics[paper_idx_str] = old_topic_idx_to_title[old_topic_idx]
        else:
            # Topic not found, keep original
            merged_paper_topics[paper_idx_str] = old_topic_idx

    # Count papers per merged topic (by title)
    merged_topic_counts = Counter(merged_paper_topics.values())

    # Sort merged topics by paper count (descending), then by title
    sorted_titles = sorted(
        title_to_merged_data.keys(),
        key=lambda title: (-merged_topic_counts.get(title, 0), title)
    )

    # Create mapping from title to new sequential index
    title_to_new_idx = {title: new_idx for new_idx, title in enumerate(sorted_titles)}

    # Create mapping from old topic index to new sequential index
    old_to_new_topic_idx = {}
    for old_idx, title in old_topic_idx_to_title.items():
        old_to_new_topic_idx[old_idx] = title_to_new_idx[title]

    # Build labels and colors lists in sorted order
    labels = []
    colors = []

    for title in sorted_titles:
        topic_data = title_to_merged_data[title]
        labels.append(topic_data[title_field])
        colors.append(topic_data['color'])

    print("\nTopics (sorted by paper count):")
    for i, (label, color) in enumerate(zip(labels, colors)):
        print(f"  {i}: {label} ({color})")

    # Update papers with topic labels (remapped to sorted order)
    print("\nUpdating papers with topic labels...")
    for paper_idx, paper in enumerate(papers):
        # Get original topic for this paper
        old_topic_idx = paper_topics.get(str(paper_idx))

        if old_topic_idx is not None:
            # Remap to new sorted index
            paper['label'] = old_to_new_topic_idx[old_topic_idx]
        else:
            # Default to 0 if no topic assigned
            paper['label'] = 0
            msg = f"Warning: Paper {paper_idx} has no topic assignment"
            print(msg)

    # Generate JavaScript content
    print("\nGenerating JavaScript content...")
    js_content = get_js_content(papers=papers, labels=labels, colors=colors)

    # Save to file
    print(f"Writing to {args.output}...")
    with open(args.output, 'w') as f:
        f.write(js_content)

    print(f"\nSuccessfully created {args.output}")

    # Print statistics
    new_topic_counts = Counter([p['label'] for p in papers])
    print("\nPapers per topic (sorted by count):")
    for new_idx in range(len(labels)):
        count = new_topic_counts.get(new_idx, 0)
        percentage = (count / len(papers)) * 100
        topic_title = labels[new_idx]

        # Find which original topic indices were merged into this topic
        original_indices = title_to_topic_indices[sorted_titles[new_idx]]
        original_indices_str = ', '.join(map(str, sorted(original_indices)))

        print(f"  {new_idx:2d}. {topic_title:35s}: "
              f"{count:4d} papers ({percentage:5.1f}%) [original idx: {original_indices_str}]")

    print(f"\nTotal papers: {len(papers)}")
    print(f"Original topics: {len(topics)}, Merged topics: {len(labels)}")


if __name__ == '__main__':
    main()
