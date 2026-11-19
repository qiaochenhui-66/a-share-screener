#!/usr/bin/env python3
"""Snapshot A-share screener for GitHub Actions + Pages.

No browser-side live data access. A failed fetch never overwrites the last success.
"""
import argparse
import json
import logging
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "docs" / "data"
LOG = logging.getLogger("screener")


def is_main_board(code):
    """Current Shanghai/Shenzhen A-share main-board code families."""
    code = str(code).strip().zfill(6)
    return (len(code) == 6 and code.isdigit()
            and code.startswith(("600", "601", "603", "605", "000", "001", "002", "003")))


def numeric(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        num = float(str(value).replace(",", "").replace("%", "").strip())
        return num if math.isfinite(num) else None
    except (TypeError, ValueError):
        return None


def normalize_and_filter(rows):
    candidates = []
    valid_records = 0
    for row in rows:
        code = str(row.get("代码", "")).strip()
        name = str(row.get("名称", "")).strip()
        change = numeric(row.get("涨跌幅"))
        turnover = numeric(row.get("换手率"))
        ratio = numeric(row.get("量比"))
        price = numeric(row.get("最新价"))
        if code and name and change is not None:
            valid_records += 1
        if not is_main_board(code) or not name or "ST" in name.upper():
            continue
        if None in (change, turnover, ratio, price):
            continue
        if 3 <= change <= 5 and 5 <= turnover <= 10 and ratio > 1.0:
            candidates.append({
                "code": code, "name": name, "price": round(price, 3),
                "change": round(change, 3), "turnover": round(turnover, 3),
                "ratio": round(ratio, 3),
            })
    candidates.sort(key=lambda s: (-s["ratio"], -s["change"], s["code"]))
    return candidates, valid_records


def is_trading_day(day):
    """SSE/XSHG exchange calendar; fail closed if calendar unavailable/out of range."""
    import exchange_calendars as xcals
    import pandas as pd
    cal = xcals.get_calendar("XSHG")
    return bool(cal.is_session(pd.Timestamp(day.isoformat())))


def get_spot(max_attempts=3):
    import akshare as ak
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            frame = ak.stock_zh_a_spot_em()
            required = {"代码", "名称", "最新价", "涨跌幅", "换手率", "量比"}
            missing = required - set(frame.columns)
            if missing:
                raise ValueError("行情缺少字段: " + ",".join(sorted(missing)))
            if len(frame) < 1000:
                raise ValueError(f"行情数量异常（{len(frame)}条），拒绝保存不完整快照")
            return frame.to_dict(orient="records"), len(frame)
        except Exception as exc:
            last_error = exc
            LOG.warning("行情请求 %s/%s 失败: %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                time.sleep(attempt * 7)
    raise RuntimeError("行情接口连续失败；最后错误: " + str(last_error))


def write_json_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="仅手动测试：休市日也采集，页面标记测试快照")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    now = datetime.now(TZ)
    try:
        trading = is_trading_day(now.date())
    except Exception as exc:
        LOG.error("无法确定交易日，拒绝生成新数据: %s", exc)
        return 1
    if not trading and not args.force:
        LOG.info("%s 非上交所交易日，跳过（不覆盖历史）", now.date())
        return 0
    try:
        rows, total = get_spot()
        matches, valid = normalize_and_filter(rows)
        if valid < 1000:
            raise ValueError(f"有效行情不足：{valid}，停止写入以免误报")
        # Do not present a weekend/holiday forced run as real trading-day data.
        payload = {
            "schema_version": 1,
            "date": now.date().isoformat(),
            "retrieved_at": now.isoformat(timespec="seconds"),
            "timezone": "Asia/Shanghai",
            "source": "AKShare stock_zh_a_spot_em（东方财富公开行情）",
            "test_run": not trading,
            "count": len(matches),
            "total_market_rows": total,
            "filters": {"change_min": 3, "change_max": 5,
                        "turnover_min": 5, "turnover_max": 10,
                        "ratio_gt": 1, "exclude": ["创业板", "科创板", "ST/*ST"]},
            "stocks": matches,
            "disclaimer": "行情可能延迟；仅为当次采集快照，不代表实时行情或投资建议。",
        }
        write_json_atomic(DATA_DIR / "latest.json", payload)
        write_json_atomic(DATA_DIR / "history" / f"{now.date().isoformat()}.json", payload)
        LOG.info("完成 %s: %s / %s 条符合", payload["retrieved_at"], len(matches), total)
        return 0
    except Exception as exc:
        LOG.exception("采集失败，保留原有最新成功结果: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
