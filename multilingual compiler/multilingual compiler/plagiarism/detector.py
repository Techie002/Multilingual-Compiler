import re
import math
import difflib

class PlagiarismDetector:
    def __init__(self, n_gram_size=3):
        self.n_gram_size = n_gram_size

    def check_plagiarism(self, source_code, target_code):
        """
        Runs token-based, AST-based, and Cosine similarity checks between two source code snippets.
        Returns comprehensive plagiarism breakdown.
        """
        token_sim = self.token_similarity(source_code, target_code)
        ast_sim = self.ast_similarity(source_code, target_code)
        cosine_sim = self.cosine_similarity(source_code, target_code)

        overall_sim = round((token_sim * 0.4) + (ast_sim * 0.3) + (cosine_sim * 0.3), 2)

        highlighted_matches = self.find_matching_blocks(source_code, target_code)

        flagged = overall_sim >= 70.0

        return {
            "overall_similarity": overall_sim,
            "token_similarity": round(token_sim, 2),
            "ast_similarity": round(ast_sim, 2),
            "cosine_similarity": round(cosine_sim, 2),
            "flagged": flagged,
            "matching_blocks": highlighted_matches,
            "summary": f"Plagiarism Risk: {'HIGH' if overall_sim >= 70 else 'MODERATE' if overall_sim >= 40 else 'LOW'} ({overall_sim}% overall match)."
        }

    def tokenize_clean(self, code):
        """Normalizes source code by removing comments, whitespace, and string literal variations."""
        # Strip single line comments
        clean = re.sub(r'#.*|//.*', '', code)
        # Normalize identifiers to generic token types
        clean = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'ID', clean)
        # Normalize numbers
        clean = re.sub(r'\b\d+\b', 'NUM', clean)
        tokens = clean.split()
        return tokens

    def token_similarity(self, code1, code2):
        """Token-based N-gram Jaccard Similarity."""
        tokens1 = self.tokenize_clean(code1)
        tokens2 = self.tokenize_clean(code2)

        if not tokens1 or not tokens2:
            return 0.0

        ngrams1 = set(tuple(tokens1[i:i+self.n_gram_size]) for i in range(len(tokens1) - self.n_gram_size + 1))
        ngrams2 = set(tuple(tokens2[i:i+self.n_gram_size]) for i in range(len(tokens2) - self.n_gram_size + 1))

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)

        return (len(intersection) / len(union)) * 100.0

    def ast_similarity(self, code1, code2):
        """AST structural similarity based on control flow & block hierarchy."""
        struct1 = self._get_structural_tokens(code1)
        struct2 = self._get_structural_tokens(code2)

        matcher = difflib.SequenceMatcher(None, struct1, struct2)
        return matcher.ratio() * 100.0

    def _get_structural_tokens(self, code):
        keywords = re.findall(r'\b(def|class|for|while|if|else|elif|try|except|return|import|int|void|public|static)\b', code)
        return keywords

    def cosine_similarity(self, code1, code2):
        """TF-IDF Cosine similarity over identifier frequencies."""
        words1 = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code1)
        words2 = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code2)

        if not words1 or not words2:
            return 0.0

        freq1 = {}
        for w in words1:
            freq1[w] = freq1.get(w, 0) + 1

        freq2 = {}
        for w in words2:
            freq2[w] = freq2.get(w, 0) + 1

        all_words = set(freq1.keys()).union(set(freq2.keys()))

        dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
        magnitude1 = math.sqrt(sum(v**2 for v in freq1.values()))
        magnitude2 = math.sqrt(sum(v**2 for v in freq2.values()))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return (dot_product / (magnitude1 * magnitude2)) * 100.0

    def find_matching_blocks(self, code1, code2):
        """Finds contiguous matching blocks of code lines for reporting."""
        lines1 = code1.splitlines()
        lines2 = code2.splitlines()

        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        matching_blocks = []

        for block in matcher.get_matching_blocks():
            if block.size >= 2: # Only record matches of 2 or more contiguous lines
                matching_blocks.append({
                    "source_start_line": block.a + 1,
                    "source_end_line": block.a + block.size,
                    "target_start_line": block.b + 1,
                    "target_end_line": block.b + block.size,
                    "line_count": block.size,
                    "matched_content": lines1[block.a : block.a + block.size]
                })

        return matching_blocks
