import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.nonces import NonceStore
from app.core.paths import is_within, safe_resolve
from app.core.safety import SecureDeletionManager


class TestNonceStore(unittest.TestCase):
    def test_issue_and_consume_success(self):
        store = NonceStore()
        paths = ["/tmp/a.txt", "/tmp/b.txt"]
        nonce = store.issue(paths)
        self.assertTrue(store.consume(nonce, paths))

    def test_consume_is_single_use(self):
        store = NonceStore()
        paths = ["/tmp/a.txt"]
        nonce = store.issue(paths)
        self.assertTrue(store.consume(nonce, paths))
        # Second use must fail.
        self.assertFalse(store.consume(nonce, paths))

    def test_expired_nonce_rejected(self):
        t = [1000.0]
        store = NonceStore(ttl_seconds=60, clock=lambda: t[0])
        nonce = store.issue(["/tmp/a.txt"])
        t[0] += 61
        self.assertFalse(store.consume(nonce, ["/tmp/a.txt"]))

    def test_mismatched_paths_rejected(self):
        store = NonceStore()
        nonce = store.issue(["/tmp/a.txt", "/tmp/b.txt"])
        # Different set — must not match.
        self.assertFalse(store.consume(nonce, ["/tmp/a.txt"]))
        # Different element — must not match. (Nonce is now also consumed
        # by the prior call, but we issue a fresh one to isolate the case.)
        nonce2 = store.issue(["/tmp/a.txt"])
        self.assertFalse(store.consume(nonce2, ["/tmp/c.txt"]))

    def test_path_order_does_not_matter(self):
        store = NonceStore()
        nonce = store.issue(["/tmp/a.txt", "/tmp/b.txt"])
        self.assertTrue(store.consume(nonce, ["/tmp/b.txt", "/tmp/a.txt"]))

    def test_invalid_nonce_shape_rejected(self):
        store = NonceStore()
        self.assertFalse(store.consume("", ["/tmp/a.txt"]))
        self.assertFalse(store.consume(None, ["/tmp/a.txt"]))  # type: ignore[arg-type]
        self.assertFalse(store.consume("not-a-real-nonce", ["/tmp/a.txt"]))


class TestPathHelpers(unittest.TestCase):
    def test_is_within_true_for_child(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            child = root / "sub" / "f.txt"
            self.assertTrue(is_within(child, root))

    def test_is_within_false_for_sibling(self):
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            self.assertFalse(is_within(Path(td2) / "f.txt", Path(td1)))

    def test_safe_resolve_accepts_child(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            child = root / "f.txt"
            child.write_text("hi")
            resolved = safe_resolve(str(child), root)
            self.assertEqual(resolved, child.resolve())

    def test_safe_resolve_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            escaping = str(root / ".." / ".." / "etc" / "passwd")
            with self.assertRaisesRegex(ValueError, "outside allowed root"):
                safe_resolve(escaping, root)

    def test_safe_resolve_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td_root, tempfile.TemporaryDirectory() as td_outside:
            root = Path(td_root)
            outside_file = Path(td_outside) / "secret.txt"
            outside_file.write_text("nope")
            link = root / "link.txt"
            try:
                os.symlink(outside_file, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks not supported on this platform")
            with self.assertRaisesRegex(ValueError, "outside allowed root"):
                safe_resolve(str(link), root)

    def test_safe_resolve_rejects_empty(self):
        with self.assertRaises(ValueError):
            safe_resolve("", Path("/tmp"))


class TestSecureDeletionManager(unittest.TestCase):
    def _setup(self):
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        f1 = root / "file1.txt"
        f2 = root / "file2.txt"
        f1.write_text("one")
        f2.write_text("two")
        return root, [str(f1), str(f2)]

    @patch("app.core.safety.send2trash.send2trash")
    def test_delete_files_success_with_valid_nonce(self, mock_send2trash):
        root, paths = self._setup()
        store = NonceStore()
        manager = SecureDeletionManager(allowed_root=root)
        nonce = store.issue(paths)

        result = manager.delete_files(paths, nonce, store)

        self.assertEqual(result["deleted_count"], 2)
        self.assertEqual(mock_send2trash.call_count, 2)

    def test_delete_files_rejects_invalid_nonce(self):
        root, paths = self._setup()
        store = NonceStore()
        manager = SecureDeletionManager(allowed_root=root)
        with self.assertRaisesRegex(ValueError, "deletion nonce"):
            manager.delete_files(paths, "not-a-real-nonce", store)

    def test_delete_files_rejects_expired_nonce(self):
        root, paths = self._setup()
        t = [1000.0]
        store = NonceStore(ttl_seconds=60, clock=lambda: t[0])
        manager = SecureDeletionManager(allowed_root=root)
        nonce = store.issue(paths)
        t[0] += 61
        with self.assertRaisesRegex(ValueError, "deletion nonce"):
            manager.delete_files(paths, nonce, store)

    @patch("app.core.safety.send2trash.send2trash")
    def test_delete_files_rejects_reused_nonce(self, mock_send2trash):
        root, paths = self._setup()
        store = NonceStore()
        manager = SecureDeletionManager(allowed_root=root)
        nonce = store.issue(paths)
        manager.delete_files(paths, nonce, store)
        with self.assertRaisesRegex(ValueError, "deletion nonce"):
            manager.delete_files(paths, nonce, store)

    def test_delete_files_rejects_mismatched_paths(self):
        root, paths = self._setup()
        store = NonceStore()
        manager = SecureDeletionManager(allowed_root=root)
        nonce = store.issue(paths)
        with self.assertRaisesRegex(ValueError, "deletion nonce"):
            manager.delete_files([paths[0]], nonce, store)

    @patch("app.core.safety.send2trash.send2trash")
    def test_delete_files_rejects_path_outside_root(self, mock_send2trash):
        root, _ = self._setup()
        with tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside) / "x.txt"
            outside_file.write_text("nope")
            outside_path = str(outside_file)
            store = NonceStore()
            manager = SecureDeletionManager(allowed_root=root)
            nonce = store.issue([outside_path])
            with self.assertRaisesRegex(ValueError, "Refusing to delete"):
                manager.delete_files([outside_path], nonce, store)
            mock_send2trash.assert_not_called()

    @patch("app.core.safety.send2trash.send2trash")
    @patch("app.core.safety.os.remove")
    @patch("app.core.safety.os.unlink")
    @patch("shutil.rmtree")
    def test_delete_files_never_calls_forbidden_functions(
        self, mock_rmtree, mock_unlink, mock_remove, mock_send2trash
    ):
        root, paths = self._setup()
        store = NonceStore()
        manager = SecureDeletionManager(allowed_root=root)
        nonce = store.issue(paths)
        manager.delete_files(paths, nonce, store)

        mock_remove.assert_not_called()
        mock_unlink.assert_not_called()
        mock_rmtree.assert_not_called()
        self.assertEqual(mock_send2trash.call_count, 2)


if __name__ == "__main__":
    unittest.main()
