# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Trần Nhựt Nam
- **MSSV:** 2A202602981
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/nhut-nam/K4-L3-DAY13-NguyenTranNhutNam-2A202602981-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602981`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | | Thiếu correlation_id và context enrichment |
| `validate_dashboard.py` | 6/6 panels | | Đạt cấu trúc schema chuẩn |
| `pytest` | 22 passed | | Toàn bộ unit tests ban đầu passed |
| Số traces hợp lệ | 0 | | Chưa cấu hình Langfuse credentials |
| Số PII leak | 0 | | Chưa có request chứa PII vi phạm |
| Latency P95 / TTFT P95 | 156.4ms / 0ms | | Đo lường tải baseline (10 requests) |
| Retrieval success rate | 100% | | Môi trường chưa kích hoạt incident |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware` (`app/middleware.py`), request được xóa contextvars cũ bằng `clear_contextvars()`. Middleware trích xuất header `x-request-id` nếu có sẵn từ client, nếu không sẽ tự sinh mới bằng `f"req-{uuid.uuid4().hex[:8]}"`. Correlation ID sau đó được bind vào structlog contextvars qua `bind_contextvars(correlation_id=correlation_id)` và gán vào `request.state.correlation_id`. Sau khi request được xử lý, middleware gán `correlation_id` vào header `x-request-id` và thời gian phản hồi vào `x-response-time-ms` của response.
- **Các metadata được ghi vào structured log:** Mỗi log record chứa các trường tiêu chuẩn: `ts` (ISO UTC timestamp), `level`, `service`, `event`, và `correlation_id`. Đối với API `/chat`, log được enrich thêm: `user_id_hash` (băm sha256 12 ký tự đảm bảo ẩn danh), `session_id`, `feature`, `model`, `env`, cùng các số đo hiệu năng như `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và `payload`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` được đăng ký trong chuỗi processors của `structlog` và đặt ngay TRƯỚC `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_event` duyệt đệ quy toàn bộ cấu trúc event dictionary (bao gồm cả nested payload dicts/lists), áp dụng bộ regex `PII_PATTERNS` trong `app/pii.py` (email, phone VN, CCCD 12 số, credit card 16 số, passport) để thay thế dữ liệu nhạy cảm thành các token dạng `[REDACTED_<TYPE>]` trước khi dữ liệu được ghi xuống file `data/logs.jsonl` hoặc in ra console.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt 100/100 điểm: không có bản ghi thiếu trường bắt buộc, 0 bản ghi thiếu context enrichment, 10/10 correlation IDs duy nhất được truyền thành công và 0 trường hợp leak PII. Toàn bộ 25/25 test cases của `pytest` (bao gồm `tests/test_pii.py`, `tests/test_chat_observability.py`, `tests/test_validate_logs.py`) đều pass.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng đúng 6 panel theo contract `config/dashboard.yaml`:
  1. `latency`: Theo dõi độ trễ P50, P95, P99 và TTFT P95; đơn vị `ms`, threshold P95 $\le 3000\text{ms}$.
  2. `traffic`: Số lượng request nhận được theo thời gian và request/phút; đơn vị `requests_per_minute`, threshold rate $\ge 1$.
  3. `errors`: Tỷ lệ lỗi 5xx (`error_rate_pct`), phân loại lỗi theo `error_type` và tỷ lệ retrieval thành công (`tool_success_rate_pct`); đơn vị `percent`, threshold error rate $\le 2\%$.
  4. `cost`: Chi phí ước tính tích lũy theo phút và tổng cửa sổ; đơn vị `usd`, threshold tổng chi phí $\le 2.5\text{ USD}$.
  5. `tokens`: Tổng token đầu vào (`tokens_in`) và token đầu ra (`tokens_out`); đơn vị `tokens`, threshold $\le 50,000$.
  6. `quality`: Điểm chất lượng trung bình của câu trả lời (`mean`); thang điểm 0-1, threshold $\ge 0.75$.
- **SLO và lý do chọn:**
  - Primary SLO: `fast_successful_requests` với mục tiêu **99.5%** trong cửa sổ 28 ngày.
  - SLI: $\frac{\text{Số request trả về thành công có latency } \le 3000\text{ms}}{\text{Tổng số request nhận được}} \times 100\%$.
  - Lý do chọn: Người dùng chatbot yêu cầu phản hồi nhanh dưới 3 giây để tương tác mượt mà và không bị gián đoạn bởi lỗi 5xx. Ngưỡng 3000ms tạo biên an toàn tốt so với baseline (~156ms).
- **Cách tính error budget:**
  - $\text{Error Budget} = 100\% - \text{SLO Target} = 100\% - 99.5\% = 0.5\%$.
  - Với 100,000 requests trong chu kỳ 28 ngày, hệ thống chỉ được phép có tối đa $100,000 \times 0.5\% = 500$ requests bị lỗi hoặc chậm $> 3000\text{ms}$.
  - Khi tỷ lệ lỗi/chậm tăng lên 5% trong 1 giờ, Burn Rate = 10x, toàn bộ ngân sách lỗi 28 ngày sẽ bị tiêu tán chỉ sau khoảng 2.8 ngày.
- **Ba alert và runbook tương ứng:**
  1. `high_latency_p95`: Severity warning, điều kiện `latency_ms_p95 > 3000ms` duy trì trong 5 phút. Runbook tại `docs/alerts.md#alert-1`.
  2. `high_error_rate`: Severity critical, điều kiện `error_rate_pct > 2%` duy trì trong 3 phút. Runbook tại `docs/alerts.md#alert-2`.
  3. `daily_cost_budget_exceeded`: Severity warning, điều kiện `total_cost_usd > 2.5` duy trì trong 10 phút. Runbook tại `docs/alerts.md#alert-3`.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
