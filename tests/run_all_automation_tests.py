# -*- coding: utf-8 -*-
"""
Bộ điều phối chạy tất cả các bài kiểm thử tự động (Automation Tests)
Dự án Quản lý Văn bản và Điều hành Công việc — Vietasia Travel (MIS3047)
"""

import os
import sys
import subprocess
import time

TEST_SCRIPTS = [
    ("Kiểm tra toàn bộ View & Template (Smoke Test)", "tests/test_views.py"),
    ("Kiểm thử Tự động Giai đoạn 2 (AUTO-03 Biểu mẫu & AUTO-06 Xử lý ngoại lệ)", "tests/test_phase2_automation.py"),
    ("Kiểm thử Tự động Giai đoạn 3 (AUTO-01 OCR, AUTO-07 Gợi ý AI, AUTO-08 Tóm tắt)", "tests/test_phase3_automation.py"),
    ("Kiểm thử 4 Tiêu chí Thẩm định & Luồng Trình duyệt / Phê duyệt", "tests/test_checklist_criteria.py"),
    ("Kiểm tra Phân quyền & Loại trừ Tài khoản Admin khỏi Người xử lý", "tests/verify_admin_exclusion.py"),
]

def main():
    print("=" * 75)
    print("   HỆ THỐNG KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN (AUTOMATION TEST SUITE)")
    print("   DỰ ÁN CHUYỂN ĐỔI SỐ QUẢN LÝ VĂN BẢN — VIETASIA TRAVEL")
    print("=" * 75)
    print(f"Tổng số kịch bản kiểm thử: {len(TEST_SCRIPTS)}\n")

    results = []
    total_start = time.time()

    for idx, (title, script_path) in enumerate(TEST_SCRIPTS, 1):
        print(f"\n[{idx}/{len(TEST_SCRIPTS)}] Đang chạy: {title} ({script_path})...")
        print("-" * 75)
        start_t = time.time()

        proc = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8', errors='replace')
        elapsed = time.time() - start_t

        if proc.returncode == 0:
            print(f"✅ KẾT QUẢ: THÀNH CÔNG (Thời gian: {elapsed:.2f}s)")
            results.append((title, "PASSED", elapsed))
        else:
            print(f"❌ KẾT QUẢ: THẤT BÀI (Thời gian: {elapsed:.2f}s)")
            print("\n--- CHI TIẾT LỖI ---")
            print(proc.stderr or proc.stdout)
            results.append((title, "FAILED", elapsed))

    total_time = time.time() - total_start

    print("\n" + "=" * 75)
    print("                    TỔNG HỢP KẾT QUẢ KIỂM THỬ")
    print("=" * 75)
    passed_count = sum(1 for _, status, _ in results if status == "PASSED")
    for title, status, elapsed in results:
        status_icon = "✅ ĐẠT" if status == "PASSED" else "❌ LỖI"
        print(f" - {status_icon:8} | {elapsed:5.2f}s | {title}")

    print("-" * 75)
    print(f"Tổng kết: {passed_count}/{len(results)} kịch bản kiểm thử thành công ({passed_count/len(results)*100:.1f}%)")
    print(f"Tổng thời gian thực thi: {total_time:.2f}s")
    print("=" * 75)

    if passed_count < len(results):
        sys.exit(1)

if __name__ == '__main__':
    main()

