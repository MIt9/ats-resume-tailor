import unittest

import helpers
from helpers import fx
from ats_tailor.ledger import load_pets


class LedgerLevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = helpers.make_ledger()

    def lv(self, c):
        return self.L.level(c)

    def test_confirmed(self):
        for c in ["React", "TypeScript", "Redux", "Next.js", "Angular", "Docker", "Node.js", "GraphQL", "RabbitMQ", "Jest"]:
            self.assertEqual(self.lv(c), "confirmed", c)

    def test_personal(self):
        for c in ["Redis", "Kubernetes", "MongoDB", "DynamoDB", "Elasticsearch", "Cloudflare"]:
            self.assertEqual(self.lv(c), "personal", c)  # Kubernetes: personal beats NOT in Terraform/Helm row

    def test_nestjs_personal(self):
        # Ambiguity: inventory row Status is "confirmed 2026-10-09" but Evidence says "pet projects only".
        # Task brief says NestJS is personal, so rule 2 must also look at the Evidence cell.
        self.assertEqual(self.lv("NestJS"), "personal")

    def test_python_override(self):
        self.assertEqual(self.lv("Python"), "personal")
        self.assertEqual(self.L.wording("Python"), "Python (personal projects, PyPI packages)")
        self.assertIsNone(self.L.wording("React"))

    def test_not(self):
        for c in ["Terraform", "Helm", "Zustand", "Redux Toolkit", "TanStack Query", "Vitest", "Stripe", "Kafka", "GCP"]:
            self.assertEqual(self.lv(c), "not", c)

    def test_unknown(self):
        self.assertEqual(self.lv("Svelte"), "unknown")

    def test_pwa_partial(self):
        # Status "confirmed ... (limited)" -> partial. Requires PWA to be a taxonomy canonical.
        self.assertEqual(self.lv("PWA"), "partial")

    def test_evidence(self):
        self.assertIn("silpo.ua SPA", self.L.evidence("TypeScript"))
        self.assertIsInstance(self.L.evidence("Svelte"), str)


class PetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pets = load_pets(fx("pets.md"))
        cls.by = {p.name: p for p in cls.pets}

    def test_loaded_and_private_skipped(self):
        for n in ["mcp-book-lover", "laya-cli", "mcp-elevenreader", "workatastartup-mcp", "pexels-cli", "gifboom", "silpo-agent-cli", "mcp-comfy-ui-builder"]:
            self.assertIn(n, self.by)
        self.assertFalse([p for p in self.pets if p.name.startswith("silpo-mcp")])

    def test_fields(self):
        p = self.by["mcp-book-lover"]
        self.assertEqual(p.github, "https://github.com/MIt9/mcp-book-lover")
        self.assertEqual(p.stack, ["Python", "MCP"])
        self.assertEqual(p.line, "mcp-book-lover — MCP book library manager (35+ tools, 8 sources, TTS sync)")
        self.assertEqual(self.by["mcp-comfy-ui-builder"].stack, ["TypeScript", "Node.js", "WebSockets"])

    def test_pets_for(self):
        import helpers as h
        names = {p.name for p in h.make_ledger().pets_for("Python")}
        self.assertTrue({"mcp-book-lover", "laya-cli", "gifboom"} <= names)
        self.assertNotIn("mcp-comfy-ui-builder", names)
        self.assertFalse([n for n in names if n.startswith("silpo-mcp")])


if __name__ == "__main__":
    unittest.main()
