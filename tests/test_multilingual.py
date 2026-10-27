import os
import tempfile
import unittest

import helpers
from helpers import fx, make_ledger
from ats_tailor.ledger import load_pets
from ats_tailor.postings import extract_keywords
from ats_tailor.resume import tailor


class MultilingualPostingTests(unittest.TestCase):
    def kws(self, text):
        return {k.canonical: k for k in extract_keywords(text)}

    def test_ukrainian_nice_section(self):
        text = """# Вакансія Full Stack Engineer
## Вимоги:
- Python
- TypeScript
- Docker

## Буде плюсом:
- Redis
- Kubernetes
"""
        k = self.kws(text)
        self.assertTrue(k["Python"].required)
        self.assertTrue(k["TypeScript"].required)
        self.assertTrue(k["Docker"].required)
        self.assertFalse(k["Redis"].required)
        self.assertFalse(k["Kubernetes"].required)

    def test_ukrainian_inline_nice_bullet(self):
        text = """## Вимоги:
- Python
- Redis буде плюсом
- Docker
"""
        k = self.kws(text)
        self.assertTrue(k["Python"].required)
        self.assertFalse(k["Redis"].required)
        self.assertTrue(k["Docker"].required)

    def test_international_nice_markers(self):
        markers = [
            ("плюсом буде", "Redis"),
            ("бажано", "Redis"),
            ("перевагою буде", "Redis"),
            ("буде перевагою", "Redis"),
            ("додатково", "Redis"),
            ("von vorteil", "Redis"),
            ("wünschenswert", "Redis"),
            ("atout", "Redis"),
        ]
        for marker, tech in markers:
            text = f"## Requirements\n- Docker\n## {marker.capitalize()}:\n- {tech}\n"
            k = self.kws(text)
            self.assertTrue(k["Docker"].required, f"Docker should be required for marker: {marker}")
            self.assertFalse(k[tech].required, f"{tech} should be nice-to-have for marker: {marker}")


class MultilingualPetsTests(unittest.TestCase):
    def test_ukrainian_existing_pets_fixture(self):
        pets = load_pets(fx("pets.md"))
        self.assertTrue(len(pets) > 0)
        by = {p.name: p for p in pets}
        self.assertIn("mcp-book-lover", by)
        self.assertEqual(by["mcp-book-lover"].github, "https://github.com/MIt9/mcp-book-lover")
        self.assertIn("Python", by["mcp-book-lover"].stack)

    def test_english_pet_format(self):
        content = """# Pet projects

### my-tool
- **GitHub:** https://github.com/example/my-tool
- **Stack:** Python, Redis, Docker
- **Resume line:** `my-tool — Fast automation CLI tool`

### another-pet
- **GitHub:** https://github.com/example/another-pet
- **stack:** TypeScript, Node.js
- **Resume Line:** `another-pet — Web app for developers`
"""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            pets = load_pets(tmp_path)
            by = {p.name: p for p in pets}
            self.assertIn("my-tool", by)
            self.assertEqual(by["my-tool"].github, "https://github.com/example/my-tool")
            self.assertEqual(by["my-tool"].line, "my-tool — Fast automation CLI tool")
            self.assertEqual(by["my-tool"].stack, ["Python", "Redis", "Docker"])

            self.assertIn("another-pet", by)
            self.assertEqual(by["another-pet"].github, "https://github.com/example/another-pet")
            self.assertEqual(by["another-pet"].line, "another-pet — Web app for developers")
            self.assertEqual(by["another-pet"].stack, ["TypeScript", "Node.js"])
        finally:
            os.remove(tmp_path)


class MultilingualResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = make_ledger()

    def test_ukrainian_skills_heading_and_education(self):
        resume = """# Дмитро Білик

## Про мене
Досвідчений розробник.

## Технічні навички
**Frontend:** React, HTML, CSS
**Backend:** Node.js

## Освіта
КПІ, Комп'ютерні науки
"""
        # Posting asks for TypeScript (confirmed in ledger) and Python (personal in ledger, has pets)
        posting = """## Вимоги:
- TypeScript
- Python
"""
        out, rep = tailor(posting, resume, self.L)
        # Skills section recognized and updated
        self.assertIn("## Технічні навички", out)
        self.assertIn("TypeScript", out)
        # Python is personal -> personal projects row added
        self.assertIn("**Personal projects:** Python (personal projects, PyPI packages)", out)
        # Pet section inserted before '## Освіта'
        edu_idx = out.find("## Освіта")
        pet_idx = out.find("## Personal Projects")
        self.assertNotEqual(pet_idx, -1)
        self.assertNotEqual(edu_idx, -1)
        self.assertLess(pet_idx, edu_idx)

    def test_ukrainian_existing_personal_skills_row(self):
        variations = [
            ("**Особисті проекти:** NestJS", "**Особисті проекти:**"),
            ("**Пет-проекти:** NestJS", "**Пет-проекти:**"),
            ("**Пет-проєкти:** NestJS", "**Пет-проєкти:**"),
        ]
        for line_val, prefix in variations:
            resume = f"""# Дмитро

## Навички
**Frontend:** React
{line_val}

## Освіта
КПІ
"""
            posting = "## Requirements:\n- Redis\n"
            out, rep = tailor(posting, resume, self.L)
            self.assertIn(f"{prefix} NestJS, Redis", out, f"Failed for variation: {line_val}")
            self.assertNotIn("**Personal projects:**", out, f"Should not add English row for: {line_val}")

    def test_ukrainian_existing_personal_projects_section(self):
        resume = """# Дмитро

## Ключові навички
**Frontend:** React
**Особисті проекти:** NestJS

## Особисті проекти
- **[old-pet](https://github.com/example/old-pet)** — Старий пет проект (Stack: C++)

---

## Освіта
КПІ
"""
        posting = "## Requirements:\n- Python\n"
        out, rep = tailor(posting, resume, self.L)
        # Should not create duplicate '## Personal Projects'
        self.assertNotIn("## Personal Projects", out)
        self.assertIn("## Особисті проекти", out)
        # Python pets should be added to existing '## Особисті проекти' section
        self.assertIn("mcp-book-lover", out)

    def test_ukrainian_open_source_placement(self):
        resume = """# Дмитро

## Технічні навички
**Frontend:** React
**Backend:** Node.js

## Відкритий код
- **[some-lib](https://github.com/example/some-lib)** — Бібліотека

## Інше
Сертифікати
"""
        posting = "## Requirements:\n- Python\n"
        out, rep = tailor(posting, resume, self.L)
        os_idx = out.find("## Відкритий код")
        pet_idx = out.find("## Personal Projects")
        other_idx = out.find("## Інше")
        self.assertNotEqual(os_idx, -1)
        self.assertNotEqual(pet_idx, -1)
        self.assertNotEqual(other_idx, -1)
        # Pet projects should be placed after '## Відкритий код' and before '## Інше'
        self.assertLess(os_idx, pet_idx)
        self.assertLess(pet_idx, other_idx)
