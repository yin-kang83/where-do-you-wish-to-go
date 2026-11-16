# -*- coding: utf-8 -*-
"""自含复核：只用标准库，逐层判断五个错凭证是否被抓住。

与产品仓的差别：这里不实现准则，只实现"这层该发现什么"的最小判据。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
D = HERE / "错凭证"


def load(name):
    return json.loads((D / name).read_text(encoding="utf-8"))


def c1_data():
    d = load("01-数据层-借贷不平.json")
    debit = round(sum(float(x["金额"]) for x in d["凭证"] if "借" in x), 2)
    credit = round(sum(float(x["金额"]) for x in d["凭证"] if "贷" in x), 2)
    diff = round(debit - credit, 2)
    return abs(diff) > 0.005, f"借 {debit} / 贷 {credit}，差额 {diff}"


def c2_measure():
    d = load("02-计量层-折旧算错.json")
    s = d["应采用"]
    correct = round((s["原值"] * (1 - s["残值率"])) / s["年限"] / 12, 2)
    voucher = next(float(x["金额"]) for x in d["凭证"] if "借" in x)
    return abs(voucher - correct) > 0.005, f"应为 {correct}，凭证 {voucher}"


def c3_standard():
    d = load("03-准则层-反向冲红.json")
    subs = {x.get("借") or x.get("贷") for x in d["错误冲红凭证"]}
    # 最小判据：损益类科目出现在贷方（原凭证在借方）即为反向分录
    pl = {"管理费用—办公费"}
    on_credit = any(x.get("贷") in pl for x in d["错误冲红凭证"])
    return on_credit, f"损益科目 {sorted(subs & pl)} 出现在贷方 → 反向分录"


def c4_reconcile():
    d = load("04-勾稽层-三流断.json")
    n_inv, n_god, n_pay = len(d["发票"]), len(d["货物"]), len(d["资金"])
    return min(n_inv, n_god, n_pay) == 0, f"票 {n_inv} / 货 {n_god} / 款 {n_pay}，有一流为空"


def c5_qualitative():
    d = load("05-定性层-未定性.json")
    need = {x["事项编号"] for x in d["应定性事项"]}
    have = {x["事项编号"] for x in d["已有定性记录"]}
    lack = sorted(need - have)
    return bool(lack), f"未定性 {len(lack)} 项：{'、'.join(lack)}"


CASES = [("① 数据层", c1_data), ("② 计量层", c2_measure),
         ("③ 准则层", c3_standard), ("④ 勾稽层", c4_reconcile),
         ("⑤ 定性层", c5_qualitative)]


def main():
    ok = 0
    for layer, fn in CASES:
        caught, evidence = fn()
        print(f"{layer}  {'✓ 抓住' if caught else '✗ 没抓住'}  {evidence}")
        ok += 1 if caught else 0
    print(f"\n合计：{ok}/{len(CASES)}")
    return 0 if ok == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
