import copy
from pathlib import Path
import tempfile
import unittest
from app import csv_safe,main, money, rule_extract, validate

TEXT='DOCUMENTO: TEST-1\nFORNECEDOR: Exemplo\nTOTAL: R$ 1.490,50\nMOEDA: BRL\nVENCIMENTO: 2026-11-20\n'

class PipelineTests(unittest.TestCase):
    def test_normalizes_brazilian_money(self): self.assertEqual(money('R$ 1.490,50'),'1490.50')
    def test_rejects_ambiguous_or_negative_amount(self):
        for value in ('1490.50','-1,00','NaN','1,234','0,00'):
            with self.subTest(value=value),self.assertRaises(ValueError): money(value)
    def test_valid_source(self):
        result,errors=validate(rule_extract(TEXT),TEXT)
        self.assertEqual(errors,[]); self.assertEqual(result['total'],'1490.50')
    def test_blank_supplier_does_not_capture_next_line(self):
        result=rule_extract(TEXT.replace('FORNECEDOR: Exemplo','FORNECEDOR: '))
        self.assertIsNone(result['supplier']['value'])
    def test_csv_formula_text_is_escaped(self):
        self.assertEqual(csv_safe('=1+1'),"'=1+1")
        self.assertEqual(csv_safe('1490.50'),'1490.50')
    def test_fabricated_evidence_is_not_accepted(self):
        data=rule_extract(TEXT);data['supplier']['quote']='não existe na fonte'
        self.assertTrue(any('evidência' in e for e in validate(data,TEXT)[1]))
    def test_value_must_be_inside_quote(self):
        data=rule_extract(TEXT);data['supplier']['value']='Outra empresa'
        self.assertTrue(validate(data,TEXT)[1])
    def test_impossible_date(self):
        text=TEXT.replace('2026-11-20','2026-02-30')
        self.assertTrue(any('data real' in e for e in validate(rule_extract(text),text)[1]))
    def test_missing_field_goes_to_review_and_not_csv(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root=Path(temp);(root/'in.txt').write_text(TEXT.replace('VENCIMENTO: 2026-11-20\n',''),encoding='utf-8')
            self.assertEqual(main([str(root/'in.txt'),'--output',str(root/'out')]),1)
            self.assertEqual(len((root/'out/validated.csv').read_text().splitlines()),1)
    def test_accepts_one_file_and_exports(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root=Path(temp);(root/'in.txt').write_text(TEXT,encoding='utf-8')
            self.assertEqual(main([str(root/'in.txt'),'--output',str(root/'out')]),0)
            self.assertIn('1490.50',(root/'out/validated.csv').read_text())

if __name__=='__main__':unittest.main()
