#!/usr/bin/env python
"""Create papers.js file with topic labels and colors.

This script combines:
- papers.json (with embeddings and paper data)
- topics.json (with topic titles, keywords, colors)
- paper_topics.json (mapping paper idx to topic idx)

Output:
- papers.js (JavaScript file for visualization)
"""

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
    # Load papers with embeddings
    print("Loading papers.json...")
    with open('paper-explorer/papers.json', 'r') as f:
        papers = json.load(f)

    print(f"Loaded {len(papers)} papers")

    # Load topics
    print("Loading topics.json...")
    with open('paper-explorer/topics.json', 'r') as f:
        topics = json.load(f)

    print(f"Loaded {len(topics)} topics")

    # Load paper-to-topic mapping
    print("Loading paper_topics.json...")
    with open('paper-explorer/paper_topics.json', 'r') as f:
        paper_topics = json.load(f)

    print(f"Loaded {len(paper_topics)} paper-topic mappings")

    # Count papers per topic
    topic_counts = Counter(paper_topics.values())

    # Sort topics by paper count (descending), then by topic index
    topic_indices_sorted = sorted(
        [int(idx) for idx in topics.keys()],
        key=lambda idx: (-topic_counts.get(idx, 0), idx)
    )

    # Create mapping from old topic index to new topic index (based on sorted order)
    old_to_new_topic_idx = {old_idx: new_idx for new_idx, old_idx in enumerate(topic_indices_sorted)}

    # Build labels and colors lists in sorted order
    labels = []
    colors = []

    for topic_idx in topic_indices_sorted:
        topic_data = topics[str(topic_idx)]
        labels.append(topic_data['topic_title'])
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
    print("\nGenerating papers.js...")
    js_content = get_js_content(papers=papers, labels=labels, colors=colors)

    # Save to file
    output_path = 'paper-explorer/papers.js'
    with open(output_path, 'w') as f:
        f.write(js_content)

    print(f"\nSuccessfully created {output_path}")

    # Print statistics
    new_topic_counts = Counter([p['label'] for p in papers])
    print("\nPapers per topic (sorted by count):")
    for new_idx in range(len(labels)):
        count = new_topic_counts.get(new_idx, 0)
        percentage = (count / len(papers)) * 100
        topic_title = labels[new_idx]
        old_idx = topic_indices_sorted[new_idx]
        print(f"  {new_idx:2d}. {topic_title:35s}: "
              f"{count:4d} papers ({percentage:5.1f}%) [old idx: {old_idx}]")

    print(f"\nTotal papers: {len(papers)}")


if __name__ == '__main__':
    main()
