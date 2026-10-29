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

    def test_js_alias_case_sensitive(self):
        self.assertEqual(m("JS 10y, TS 8y"), [("JavaScript", "JS")])
        self.assertEqual(m("React/JS"), [("React", "React"), ("JavaScript", "JS")])
        self.assertEqual(m("some regular js file"), [])  # case-sensitive: lowercase js must not match

    def test_cloudfront_infra_taxonomy(self):
        self.assertEqual(m("AWS, CloudFront"), [("AWS", "AWS"), ("CloudFront", "CloudFront")])
        self.assertEqual(m("AWS CloudFront distribution"), [("CloudFront", "AWS CloudFront")])

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

    def test_aws_cdk_and_postgis_do_not_collapse(self):
        self.assertEqual(m("AWS CDK infrastructure"), [("AWS CDK", "AWS CDK")])
        self.assertEqual(m("Deploy using AWS"), [("AWS", "AWS")])
        self.assertEqual(m("PostGIS queries"), [("PostGIS", "PostGIS")])
        self.assertEqual(m("PostgreSQL with PostGIS"), [("PostgreSQL", "PostgreSQL"), ("PostGIS", "PostGIS")])

    # ── Issue 1: CDK alias fix ────────────────────────────────────────────────

    def test_angular_cdk_not_aws_cdk(self):
        """'Angular CDK' must match Angular CDK (frontend), NOT AWS CDK."""
        result = m("Angular Material and Angular CDK")
        canonicals = [c for c, _ in result]
        self.assertIn("Angular CDK", canonicals)
        self.assertNotIn("AWS CDK", canonicals)

    def test_aws_cdk_still_matches(self):
        """'AWS CDK' must still match the AWS CDK taxonomy entry."""
        result = m("Deploy with AWS CDK")
        self.assertIn(("AWS CDK", "AWS CDK"), result)

    def test_bare_cdk_no_longer_matches_aws_cdk(self):
        """Bare 'CDK' must no longer match AWS CDK (removed alias)."""
        result = m("Use CDK for deployment")
        # CDK alone should NOT map to AWS CDK any more
        self.assertNotIn("AWS CDK", [c for c, _ in result])

    def test_aws_cdk_alias_lower(self):
        """aws-cdk alias must match AWS CDK case-sensitively."""
        result = m("Install aws-cdk package")
        self.assertIn(("AWS CDK", "aws-cdk"), result)
        # uppercase AWS-CDK must NOT match (case-sensitive)
        result2 = m("Install AWS-CDK package")
        self.assertNotIn("AWS CDK", [c for c, _ in result2])

    # ── Issue 6: SQL taxonomy ────────────────────────────────────────────────

    def test_sql_matches_standalone(self):
        """Standalone 'SQL' (all-caps) must match the SQL taxonomy entry."""
        result = m("SQL")
        self.assertEqual(result, [("SQL", "SQL")])

    def test_postgresql_does_not_yield_sql(self):
        """'PostgreSQL' must match PostgreSQL only, never SQL."""
        result = m("PostgreSQL")
        canonicals = [c for c, _ in result]
        self.assertIn("PostgreSQL", canonicals)
        self.assertNotIn("SQL", canonicals)

    def test_nosql_does_not_yield_sql(self):
        """'NoSQL' must not also match SQL."""
        result = m("NoSQL")
        canonicals = [c for c, _ in result]
        self.assertNotIn("SQL", canonicals)

    def test_mysql_does_not_yield_sql(self):
        """'MySQL' must not also match SQL."""
        result = m("MySQL databases")
        canonicals = [c for c, _ in result]
        self.assertNotIn("SQL", canonicals)

    def test_sqlite_does_not_yield_sql(self):
        """'SQLite' must not match SQL (SQLite has an embedded uppercase SQL)."""
        result = m("SQLite database")
        canonicals = [c for c, _ in result]
        self.assertNotIn("SQL", canonicals)

    # ── Nits: Rush.js / Testcontainers ───────────────────────────────────────

    def test_rush_js_aliases(self):
        """Rush.js and RushJS still match; bare 'Rush' no longer does."""
        self.assertEqual(m("Rush.js monorepo"), [("Rush.js", "Rush.js")])
        self.assertEqual(m("RushJS build"), [("Rush.js", "RushJS")])
        # Bare "Rush" must not match
        self.assertEqual(m("In a rush to deliver"), [])

    def test_testcontainers_no_duplicate_alias(self):
        """Testcontainers and Test Containers match; duplicate 'TestContainers' alias is removed.
        Note: 'TestContainers' still matches via the case-insensitive 'Testcontainers' alias — that's
        correct and expected; what's removed is the *redundant* separate alias entry."""
        r1 = find_matches("Testcontainers")
        r2 = find_matches("Test Containers")
        self.assertEqual(len(r1), 1)
        self.assertEqual(r1[0].canonical, "Testcontainers")
        self.assertEqual(len(r2), 1)
        self.assertEqual(r2[0].canonical, "Testcontainers")
        # Verify the taxonomy aliases list no longer has TestContainers as a distinct entry
        from ats_tailor.taxonomy import ENTRIES
        tc_entry = next(e for e in ENTRIES if e["canonical"] == "Testcontainers")
        # TestContainers must NOT appear as a distinct alias (it was the duplicate)
        self.assertNotIn("TestContainers", tc_entry["aliases"])
        # The two surviving aliases are 'Testcontainers' and 'Test Containers'
        self.assertEqual(set(tc_entry["aliases"]), {"Testcontainers", "Test Containers"})

    def test_angular_cdk_negative_aws_cdk(self):
        """Negative: 'CDK for Terraform' must not resolve to AWS CDK."""
        result = m("CDK for Terraform")
        self.assertNotIn("AWS CDK", [c for c, _ in result])


if __name__ == "__main__":
    unittest.main()
