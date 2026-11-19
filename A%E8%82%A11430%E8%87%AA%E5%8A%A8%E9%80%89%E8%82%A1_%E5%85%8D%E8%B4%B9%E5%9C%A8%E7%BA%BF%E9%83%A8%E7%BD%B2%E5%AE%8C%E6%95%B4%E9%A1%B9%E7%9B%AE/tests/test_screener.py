import unittest
from screener import is_main_board, normalize_and_filter, numeric


class FilterTests(unittest.TestCase):
    def test_main_board_only(self):
        for c in ('600000','601001','603999','605199','000001','001234','002001','003000'):
            self.assertTrue(is_main_board(c), c)
        for c in ('300001','301001','688001','689001','8xxxxx','430001','900001','200001'):
            self.assertFalse(is_main_board(c), c)

    def test_bounds_and_exclusions(self):
        def row(code, name, chg, turn, ratio):
            return {'代码':code,'名称':name,'最新价':10,'涨跌幅':chg,'换手率':turn,'量比':ratio}
        items = [row('600000','浦发银行',3,5,1.001),row('000001','平安银行',5,10,2.0),
                 row('300123','创业板',4,7,3),row('688123','科创板',4,7,3),
                 row('600001','ST测试',4,7,3),row('603001','*st测试',4,7,3),
                 row('002001','主板',4,7,1),row('002002','主板',2.99,7,2),
                 row('002003','主板',4,10.01,2),row('002004','主板',4,7,None)]
        result, valid = normalize_and_filter(items)
        self.assertEqual([x['code'] for x in result], ['000001','600000'])
        self.assertGreater(valid, 0)

    def test_numeric(self):
        self.assertIsNone(numeric('—'))
        self.assertIsNone(numeric(float('nan')))
        self.assertEqual(numeric('3.5%'),3.5)


if __name__ == '__main__':
    unittest.main()
