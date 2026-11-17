"""
Application: app.py
Máy chủ Web & API Trung tâm Điều hành AI Agent Đánh giá Yêu cầu Chào giá - Thiên Minh Networks
Sử dụng thư viện chuẩn của Python (http.server), hoàn toàn độc lập không cần cài thêm package bên ngoài.
"""

import os
import sys
import json
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import re

from backend.parsers import parse_docx, parse_csv, parse_google_sheets, parse_raw_text
from backend.agent_engine import ThienMinhAIAgent
from backend.export_docs import (
    export_requirements_matrix_docx,
    export_official_quotation_docx,
    export_approval_form_docx
)
from backend.gemini_service import gemini_agent

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_path(rel_path):
    if os.path.exists(rel_path):
        return rel_path
    abs_path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(abs_path):
        return abs_path
    return rel_path

agent = ThienMinhAIAgent()

# Bộ nhớ tạm lưu trữ session dự án gần nhất
latest_states = {}
cleaning_sessions = {}

def extract_input_data(content_type, body):
    parsed_data = None
    source_name = 'Tập tin người dùng'
    if 'application/json' in content_type:
        payload = json.loads(body.decode('utf-8'))
        input_type = payload.get('input_type', 'sample')

        if input_type == 'sample':
            sample_id = payload.get('sample_id', 'alpha')
            if sample_id == 'alpha':
                parsed_data = parse_docx(get_file_path('data/sample_rfqs/RFQ_01_Alpha_LAN_WiFi.docx'))
                source_name = 'AlphaTech VN (Mẫu Chuẩn)'
            elif sample_id == 'vietfin':
                parsed_data = parse_docx(get_file_path('data/sample_rfqs/RFQ_02_VietFin_Bank.docx'))
                source_name = 'VietFin Bank (Mẫu Chuyển Duyệt)'
            elif sample_id == 'ankhang':
                parsed_data = parse_docx(get_file_path('data/sample_rfqs/RFQ_03_BenhVien_AnKhang.docx'))
                source_name = 'BV An Khang (Mẫu Đề Xuất Loại)'
        elif input_type == 'google_sheets':
            url = payload.get('url', '')
            parsed_data = parse_google_sheets(url)
            source_name = 'Google Sheets Trực Tuyến'
        elif input_type == 'raw_text':
            text = payload.get('text', '')
            parsed_data = parse_raw_text(text)
            source_name = 'Văn bản nhập trực tiếp'
        elif input_type == 'csv_data':
            csv_text = payload.get('csv_text', '')
            parsed_data = parse_csv(csv_text)
            source_name = 'Dữ liệu CSV'

    elif 'multipart/form-data' in content_type:
        boundary = content_type.split('boundary=')[1].encode('utf-8')
        parts = body.split(boundary)
        file_bytes = None
        file_name = ''
        for part in parts:
            if b'filename="' in part:
                header_end = part.find(b'\r\n\r\n')
                header_part = part[:header_end].decode('utf-8', errors='ignore')
                file_bytes = part[header_end + 4:-2]
                fn_match = re.search(r'filename="([^"]+)"', header_part)
                if fn_match:
                    file_name = fn_match.group(1)
                break

        if file_bytes:
            source_name = file_name or 'Tệp tải lên'
            if file_name.lower().endswith('.docx'):
                parsed_data = parse_docx(file_bytes)
            elif file_name.lower().endswith('.csv'):
                parsed_data = parse_csv(file_bytes)
            else:
                try:
                    parsed_data = parse_docx(file_bytes)
                except Exception:
                    parsed_data = parse_csv(file_bytes)

    return parsed_data, source_name

class ThienMinhRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Hỗ trợ CORS nếu gọi từ giao diện khác
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_static(self, file_path):
        if not os.path.exists(file_path):
            self.send_error(404, 'File Not Found')
            return
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        with open(file_path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', f'{mime_type}; charset=utf-8' if 'text' in mime_type or 'html' in mime_type or 'javascript' in mime_type else mime_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. API: Solution Catalog
        if path == '/api/catalog':
            catalog_list = agent.catalog_df.to_dict(orient='records')
            self.send_json({'catalog': catalog_list})
            return

        # 2. API: Policies & Schedule
        elif path == '/api/policies':
            self.send_json(agent.policies)
            return

        # 3. API: Danh sách mẫu có sẵn
        elif path == '/api/sample-files':
            samples = [
                {
                    'id': 'alpha',
                    'name': 'Dự án AlphaTech (LAN & Wi-Fi 6 Văn phòng)',
                    'type': 'Chuẩn mực 100% - Đạt chuẩn ngay',
                    'tag': 'PASS_READY',
                    'file': 'data/sample_rfqs/RFQ_01_Alpha_LAN_WiFi.docx',
                    'description': 'Nâng cấp mạng văn phòng 5 tầng, 200 user, ngân sách 450M, chiết khấu 6%, đủ danh mục.'
                },
                {
                    'id': 'vietfin',
                    'name': 'Dự án Ngân hàng VietFin (Core & An ninh DC)',
                    'type': 'Phải Chuyển duyệt & Xác minh trước',
                    'tag': 'NEEDS_ESCALATION',
                    'file': 'data/sample_rfqs/RFQ_02_VietFin_Bank.docx',
                    'description': 'Core L3 10G, Firewall HA, Thiết bị DDoS ngoài danh mục, chiết khấu 14%, lịch gấp 15 ngày.'
                },
                {
                    'id': 'ankhang',
                    'name': 'Dự án Bệnh viện An Khang (Yêu cầu phi thực tế)',
                    'type': 'Đề xuất Loại bỏ (Thua lỗ/Bất khả thi)',
                    'tag': 'RECOMMEND_REJECT',
                    'file': 'data/sample_rfqs/RFQ_03_BenhVien_AnKhang.docx',
                    'description': 'Đòi hỏi cấu hình > 1 tỷ nhưng ngân sách chỉ 50M (chỉ đạt 12% giá vốn), lịch gấp 3 ngày.'
                }
            ]
            self.send_json({'samples': samples})
            return

        # 4. API: Tải file xuất DOCX
        elif path.startswith('/api/download/'):
            doc_type = path.replace('/api/download/', '')
            rfq_code = query.get('rfq_code', ['latest'])[0]
            target_state = latest_states.get(rfq_code) or (list(latest_states.values())[-1] if latest_states else None)

            if not target_state:
                self.send_json({'error': 'Chưa có dữ liệu dự án tương ứng để xuất file.'}, 404)
                return

            import tempfile
            export_dir = '/tmp/exports' if os.environ.get('VERCEL') else (os.path.join(tempfile.gettempdir(), 'exports') if not os.access('.', os.W_OK) else get_file_path('exports'))
            try:
                os.makedirs(export_dir, exist_ok=True)
            except Exception:
                export_dir = tempfile.gettempdir()

            out_file = None
            filename = f"{doc_type}_{target_state['receipt_classification']['rfq_code']}.docx"

            if doc_type == 'requirements_matrix':
                out_file = os.path.join(export_dir, f"Matrix_{target_state['receipt_classification']['rfq_code']}.docx")
                export_requirements_matrix_docx(target_state, out_file)
            elif doc_type == 'official_quotation':
                out_file = os.path.join(export_dir, f"Quotation_{target_state['receipt_classification']['rfq_code']}.docx")
                export_official_quotation_docx(target_state, out_file)
            elif doc_type == 'approval_form':
                out_file = os.path.join(export_dir, f"Approval_{target_state['receipt_classification']['rfq_code']}.docx")
                export_approval_form_docx(target_state, out_file)
            
            if out_file and os.path.exists(out_file):
                with open(out_file, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                self.send_json({'error': 'Không thể tạo file báo cáo yêu cầu.'}, 400)
                return

        # 5. Phục vụ giao diện tĩnh
        elif path == '/' or path == '/index.html':
            self.serve_static('static/index.html')
            return
        elif path.startswith('/static/'):
            self.serve_static(path.lstrip('/'))
            return
        else:
            self.send_json({'error': 'Endpoint not found'}, 404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type', '')

        body = self.rfile.read(content_length)

        # 1. API: Bước 1 -> Bước 2: Tiếp nhận tệp và Làm sạch dữ liệu (Data Cleaning & Canonical Staging)
        if path == '/api/clean-data':
            try:
                parsed_data, source_name = extract_input_data(content_type, body)
                if not parsed_data:
                    self.send_json({'error': 'Không nhận diện được nội dung hoặc định dạng tập tin đầu vào.', 'return_to_step': 1}, 400)
                    return

                # Phase 1: Phân loại & đăng ký hồ sơ
                phase1 = agent.phase1_receipt_and_classification(parsed_data)
                rfq_code = phase1['rfq_code']

                # Phase 2a: Trích xuất thông tin
                phase2a = agent.phase2a_extract_information(parsed_data, phase1)
                items = phase2a.get('extracted_items', [])

                # Kiểm tra tính toàn vẹn (Validation & Error Check)
                errors = []
                warnings = []
                if not items or len(items) == 0:
                    errors.append('Không tìm thấy bất kỳ dòng hạng mục thiết bị nào trong tệp. Vui lòng kiểm tra lại định dạng bảng.')

                cleaned_items = []
                for idx, it in enumerate(items):
                    stt = str(it.get('stt') or (idx + 1)).strip()
                    name = str(it.get('item_name') or '').strip()
                    qty = it.get('quantity', 0)
                    unit = str(it.get('unit') or 'Bộ').strip()
                    specs = str(it.get('specs') or '').strip()

                    row_errors = []
                    if not name:
                        row_errors.append(f'Dòng {stt}: Tên thiết bị không được để trống.')
                    try:
                        qty_num = int(qty)
                        if qty_num <= 0:
                            row_errors.append(f'Dòng {stt} ({name}): Số lượng phải lớn hơn 0 (hiện là {qty}).')
                    except Exception:
                        row_errors.append(f'Dòng {stt} ({name}): Số lượng không hợp lệ ({qty}).')

                    if not specs:
                        warnings.append(f'Dòng {stt} ({name}): Thiếu thông số kỹ thuật chi tiết.')

                    cleaned_items.append({
                        'stt': stt,
                        'item_name': name,
                        'quantity': qty,
                        'unit': unit,
                        'specs': specs,
                        'has_error': len(row_errors) > 0,
                        'error_msg': ' · '.join(row_errors) if row_errors else ''
                    })
                    errors.extend(row_errors)

                phase2a['extracted_items'] = cleaned_items

                # Lưu vào cleaning_sessions
                cleaning_sessions[rfq_code] = {
                    'phase1': phase1,
                    'phase2a': phase2a,
                    'parsed_data': parsed_data,
                    'source_name': source_name
                }

                self.send_json({
                    'success': True,
                    'rfq_code': rfq_code,
                    'customer_name': phase1['customer_name'],
                    'project_type': phase1['project_type'],
                    'source_name': source_name,
                    'phase1': phase1,
                    'phase2a': phase2a,
                    'items': cleaned_items,
                    'validation': {
                        'is_valid': len(errors) == 0,
                        'error_count': len(errors),
                        'errors': errors,
                        'warning_count': len(warnings),
                        'warnings': warnings,
                        'total_items': len(cleaned_items)
                    }
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({'error': f"Lỗi làm sạch dữ liệu: {str(e)}", 'return_to_step': 1}, 500)
            return

        # 2. API: Bước 2 -> Bước 3: Chạy Phân Tích AI 4 Cấp Độ từ Bảng Đã Làm Sạch
        elif path == '/api/run-analysis':
            try:
                payload = json.loads(body.decode('utf-8'))
                rfq_code = payload.get('rfq_code')
                updated_items = payload.get('items')

                session = cleaning_sessions.get(rfq_code)
                if not session:
                    if rfq_code in latest_states:
                        self.send_json({
                            'success': True,
                            'message': 'Đã hoàn tất phân tích.',
                            'state': latest_states[rfq_code]
                        })
                        return
                    self.send_json({'error': f'Không tìm thấy phiên làm việc {rfq_code}. Vui lòng nạp tệp lại từ Bước 1.', 'return_to_step': 1}, 404)
                    return

                phase1 = session['phase1']
                phase2a = session['phase2a']

                if updated_items:
                    clean_list = []
                    for it in updated_items:
                        qty = 1
                        try:
                            qty = int(it.get('quantity', 1))
                        except Exception:
                            qty = 1
                        clean_list.append({
                            'stt': str(it.get('stt', len(clean_list)+1)),
                            'item_name': str(it.get('item_name', '')),
                            'quantity': qty,
                            'unit': str(it.get('unit', 'Bộ')),
                            'specs': str(it.get('specs', 'Tiêu chuẩn'))
                        })
                    phase2a['extracted_items'] = clean_list

                # Chạy các pha tiếp theo của AI Agent (2b Khớp catalog, 2c Tính giá, 2d Tạo ma trận)
                phase2b = agent.phase2b_match_solution_and_capability(phase2a, phase1)
                phase2c = agent.phase2c_price_and_discount(phase2a, phase2b)
                phase2d = agent.phase2d_generate_draft_output(phase1, phase2a, phase2b, phase2c)

                result_state = {
                    'receipt_classification': phase1,
                    'information_extraction': phase2a,
                    'solution_match': phase2b,
                    'price_and_discount': phase2c,
                    'draft_output': phase2d,
                    'human_decision': None,
                    'final_quotation': None,
                    'current_phase': 3 if phase2d['next_phase'] == 3 else 4
                }

                if phase2d['recommendation_code'] == 'PASS_READY':
                    result_state['human_decision'] = {
                        'phase': 3,
                        'phase_name': 'Kiểm tra của Con người (Tự động thông qua)',
                        'decision_type': 'APPROVE_SCHEME',
                        'decision_status': 'PHÙ HỢP & HỢP LỆ (PASS)',
                        'reviewer_name': 'Trần Nam - Trưởng phòng Kinh doanh',
                        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'notes': 'Hồ sơ chuẩn 100%, không có điều kiện bất thường. Tự động chuyển hoàn thiện bản chào giá.',
                        'message': 'Đã hoàn tất kiểm tra và chuyển tiếp sang Phase 4.',
                        'is_approved': True,
                        'is_rejected': False,
                        'next_step': 'Phase 4: Hoàn thiện Báo giá'
                    }
                    result_state['final_quotation'] = agent.phase4_finalize_quotation(result_state)

                latest_states[rfq_code] = result_state

                self.send_json({
                    'success': True,
                    'message': 'Đã hoàn thành phân tích AI 4 cấp độ.',
                    'state': result_state
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({'error': f"Lỗi phân tích AI: {str(e)}"}, 500)
            return

        # 3. API: Tiếp nhận hồ sơ và chạy Pipeline toàn diện một chạm
        elif path == '/api/upload-and-analyze':
            try:
                parsed_data, source_name = extract_input_data(content_type, body)
                if not parsed_data:
                    self.send_json({'error': 'Không nhận diện được nội dung hoặc định dạng tập tin đầu vào.'}, 400)
                    return

                # Chạy quy trình AI Agent tự động
                result_state = agent.run_automated_pipeline(parsed_data)
                rfq_code = result_state['receipt_classification']['rfq_code']
                latest_states[rfq_code] = result_state

                # Cũng lưu vào cleaning_sessions để hỗ trợ sửa bước 2
                cleaning_sessions[rfq_code] = {
                    'phase1': result_state['receipt_classification'],
                    'phase2a': result_state['information_extraction'],
                    'parsed_data': parsed_data,
                    'source_name': source_name
                }

                self.send_json({
                    'success': True,
                    'message': 'Đã hoàn thành phân tích tự động bởi AI Agent Thiên Minh Networks.',
                    'source_name': source_name,
                    'state': result_state
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({'error': f"Lỗi xử lý: {str(e)}"}, 500)
            return

        # 2. API: Quyết định Kiểm tra của Con người (Phase 3 Checkpoint Decision)
        elif path == '/api/human-decision':
            try:
                payload = json.loads(body.decode('utf-8'))
                rfq_code = payload.get('rfq_code')
                decision_data = payload.get('decision_data', {})
                
                target_state = latest_states.get(rfq_code)
                if not target_state:
                    self.send_json({'error': f'Không tìm thấy phiên làm việc cho mã {rfq_code}'}, 404)
                    return

                # Xử lý quyết định của con người
                decision_record = agent.phase3_human_decision(target_state, decision_data)
                target_state['human_decision'] = decision_record

                # Nếu được duyệt (Approve Scheme hoặc Hội đồng thông qua ngoại lệ) -> Chuyển sang Phase 4
                if decision_record['is_approved']:
                    final_quotation = agent.phase4_finalize_quotation(target_state)
                    target_state['final_quotation'] = final_quotation
                    target_state['current_phase'] = 4
                elif decision_record['is_rejected']:
                    target_state['current_phase'] = 3
                elif decision_data.get('decision_type') == 'REQUEST_ADJUSTMENT':
                    # Nếu yêu cầu hiệu chỉnh tỷ lệ chiết khấu hoặc ghi chú:
                    new_discount = decision_data.get('adjusted_discount')
                    if new_discount is not None:
                        target_state['information_extraction']['requested_discount_pct'] = float(new_discount)
                        # Tái tính toán
                        re_price = agent.phase2c_price_and_discount(
                            target_state['information_extraction'],
                            target_state['solution_match']
                        )
                        target_state['price_and_discount'] = re_price
                        re_draft = agent.phase2d_generate_draft_output(
                            target_state['receipt_classification'],
                            target_state['information_extraction'],
                            target_state['solution_match'],
                            re_price
                        )
                        target_state['draft_output'] = re_draft

                latest_states[rfq_code] = target_state
                self.send_json({
                    'success': True,
                    'message': decision_record['message'],
                    'state': target_state
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({'error': f"Lỗi xử lý quyết định: {str(e)}"}, 500)
            return

        # 3. API: Gemini AI Chat Assistant (Hỏi đáp thông minh về hồ sơ chào giá)
        elif path == '/api/gemini-chat':
            try:
                payload = json.loads(body.decode('utf-8'))
                message = payload.get('message', '')
                rfq_code = payload.get('rfq_code', '')
                target_state = latest_states.get(rfq_code) or (list(latest_states.values())[-1] if latest_states else {})

                reply = gemini_agent.chat_about_project(message, target_state)
                self.send_json({
                    'success': True,
                    'reply': reply
                })
            except Exception as e:
                self.send_json({'error': f"Lỗi Gemini Chat: {str(e)}"}, 500)
            return

        # 4. API: Gemini Deep Analysis (Phân tích chuyên sâu bởi Gemini 3.5 Flash)
        elif path == '/api/gemini-deep-analysis':
            try:
                payload = json.loads(body.decode('utf-8'))
                rfq_code = payload.get('rfq_code', '')
                target_state = latest_states.get(rfq_code) or (list(latest_states.values())[-1] if latest_states else {})
                
                rfq_text = json.dumps(target_state.get('information_extraction', {}), ensure_ascii=False)
                catalog_summary = agent.catalog_df[['product_name', 'specs', 'unit_price']].to_string() if not agent.catalog_df.empty else ""

                analysis_result = gemini_agent.analyze_rfq_deep(rfq_text, catalog_summary)
                self.send_json({
                    'success': True,
                    'analysis': analysis_result
                })
            except Exception as e:
                self.send_json({'error': f"Lỗi Gemini Deep Analysis: {str(e)}"}, 500)
            return

        else:
            self.send_json({'error': 'Endpoint not found'}, 404)

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ThienMinhRequestHandler)
    print(f"================================================================", flush=True)
    print(f" Thiên Minh Networks AI Agent Server đang hoạt động tại cổng {PORT}", flush=True)
    print(f" URL: http://localhost:{PORT}", flush=True)
    print(f"================================================================", flush=True)
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()

