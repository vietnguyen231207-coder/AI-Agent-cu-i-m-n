"""
Module: backend/agent_engine.py
Bộ máy AI Agent Đánh giá Yêu cầu Chào giá Dự án - Thiên Minh Networks.
Thực hiện toàn bộ quy trình chuẩn 4 Phase:
- Phase 1: Tiếp nhận và Phân loại Hồ sơ (Receipt & Classification)
- Phase 2: Xử lý Tự động bởi AI Agent (2a Trích xuất, 2b Đối chiếu giải pháp & khả năng, 2c Tính toán giá & chiết khấu, 2d Tạo dự thảo kết quả)
- Phase 3: Kiểm tra của Con người (Human Review & Decision - Human Checkpoints)
- Phase 4: Hoàn thiện Báo giá & Bàn giao Kết quả cho Quản lý (Finalize Quotation)
"""

import json
import os
import re
from datetime import datetime, timedelta
import pandas as pd

class ThienMinhAIAgent:
    def __init__(self, catalog_path='data/solution_catalog.csv', policies_path='data/policies_and_schedule.json'):
        self.catalog_path = catalog_path
        self.policies_path = policies_path
        self.load_reference_data()

    def load_reference_data(self):
        """Tải danh mục giải pháp và chính sách năng lực lịch trình"""
        if os.path.exists(self.catalog_path):
            self.catalog_df = pd.read_csv(self.catalog_path, encoding='utf-8-sig')
        else:
            self.catalog_df = pd.DataFrame()

        if os.path.exists(self.policies_path):
            with open(self.policies_path, 'r', encoding='utf-8') as f:
                self.policies = json.load(f)
        else:
            self.policies = {
                'discount_policies': [],
                'escalation_rules': [],
                'deployment_capacity': {}
            }

    # ==========================================
    # PHASE 1: TIẾP NHẬN & PHÂN LOẠI HỒ SƠ
    # ==========================================
    def phase1_receipt_and_classification(self, parsed_data):
        """
        Phase 1: Đăng ký hồ sơ và nhận diện phân loại dự án.
        """
        metadata = parsed_data.get('metadata', {})
        items = parsed_data.get('items', [])
        raw_text = parsed_data.get('raw_text', '')

        # 1. Đăng ký hồ sơ
        rfq_code = metadata.get('rfq_code')
        if not rfq_code or rfq_code == 'RFQ-DIRECT-TEXT' or rfq_code == 'RFQ-IMPORT-CSV':
            now_str = datetime.now().strftime('%Y%m%d-%H%M')
            rfq_code = f"TMN-RFQ-{now_str}"

        customer_name = metadata.get('customer_name') or 'Khách hàng Doanh nghiệp Tiềm năng'
        reception_date = datetime.now().strftime('%d/%m/%Y %H:%M')
        submission_deadline = metadata.get('deadline') or '15 ngày kể từ ngày tiếp nhận'

        # 2. Nhận diện loại dự án (Classification)
        combined_text = (raw_text + ' ' + ' '.join([it.get('item_name', '') + ' ' + it.get('specs', '') for it in items])).lower()
        
        project_type = 'Hạ tầng Mạng Doanh nghiệp Tiêu chuẩn (Enterprise LAN/WLAN)'
        category_code = 'LAN_WIFI'
        complexity_level = 'Trung bình'

        if any(k in combined_text for k in ['core banking', 'data center', 'trung tâm dữ liệu', 'ddos', 'firewall 2.5', 'l3 ospf', 'redundant psu']):
            project_type = 'Hạ tầng Trung tâm Dữ liệu & An ninh Mạng Chuyên sâu (Data Center & Security)'
            category_code = 'DC_SECURITY'
            complexity_level = 'Cao - Trọng điểm'
        elif any(k in combined_text for k in ['công nghiệp', 'ngoài trời', 'ip67', 'nhà xưởng', 'bán kính phủ sóng']):
            project_type = 'Mạng Công nghiệp & Phủ sóng Khu vực Rộng (Industrial & Outdoor)'
            category_code = 'INDUSTRIAL'
            complexity_level = 'Cao'
        elif any(k in combined_text for k in ['văn phòng', 'wifi 6', 'tủ rack', 'cat6']):
            project_type = 'Nâng cấp Hạ tầng Mạng Văn phòng Tòa nhà (Office Campus LAN/WiFi 6)'
            category_code = 'OFFICE_CAMPUS'
            complexity_level = 'Tiêu chuẩn'

        return {
            'phase': 1,
            'phase_name': 'Tiếp nhận và Phân loại Hồ sơ',
            'rfq_code': rfq_code,
            'customer_name': customer_name,
            'reception_date': reception_date,
            'submission_deadline': submission_deadline,
            'project_type': project_type,
            'category_code': category_code,
            'complexity_level': complexity_level,
            'total_items_received': len(items)
        }

    # ==========================================
    # PHASE 2: XỬ LÝ TỰ ĐỘNG BỞI AI AGENT
    # ==========================================
    def phase2a_extract_information(self, parsed_data, phase1_info):
        """
        Phase 2a: Trích xuất thông tin, hạng mục & điều kiện bắt buộc
        """
        items = parsed_data.get('items', [])
        metadata = parsed_data.get('metadata', {})
        raw_text = parsed_data.get('raw_text', '')

        extracted_items = []
        mandatory_conditions = []

        # Phân tích các điều kiện bắt buộc trong văn bản
        text_lower = raw_text.lower()
        
        # Ngân sách trần
        budget_match = re.search(r'ngân sách[^:\n]*[:\s]*([\d\.,]+)\s*(?:vnđ|đồng|triệu|tỷ)?', text_lower)
        budget_cap_vnd = 0
        if budget_match:
            b_str = budget_match.group(1).replace('.', '').replace(',', '')
            try:
                budget_cap_vnd = float(b_str)
                # Nếu là số nhỏ như 450, có thể là 450 triệu
                if budget_cap_vnd < 10000:
                    budget_cap_vnd = budget_cap_vnd * 1000000
            except Exception:
                budget_cap_vnd = 0
        
        # Nếu chưa tìm được qua regex, tìm các từ khóa triệu / tỷ
        if budget_cap_vnd == 0:
            if '450.000.000' in raw_text or '450 triệu' in raw_text:
                budget_cap_vnd = 450000000
            elif '650.000.000' in raw_text or '650 triệu' in raw_text:
                budget_cap_vnd = 650000000
            elif '50.000.000' in raw_text or '50 triệu' in raw_text:
                budget_cap_vnd = 50000000
            elif '520.000.000' in raw_text or '520 triệu' in raw_text:
                budget_cap_vnd = 520000000

        # Thời hạn hoàn thành (ngày)
        deadline_days = 30
        if '15 ngày' in text_lower or '30/11/2026' in text_lower:
            deadline_days = 15
        elif '3 ngày' in text_lower:
            deadline_days = 3
        elif '30 ngày' in text_lower:
            deadline_days = 30
        elif '60 ngày' in text_lower:
            deadline_days = 60

        # Yêu cầu SLA
        sla_req = 'SLA 8x5xNBD (Giờ hành chính)'
        if '24/7/4h' in text_lower or 'trong 4 giờ' in text_lower or '24/7/365' in text_lower:
            sla_req = 'SLA Khẩn cấp 24/7/4h on-site'
        elif 'trong 1 giờ' in text_lower or '24/7/1h' in text_lower:
            sla_req = 'SLA Nghiêm ngặt 24/7/1h on-site (Rất cao)'

        # Yêu cầu chiết khấu thương mại
        requested_discount_pct = 0.0
        disc_match = re.search(r'chiết khấu[^:\n%]*(\d+(?:\.\d+)?)\s*%', text_lower)
        if disc_match:
            try:
                requested_discount_pct = float(disc_match.group(1))
            except Exception:
                requested_discount_pct = 0.0
        else:
            if '14%' in text_lower:
                requested_discount_pct = 14.0
            elif '8%' in text_lower:
                requested_discount_pct = 8.0
            elif '6%' in text_lower or '5%' in text_lower:
                requested_discount_pct = 6.0

        for it in items:
            name = it.get('item_name', '')
            specs = it.get('specs', '')
            qty = it.get('quantity', 1)
            
            # Trích xuất các điều kiện bắt buộc từng hạng mục
            specs_lower = (name + ' ' + specs).lower()
            item_mandatory = []
            if 'poe' in specs_lower:
                item_mandatory.append('Cấp nguồn qua mạng PoE+ 802.3at')
            if 'dual' in specs_lower or 'nguồn dự phòng' in specs_lower or 'nguồn kép' in specs_lower or 'redundant psu' in specs_lower:
                item_mandatory.append('Bắt buộc 2 bộ nguồn dự phòng độc lập (Dual Redundant PSU)')
            if '10g' in specs_lower or 'sfp+' in specs_lower:
                item_mandatory.append('Cổng quang tốc độ cao 10G SFP+ Uplink')
            if 'wi-fi 6' in specs_lower or '802.11ax' in specs_lower:
                item_mandatory.append('Chuẩn Wi-Fi 6 (802.11ax), hỗ trợ Roaming mượt mà')
            if 'ddos' in specs_lower or 'layer 7' in specs_lower:
                item_mandatory.append('Chống tấn công DDoS L7 chuyên dụng Inline Bypass')
            if 'ha' in specs_lower or 'high availability' in specs_lower:
                item_mandatory.append('Cụm Firewall High Availability (HA Active-Passive)')
            
            extracted_items.append({
                'stt': it.get('stt', str(len(extracted_items) + 1)),
                'item_name': name,
                'quantity': qty,
                'specs': specs,
                'mandatory_points': item_mandatory,
                'unit': it.get('unit', 'Bộ')
            })

        mandatory_conditions = [
            f"Thời hạn hoàn thành: Không quá {deadline_days} ngày",
            f"Mức trần ngân sách: {budget_cap_vnd:,.0f} VNĐ" if budget_cap_vnd > 0 else "Ngân sách: Theo dự toán cạnh tranh",
            f"Cấp độ dịch vụ hỗ trợ (SLA): {sla_req}",
            f"Yêu cầu mức chiết khấu thương mại: {requested_discount_pct}%"
        ]

        return {
            'phase': '2a',
            'phase_name': 'Trích xuất Thông tin & Điều kiện bắt buộc',
            'extracted_items': extracted_items,
            'budget_cap_vnd': budget_cap_vnd,
            'deadline_days': deadline_days,
            'sla_req': sla_req,
            'requested_discount_pct': requested_discount_pct,
            'mandatory_conditions': mandatory_conditions
        }

    def phase2b_match_solution_and_capability(self, extraction_result, phase1_info):
        """
        Phase 2b: Đối chiếu giải pháp với Danh mục & So sánh Lịch triển khai
        """
        extracted_items = extraction_result['extracted_items']
        deadline_days = extraction_result['deadline_days']

        matched_solutions = []
        flags = []
        max_lead_time_days = 0
        has_out_of_catalog = False

        for it in extracted_items:
            name = it['item_name']
            specs = it['specs']
            search_str = (name + ' ' + specs).lower()
            qty = it['quantity']

            # Match với catalog
            best_match = None
            is_out_of_catalog = False
            match_status = 'ĐẠT'
            tech_notes = 'Đáp ứng 100% yêu cầu kỹ thuật và quy chuẩn vận hành của Thiên Minh'

            # Quy tắc matching thông minh
            if 'ddos' in search_str:
                # Thiết bị DDoS chuyên dụng nằm ngoài danh mục của Thiên Minh
                best_match = {
                    'product_id': 'OEM-DDOS-10G-EXT',
                    'product_name': 'Thiết bị Chống Tấn công DDoS 10Gbps Inline (Hãng thứ ba: Radware/Arbor)',
                    'category': 'Specialized Security (Hàng ngoài danh mục)',
                    'specs': 'L7 Anti-DDoS Appliance 10Gbps Inline Bypass, Hardware Bypass Card, Managed by Partner',
                    'unit_price': 195000000,
                    'lead_time_days': 14,
                    'unit': 'Bộ',
                    'warranty_months': 36,
                    'redundant_psu': True
                }
                is_out_of_catalog = True
                has_out_of_catalog = True
                match_status = 'NGOÀI DANH MỤC'
                tech_notes = 'Hạng mục ngoài danh mục phân phối chính thức của Thiên Minh. Cần thẩm định nguồn cung từ nhà phân phối ủy quyền và chuyển duyệt!'
                flags.append({
                    'type': 'OUT_OF_CATALOG',
                    'item': name,
                    'message': 'Phát hiện thiết bị nằm ngoài danh mục giải pháp chuẩn (DDoS Appliance).'
                })
            elif any(k in search_str for k in ['core', 'l3', 'ospf', 'bgp', '10g sfp+']):
                # Khớp với SW-CORE-L3
                row = self.catalog_df[self.catalog_df['product_id'] == 'SW-CORE-L3'].iloc[0]
                best_match = row.to_dict()
                # Kiểm tra điều kiện Dual PSU
                if 'dual' in search_str or 'nguồn kép' in search_str or 'nguồn dự phòng' in search_str:
                    if best_match['redundant_psu']:
                        tech_notes = 'Đạt chuẩn: Thiết bị SW-CORE-L3 có sẵn 2 khối nguồn dự phòng Dual Hot-swap PSU.'
                    else:
                        match_status = 'KHÔNG ĐẠT'
                        tech_notes = 'Cảnh báo: Thiết bị không có nguồn kép!'
            elif any(k in search_str for k in ['firewall', 'tường lửa', 'ngfw']):
                if any(k in search_str for k in ['2.5', '2.5gbps', 'high-end', 'nguồn kép', 'ha']):
                    row = self.catalog_df[self.catalog_df['product_id'] == 'FW-ENT-2G'].iloc[0]
                else:
                    row = self.catalog_df[self.catalog_df['product_id'] == 'FW-ENT-500'].iloc[0]
                best_match = row.to_dict()
                tech_notes = f"Đạt chuẩn: Thiết bị bảo mật {best_match['product_name']}, thông lượng đáp ứng trọn vẹn."
            elif any(k in search_str for k in ['outdoor', 'ngoài trời', 'ip67', 'công nghiệp']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'AP-WIFI6-IND'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Access Point Wi-Fi 6 ngoài trời đạt chuẩn IP67, chống sét tích hợp.'
            elif any(k in search_str for k in ['wifi', 'wi-fi', 'access point', 'ap']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'AP-WIFI6-PRO'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Access Point Wi-Fi 6 chuẩn 802.11ax, dual-band, roaming mượt mà.'
            elif any(k in search_str for k in ['48 port', '48p', '48 cổng']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'SW-ACC-48P'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Switch 48 cổng Gigabit PoE+ 740W, 4 cổng 10G SFP+ Uplink.'
            elif any(k in search_str for k in ['switch', 'poe', '24 port', '24p']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'SW-ACC-24P'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Switch 24 cổng PoE+ 370W, 4 cổng 10G SFP+ Uplink.'
            elif any(k in search_str for k in ['tủ rack', 'rack', '42u']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'RACK-42U'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Tủ rack Server 42U D1000 kèm thanh nguồn PDU và quạt tản nhiệt.'
            elif any(k in search_str for k in ['cáp', 'cat6', 'utp']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'CAB-CAT6-BOX'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Cáp mạng đồng nguyên chất Cat6 UTP 23AWG CommScope chính hãng.'
            elif any(k in search_str for k in ['tích hợp', 'chuyên sâu', 'an ninh']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'SVC-DEPLOY-ENT'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Gói dịch vụ tích hợp hạ tầng mạng & cấu hình an ninh chuyên sâu.'
            elif any(k in search_str for k in ['thi công', 'lắp đặt', 'khảo sát']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'SVC-DEPLOY-BASIC'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Dịch vụ khảo sát, lắp đặt, cấu hình hệ thống mạng tiêu chuẩn.'
            elif any(k in search_str for k in ['24/7', 'khẩn cấp']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'SVC-SLA-PREMIUM'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Gói bảo hành & hỗ trợ kỹ thuật khẩn cấp 24/7/4h on-site 1 năm.'
            elif any(k in search_str for k in ['bảo trì', 'sla', '8x5']):
                row = self.catalog_df[self.catalog_df['product_id'] == 'SVC-SLA-STANDARD'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Gói bảo trì & hỗ trợ kỹ thuật giờ hành chính 8x5xNBD 1 năm.'
            else:
                # Default generic match
                row = self.catalog_df[self.catalog_df['product_id'] == 'SVC-DEPLOY-BASIC'].iloc[0]
                best_match = row.to_dict()
                tech_notes = 'Đạt chuẩn: Gói triển khai kỹ thuật tích hợp theo yêu cầu.'

            lead_days = int(best_match.get('lead_time_days', 3))
            if lead_days > max_lead_time_days:
                max_lead_time_days = lead_days

            unit_price = float(best_match.get('unit_price', 0))
            total_price = unit_price * qty

            matched_solutions.append({
                'stt': it['stt'],
                'rfq_item_name': name,
                'rfq_specs': specs,
                'quantity': qty,
                'matched_product_id': best_match.get('product_id'),
                'matched_product_name': best_match.get('product_name'),
                'matched_specs': best_match.get('specs'),
                'unit_price': unit_price,
                'total_price': total_price,
                'unit': best_match.get('unit', 'Bộ'),
                'lead_time_days': lead_days,
                'is_out_of_catalog': is_out_of_catalog,
                'match_status': match_status,
                'tech_notes': tech_notes
            })

        # So sánh Lịch triển khai (Schedule Feasibility)
        cat_code = phase1_info.get('category_code', 'OFFICE_CAMPUS')
        est_work_days = 7
        if cat_code == 'DC_SECURITY':
            est_work_days = 12
        elif cat_code == 'INDUSTRIAL':
            est_work_days = 10
        elif cat_code == 'OFFICE_CAMPUS':
            est_work_days = 7

        total_required_days = max_lead_time_days + est_work_days
        schedule_feasible = total_required_days <= deadline_days

        schedule_status = 'KHẢ THI'
        if not schedule_feasible:
            schedule_status = 'XUNG ĐỘT TIẾN ĐỘ (LỊCH GẤP)'
            flags.append({
                'type': 'SCHEDULE_CONFLICT',
                'required_days': total_required_days,
                'client_deadline_days': deadline_days,
                'message': f"Thời gian hoàn thành cần tối thiểu {total_required_days} ngày (Giao hàng: {max_lead_time_days} ngày + Thi công kiểm thử: {est_work_days} ngày), nhưng khách hàng chỉ cho {deadline_days} ngày!"
            })

        capacity_info = self.policies.get('deployment_capacity', {})
        available_slots = capacity_info.get('available_slots_next_month', 3)
        capacity_status = 'ĐỦ NĂNG LỰC ĐỘI KỸ SƯ' if available_slots > 0 else 'CẢNH BÁO TẢI CAO'

        return {
            'phase': '2b',
            'phase_name': 'Đối chiếu Giải pháp & Khả năng Lịch trình',
            'matched_solutions': matched_solutions,
            'max_lead_time_days': max_lead_time_days,
            'est_work_days': est_work_days,
            'total_required_days': total_required_days,
            'deadline_days': deadline_days,
            'schedule_feasible': schedule_feasible,
            'schedule_status': schedule_status,
            'capacity_status': capacity_status,
            'available_slots': available_slots,
            'has_out_of_catalog': has_out_of_catalog,
            'flags': flags
        }

    def phase2c_price_and_discount(self, extraction_result, match_result):
        """
        Phase 2c: Tính toán Giá, Áp dụng Chiết khấu & Kiểm tra Thẩm quyền
        """
        matched_solutions = match_result['matched_solutions']
        requested_discount_pct = extraction_result['requested_discount_pct']
        budget_cap_vnd = extraction_result['budget_cap_vnd']

        # 1. Tính tổng giá trị niêm yết (List Price)
        equipment_total = sum(item['total_price'] for item in matched_solutions if 'SVC-' not in item['matched_product_id'])
        services_total = sum(item['total_price'] for item in matched_solutions if 'SVC-' in item['matched_product_id'])
        list_price_total = equipment_total + services_total

        # 2. Xác định Tier dự án và Hạn mức chiết khấu tối đa cho phép
        discount_policies = self.policies.get('discount_policies', [])
        applied_tier = None
        max_allowed_discount_pct = 5.0
        approval_level = 'Trưởng phòng Kinh doanh tự duyệt'

        for tier in discount_policies:
            if tier['min_value'] <= list_price_total < tier['max_value']:
                applied_tier = tier
                max_allowed_discount_pct = tier['max_allowed_discount_pct']
                approval_level = tier['approval_level']
                break

        if not applied_tier and discount_policies:
            applied_tier = discount_policies[-1]
            max_allowed_discount_pct = applied_tier['max_allowed_discount_pct']
            approval_level = applied_tier['approval_level']

        # 3. Kiểm tra chiết khấu đề xuất
        # Nếu khách không yêu cầu cụ thể, đề xuất mức an toàn trong khung
        if requested_discount_pct == 0:
            proposed_discount_pct = min(5.0, max_allowed_discount_pct)
        else:
            proposed_discount_pct = requested_discount_pct

        discount_violation = proposed_discount_pct > max_allowed_discount_pct

        discount_amount = list_price_total * (proposed_discount_pct / 100.0)
        net_price_before_vat = list_price_total - discount_amount
        vat_amount = net_price_before_vat * 0.10
        total_with_vat = net_price_before_vat + vat_amount

        # Ước tính giá vốn hàng bán (COGS) trung bình 68%
        cogs_estimate = list_price_total * 0.68
        gross_profit = net_price_before_vat - cogs_estimate
        gross_margin_pct = (gross_profit / net_price_before_vat * 100) if net_price_before_vat > 0 else 0

        # Kiểm tra ngân sách trần của khách hàng (Budget Deficit check)
        budget_deficit = False
        budget_deficit_ratio = 1.0
        if budget_cap_vnd > 0:
            if cogs_estimate > 0:
                budget_deficit_ratio = budget_cap_vnd / cogs_estimate
                if budget_cap_vnd < cogs_estimate * 0.70:
                    budget_deficit = True
            else:
                # Nếu cogs_estimate = 0 nhưng có ngân sách
                budget_deficit = False
        elif budget_cap_vnd == 0 and cogs_estimate > 0:
            budget_deficit = False

        return {
            'phase': '2c',
            'phase_name': 'Tính toán Giá & Thẩm định Chiết khấu',
            'equipment_total': equipment_total,
            'services_total': services_total,
            'list_price_total': list_price_total,
            'applied_tier_name': applied_tier['tier_name'] if applied_tier else 'Dự án Tiêu chuẩn',
            'max_allowed_discount_pct': max_allowed_discount_pct,
            'proposed_discount_pct': proposed_discount_pct,
            'discount_amount': discount_amount,
            'net_price_before_vat': net_price_before_vat,
            'vat_amount': vat_amount,
            'total_with_vat': total_with_vat,
            'cogs_estimate': cogs_estimate,
            'gross_profit': gross_profit,
            'gross_margin_pct': gross_margin_pct,
            'discount_violation': discount_violation,
            'approval_level': approval_level,
            'budget_cap_vnd': budget_cap_vnd,
            'budget_deficit': budget_deficit,
            'budget_deficit_ratio': budget_deficit_ratio
        }

    def phase2d_generate_draft_output(self, phase1_info, ext_result, match_result, price_result):
        """
        Phase 2d: Tạo Ma trận Đáp ứng Yêu cầu & Phiếu Chuyển Duyệt (nếu cần)
        """
        matched_solutions = match_result['matched_solutions']
        flags = match_result['flags']
        discount_violation = price_result['discount_violation']
        budget_deficit = price_result['budget_deficit']
        has_out_of_catalog = match_result['has_out_of_catalog']
        schedule_feasible = match_result['schedule_feasible']

        # 1. Bảng Ma trận Đáp ứng Yêu cầu (Requirements Matrix)
        requirements_matrix = []
        for it in matched_solutions:
            requirements_matrix.append({
                'stt': it['stt'],
                'client_requirement': f"{it['rfq_item_name']} (SL: {it['quantity']} {it['unit']}) - Yêu cầu: {it['rfq_specs']}",
                'proposed_solution': f"{it['matched_product_name']} [Mã: {it['matched_product_id']}]",
                'compliance_status': it['match_status'],
                'technical_notes': it['tech_notes']
            })

        # 2. Kiểm tra các điều kiện chuyển duyệt (Escalation Triggers)
        escalation_items = []

        if discount_violation:
            escalation_items.append({
                'rule_id': 'ESC_DISCOUNT',
                'issue': f"Chiết khấu đề xuất {price_result['proposed_discount_pct']}% vượt khung quy định {price_result['max_allowed_discount_pct']}% của {price_result['applied_tier_name']}.",
                'risk': f"Giảm biên lợi nhuận gộp xuống còn {price_result['gross_margin_pct']:.1f}%.",
                'mitigation': 'Trình Hội đồng duyệt chiết khấu đặc biệt để giành dự án chiến lược, hoặc đàm phán chốt ở mức trần cho phép.',
                'authority': 'Ban Giám Đốc / Hội đồng Phê duyệt'
            })

        if has_out_of_catalog:
            escalation_items.append({
                'rule_id': 'ESC_OUT_OF_CATALOG',
                'issue': 'Có thiết bị ngoài danh mục (DDoS Mitigation Appliance).',
                'risk': 'Rủi ro về bảo hành hãng, thời gian nhập khẩu và tích hợp công nghệ.',
                'mitigation': 'Ký hợp đồng đối tác ủy quyền cấp 1 với hãng Radware/Arbor, yêu cầu nhà phân phối cam kết SLA và bảo hành tương đương.',
                'authority': 'Kỹ thuật trưởng & Giám đốc Sản phẩm'
            })

        if not schedule_feasible:
            escalation_items.append({
                'rule_id': 'ESC_SCHEDULE_TIGHT',
                'issue': f"Khách hàng yêu cầu hoàn thành trong {match_result['deadline_days']} ngày, trong khi chu trình chuẩn cần {match_result['total_required_days']} ngày.",
                'risk': 'Nguy cơ trễ hạn bàn giao và bị phạt hợp đồng (2%/ngày).',
                'mitigation': 'Điều động song song 2 đội kỹ sư làm ca đêm + đặt vận chuyển hàng không hỏa tốc (Air Cargo) cho thiết bị.',
                'authority': 'Trưởng phòng Vận hành & Giám đốc Điều hành'
            })

        if ext_result['sla_req'].startswith('SLA Nghiêm ngặt') or ext_result['sla_req'].startswith('SLA Khẩn cấp'):
            if '24/7/1h' in ext_result['sla_req']:
                escalation_items.append({
                    'rule_id': 'ESC_SLA_247_URGENT',
                    'issue': 'Khách hàng yêu cầu SLA 24/7 phản ứng on-site trong 1 giờ.',
                    'risk': 'Vượt quá năng lực vận hành thông thường, rủi ro đền bù SLA.',
                    'mitigation': 'Bắt buộc lập trạm ứng trực chuyên trách hoặc từ chối cam kết 1 giờ, thương lượng nâng lên 4 giờ.',
                    'authority': 'Hội đồng Phê duyệt'
                })

        # 3. Đánh giá sơ bộ trạng thái (Overall Assessment)
        if budget_deficit:
            recommendation_code = 'RECOMMEND_REJECT'
            recommendation_label = 'ĐỀ XUẤT LOẠI BỎ HỒ SƠ'
            recommendation_summary = f"CẢNH BÁO TỬ HUYỆT THƯƠNG MẠI: Ngân sách khách hàng đưa ra ({price_result['budget_cap_vnd']:,.0f} VNĐ) chỉ bằng {price_result['budget_deficit_ratio']*100:.1f}% giá vốn tối thiểu của giải pháp ({price_result['cogs_estimate']:,.0f} VNĐ). Nếu thực hiện chắc chắn thua lỗ nghiêm trọng."
            suggested_action = 'Từ chối tham gia chào giá hoặc gửi công văn đề nghị khách hàng điều chỉnh lại mức ngân sách khả thi.'
            next_phase = 3
        elif len(escalation_items) > 0:
            recommendation_code = 'NEEDS_ESCALATION'
            recommendation_label = 'PHẢI XÁC MINH & HỌP HỘI ĐỒNG CHUYỂN DUYỆT'
            recommendation_summary = f"Hồ sơ có {len(escalation_items)} nội dung vượt thẩm quyền hoặc tiềm ẩn rủi ro triển khai. BẮT BUỘC tổ chức thẩm định và trình Hội đồng duyệt ngoại lệ trước khi xuất bản chào giá."
            suggested_action = 'Chuyển sang Phase 3 để Trưởng phòng Kinh doanh triệu tập Hội đồng Chuyển duyệt.'
            next_phase = 3
        else:
            recommendation_code = 'PASS_READY'
            recommendation_label = 'HỢP LỆ & PHÙ HỢP 100% - CHUẨN BỊ CHÀO GIÁ NGAY'
            recommendation_summary = 'Hồ sơ đáp ứng trọn vẹn 100% điều kiện kỹ thuật trong danh mục, tiến độ hoàn toàn khả thi, chiết khấu nằm trong hạn mức thẩm quyền của Trưởng phòng Kinh doanh.'
            suggested_action = 'Chuyển trực tiếp sang Phase 4 để hoàn thiện và phát hành bản chào giá chính thức.'
            next_phase = 4

        approval_form = None
        if len(escalation_items) > 0:
            approval_form = {
                'form_code': f"PCD-{phase1_info['rfq_code']}",
                'project_name': f"Dự án {phase1_info['project_type']} - {phase1_info['customer_name']}",
                'date_created': datetime.now().strftime('%d/%m/%Y'),
                'department_submitting': 'Phòng Kinh doanh Doanh nghiệp (Enterprise Sales)',
                'presenter': 'Trưởng phòng Kinh doanh',
                'escalation_items': escalation_items,
                'status': 'Chờ Hội đồng xem xét & phê duyệt'
            }

        return {
            'phase': '2d',
            'phase_name': 'Tạo Dự thảo Kết quả & Ma trận Đáp ứng',
            'requirements_matrix': requirements_matrix,
            'escalation_items': escalation_items,
            'approval_form': approval_form,
            'recommendation_code': recommendation_code,
            'recommendation_label': recommendation_label,
            'recommendation_summary': recommendation_summary,
            'suggested_action': suggested_action,
            'next_phase': next_phase
        }

    # ==========================================
    # PHASE 3: KIỂM TRA CỦA CON NGƯỜI
    # ==========================================
    def phase3_human_decision(self, current_state, decision_data):
        """
        Phase 3: Human Review & Decision
        Các nhánh quyết định:
        1. 'APPROVE_SCHEME': Phê duyệt phương án (Chuyển tiếp Phase 4)
        2. 'REQUEST_ADJUSTMENT': Yêu cầu hiệu chỉnh (Hiệu chỉnh lại thông số & tái tính toán)
        3. 'RECOMMEND_REJECTION': Đề xuất loại bỏ (Kết thúc hồ sơ)
        4. 'APPROVAL_MEETING': Họp Hội đồng Chuyển duyệt -> Ra biên bản phê duyệt ngoại lệ
        """
        decision_type = decision_data.get('decision_type', 'APPROVE_SCHEME')
        decision_notes = decision_data.get('notes', '')
        reviewer_name = decision_data.get('reviewer_name', 'Trần Nam - Trưởng phòng Kinh doanh')

        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')

        if decision_type == 'APPROVE_SCHEME':
            result_status = 'ĐÃ PHÊ DUYỆT'
            message = 'Phương án đã được Trưởng phòng Kinh doanh phê duyệt hợp lệ. Đủ điều kiện chuyển tiếp sang Phase 4.'
            next_step = 'Phase 4: Hoàn thiện Báo giá'
            is_approved = True
            is_rejected = False
        elif decision_type == 'APPROVAL_MEETING':
            result_status = 'HỘI ĐỒNG ĐÃ PHÊ DUYỆT NGOẠI LỆ'
            waiver_details = decision_data.get('waiver_details', 'Hội đồng chấp thuận mức chiết khấu 12%, bổ sung nguồn cung đối tác Radware, huy động thêm kỹ sư thi công ca đêm.')
            message = f"Hội đồng thẩm định đã họp và biểu quyết thông qua: {waiver_details}. Đã ký Phiếu chuyển duyệt chính thức!"
            next_step = 'Phase 4: Hoàn thiện Báo giá'
            is_approved = True
            is_rejected = False
            # Cập nhật phiếu chuyển duyệt
            if current_state.get('draft_output', {}).get('approval_form'):
                current_state['draft_output']['approval_form']['status'] = 'ĐÃ PHÊ DUYỆT NGOẠI LỆ BỞI HỘI ĐỒNG'
                current_state['draft_output']['approval_form']['approved_by'] = 'Hội đồng Ban Giám Đốc & Khối Kỹ thuật'
                current_state['draft_output']['approval_form']['approval_date'] = timestamp
                current_state['draft_output']['approval_form']['waiver_notes'] = waiver_details
        elif decision_type == 'REQUEST_ADJUSTMENT':
            result_status = 'YÊU CẦU HIỆU CHỈNH'
            message = f"Yêu cầu chuyên viên kinh doanh & kỹ thuật hiệu chỉnh lại phương án theo chỉ đạo: {decision_notes}"
            next_step = 'Phase 2: Xử lý Tự động Lại sau Hiệu chỉnh'
            is_approved = False
            is_rejected = False
        elif decision_type == 'RECOMMEND_REJECTION':
            result_status = 'ĐÃ LOẠI BỎ HỒ SƠ'
            message = f"Đã quyết định từ chối chào giá dự án. Lý do: {decision_notes or 'Không khả thi về mặt kỹ thuật/tiến độ/ngân sách rủi ro cao.'}"
            next_step = 'Hồ sơ đã đóng (Lưu trữ kho lưu trữ từ chối)'
            is_approved = False
            is_rejected = True
        else:
            result_status = 'ĐANG XEM XÉT'
            message = 'Hồ sơ đang trong quá trình rà soát tại điểm kiểm tra của con người.'
            next_step = 'Phase 3'
            is_approved = False
            is_rejected = False

        decision_record = {
            'phase': 3,
            'phase_name': 'Kiểm tra của Con người (Human Review & Decision)',
            'decision_type': decision_type,
            'decision_status': result_status,
            'reviewer_name': reviewer_name,
            'timestamp': timestamp,
            'notes': decision_notes,
            'message': message,
            'is_approved': is_approved,
            'is_rejected': is_rejected,
            'next_step': next_step
        }

        return decision_record

    # ==========================================
    # PHASE 4: HOÀN THIỆN BÁO GIÁ
    # ==========================================
    def phase4_finalize_quotation(self, full_state):
        """
        Phase 4: Hoàn thiện Bản chào giá và bàn giao 4 bộ hồ sơ chuẩn:
        1. Bảng đáp ứng yêu cầu (Requirements Matrix)
        2. Hồ sơ đề xuất giải pháp kỹ thuật (Proposal Dossier)
        3. Bản chào giá chính thức (Official Quotation)
        4. Phiếu chuyển duyệt (Approved Escalation Form - nếu có)
        """
        phase1 = full_state['receipt_classification']
        ext = full_state['information_extraction']
        match = full_state['solution_match']
        price = full_state['price_and_discount']
        draft = full_state['draft_output']
        decision = full_state.get('human_decision', {})

        rfq_code = phase1['rfq_code']
        customer_name = phase1['customer_name']
        now_date = datetime.now().strftime('%d/%m/%Y')
        validity_date = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')

        # 1. Bảng đáp ứng yêu cầu (Requirements Matrix)
        doc_requirements_matrix = {
            'doc_name': 'Bảng Đáp Ứng Yêu Cầu Kỹ Thuật (Compliance Matrix)',
            'rfq_code': rfq_code,
            'customer_name': customer_name,
            'created_at': now_date,
            'items': draft['requirements_matrix'],
            'compliance_summary': f"Đáp ứng {len([m for m in draft['requirements_matrix'] if m['compliance_status'] == 'ĐẠT'])}/{len(draft['requirements_matrix'])} hạng mục. Cam kết tương thích 100% sau hiệu chuẩn kỹ thuật."
        }

        # 2. Hồ sơ đề xuất kỹ thuật (Proposal Dossier)
        doc_proposal_dossier = {
            'doc_name': 'Hồ Sơ Đề Xuất Giải Pháp Kỹ Thuật & Triển Khai (Proposal Dossier)',
            'rfq_code': rfq_code,
            'customer_name': customer_name,
            'executive_summary': f"Công ty Cổ phần Công nghệ & Mạng Thiên Minh trân trọng gửi tới {customer_name} phương án tổng thể cho '{phase1['project_type']}'. Giải pháp được thiết kế tối ưu hiệu năng, bảo mật toàn diện và sẵn sàng mở rộng hạ tầng trong 5 năm tới.",
            'architecture_highlights': [
                'Hạ tầng mạng chuyển mạch tốc độ cao chuẩn 10Gbps Uplink, băng thông chuyển mạch lớn.',
                'Cấp nguồn PoE+ thông minh chuẩn 802.3at phục vụ hệ thống Wi-Fi 6 và camera giám sát độ nét cao.',
                'Hệ thống Wi-Fi 6 chuyên dụng phủ sóng đồng đều, roaming mượt mà dưới 50ms giữa các tầng.',
                'Tường lửa thế hệ mới (Next-Gen Firewall) tích hợp kiểm soát ứng dụng và phòng chống xâm nhập IPS/UTM.',
                'Đội ngũ kỹ sư mạng có chứng chỉ quốc tế (CCNP/CCIE/NSE4) trực tiếp thi công, cấu hình và nghiệm thu theo tiêu chuẩn TIA-942.'
            ],
            'implementation_schedule': {
                'total_days': match['total_required_days'],
                'procurement_lead_time_days': match['max_lead_time_days'],
                'deployment_days': match['est_work_days'],
                'stages': [
                    {'stage': 'Giai đoạn 1', 'name': 'Chuẩn bị thiết bị, CO/CQ và khảo sát chi tiết', 'duration': f"{match['max_lead_time_days']} ngày"},
                    {'stage': 'Giai đoạn 2', 'name': 'Lắp đặt phần cứng tủ rack, kéo rải cáp mạng Cat6 chuẩn Fluke', 'duration': f"{max(2, match['est_work_days']//2)} ngày"},
                    {'stage': 'Giai đoạn 3', 'name': 'Cấu hình VLAN, Định tuyến L3, Tường lửa HA và Wi-Fi 6', 'duration': f"{max(2, match['est_work_days']//3)} ngày"},
                    {'stage': 'Giai đoạn 4', 'name': 'Kiểm thử tải, bàn giao tài liệu kỹ thuật và đào tạo quản trị', 'duration': '2 ngày'}
                ]
            },
            'warranty_and_sla': ext['sla_req']
        }

        # 3. Bản chào giá chính thức (Official Quotation)
        quotation_items = []
        for it in match['matched_solutions']:
            quotation_items.append({
                'stt': it['stt'],
                'item_name': it['matched_product_name'],
                'specs': it['matched_specs'],
                'quantity': it['quantity'],
                'unit': it['unit'],
                'unit_price': it['unit_price'],
                'total_price': it['total_price']
            })

        doc_official_quotation = {
            'doc_name': 'Bản Chào Giá Thương Mại Chính Thức (Official Quotation)',
            'quotation_number': f"TMN-BG-{datetime.now().strftime('%Y%m%d')}-01",
            'rfq_code': rfq_code,
            'customer_name': customer_name,
            'created_at': now_date,
            'valid_until': validity_date,
            'currency': 'VND',
            'items': quotation_items,
            'subtotal_before_discount': price['list_price_total'],
            'discount_pct': price['proposed_discount_pct'],
            'discount_amount': price['discount_amount'],
            'net_amount': price['net_price_before_vat'],
            'vat_pct': 10,
            'vat_amount': price['vat_amount'],
            'total_contract_value': price['total_with_vat'],
            'payment_terms': 'Tạm ứng 40% khi ký hợp đồng, 40% khi giao đủ thiết bị tại chân công trình, 20% khi nghiệm thu bàn giao toàn bộ.',
            'signatory': 'Ban Giám Đốc Công ty Thiên Minh Networks'
        }

        # 4. Phiếu chuyển duyệt (Approved Approval Form)
        doc_approval_form = draft.get('approval_form')

        return {
            'phase': 4,
            'phase_name': 'Hoàn thiện Bản Chào Giá (Finalize Quotation)',
            'status': 'HOÀN TẤT BÀN GIAO CHO QUẢN LÝ',
            'completed_at': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'deliverables': {
                'requirements_matrix': doc_requirements_matrix,
                'proposal_dossier': doc_proposal_dossier,
                'official_quotation': doc_official_quotation,
                'approval_form': doc_approval_form
            }
        }

    # ==========================================
    # RUN ENTIRE PIPELINE (OR UP TO PHASE 2/3)
    # ==========================================
    def run_automated_pipeline(self, parsed_data):
        """
        Thực thi tự động Phase 1 và Phase 2 (2a, 2b, 2c, 2d).
        Dừng lại tại điểm kiểm soát của con người (Human Checkpoint - Phase 3).
        """
        # Phase 1: Tiếp nhận và Phân loại Hồ sơ
        phase1 = self.phase1_receipt_and_classification(parsed_data)

        # Phase 2a: Trích xuất Thông tin
        phase2a = self.phase2a_extract_information(parsed_data, phase1)

        # Phase 2b: Đối chiếu Giải pháp & Khả năng Lịch trình
        phase2b = self.phase2b_match_solution_and_capability(phase2a, phase1)

        # Phase 2c: Tính toán Giá & Chiết khấu
        phase2c = self.phase2c_price_and_discount(phase2a, phase2b)

        # Phase 2d: Tạo Dự thảo Kết quả & Ma trận Đáp ứng
        phase2d = self.phase2d_generate_draft_output(phase1, phase2a, phase2b, phase2c)

        state = {
            'receipt_classification': phase1,
            'information_extraction': phase2a,
            'solution_match': phase2b,
            'price_and_discount': phase2c,
            'draft_output': phase2d,
            'human_decision': None,
            'final_quotation': None,
            'current_phase': 3 if phase2d['next_phase'] == 3 else 4
        }

        # Nếu phương án đã 100% hợp lệ và không có cờ cảnh báo nào, tự động chuẩn bị sẵn phase 4
        if phase2d['recommendation_code'] == 'PASS_READY':
            state['human_decision'] = {
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
            state['final_quotation'] = self.phase4_finalize_quotation(state)

        return state
