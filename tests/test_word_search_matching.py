import unittest

from src.methods import get_word_states


class MyTestCase(unittest.TestCase):
    def test_noun(self):
        self.assertIn("печенюха", get_word_states("печенюху"))

    def test_verb(self):
        self.assertIn("прогуляйся", get_word_states("прогуляюсь"))

    def test_adjective(self):
        self.assertIn("вымыты", get_word_states("вымытый"))

    def test_adverb(self):
        self.assertIn("горячо", get_word_states("горячо")) #

    def test_gerund(self):
        self.assertIn("высвободив", get_word_states("высвободивший"))

    def test_pronoun(self):
        self.assertIn("наш", get_word_states("нашего"))


if __name__ == '__main__':
    unittest.main()
