import unittest
from src.aixml.tree import TreeNode

class TestTreeNode(unittest.TestCase):
    def test_add_child(self):
        root = TreeNode('root','Root Content',{'id':'1'})
        child1 = TreeNode('child1','Child 1 Content',{'id':'1.1'})
        child2 = TreeNode('child2','Child 2 Content',{'id':'1.2'})

        root.add_child(child1)
        root.add_child(child2)

        self.assertEqual(len(root.children), 2)
        self.assertEqual(root.children[0].tag, 'child1')
        self.assertEqual(root.children[1].tag, 'child2')