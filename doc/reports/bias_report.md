# Đánh giá LLM Judge Phase B

Nhóm: BaKhi.

Người phụ trách Phase B: Phạm Quân - 2A202602890

Phạm vi thực hiện: chạy batch judge live, kiểm tra kết quả pairwise/calibration
và tổng hợp phân tích bias trong báo cáo này. Kết quả và giới hạn bên dưới chỉ
áp dụng cho artifacts/mẫu được đánh giá; không khẳng định judge tổng quát luôn
chính xác.

Nguồn kết quả: [artifacts/judge_results.json](../../artifacts/judge_results.json).
Run live: 2026-10-12 14:20:26 UTC. Judge model: `gemini-3.1-flash-lite`;
metadata ghi `generation: []`, evaluator và guard rỗng.

## Năm cặp A/B và hai lượt

A lấy nguyên từ `answer` trong [artifacts/answers_50q.json](../../artifacts/answers_50q.json);
B lấy nguyên từ `model_answer` trong [fixtures/human_labels_10q.json](../../fixtures/human_labels_10q.json);
reference lấy từ [fixtures/test_set_50q.json](../../fixtures/test_set_50q.json).
Các đoạn A dưới đây chỉ trích ngắn để dễ đọc; artifact giữ nguyên toàn bộ A/B.
Pass 2 hiển thị winner và scores đã quy đổi về A/B ban đầu; reasoning pass 2
vẫn dùng ký hiệu A/B của lượt đã hoán đổi.

| ID | Question | A (trích) / B | Pass 1 → pass 2 | Kết quả / nhất quán | Scores P1; P2 (A, B) | Nhận xét |
|---:|---|---|---|---|---|---|
| 1 | Số ngày nghỉ khi kết hôn? | A: đoạn trích lạc đề từ `hoan_chi_dao_tao.md`; B: 3 ngày làm việc có lương | B → B | B / có | (0.0, 1.0); (0.0, 1.0) | B trả lời trực tiếp; A là nội dung đào tạo bị cắt/lỗi định dạng. |
| 5 | Ai duyệt thiết bị giá 55 triệu? | A: đoạn trích rời rạc từ `mua_sam.md`; B: Giám đốc phòng ban | tie → B | tie / không | (0.1, 0.1); (0.0, 0.2) | Cả hai không khớp reference (Tổng Giám đốc); lượt đảo thứ tự không đồng thuận. |
| 12 | Thưởng Tết tối thiểu từ 6 tháng? | A: đoạn trích dài, lặp từ `thuong_tet.md`; B: 1 tháng lương | B → B | B / có | (0.3, 1.0); (0.4, 1.0) | B súc tích và đúng; A lặp, dở dang. |
| 21 | Senior 9 năm: phép năm và khoảng lương? | A: đoạn trích chính sách nghỉ phép, thiếu lương; B: 18 ngày và 20–35 triệu | B → B | B / có | (0.4, 1.0); (0.3, 1.0) | B trả lời cả hai ý; A thiếu khoảng lương và bị lặp/cắt. |
| 41 | Số ngày phép năm? | A: trích chính sách nghỉ phép đặc biệt; B: 12 ngày (policy cũ) | tie → B | tie / không | (0.1, 0.2); (0.0, 0.3) | A lạc đề; B dùng mức 12 ngày cũ thay vì 15 ngày theo reference hiện hành. |

Position inconsistency: **2/5 = 0.4** (IDs 5, 41).
Verbosity win rate: **0/3 = 0.0** trên 3 cặp decisive; không có winner
dài hơn trong các cặp này.

Hai cặp 5 và 41 đổi từ tie ở lượt đầu sang B ở lượt đảo, nên bị quy về tie
theo quy tắc consensus. Đây là dấu hiệu judge chưa ổn định theo thứ tự hoặc
cách diễn đạt, không đủ để kết luận riêng nguyên nhân là position bias. Ba
cặp decisive đều chọn B; các answer A trong artifact là đoạn trích pipeline
dài/lỗi/trùng lặp, nhưng tỷ lệ verbosity vẫn được tính đúng theo định nghĩa
“winner dài hơn”, không suy ra bias chỉ từ độ dài tổng thể.

## Calibration trên đúng model_answer

Mỗi lượt binary gửi đúng question và `model_answer` gốc cùng reference; không
gửi nhãn hay ghi chú của người. Bảng dưới giữ thứ tự trong artifact.

| ID | Model answer gốc | Judge | Human | Đồng ý | Lý do judge |
|---:|---|---:|---:|:---:|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | 1 | Có | Đúng số ngày và tính chất có lương theo reference. |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | Có | Đơn hàng trên 50 triệu cần Tổng Giám đốc phê duyệt. |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | Có | Nêu đúng mức thưởng tối thiểu cho nhân viên đủ điều kiện. |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | 1 | Có | Khớp policy v2024 về ngày phép và khoảng lương. |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | Có | Đúng số tiền hoàn trả và lý do theo thời hạn cam kết. |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | 0 | Có | Thiếu Kế toán trưởng và tính phí phạt sai. |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | Có | Tính đúng ngày phép và tổng phụ cấp theo reference. |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | Có | Dùng policy v2023 đã bị thay thế; hiện hành là 15 ngày cơ bản. |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | 1 | Có | Khớp điều kiện nghỉ phép của nhân viên thử việc. |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | Có | Reference cấm VPN cá nhân; câu trả lời lại cho phép. |

**Cohen’s κ = 1.0.** Observed agreement = 10/10 = 1.0. Với 6 nhãn human
bằng 1 và 4 nhãn bằng 0, expected chance agreement = 0.6² + 0.4² = 0.52;
κ = (1.0 − 0.52) / (1 − 0.52) = 1.0. Không có ID nào lệch human trong mẫu
này.

## Giới hạn và cách dùng judge

Kết quả dùng `gemini-3.1-flash-lite`, prompt pairwise ba tiêu chí (độ chính
xác, đầy đủ, súc tích), 5 cặp và 10 nhãn nhị phân. κ hoàn hảo chỉ phản ánh
10 `model_answer` đã cung cấp, không chứng minh judge tổng quát luôn đúng;
cần mở rộng mẫu và review các quyết định thủ công trước khi dùng làm gate.
Các cặp 5 và 41 cần xem lại vì hai lượt không đồng thuận; cặp 5 đặc biệt cần
đối chiếu cả hai answer với thẩm quyền phê duyệt trong policy. Winner của cặp
A/B không được đổi thành nhãn tốt/xấu: calibration là đánh giá từng answer
riêng, đúng reference và đúng thứ tự nguồn.
