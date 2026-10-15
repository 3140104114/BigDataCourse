"""复现OCW搜索页的POST搜索请求。每次只请求一批数据。"""
import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin
import requests

ROOT = Path(__file__).resolve().parent
API_URL = "https://open.mit.edu/api/v0/search/"
PAYLOAD_FILE = ROOT / "payload.json"

def main():
    # 实际授课时用Network中复制的原始Request Payload替换此文件。
    payload = json.loads(PAYLOAD_FILE.read_text(encoding="utf-8"))
    out = ROOT / "output" / datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
    out.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    metadata = {"page_url": "https://ocw.mit.edu/search/?q=python",
                "request_url": API_URL, "method": "POST", "collected_at": now,
                "status": "incomplete", "scope": "one search batch"}
    (out / "request_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        response = requests.post(API_URL, json=payload,
                                 headers={"Accept": "application/json"}, timeout=30)
        metadata.update(http_status=response.status_code,
                        content_type=response.headers.get("Content-Type", ""))
        (out / "response.json").write_bytes(response.content)
        response.raise_for_status()
        data = response.json()
        hits = data["hits"]["hits"]
        if not isinstance(hits, list):
            raise ValueError("hits.hits不是列表，请重新检查真实响应结构")
        rows = []
        for hit in hits:
            item = hit["_source"]
            runs = item.get("runs") or []
            slug = runs[0].get("slug", "") if runs else ""
            rows.append({
                "resource_id": item.get("id", ""),
                "title": item.get("title", ""),
                "course_number": item.get("coursenum", ""),
                "provider": "; ".join(item.get("offered_by") or []),
                "departments": "; ".join(item.get("department_name") or []),
                "topics": "; ".join(item.get("topics") or []),
                "description": item.get("short_description") or "",
                "course_url": urljoin("https://ocw.mit.edu/", slug) if slug else "",
                "source_url": API_URL, "collected_at": now,
            })
        fields = ["resource_id", "title", "course_number", "provider", "departments",
                  "topics", "description", "course_url", "source_url", "collected_at"]
        with (out / "courses.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        total = data["hits"]["total"]
        total = total.get("value") if isinstance(total, dict) else total
        metadata.update(total_matches=total, returned_count=len(rows),
                        status="batch_saved" if rows else "empty_batch")
        print("HTTP状态：", response.status_code)
        print("匹配总数：", total, "本批保存：", len(rows))
        for row in rows[:3]:
            print(row["title"])
    except (requests.RequestException, ValueError, KeyError, TypeError, OSError) as exc:
        metadata["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (out / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("结果目录：", out)

if __name__ == "__main__":
    main()






