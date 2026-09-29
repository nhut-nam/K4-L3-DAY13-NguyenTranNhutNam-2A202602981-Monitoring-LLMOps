# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Trần Nhựt Nam
- **MSSV:** 2A202602981
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/nhut-nam/K4-L3-DAY13-NguyenTranNhutNam-2A202602981-Monitoring-LLMOps
- **Commit SHA cuối:** `7f3b37717d02e8f834fdb7a49e26be4a6023f792`
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602981`

## 2. Evidence index

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
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ tiêu chuẩn Schema, Correlation ID, Context Enrichment, PII Masking |
| `validate_dashboard.py` | 6/6 panels | 6/6 panels | Đầy đủ 6 panel hợp lệ theo dashboard contract chuẩn |
| `pytest` | 22 passed | 25 passed | Đạt 100% test cases (bổ sung tests mở rộng CCCD, credit card, passport) |
| Số traces hợp lệ | 0 | 35+ observations | Traces được ghi nhận đầy đủ hierarchy root + retrieval + generation trên Langfuse Cloud |
| Số PII leak | 0 | 0 | Scrubbing đệ quy triệt để trên cả chuỗi lẫn nested dictionary/list |
| Latency P95 / TTFT P95 | 156.4ms / 0ms | 156.4ms / 50ms | Baseline ổn định; khi kích hoạt incident P95 tăng vọt > 3700ms |
| Retrieval success rate | 100% | 100% | Toàn bộ các lượt gọi retriever trả về kết quả thành công |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware` (`app/middleware.py`), request được xóa contextvars cũ bằng `clear_contextvars()`. Middleware trích xuất header `x-request-id` nếu có sẵn từ client, nếu không sẽ tự sinh mới bằng `f"req-{uuid.uuid4().hex[:8]}"`. Correlation ID sau đó được bind vào structlog contextvars qua `bind_contextvars(correlation_id=correlation_id)` và gán vào `request.state.correlation_id`. Sau khi request được xử lý, middleware gán `correlation_id` vào header `x-request-id` và thời gian phản hồi vào `x-response-time-ms` của response.
- **Các metadata được ghi vào structured log:** Mỗi log record chứa các trường tiêu chuẩn: `ts` (ISO UTC timestamp), `level`, `service`, `event`, và `correlation_id`. Đối với API `/chat`, log được enrich thêm: `user_id_hash` (băm sha256 12 ký tự đảm bảo ẩn danh), `session_id`, `feature`, `model`, `env`, cùng các số đo hiệu năng như `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và `payload`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` được đăng ký trong chuỗi processors của `structlog` và đặt ngay TRƯỚC `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_event` duyệt đệ quy toàn bộ cấu trúc event dictionary (bao gồm cả nested payload dicts/lists), áp dụng bộ regex `PII_PATTERNS` trong `app/pii.py` (email, phone VN, CCCD 12 số, credit card 16 số, passport) để thay thế dữ liệu nhạy cảm thành các token dạng `[REDACTED_<TYPE>]` trước khi dữ liệu được ghi xuống file `data/logs.jsonl` hoặc in ra console.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt 100/100 điểm: không có bản ghi thiếu trường bắt buộc, 0 bản ghi thiếu context enrichment, 10/10 correlation IDs duy nhất được truyền thành công và 0 trường hợp leak PII. Toàn bộ 25/25 test cases của `pytest` (bao gồm `tests/test_pii.py`, `tests/test_chat_observability.py`, `tests/test_validate_logs.py`) đều pass.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Project trên Langfuse Cloud được đặt tên theo đúng MSSV: `day13-k4-l3a-2A202602981`. Cặp API key (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`) được tạo trực tiếp từ Project Settings của project này và cấu hình trong `.env`. Toàn bộ traces đều gắn tag sinh viên và xuất hiện trong đúng dashboard của project cá nhân.
- **Cấu trúc root/retrieval/generation observations:**
  - Root observation: `lab-agent-run` (type `agent`), bao bọc toàn bộ chu trình xử lý của agent.
  - Child observation 1: `retrieval` (type `retriever`), đo lường bước RAG truy xuất dữ liệu ngữ cảnh `retrieve(message)`.
  - Child observation 2: `llm-generation` (type `generation`), đo lường bước gọi mô hình ngôn ngữ sinh câu trả lời, ghi nhận input messages, model, usage tokens (`input`, `output`, `total`), và cost.
- **Metadata và tag đã ghi vào trace:** Ghi nhận `session_id`, `user_id_hash`, `correlation_id`, `feature`, `model`, `env`, và tags phân loại `["day13", "k4-l3a", "student-2A202602981"]`.
- **Chiến lược prompt version, label và rollback:**
  - Quản lý prompt `day13-chat` qua Langfuse Prompts.
  - Phiên bản 1 (v1) được gán labels `baseline` và `production`.
  - Phiên bản 2 (v2) được thêm ràng buộc phong cách ngắn gọn và gán label `candidate`.
  - Quy trình rollback tức thì: chuyển label `production` từ v2 trở lại v1 trên Langfuse UI mà không cần sửa code hay rebuild/restart service. Ứng dụng tự động fetch prompt có nhãn `production` và hoàn trả phong cách ban đầu an toàn.

## 6. Metrics, SLO và Alerts

- **Sáu metric chính và ngưỡng:**
  1. `latency_p95`: Độ trễ phân vị P95 của request `/chat`; đơn vị `ms`, ngưỡng baseline $\le 3000\text{ms}$.
  2. `error_rate`: Tỷ lệ lỗi 5xx trên tổng số request; đơn vị `%`, ngưỡng baseline $\le 1.0\%$.
  3. `ttft_p95`: Thời gian từ lúc gửi yêu cầu đến khi nhận token đầu tiên (Time To First Token) phân vị P95; đơn vị `ms`, ngưỡng $\le 800\text{ms}$.
  4. `cost`: Chi phí ước tính tích lũy (`cost_usd`); đơn vị `USD`, ngân sách vận hành $\le 2.0\text{ USD/ngày}$.
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

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 16:43:00 - 16:44:30 ICT (09:43:00Z - 09:44:30Z)
- **Triệu chứng từ metrics:**
  - Trong quá trình chạy load test challenge (5 concurrent requests), độ trễ request tại server tăng vọt từ ~156ms lên tới **2652ms - 3723ms** (vượt xa ngưỡng `latency_threshold_ms: 2000` của challenge).
  - Phía client đo được tổng thời gian phản hồi (chờ kết nối và xử lý tuần tự/nghẽn) lên tới **11,706ms - 14,365ms**.
  - Metric Latency P95 trên dashboard vọt qua vạch cảnh báo, kích hoạt alert `high_latency_p95`.
- **Log line và correlation ID liên quan:**
  - Request tiêu biểu: `req-b4f19c2c` (cùng các request bị ảnh hưởng `req-673da633`, `req-7e86f1c8`, `req-e76debea`, `req-cb5059c1`).
  - Trích xuất từ `data/logs.jsonl` (line 45):
    ```json
    {"service": "api", "latency_ms": 3723, "ttft_ms": 50, "tokens_in": 35, "tokens_out": 135, "cost_usd": 0.00213, "quality_score": 0.8, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "env": "dev", "model": "claude-sonnet-4-5", "session_id": "k4-l3a-challenge-s05", "feature": "monitoring", "correlation_id": "req-b4f19c2c", "user_id_hash": "ed72e61117f6", "level": "info", "ts": "2026-09-29T09:43:33.712789Z"}
    ```
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID / Correlation ID: `req-b4f19c2c` (Trace name: `chat-request` / Agent run: `lab-agent-run`).
  - Span gây nghẽn: `retrieval` (retriever observation). Trong waterfall trace, span `retrieval` chiếm đến ~3500ms tổng thời gian xử lý, trong khi span `llm-generation` hoàn thành bình thường trong ~150ms.
- **Root cause:**
  - Sự cố `rag_slow` kích hoạt độ trễ nhân tạo trong hàm `retrieve(message)`. Trong môi trường thực tế, hiện tượng này tương ứng với:
    1. Vector Database / Knowledge Base bị quá tải tài nguyên I/O hoặc CPU khi số lượng truy vấn đồng thời tăng.
    2. Thiếu cấu hình chỉ mục tìm kiếm (HNSW / IVFFlat) khiến tìm kiếm tương đồng vector bị suy thoái về dạng brute-force (flat scan).
    3. Kết nối mạng giữa AI Service và Vector DB bị nghẽn (network latency spike).
- **Fix action:**
  - Ngay lập tức tắt cờ incident bằng lệnh `python scripts/inject_incident.py --disable` (tương đương gọi `POST /incidents/rag_slow/disable`).
  - Với môi trường production thực tế:
    1. Tăng replica/node cho cụm Vector DB (horizontal scaling).
    2. Bổ sung tầng Semantic Caching (Redis) cho các embedding queries phổ biến để giảm tải trực tiếp cho Vector DB.
    3. Đánh lại index (re-indexing) cho vector collection với tham số tìm kiếm tối ưu.
- **Preventive measure:**
  - **Retrieval Timeout:** Thiết lập hard timeout cho bước retrieval (ví dụ: tối đa 1500ms).
  - **Circuit Breaker & Fallback:** Khi retrieval service bị chậm hoặc quá tải liên tục, Circuit Breaker tự ngắt và kích hoạt Fallback Retriever (chuyển sang keyword search BM25 nhẹ hơn hoặc trả câu trả lời từ LLM kèm disclaimer).
  - **Granular Observability:** Thêm SLI/Alert riêng biệt cho `retrieval_latency_p95` thay vì chỉ theo dõi end-to-end `request_latency_p95`.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  - Quyết định cài đặt processor `scrub_event` tại vị trí trung tâm trong chuỗi structlog pipeline, duyệt đệ quy qua tất cả nested payload dicts/lists. Lý do: trong hệ thống AI Agent, dữ liệu đầu vào và đầu ra thường được đóng gói lồng nhau trong các object metadata phức tạp; nếu chỉ scrub các key cố định ở tầng ngoài cùng thì PII lọt vào arguments hoặc context retrieval sẽ bị ghi trần ra log, vi phạm nghiêm trọng chính sách bảo mật GDPR/PDPA.
- **Một lỗi/blocker đã gặp:**
  - Langfuse Cloud API v3 (`/api/public/observations`, `/api/public/traces`) bị ngừng hỗ trợ (deprecated) cho các Organization tạo mới sau tháng 09/2026, trả về mã lỗi `400 LEGACY_API_UNAVAILABLE_FOR_NEW_ORGANIZATION`.
- **Cách tìm nguyên nhân và xử lý:**
  - Khi xem response JSON từ Langfuse endpoint, nhận thấy thông báo lỗi yêu cầu chuyển sang API v2 (`/api/public/v2/observations?fromStartTime=...`). Đồng thời, trong mã nguồn `app/agent.py`, thay vì metadata rời rạc ở từng span đơn lẻ, ta sử dụng đúng kiến trúc SDK v4 với context manager và propagate metadata ở cấp Trace, giúp toàn bộ child observations kế thừa chính xác context.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics** là còi báo động: cho biết *khi nào* và *ở đâu* có sự bất thường (vd: P95 latency tăng từ 156ms lên 3700ms).
  - **Logs** là bằng chứng cụ thể: cung cấp ngữ cảnh chi tiết kèm `correlation_id` của các request bị lỗi/chậm (vd: tìm thấy request `req-b4f19c2c` có `latency_ms: 3723`).
  - **Traces** là kính hiển vi: hiển thị chi tiết waterfall phân rã thời gian từng bước bên trong request đó, chỉ ra chính xác span nào tiêu tốn thời gian (vd: span `retrieval` tốn 3500ms, loại trừ giả thuyết do LLM quá tải).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Prompt trong LLMOps đóng vai trò tương tự "mã nguồn" nhưng có tính xác suất cao. Việc gán version (`v1`, `v2`) và labels (`production`, `candidate`) cho phép A/B testing và triển khai an toàn. Khi một prompt mới gây suy giảm chất lượng hoặc tiêu tốn token bất thường, khả năng rollback qua tag/label ngay trên Langfuse giúp đội ngũ khôi phục dịch vụ tức thì mà không cần re-deploy hệ thống. Quản lý token/cost giúp ngăn ngừa rủi ro vượt ngân sách và duy trì SLO dịch vụ.
- **Điều quan trọng nhất đã học:**
  - Xây dựng hệ thống quan sát toàn diện (Observability) cho LLM không chỉ đơn thuần là in log hay theo dõi CPU/RAM truyền thống, mà đòi hỏi sự gắn kết chặt chẽ giữa Golden Signals (Latency, Traffic, Errors, Saturation) với các số đo đặc thù AI (Tokens, Cost, Quality, Tool success, Prompt lineage).
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  - Hệ thống hiện tại mới đo lường chất lượng (`quality_score`) qua mô phỏng tĩnh; trong thực tế cần tích hợp LLM-as-a-Judge bất đồng bộ (asynchronous evaluation worker) hoặc thu thập tín hiệu Human-in-the-loop (thumbs-up/thumbs-down) để đánh giá chất lượng liên tục.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
