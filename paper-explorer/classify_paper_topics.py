"""Classify research paper topics using LDA implementation using scikit-learn.

Inputs:

- Path to JSON list of research papers (title, abstract).
- Number of topics

Topics are classified based on title + abstract.

Outputs:

- Mapping of topic idx to keywords
- Mapping of paper idx to topic idx

Usage:

paper-explorer/classify_paper_topics.py --input_path=paper-explorer/papers.json --topics_path=paper-explorer/paper_topics.json --paper_to_topic_path=paper-explorer/paper_topics.json

"""

import json
import argparse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

# English stop words tailored to research papers
stop_words = {
    # Common English stop words
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but',
    'by', 'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself',
    'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just',
    'me', 'might', 'more', 'most', 'must', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off',
    'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 's',
    'same', 'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs',
    'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to',
    'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which',
    'while', 'who', 'whom', 'why', 'will', 'with', 'would', 'you', 'your', 'yours', 'yourself',
    'yourselves',
    # Research paper specific stop words
    'abstract', 'article', 'paper', 'study', 'research', 'results', 'conclusion', 'introduction',
    'method', 'methodology', 'approach', 'analysis', 'figure', 'table', 'section', 'based',
    'using', 'show', 'shows', 'presented', 'propose', 'proposed', 'discuss', 'discussed',
    'demonstrate', 'demonstrated', 'investigate', 'investigated', 'examine', 'examined'
}


def load_papers(input_path):
    """Load papers from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    return papers


def preprocess_papers(papers):
    """Extract and combine title and abstract from papers."""
    documents = []
    for paper in papers:
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        # Combine title and abstract, handle missing values
        text = f"{title} {abstract}".strip()
        documents.append(text)
    return documents


def train_lda_model(documents, n_topics, max_features=3000, max_iter=50, random_state=42):
    """Train LDA model on documents."""
    # Calculate min_df based on corpus size for better filtering
    n_docs = len(documents)

    # Create document-term matrix
    vectorizer = CountVectorizer(
        max_features=max_features,
        stop_words=list(stop_words),
        lowercase=True,
        min_df=max(3, int(n_docs * 0.002)),  # Filter rare terms (min 3 or 0.2%)
        max_df=0.7  # Ignore very common terms (70% threshold)
    )
    doc_term_matrix = vectorizer.fit_transform(documents)

    # Train LDA model
    # Use batch learning for better topic balance
    # alpha: controls document-topic density (higher = more topics per doc)
    # eta (beta): controls topic-word density
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        max_iter=max_iter,
        learning_method='batch',  # Use batch for better convergence
        learning_offset=10.,
        doc_topic_prior=None,  # Use symmetric prior (1/n_topics)
        topic_word_prior=None,  # Use symmetric prior
        random_state=random_state,
        n_jobs=-1,
        evaluate_every=5,
        perp_tol=0.01
    )
    lda.fit(doc_term_matrix)

    return lda, vectorizer, doc_term_matrix


def extract_topics(lda, vectorizer, n_words=10):
    """Extract top keywords for each topic."""
    topics = {}
    feature_names = vectorizer.get_feature_names_out()

    for topic_idx, topic in enumerate(lda.components_):
        top_indices = topic.argsort()[-n_words:][::-1]
        top_words = [feature_names[i] for i in top_indices]
        topics[topic_idx] = {"keywords": top_words}

    return topics


def assign_papers_to_topics(lda, doc_term_matrix):
    """Assign each paper to its most probable topic."""
    topic_distributions = lda.transform(doc_term_matrix)
    paper_topics = {}

    for paper_idx, distribution in enumerate(topic_distributions):
        topic_idx = int(np.argmax(distribution))
        paper_topics[paper_idx] = topic_idx

    return paper_topics


def save_json(data, output_path):
    """Save data to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Classify research paper topics using LDA'
    )
    parser.add_argument(
        '--input_path',
        type=str,
        required=True,
        help='Path to input JSON file containing papers'
    )
    parser.add_argument(
        '--topics_path',
        type=str,
        required=True,
        help='Path to output JSON file for topic keywords'
    )
    parser.add_argument(
        '--paper_to_topic_path',
        type=str,
        required=True,
        help='Path to output JSON file for paper-to-topic mapping'
    )
    parser.add_argument(
        '--n_topics',
        type=int,
        default=10,
        help='Number of topics to extract (default: 10)'
    )
    parser.add_argument(
        '--n_words',
        type=int,
        default=10,
        help='Number of keywords per topic (default: 10)'
    )
    parser.add_argument(
        '--max_features',
        type=int,
        default=3000,
        help='Maximum number of features for vectorizer (default: 3000)'
    )
    parser.add_argument(
        '--max_iter',
        type=int,
        default=50,
        help='Maximum number of iterations for LDA (default: 50)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of papers to process (default: None, process all)'
    )

    args = parser.parse_args()

    print(f"Loading papers from {args.input_path}...")
    papers = load_papers(args.input_path)

    if args.limit is not None:
        papers = papers[:args.limit]
        print(f"Limited to {len(papers)} papers")
    else:
        print(f"Loaded {len(papers)} papers")

    print("Preprocessing papers...")
    documents = preprocess_papers(papers)

    print(f"Training LDA model with {args.n_topics} topics...")
    lda, vectorizer, doc_term_matrix = train_lda_model(
        documents,
        args.n_topics,
        max_features=args.max_features,
        max_iter=args.max_iter
    )

    print(f"Extracting top {args.n_words} keywords per topic...")
    topics = extract_topics(lda, vectorizer, n_words=args.n_words)

    print("Assigning papers to topics...")
    paper_topics = assign_papers_to_topics(lda, doc_term_matrix)

    print(f"Saving topics to {args.topics_path}...")
    save_json(topics, args.topics_path)

    print(f"Saving paper-to-topic mapping to {args.paper_to_topic_path}...")
    save_json(paper_topics, args.paper_to_topic_path)

    print("\nTopic keywords:")
    for topic_idx, topic_data in topics.items():
        keywords = topic_data["keywords"]
        print(f"Topic {topic_idx}: {', '.join(keywords)}")

    print(f"\nDone! Classified {len(paper_topics)} papers into {args.n_topics} topics.")


if __name__ == '__main__':
    main()

