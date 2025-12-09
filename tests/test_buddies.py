import tempfile
import unittest
from pathlib import Path

from aibuddies.buddies import Buddy, BuddyStore
from aibuddies.config import Paths


class BuddyStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.paths = Paths(home=Path(self.tmpdir.name))
        self.store = BuddyStore(self.paths)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_create_list_update(self) -> None:
        buddy = Buddy(name="Tester", persona_prompt="You help test things.", context_sources=["clipboard"])
        self.store.create(buddy)

        listed = self.store.list()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].name, "Tester")
        self.assertEqual(listed[0].context_sources, ["clipboard"])

        self.store.update("Tester", {"context_sources": ["window", "docs"]})
        updated = self.store.get("Tester")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.context_sources, ["window", "docs"])

    def test_delete(self) -> None:
        buddy = Buddy(name="DeleteMe", persona_prompt="Remove me.")
        self.store.create(buddy)
        self.assertIsNotNone(self.store.get("DeleteMe"))
        deleted = self.store.delete("DeleteMe")
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get("DeleteMe"))


if __name__ == "__main__":
    unittest.main()
