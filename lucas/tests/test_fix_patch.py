import unittest
from lucas.fix_patch import fix_patch

class TestFixPatch(unittest.TestCase):
    def test_empty_patch(self):
        patch_content = ""
        expected_output = ""
        self.assertEqual(fix_patch(patch_content), expected_output)

    def test_no_hunks(self):
        patch_content = "Hello world!\n"
        expected_output = "Hello world!\n"
        self.assertEqual(fix_patch(patch_content), expected_output)

    def test_single_hunk(self):
        patch_content = "@@ -1,2 +1,2 @@\n- line 1\n  line 2\n+ line 3\n"
        expected_output = "@@ -1,2 +1,2 @@\n- line 1\n  line 2\n+ line 3\n"
        self.assertEqual(fix_patch(patch_content), expected_output)

    def test_single_hunk_fix(self):
        patch_content = "@@ -1,2 +1,1 @@\n- line 1\n  line 2\n+ line 3\n"
        expected_output = "@@ -1,2 +1,2 @@\n- line 1\n  line 2\n+ line 3\n"
        self.assertEqual(fix_patch(patch_content), expected_output)


if __name__ == '__main__':
    unittest.main()

