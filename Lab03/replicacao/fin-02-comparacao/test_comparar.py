import tempfile
import unittest
from pathlib import Path

from comparar import carregar, diferenca, numero


class ComparacaoTest(unittest.TestCase):
    def test_base_publicada_e_sinal(self):
        self.assertEqual(diferenca(0.2, 0.3)[1], 'calculada')
        self.assertAlmostEqual(diferenca(0.2, 0.3)[0], 50)
        self.assertAlmostEqual(diferenca(0.2, 0.1)[0], -50)

    def test_zero_nao_vira_erro_zero(self):
        self.assertEqual(diferenca(0, 0), (None, 'base_zero'))
        self.assertEqual(diferenca(0, 0.3), (None, 'base_zero'))

    def test_ausencia_nao_vira_zero(self):
        self.assertIsNone(numero(''))
        self.assertEqual(numero('0'), 0)
        self.assertEqual(diferenca(None, 0), (None, 'ausente'))
        self.assertEqual(diferenca(1, None), (None, 'ausente'))

    def test_rejeita_nao_finitos(self):
        for valor in ('nan', 'inf', '-inf'):
            with self.assertRaises(ValueError):
                numero(valor)

    def test_identidade_e_duplicatas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'dados.csv'
            caminho.write_text('repo,x\nOwner/Repo,1\n', encoding='utf-8-sig')
            self.assertIn('owner/repo', carregar(caminho))
            caminho.write_text('repo,x\nOwner/Repo,1\nowner/repo,2\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                carregar(caminho)


if __name__ == '__main__':
    unittest.main()
