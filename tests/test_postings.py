import unittest

import helpers
from helpers import fx, read
from ats_tailor.postings import extract_keywords, extract_unrecognized
from ats_tailor.taxonomy import find_matches


class PostingTests(unittest.TestCase):
    def kws(self, text):
        return {k.canonical: k for k in extract_keywords(text)}

    def test_posting_a_keywords(self):
        k = self.kws(read(fx("posting_a.md")))
        self.assertEqual(set(k), {"React", "TypeScript", "Node.js", "GraphQL", "NestJS", "Kubernetes", "Kafka",
                                  "Terraform", "Vitest", "Stripe", "Redis", "Svelte", "Docker"})
        self.assertEqual(k["React"].spelling, "React.js")
        self.assertEqual(k["Node.js"].spelling, "Node.js")

    def test_required_vs_nice(self):
        k = self.kws(read(fx("posting_a.md")))
        for c in ["Redis", "Svelte", "Docker"]:
            self.assertFalse(k[c].required, c)
        for c in ["React", "TypeScript", "Node.js", "GraphQL", "NestJS", "Kubernetes", "Kafka", "Terraform", "Vitest", "Stripe"]:
            self.assertTrue(k[c].required, c)

    def test_required_wins_when_in_both(self):
        k = self.kws("## Requirements\n- Docker\n\n## Nice to have\n- Docker\n- Redis\n")
        self.assertTrue(k["Docker"].required)
        self.assertFalse(k["Redis"].required)
        self.assertEqual(k["Docker"].count, 2)

    def test_nice_markers_and_section_end(self):
        t = "# Job\n## Bonus\n- Redis\n### Details\n- Svelte\n## Stack\n- Docker\n"
        k = self.kws(t)
        self.assertFalse(k["Redis"].required)
        self.assertFalse(k["Svelte"].required)  # deeper heading does not end the nice section
        self.assertTrue(k["Docker"].required)   # equal-level heading ends it
        k = self.kws("Requirements:\n- Docker\nNice to have:\n- Redis\n")  # plain-line marker
        self.assertTrue(k["Docker"].required)
        self.assertFalse(k["Redis"].required)

    def test_spellings_prefer_first_required(self):
        t = "## Nice to have\n- ReactJS\n## Requirements\n- React.js\n- React\n"
        k = self.kws(t)["React"]
        self.assertEqual(k.spelling, "React.js")
        self.assertEqual(k.spellings, ["ReactJS", "React.js", "React"])
        self.assertEqual(k.count, 3)

    def test_spelling_first_overall_when_no_required(self):
        k = self.kws("## Nice to have\n- ReactJS\n- React\n")["React"]
        self.assertEqual(k.spelling, "ReactJS")

    def test_unrecognized(self):
        t = read(fx("posting_a.md"))
        spans = [(x.start, x.end) for x in find_matches(t)]
        self.assertEqual(extract_unrecognized(t, spans), ["FooBarDB"])

    def test_unrecognized_patterns_and_stoplist(self):
        t = "Need QuxJS, Blarg.js and ZEBRADB. Remote EU, CEO, B2B, KPI, ASAP and THE team.\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        for x in ["QuxJS", "Blarg.js", "ZEBRADB"]:
            self.assertIn(x, u)
        for x in ["EU", "CEO", "B2B", "KPI", "ASAP", "THE"]:
            self.assertNotIn(x, u)

    def test_known_not_unrecognized(self):
        t = "TypeScript GraphQL NestJS Node.js"
        spans = [(x.start, x.end) for x in find_matches(t)]
        self.assertEqual(extract_unrecognized(t, spans), [])


if __name__ == "__main__":
    unittest.main()
