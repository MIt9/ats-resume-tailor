import unittest

import helpers
from helpers import fx, read
from ats_tailor.postings import (
    extract_keywords,
    extract_unrecognized,
    extract_unrecognized_classified,
    extract_company_names,
)
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

    # ── Issue 3: company-name heuristic must not swallow real tech ────────────

    def test_posthog_not_swallowed_as_company(self):
        """'PostHog is a must' pattern must NOT drop PostHog from unrecognized terms."""
        t = "## Requirements\nPostHog is a must for us.\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        self.assertIn("PostHog", u)

    def test_clickhouse_not_swallowed_by_end_of_line_dash(self):
        """'Stack: Node.js - ClickHouse' must NOT drop ClickHouse."""
        t = "## Requirements\nStack: Node.js - ClickHouse\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        self.assertIn("ClickHouse", u)

    def test_company_names_limited_to_title_patterns(self):
        """extract_company_names keeps only Djinni/LLC patterns; 'is/was an' and end-dash are gone."""
        # "is/was an" pattern removed — should NOT extract the company
        names = extract_company_names("PostHog is a must for us.\n")
        self.assertNotIn("PostHog", names)
        # End-of-line dash pattern removed — should NOT extract ClickHouse
        names2 = extract_company_names("Stack: Node.js - ClickHouse\n")
        self.assertNotIn("ClickHouse", names2)
        # Djinni "в X –" still works
        names3 = extract_company_names("Розробник в Acme –\n")
        self.assertIn("Acme", names3)
        # LLC suffix still works
        names4 = extract_company_names("Join Globex LLC today\n")
        self.assertIn("Globex", names4)

    # ── Issue 4: state machine — one-line inline markers; emoji bullets ───────

    def test_inline_preferred_on_bullet_is_one_line_only(self):
        """A 'preferred' marker on a single emoji-bullet line must not demote following lines."""
        t = (
            "## Requirements\n"
            "- React\n"
            "- TypeScript\n"
            "🔹 Angular 18+ preferred\n"
            "- Docker\n"
        )
        k = self.kws(t)
        self.assertTrue(k["React"].required, "React should be required")
        self.assertTrue(k["TypeScript"].required, "TypeScript should be required")
        self.assertTrue(k["Docker"].required, "Docker after preferred bullet must still be required")
        # Angular on the preferred bullet must be nice-to-have (one-line demotion)
        self.assertFalse(k["Angular"].required, "Angular on preferred bullet must be nice-to-have")

    def test_emoji_bullets_are_bullets(self):
        """Lines starting with emoji bullets (🔹 • ▪ ✔ ✅ ➤) are treated as bullets."""
        from ats_tailor.postings import _BULLET
        for bullet_line in ["🔹 Angular preferred", "• React", "▪ Vue.js", "✔ TypeScript", "✅ Node.js", "➤ Python"]:
            self.assertTrue(_BULLET.match(bullet_line), f"Expected bullet match for: {bullet_line!r}")

    def test_revieve_style_bonus_bullet_demotes_only_that_line(self):
        """'bonus if you already live in them' must demote only its bullet, not the following TypeScript/React bullet."""
        t = (
            "## Requirements\n"
            "- TypeScript / React\n"
            "- bonus if you already live in them (Claude Code, MCP)\n"
            "- TypeScript\n"
            "- React\n"
        )
        k = self.kws(t)
        self.assertTrue(k["TypeScript"].required, "TypeScript must be required")
        self.assertTrue(k["React"].required, "React must be required")
        # Claude Code may be in kws but not required (it's on a bonus bullet)
        if "Claude Code" in k:
            self.assertFalse(k["Claude Code"].required, "Claude Code is on bonus line, must be nice-to-have")

    def test_heading_switches_section_state(self):
        """Headings still control section state; an emoji-bullet nice-to-have must not switch global state."""
        t = (
            "## Requirements\n"
            "🔹 React preferred\n"
            "- TypeScript\n"
            "\n## Nice to have\n"
            "- Redis\n"
        )
        k = self.kws(t)
        # TypeScript is after an emoji-bullet preferred, but in ## Requirements — must be required
        self.assertTrue(k["TypeScript"].required, "TypeScript in Requirements section must be required")
        self.assertFalse(k["Redis"].required, "Redis in Nice to have section must be nice-to-have")

    # ── Issue 5: HIPAA / GDPR / SOC / ISO / PCI / DSS not filtered ───────────

    def test_compliance_terms_not_in_stop_list(self):
        """HIPAA, GDPR, SOC, ISO, PCI, DSS must surface as unrecognized tech terms, not be dropped."""
        t = "## Requirements\n- HIPAA and SOC 2 experience\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        self.assertIn("HIPAA", u)
        self.assertIn("SOC", u)

    def test_gdpr_iso_pci_dss_not_filtered(self):
        """GDPR, ISO, PCI, DSS must not be in the stop list."""
        t = "## Requirements\n- GDPR compliance, ISO 27001, PCI DSS\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        self.assertIn("GDPR", u)
        self.assertIn("ISO", u)
        self.assertIn("PCI", u)
        self.assertIn("DSS", u)

    def test_noise_still_filtered(self):
        """LLC, INC, KPMG, PWC, ABOUT, STACK, HIRING, PROCESS noise must still be filtered."""
        from ats_tailor.postings import _STOP
        for token in ["LLC", "INC", "KPMG", "PWC", "ABOUT", "STACK", "HIRING", "PROCESS"]:
            self.assertIn(token, _STOP, f"{token} should still be in _STOP")

    def test_country_dropdown_runon_filtered(self):
        """Country dropdown run-together names (long + contains 2+ country names) are noise-filtered."""
        # "GermanyPolandUkraine" — 3 countries, > 18 chars, should be noise
        t = "## Requirements\n- GermanyPolandUkraine experience\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        self.assertNotIn("GermanyPolandUkraine", u)

    def test_about_stack_headings_filtered(self):
        """ABOUT, STACK heading-style tokens remain in stop list."""
        from ats_tailor.postings import _STOP
        self.assertIn("ABOUT", _STOP)
        self.assertIn("STACK", _STOP)

    # ── Issue 6: SQL in taxonomy via unrecognized classification ─────────────

    def test_sql_requirement_matched_not_unrecognized(self):
        """'SQL' in requirements must be matched by taxonomy (not appear in unrecognized)."""
        t = "## Requirements\n- SQL\n"
        spans = [(x.start, x.end) for x in find_matches(t)]
        u = extract_unrecognized(t, spans)
        self.assertNotIn("SQL", u)
        # And extract_keywords should find it
        k = self.kws(t)
        self.assertIn("SQL", k)
        self.assertTrue(k["SQL"].required)

    def test_postgresql_alone_does_not_yield_sql(self):
        """'PostgreSQL' alone must match PostgreSQL, not SQL."""
        t = "## Requirements\n- PostgreSQL\n"
        k = self.kws(t)
        self.assertIn("PostgreSQL", k)
        self.assertNotIn("SQL", k)


if __name__ == "__main__":
    unittest.main()
