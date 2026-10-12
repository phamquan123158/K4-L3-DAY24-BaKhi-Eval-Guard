# Nhóm thực hiện K4 Track 3B

Tên nhóm: BaKhi

Repo chung: https://github.com/phamquan123158/K4-L3-DAY24-BaKhi-Eval-Guard

Trưởng nhóm/người nộp: Phạm Quân - 2A202602890

Ngày lab/deadline áp dụng:

Commit dùng để chấm: d860aa42becc24f69c78af6170512234a08fadab (Phase C implementation/artifacts; commit TEAM phía sau chỉ ghi SHA này).

Thông tin nhóm và các thành viên khác để trống theo yêu cầu. Danh sách này chưa
phải danh sách đầy đủ của nhóm.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Hoàng Công Minh | 2A202602774 | Thành viên; phụ trách Phase C và phần guardrails của blueprint | src/phase_c_guard.py; tests/test_phase_c.py; doc/reports/blueprint.md |
| 2 | Phạm Quân | 2A202602890 | Thành viên; phụ trách Phase A (RAGAS) và Phase B (LLM Judge) | src/m4_eval.py; artifacts/ragas_50q.json; artifacts/judge_results.json; doc/reports/failure_clusters.md; doc/reports/bias_report.md |

Người tích hợp/chạy batch/nộp link:

Phân công A/B: Phạm Quân - 2A202602890.

## Môi trường và chuẩn bị trước lớp

Windows, Python 3.11.15 trong .venv, Microsoft C++ Build Tools 2026, Windows SDK;
Annoy 1.17.3 build thành công. pip check không báo dependencies hỏng.
spaCy 3.7.5 dùng en_core_web_lg 3.7.1; PyArrow 20 tương thích NumPy 1.26.4.

Presidio thật đã detect/redact email và CCCD thử nghiệm. NeMo 0.10.0 đã khởi tạo
với gemini-3.5-flash-lite qua endpoint Gemini tương thích OpenAI.
Key giữ trong .env, không đưa vào báo cáo/source.

Docker CLI/daemon WSL hoạt động, tải Qdrant v1.9.7 trước đó bị timeout TLS.
Phase C dùng fixtures, không cần Qdrant. Không quy phần m1–m5/A/B cho người
phụ trách C.

## Tiến độ Phase A và Phase B

### Phase A — RAGAS

- Đã chạy live 50 câu, đủ 20 factual / 20 multi_hop / 10 adversarial và 4
  metric RAGAS mỗi câu; evaluator dùng `gemini-3.5-flash-lite` cùng
  `gemini-embedding-001`. Do giới hạn Gemini không nhận nhiều candidates,
  `answer_relevancy` dùng `strictness=1` (khác mặc định 3).
- Artifact [artifacts/ragas_50q.json](../artifacts/ragas_50q.json) có
  provenance và SHA-256 input; đã qua schema, source-hash và Phase A checks.
- Lưu ý: cả 50 answer đầu vào có `generation_mode=extractive_fallback`, không
  có generation model. Đây là đánh giá RAGAS live trên answer/context/reference
  đã lưu, không phải đánh giá end-to-end answer do LLM sinh.
- Báo cáo lỗi, điểm theo distribution, bottom 10 và matrix:
  [doc/reports/failure_clusters.md](reports/failure_clusters.md).
- Báo cáo Phase A ghi người phụ trách là Phạm Quân - 2A202602890.

### Phase B — LLM Judge

- Đã chạy live judge với `gemini-3.1-flash-lite`; artifact
  [artifacts/judge_results.json](../artifacts/judge_results.json) ghi kết quả
  5 cặp A/B qua hai lượt và calibration 10 nhãn.
- Kết quả được ghi nhận: position inconsistency 2/5; verbosity win rate 0/3
  trên các cặp decisive; calibration khớp human 10/10, Cohen's κ = 1.0.
  Các kết quả này chỉ áp dụng trên mẫu đã chạy, không khẳng định judge tổng
  quát luôn chính xác.
- Báo cáo phân tích:
  [doc/reports/bias_report.md](reports/bias_report.md).
- Người được nhóm phân công phụ trách Phase B: Phạm Quân - 2A202602890.

## Reports

| Phase | Báo cáo | Artifact |
|---|---|---|
| A — RAGAS và failure clusters | [failure_clusters.md](reports/failure_clusters.md) | [ragas_50q.json](../artifacts/ragas_50q.json) |
| B — LLM Judge và bias/calibration | [bias_report.md](reports/bias_report.md) | [judge_results.json](../artifacts/judge_results.json) |

## INDIVIDUAL

### PhamQuan-2A202602890

- Vai trò: thành viên; được nhóm phân công phụ trách Phase A và Phase B.
- Phase A: cấu hình evaluator RAGAS với Gemini chat model và Gemini embeddings,
  chạy batch live 50 câu, kiểm tra artifact/provenance, phân tích bottom 10,
  worst-metric matrix và cập nhật failure-cluster report.
- Phase B: chạy live LLM Judge cho 5 cặp A/B qua hai lượt và calibration 10
  nhãn; kiểm tra kết quả, position inconsistency, verbosity win rate, Cohen's
  κ và cập nhật bias report.
- Bằng chứng: `src/m4_eval.py`, `artifacts/ragas_50q.json`,
  `artifacts/judge_results.json`, `doc/reports/failure_clusters.md` và
  `doc/reports/bias_report.md`. Xem các giới hạn và chi tiết kết quả trong
  từng báo cáo; đặc biệt, Phase A dùng answer đầu vào `extractive_fallback`.
- Công việc được thực hiện có hỗ trợ AI; người phụ trách cần tự rà soát và có
  thể giải thích cách chạy, kết quả, cùng các giới hạn của artifacts.

### HoangCongMinh-2A202602774

- Vai trò: thành viên; phụ trách Phase C Tasks 9a–12 và phần guardrails của blueprint.
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
