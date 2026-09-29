# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_latency_p95
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack (#alerts-ops)
- SLI/SLO liên quan: primary_slo (`fast_successful_requests`: latency <= 3000ms, target 99.5%)
- Điều kiện và thời gian duy trì: Latency P95 vượt quá 3000ms liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Người dùng cảm nhận độ trễ phản hồi chat quá lâu, trải nghiệm tương tác bị gián đoạn.
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel Latency trên Dashboard để kiểm tra TTFT P95 và so sánh với tổng latency.
  2. Lọc `data/logs.jsonl` tìm các request có `latency_ms > 3000` trong 5 phút gần nhất, trích xuất `correlation_id`.
  3. Mở Trace trên Langfuse tương ứng với `correlation_id` đó để kiểm tra span waterfall (xác định bottleneck nằm ở span `retrieval` hay `llm-generation`).
- Mitigation tạm thời:
  - Nếu span `retrieval` chậm (ví dụ do database/index quá tải hoặc incident `rag_slow`): bật cache tài liệu, giảm số lượng top-k doc cần retrieve hoặc failover sang fallback retriever.
  - Nếu span `llm-generation` chậm: giảm max tokens trả về, kiểm tra timeout downstream LLM provider.
- Owner: @oncall-sre

## Alert 2

- Tên: high_error_rate
- Severity: critical
- Duration: 3m
- Kênh thông báo: Slack (#alerts-critical)
- SLI/SLO liên quan: guardrails (`error_rate_pct_max: 2` và `retrieval_success_rate_pct_min: 90`)
- Điều kiện và thời gian duy trì: Tỷ lệ request lỗi 5xx (`request_failed`) vượt quá 2% hoặc tỷ lệ retrieval thất bại vượt quá 10% trong 3 phút liên tục.
- Ảnh hưởng tới người dùng: Người dùng nhận thông báo lỗi 500 khi gửi tin nhắn chat, không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel Errors trên Dashboard để xác định loại lỗi phổ biến (`error_type`) và tỷ lệ `tool_success_rate_pct`.
  2. Kiểm tra log `data/logs.jsonl` với query `event == "request_failed"` để xem `detail` của exception.
  3. Lấy `correlation_id` của request lỗi và kiểm tra span tree trên Langfuse để xem exception phát sinh từ bước nào.
- Mitigation tạm thời:
  - Nếu lỗi do retrieval exception (RuntimeError / tool_fail): kích hoạt bypass retrieval để bot trả lời dựa trên direct prompt mà không kèm docs, hoặc restart pod dịch vụ.
  - Thông báo incident cho team liên quan và cập nhật status page nếu lỗi kéo dài.
- Owner: @oncall-sre

## Alert 3

- Tên: daily_cost_budget_exceeded
- Severity: warning
- Duration: 10m
- Kênh thông báo: Slack (#alerts-finops)
- SLI/SLO liên quan: guardrails (`daily_cost_usd_max: 2.5`)
- Điều kiện và thời gian duy trì: Tổng chi phí tích lũy trong ngày vượt quá 2.5 USD hoặc cost rate tăng đột biến trong 10 phút.
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp tới latency của người dùng nhưng gây rủi ro cạn kiệt ngân sách dự án (cost spike / abuse).
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel Cost và Tokens trên Dashboard để xác định lượng token vào/ra (`tokens_in`, `tokens_out`) có tăng đột biến không.
  2. Lọc log để tìm các `user_id_hash` hoặc `session_id` có lượng request hoặc token tiêu thụ bất thường.
  3. Mở Trace trên Langfuse để kiểm tra độ dài prompt và câu trả lời sinh ra từ LLM.
- Mitigation tạm thời:
  - Áp dụng rate limit theo `user_id` / IP.
  - Giảm max output tokens của model trong configuration.
  - Rollback prompt nếu prompt mới dẫn tới output quá dài (verbose generation).
- Owner: @llmops-lead
