import unittest

import helpers  # noqa: F401  (sets sys.path)
from ats_tailor.taxonomy import find_matches


def m(text):
    return [(x.canonical, x.spelling) for x in find_matches(text)]


class TaxonomyTests(unittest.TestCase):
    def test_react_spellings_preserved(self):
        self.assertEqual(m("React.js"), [("React", "React.js")])
        self.assertEqual(m("ReactJS"), [("React", "ReactJS")])
        self.assertEqual(m("React JS"), [("React", "React JS")])
        self.assertEqual(m("React"), [("React", "React")])

    def test_case_insensitive_keeps_posting_casing(self):
        self.assertEqual(m("typescript"), [("TypeScript", "typescript")])

    def test_react_sentence_end(self):
        r = find_matches("We love React.")
        self.assertEqual([(x.canonical, x.spelling) for x in r], [("React", "React")])
        self.assertEqual("We love React."[r[0].start:r[0].end], "React")

    def test_react_dot_js_not_split(self):
        self.assertEqual(m("Strong React.js skills"), [("React", "React.js")])

    def test_react_query_is_tanstack_not_react(self):
        self.assertEqual(m("React Query"), [("TanStack Query", "React Query")])

    def test_redux_toolkit_not_also_redux(self):
        self.assertEqual(m("Redux Toolkit"), [("Redux Toolkit", "Redux Toolkit")])
        self.assertEqual(m("Redux"), [("Redux", "Redux")])

    def test_nextjs_not_node_or_js(self):
        self.assertEqual(m("Next.js"), [("Next.js", "Next.js")])

    def test_javascript_not_java(self):
        self.assertEqual(m("JavaScript"), [("JavaScript", "JavaScript")])

    def test_token_boundaries(self):
        self.assertEqual(m("Reactive programming"), [])
        self.assertEqual(m("React+"), [])  # not followed by [A-Za-z0-9_+#]

    def test_positions_ordered_nonoverlapping(self):
        text = "Redux Toolkit, React Query and Next.js"
        r = find_matches(text)
        self.assertEqual([x.canonical for x in r], ["Redux Toolkit", "TanStack Query", "Next.js"])
        for x in r:
            self.assertEqual(text[x.start:x.end], x.spelling)
        for a, b in zip(r, r[1:]):
            self.assertLessEqual(a.end, b.start)

    def test_go_rules(self):
        self.assertEqual(m("Go to market strategy"), [])
        self.assertEqual(m("We use Go, Python"), [("Go", "Go"), ("Python", "Python")])
        self.assertEqual(m("Go microservices"), [("Go", "Go")])
        self.assertEqual(m("Golang"), [("Go", "Golang")])
        self.assertEqual(m("go to the backend service"), [])  # only capitalized Go

    def test_node_rules(self):
        self.assertEqual(m("Node.js"), [("Node.js", "Node.js")])
        self.assertEqual(m("Node, Express"), [("Node.js", "Node"), ("Express", "Express")])
        self.assertEqual(m("Node and React"), [("Node.js", "Node"), ("React", "React")])
        self.assertEqual(m("React/Node"), [("React", "React"), ("Node.js", "Node")])
        self.assertEqual(m("(React, Node)"), [("React", "React"), ("Node.js", "Node")])
        self.assertEqual(m("Backend: Node"), [("Node.js", "Node")])
        self.assertEqual(m("Node modules folder"), [])
        self.assertEqual(m("node and npm"), [])  # only capitalized Node

    def test_multiword_and_symbol_aliases(self):
        self.assertEqual(m("CI/CD"), [("CI/CD", "CI/CD")])
        self.assertEqual(m("A/B testing"), [("A/B Testing", "A/B testing")])
        self.assertEqual(m("Kubernetes or K8s"), [("Kubernetes", "Kubernetes"), ("Kubernetes", "K8s")])
        self.assertEqual(m("Postgres"), [("PostgreSQL", "Postgres")])
        self.assertEqual(m("Model Context Protocol"), [("MCP", "Model Context Protocol")])

    def test_unknown_tech_not_matched(self):
        self.assertEqual(m("FooBarDB"), [])


if __name__ == "__main__":
    unittest.main()
