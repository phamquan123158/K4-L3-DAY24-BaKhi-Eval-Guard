# Phân tích lỗi Phase A

Nhóm: BaKhi

Người phụ trách: Phạm Quân - 2A202602890

Nguồn: [artifacts/ragas_50q.json](../../artifacts/ragas_50q.json).
Run live hoàn tất: `2026-10-12T15:40:53Z`. Evaluator thực tế được cấu hình
trong m4: `gemini-3.5-flash-lite` và `gemini-embedding-001`; metadata lưu đủ
hai model IDs cùng SHA-256 hiện tại của `answers_50q.json` và
`test_set_50q.json`.

Phân biệt nguồn answer và evaluator: cả 50 answer đầu vào đều có
`generation_mode=extractive_fallback`, không có generation model. RAGAS vẫn
được chạy thật trên đúng các answer/context/reference đã lưu; evaluator dùng
Gemini thật và embedding Gemini thật. Vì Gemini OpenAI-compatible không nhận
nhiều candidates trong một request, RAGAS `answer_relevancy` dùng
`strictness=1` thay mặc định 3. Bốn metric khác vẫn là các metric RAGAS trong
run. Đây là hạn chế cần cân nhắc khi so sánh với run dùng strictness mặc định.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---:|---:|---:|
| faithfulness | 0.9923 | 1.0000 | 0.9818 |
| answer_relevancy | 0.8347 | 0.7396 | 0.8130 |
| context_precision | 0.5833 | 0.2917 | 0.6667 |
| context_recall | 0.6500 | 0.4292 | 0.5583 |
| avg_score | 0.7651 | 0.6151 | 0.7550 |

## Bottom 10 và kiểm tra evidence

Mỗi hàng dưới đây tương ứng với per-question row cùng question ID trong
artifact. Các diagnosis/fix mô tả điểm số và nội dung thật của answer/context,
không xem score tự nó là chứng minh nguyên nhân.

| Rank / ID | Distribution | Avg / worst metric | Evidence và hướng xử lý |
|---|---|---|---|
| 1 / 22 | multi_hop | 0.3968 / context_precision | Cần policy mua sắm và yêu cầu CNTT cho laptop 30 triệu; contexts lại chủ yếu là đào tạo/đào tạo nội bộ/nghỉ không lương. Mở rộng retrieval đa tài liệu và lọc metadata theo policy mua sắm + CNTT. |
| 2 / 40 | multi_hop | 0.4033 / context_precision | Hỏi cách báo cáo vi phạm bảo mật khi đang thử việc; contexts có chi phí/hoàn ứng và thử việc, thiếu hướng dẫn xử lý sự cố. Ưu tiên incident-response/security policy, không để điều kiện thử việc lấn át ý hỏi chính. |
| 3 / 9 | factual | 0.4057 / context_precision | Hỏi nghỉ khi vợ sinh con; contexts trả về chi phí, đào tạo và nghỉ ốm thay vì chế độ nghỉ khi vợ sinh. Bổ sung alias/intent về nghỉ thai sản của cha và lọc tài liệu nghỉ phép liên quan. |
| 4 / 8 | factual | 0.4096 / context_precision | Hỏi ngày nghỉ khi cha/mẹ mất; contexts gồm thưởng Tết, nghỉ ốm, hoàn chi đào tạo. Tăng recall đúng policy nghỉ tang và lọc các chunk không liên quan. |
| 5 / 50 | adversarial | 0.4195 / context_precision | Câu hỏi gài về VPN cá nhân khi WFH; contexts có hạn chế WFH nhưng không thấy policy VPN cá nhân. Truy xuất kết hợp policy remote-work và VPN; giữ điều kiện cấm/version chính xác. |
| 6 / 33 | multi_hop | 0.4234 / context_precision | Hỏi tổng phụ cấp Manager và phép năm v2024; answer trích policy nghỉ phép v2023, trong khi reference cần cả allowance và v2024. Ràng buộc version và nối đúng policy phụ cấp + phép năm hiện hành. |
| 7 / 5 | factual | 0.4248 / context_precision | Hỏi thẩm quyền duyệt thiết bị 55 triệu; contexts có quy trình mua sắm nhưng lẫn thử việc; ground truth yêu cầu Tổng Giám đốc. Tăng độ chính xác ngưỡng giá và giảm chunk nhiễu. |
| 8 / 31 | multi_hop | 0.4294 / context_precision | Hỏi trần khách sạn công tác trong nước cho hai đêm; contexts có đoạn công tác nhưng lẫn phụ cấp và quy định nước ngoài. Tách retrieval trong nước/nước ngoài và tính tổng từ trần mỗi đêm. |
| 9 / 27 | multi_hop | 0.4367 / context_precision | Cần phép v2024 sau khi trừ 4 ngày nghỉ ốm không giấy y tế; contexts gồm policy nghỉ ốm và v2023, có nguy cơ nhầm version. Truy xuất đồng thời v2024 và điều kiện khấu trừ phép, rồi kiểm tra phép tính. |
| 10 / 39 | multi_hop | 0.4464 / context_precision | Hỏi so sánh policy mật khẩu v1.0/v2.0; contexts có cả hai phiên bản nhưng lẫn policy nghỉ ốm. Giữ đủ hai phiên bản để so sánh và loại chunk ngoài chủ đề. |

Các hàng bottom đều có `context_precision=0.0` và `context_recall=0.0` theo
RAGAS run; `faithfulness` của chúng lại cao (1.0 trong artifact). Vì vậy cần
đọc song song answer/reference/context thay vì suy luận rằng answer đúng chỉ
từ faithfulness hoặc rằng retrieval hoàn toàn rỗng chỉ từ hai điểm retrieval.
Các context được ghi trong artifact là nguồn để rà soát thủ công trước khi
thay đổi retriever.

## Matrix và nhóm yếu nhất

Matrix đếm mỗi câu theo metric có điểm thấp nhất:

| Worst metric | factual | multi_hop | adversarial | Tổng |
|---|---:|---:|---:|---:|
| faithfulness | 0 | 0 | 0 | 0 |
| context_recall | 3 | 3 | 5 | 11 |
| context_precision | 9 | 14 | 3 | 26 |
| answer_relevancy | 8 | 3 | 2 | 13 |
| **Tổng** | **20** | **20** | **10** | **50** |

Nhóm yếu theo mean `avg_score` thấp nhất là `multi_hop` (**0.6151**), không
phải nhóm nhiều câu nhất. `context_precision` là worst metric thường gặp nhất
(26/50); `context_recall` là điểm trung bình yếu nhất ở nhóm adversarial
(0.5583). Ưu tiên cải thiện precision cho retrieval đa tài liệu/version và
review recall trên các câu phủ định hoặc có điều kiện. Đây là tín hiệu của
run hiện tại, không phải bằng chứng nhân quả.

## Giới hạn và hành động tiếp theo

Artifact đã qua schema, source-hash, 50-row, 20/20/10 distribution, metric
range, bottom-10 và matrix validation. Kết quả mô tả một run với answer đầu
vào dạng extractive fallback, model evaluator Gemini và answer-relevancy
strictness 1. Muốn so sánh chất lượng end-to-end của generation cần tạo lại
answers bằng pipeline generation thật rồi chạy lại Phase A; không diễn giải
Phase A hiện tại như đánh giá answer do LLM generation tạo ra.
