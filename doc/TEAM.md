# Nhóm thực hiện K4 Track 3B

Tên nhóm:

Repo chung:

Trưởng nhóm/người nộp: **Hoàng Công Minh — 2A202602774**.

Ngày lab/deadline áp dụng:

Commit dùng để chấm: d860aa42becc24f69c78af6170512234a08fadab (Phase C implementation/artifacts; commit TEAM phía sau chỉ ghi SHA này). Repo chưa push.

Thông tin nhóm và các thành viên khác để trống theo yêu cầu. Danh sách này chưa
phải danh sách đầy đủ của nhóm.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Hoàng Công Minh | 2A202602774 | Nhóm trưởng; Phase C và phần guardrails của blueprint | src/phase_c_guard.py; tests/test_phase_c.py; doc/reports/blueprint.md |

Người tích hợp/chạy batch/nộp link:

Các thành viên và phân công A/B:

## Môi trường và chuẩn bị trước lớp

Windows, Python 3.11.15 trong .venv, Microsoft C++ Build Tools 2026, Windows SDK;
Annoy 1.17.3 build thành công. pip check không báo dependencies hỏng.
spaCy 3.7.5 dùng en_core_web_lg 3.7.1; PyArrow 20 tương thích NumPy 1.26.4.

Presidio thật đã detect/redact email và CCCD thử nghiệm. NeMo 0.10.0 đã khởi tạo
với gemini-3.5-flash-lite qua endpoint Gemini tương thích OpenAI.
Key giữ trong .env, không đưa vào báo cáo/source.

Docker CLI/daemon WSL hoạt động, tải Qdrant v1.9.7 trước đó bị timeout TLS.
Phase C dùng fixtures, không cần Qdrant. m1–m5/answers_50q.json có trong repo;
chưa có báo cáo A/B để đối chiếu. Không quy phần m1–m5/A/B cho người phụ trách C.

## INDIVIDUAL

### HoangCongMinh-2A202602774

- Phần được giao: Phase C Tasks 9a–12 và phần guardrails của blueprint.
- Triển khai có Codex hỗ trợ: năm hàm PII/input/output/suite/latency; activated
  rails quyết định block; suite kiểm tra Presidio trước NeMo; latency có hai
  warm-up, ít nhất 20 timed samples và một event loop.
- Khắc phục: dùng chat completions cho Gemini với NeMo; giới hạn gate PII vào
  CCCD/CMND, điện thoại và email, tránh English NER nhận nhầm tiếng Việt.
- Bằng chứng: source, ba regression tests false positives, blueprint và
  artifacts/guard_results.json chứa batch live.
- Kiểm tra offline trước lần điều chỉnh quota cuối: python -m pytest
  tests/test_phase_c.py tests/test_support.py tests/test_report_contracts.py
  -q --basetemp=.venv-tools/pytest-final đạt **76 passed**. Đây là mock/offline
  tests; lượt chạy sau đó kiểm tra riêng report C và source hashes bằng checker.
- Batch Gemini được người dùng xác nhận: chạy live bằng gemini-3.5-flash-lite,
  timestamp 2026-10-12T13:06:11.136556+00:00; attacks 20/20, clean 8/8,
  outputs 4/4; schema/source hashes/quality C đạt checker.
- Latency sau tối ưu: 20 timed samples, 2 warm-up mỗi tầng; input guard P95
  2429.126 ms, vượt budget 500 ms. Quota Gemini vẫn giãn 4.5 giây giữa requests,
  nhưng admission wait được tách khỏi timer; lượt trước gồm chờ có P95 4811.519 ms.
- Commit Phase C: d860aa42becc24f69c78af6170512234a08fadab; dùng author Git
  Hoang Cong Minh. Commit local, chưa push lên repo nhóm.
- Lượt đầu giữ ở guard_results_initial.json để đối chiếu chặn sai clean;
  tăng self-check từ mặc định 3 token lên 256 để sửa chặn sai clean; sau đó
  giảm xuống 16 token cho batch tối ưu và kiểm tra lại đủ 20/8/4 cases.
- Nội dung cần tự giải thích/kiểm chứng: clean controls phát hiện always-block;
  expected chỉ dùng đối chiếu; input sequential khác RAG/output/full request;
  không suy block từ chữ “xin lỗi/không thể”.
- Giới hạn: PERSON/LOCATION từ NER tiếng Anh không dùng làm gate tiếng Việt;
  yêu cầu truy xuất dữ liệu nhân viên do NeMo kiểm tra; A/B cần nhóm tích hợp.
- AI hỗ trợ: Codex đọc starter, hỗ trợ môi trường, code, tests và báo cáo.
  Hoàng Công Minh cần tự rà soát/giải thích phần khai. Không khai mock là
  thực nghiệm thật hoặc phần có AI hỗ trợ là tự thực hiện hoàn toàn.

## Cập nhật sau khi nộp

Chưa ghi nhận thông tin nộp bài hoặc cập nhật sau khi nộp.
