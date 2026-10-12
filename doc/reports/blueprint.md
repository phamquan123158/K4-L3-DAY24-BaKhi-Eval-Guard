# Blueprint CI/CD cho RAG và guardrails

Nhóm:

Người phụ trách Phase C: **Hoàng Công Minh — 2A202602774**.

Đây là **đề xuất CI/CD**, chưa triển khai/chạy workflow.
Nguồn dự kiến: artifacts/ragas_50q.json, artifacts/judge_results.json và
artifacts/guard_results.json; hiện đã có report C, chưa có reports A/B.
Không lấy mock tests để điền số đo hoặc điểm chất lượng.

Run timestamp C: 2026-10-12T13:06:11.136556+00:00 (20:06:11 UTC+07).
Guard cấu hình: gemini-3.5-flash-lite, NeMo 0.10.0, endpoint Gemini tương thích
OpenAI. Metadata được lấy từ các NeMo instances thực sự sử dụng.
Models generation/evaluator/judge A/B: chưa có metadata report để đối chiếu.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.

Input chứa CCCD/CMND, điện thoại Việt Nam/quốc tế hoặc email bị chặn trước
NeMo/RAG. Presidio trả types, scores, offsets và bản ẩn PII. English NER
PERSON/LOCATION không quyết định block do nhận nhầm tiếng Việt; đây là giới hạn,
không phải tuyên bố nhận diện đủ mọi PII. Không dùng id/category/expected của
fixtures để quyết định actual.

NeMo kiểm tra phạm vi HR/IT, jailbreak, injection và truy xuất dữ liệu nhân viên.
Block dựa activated_rails.stop, không dựa từ khóa refusal trong response.
Output rail nhận question và answer có sẵn; giữ answer sạch, thay answer khi
rail dừng. Cho phép khung lương chung, chính sách VPN/mật khẩu, public helpdesk;
chặn personal identifiers, credentials và hồ sơ bí mật. Self-check output
không thay đánh giá factual accuracy/faithfulness với retrieved contexts.

Request production dừng sớm khi bị chặn. Nếu engines/API lỗi, đề xuất fail-closed:
thông báo không xử lý được, không trả answer chưa kiểm tra. Hàm lab truyền
exception lên runner, không giả allowed/safe hoặc report pass.
RAG fallback phải ghi generation_mode/giới hạn, không bỏ guard.

Key ở .env/secret store CI. Production logs chỉ giữ request ID, entity types,
layer/reason, latency, model/policy version và trạng thái; không log key/raw PII
hay confidential answers. Artifacts dùng fixtures giả lập, tách khỏi dữ liệu
người dùng thật; kiểm tra secrets trước commit.

## Phạm vi và số đo latency

Task 12: **input_layers_sequential**, luôn đo Presidio rồi NeMo input kể cả khi
PII chặn. Engines tạo trước đo và reuse. Hai warm-up thật mỗi tầng loại khỏi
samples; ít nhất 20 timed samples bằng perf_counter, luân phiên clean inputs.
Percentile linear tại (n-1)*q; tổng từ tổng từng sample, không cộng hai P95 riêng.

Số mẫu timed: 20; warm-up thực: 2 lượt mỗi tầng, loại khỏi samples.
Phương pháp: linear; scope: input_layers_sequential.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 5.520 | 6.517 | 6.803 | Live |
| NeMo input | 1057.480 | 2423.549 | 2528.383 | Live, quota wait excluded |
| Input guard sequential | 1063.235 | 2429.126 | 2534.060 | Live, quota wait excluded |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài Task 12 |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài Task 12 |
| Full guard / request dừng sớm | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer target 500 ms; latency_budget_ok=false: P95 2429.126 ms vượt target.
Gemini giới hạn 15 requests/phút ở lượt chạy này; runner vẫn giãn 4.5 giây
giữa các requests để tuân thủ quota. Khoảng chờ admission chạy trước timer và
được tách khỏi latency xử lý guard; vì vậy batch vẫn mất vài phút. Số đo vẫn
gồm network/provider response và NeMo overhead, không phải full request.
Lượt đầu tính cả khoảng chờ có P95 4811.519 ms; lượt mới tách khoảng chờ, giảm
P95 xuống 2429.126 ms nhưng vẫn vượt target. Phần lớn thời gian còn lại là
request tới Gemini; không thể đạt 500 ms ổn định chỉ bằng tối ưu Presidio.
Nếu vượt target, ghi số thật; tối ưu prompt/output Yes/No, kiểm tra cache đúng
policy version rồi đo lại clean controls, không bỏ guard để làm đẹp latency.
Đo các scope còn lại bằng timestamps quanh retrieve/rerank/generate, output
rail/toàn request; tách allowed/blocked/error, ít nhất 20 timed samples mỗi nhánh
sau warm-up; ghi model/policy/timestamps và percentile trên samples thực.

## CI gates đề xuất

1. Job offline chạy python -m pytest tests/ -q và schema checks; failures trả
   nonzero. A/B còn TODO thì toàn bộ student tests/checker vẫn báo thiếu bài.
2. Job API có secret, bật riêng cho phases đã làm bằng
   scripts/run_experiments.py --phase a|b|c --live; C có --latency-samples 20.
   Không gọi API trên mọi push để tránh phí/quota.
3. Khi đủ artifacts/reports, chạy python scripts/check_lab.py. Runner C lưu
   cả batch thật không đạt chất lượng; có JSON không tự đồng nghĩa đạt gate.
4. Gate production đề xuất: faithfulness mean >=0.75, avg_score >=0.65 trên 50
   câu; attacks >=18/20, clean 8/8, output 4/4. Cần script đọc JSON/exit(1)
   nếu không đạt các ngưỡng production; script/workflow này chưa triển khai.
5. Full guard P95 <500 ms chỉ dùng sau khi đo đúng full-guard scope. Input-layer
   budget dùng số Task 12 riêng; MIN_* không tự tạo quality gate.

Mốc lab vẫn attacks >=15/20 và clean 8/8; bonus >=18/20 kèm clean đạt.
A/B và blueprint cần nhóm tích hợp trước khi nộp repo chung.

## Monitoring và cải tiến

Theo dõi block rate theo layer/category, false positives trên clean controls,
output safe/blocked/error, P50/P95/P99 theo scope, API timeout/429, model/policy
version. Cảnh báo đề xuất khi clean bị chặn, output nhạy cảm lọt, quality tụt gate
hoặc latency vượt target trong 3 cửa sổ liên tiếp. Error không tính thành allowed.
Samples redact, hạn chế truy cập/retention, không dùng hồ sơ nhân viên thật debug.
Hoàng Công Minh rà soát guardrails; người phụ trách A/B/vận hành chưa cung cấp.

RAGAS mean/worst distribution: chưa có kết quả A.
Cohen's kappa: chưa có kết quả B.
Attacks passed: 20/20 (100%) ở lượt mới.
Clean passed: 8/8; false_positive_rate: 0%.
Outputs passed: 4/4 (2 safe được giữ nguyên, 2 unsafe được thay bằng refusal).
Schema, source hashes và quality contract C đều được scripts/check_lab.py xác nhận.

Lượt đầu được giữ ở artifacts/guard_results_initial.json: attacks 20/20,
clean 0/8, output 2/4. NeMo mặc định giới hạn self-check 3 token gây chặn sai;
tăng max_tokens lên 256 để sửa lỗi, sau đó giảm xuống 16 cho câu trả lời Yes/No.
Batch live mới nhất giữ chất lượng 20/8/4. Không chỉnh classifications trong
JSON và không dùng expected để ra quyết định.

Cải tiến cần kiểm chứng:
- Test tên/địa chỉ tiếng Việt trước khi mở rộng PII gate; thêm clean controls
  để tránh tái diễn false positives của English NER.
- Thêm jailbreak đa ngôn ngữ và yêu cầu PII không có số/email; đối chiếu rail
  decisions, không chỉ tỷ lệ attacks hiện có.
- Kiểm tra public helpdesk/khung lương chung ở output, phân biệt policy công khai
  với personal data/credentials.
- Đo RAG/output/full request riêng; phân tích nhánh dừng sớm/latency API.
- Chạy lại khi đổi model/policy, đối chiếu metadata/source hashes phát hiện
  reports cũ; bộ 50/20/8/4 nhỏ không chứng minh an toàn production.

## Kiểm chứng hiện có

python -m pytest tests/test_phase_c.py tests/test_support.py
tests/test_report_contracts.py -q --basetemp=.venv-tools/pytest-final: **76 passed**.
Mock tests không tạo số đo được chấp nhận cho Task 12. Presidio thật đã kiểm tra.
Bảng số đo lấy từ batch Gemini live. Codex hỗ trợ code/báo cáo; đóng góp ở TEAM.

Nguồn Gemini: [Google — OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai).
Nguồn yêu cầu: doc/ASSIGNMENT.md, doc/RUBRIC.md, doc/REPORT_SCHEMAS.md của starter.
