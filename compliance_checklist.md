# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: **dpo@medviet.vn**

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | Envelope Encryption (AES-256-GCM) with SimpleVault | ✅ Done | Infra Team |
| Audit logging | Structured logging of endpoint access & Casbin/OPA decisions | ✅ Done | Platform Team |
| Breach detection | TruffleHog + Bandit SAST + Great Expectations validation | ✅ Done | Security Team |

## F. Technical Solution Descriptions

### 1. Audit Logging
- **Mô tả:** Hệ thống sử dụng FastAPI middleware để tự động ghi log có cấu trúc (Structured Logging) cho mọi API request. Mỗi bản ghi log bao gồm các trường: `timestamp`, `username`, `role`, `resource`, `action`, `client_ip` và kết quả phân quyền của Casbin/OPA.
- **Lưu trữ:** Log được đẩy về hệ thống ELK Stack (Elasticsearch, Logstash, Kibana) hoặc AWS CloudWatch Logs được cấu hình chính sách WORM (Write Once, Read Many) để ngăn chặn việc chỉnh sửa hoặc xóa lịch sử truy cập của quản trị viên hệ thống.

### 2. Breach Detection
- **Mô tả:** 
  1. **Source Code & Credentials:** Sử dụng `git-secrets` kết hợp `TruffleHog` để quét toàn bộ lịch sử commit và ngăn chặn việc lộ lọt khoá mật khẩu (AWS keys, database passwords, private keys).
  2. **Data Pipeline Leakage:** Sử dụng `Great Expectations` để tự động kiểm tra tính toàn vẹn của dữ liệu sau khi ẩn danh hoá (đảm bảo không còn bất kỳ số CCCD gốc hoặc thông tin nhạy cảm nào bị rò rỉ).
  3. **Runtime Monitoring:** Cấu hình Prometheus & Grafana để thu thập chỉ số HTTP requests. Sử dụng Prometheus Alertmanager để gửi cảnh báo tự động qua Slack/Email khi phát hiện lượng truy cập bất thường hoặc tỷ lệ lỗi 403 (unauthorized access) tăng đột biến.