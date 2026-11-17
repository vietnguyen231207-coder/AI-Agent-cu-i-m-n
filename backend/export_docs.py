"""
Module: backend/export_docs.py
Tạo và xuất 4 bộ tài liệu hoàn chỉnh dưới dạng file DOCX chuyên nghiệp:
1. Bảng ma trận đáp ứng yêu cầu (Requirements Compliance Matrix)
2. Hồ sơ đề xuất giải pháp kỹ thuật (Technical Proposal Dossier)
3. Bản chào giá thương mại chính thức (Official Commercial Quotation)
4. Phiếu chuyển duyệt thẩm định (Approval / Escalation Form)
"""

import os
from datetime import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Đặt màu nền cho cell trong bảng Word"""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_styled_header(doc, title_text, subtitle_text):
    """Tạo Header phong cách doanh nghiệp Thiên Minh Networks"""
    p_comp = doc.add_paragraph()
    r_comp = p_comp.add_run('CÔNG TY CỔ PHẦN CÔNG NGHỆ & MẠNG THIÊN MINH (THIEN MINH NETWORKS)\n')
    r_comp.bold = True
    r_comp.font.size = Pt(10)
    r_comp.font.color.rgb = RGBColor(14, 116, 144) # Teal/Cyan brand
    
    r_sub = p_comp.add_run('Địa chỉ: Tầng 8, Tòa nhà Công nghệ Thiên Minh, Cầu Giấy, Hà Nội | Hotline: (024) 3999 8888\nWebsite: www.thienminhnetworks.vn | Email: rfq@thienminhnetworks.vn')
    r_sub.font.size = Pt(8.5)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)
    p_comp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Đường kẻ phân cách
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_after = Pt(12)

    # Tiêu đề tài liệu
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_title.add_run(title_text + '\n')
    r_t.bold = True
    r_t.font.size = Pt(16)
    r_t.font.color.rgb = RGBColor(15, 23, 42)

    if subtitle_text:
        r_st = p_title.add_run(subtitle_text)
        r_st.font.size = Pt(11)
        r_st.italic = True
        r_st.font.color.rgb = RGBColor(71, 85, 105)

def export_requirements_matrix_docx(state, output_path):
    """Xuất Bảng đáp ứng yêu cầu (Requirements Matrix)"""
    doc = docx.Document()
    phase1 = state['receipt_classification']
    draft = state['draft_output']

    create_styled_header(doc, 'BẢNG MA TRẬN ĐÁP ỨNG YÊU CẦU KỸ THUẬT', f"Mã hồ sơ: {phase1['rfq_code']} | Khách hàng: {phase1['customer_name']}")

    # Thông tin tóm tắt
    p_meta = doc.add_paragraph()
    p_meta.add_run('Dự án: ').bold = True
    p_meta.add_run(f"{phase1['project_type']}\n")
    p_meta.add_run('Thời gian lập: ').bold = True
    p_meta.add_run(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    p_meta.add_run('Bộ phận đánh giá: ').bold = True
    p_meta.add_run("Khối Giải pháp Kỹ thuật & Hệ thống AI Agent Thiên Minh\n")

    # Bảng Matrix
    items = draft['requirements_matrix']
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ['STT', 'Yêu cầu của Khách hàng (RFQ)', 'Giải pháp Thiên Minh Đề xuất', 'Trạng thái & Ghi chú']
    for idx, text in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = text
        set_cell_background(cell, '0E7490')
        p = cell.paragraphs[0]
        for run in p.runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9.5)

    for item in items:
        row = table.add_row().cells
        row[0].text = str(item['stt'])
        row[1].text = str(item['client_requirement'])
        row[2].text = str(item['proposed_solution'])
        status_text = f"[{item['compliance_status']}]\n{item['technical_notes']}"
        row[3].text = status_text
        
        # Color coding status
        if item['compliance_status'] == 'ĐẠT':
            set_cell_background(row[3], 'F0FDF4') # Light green
        elif item['compliance_status'] == 'NGOÀI DANH MỤC':
            set_cell_background(row[3], 'FEF2F2') # Light red
        else:
            set_cell_background(row[3], 'FFFBEB') # Light yellow

    doc.add_paragraph().paragraph_format.space_before = Pt(16)
    p_sign = doc.add_paragraph()
    p_sign.add_run('XÁC NHẬN CỦA BỘ PHẬN KỸ THUẬT VẬN HÀNH\n').bold = True
    p_sign.add_run('(Ký và ghi rõ họ tên)\n\n\n\n')
    p_sign.add_run('Trưởng phòng Kỹ thuật Hệ thống')
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save(output_path)
    return output_path

def export_official_quotation_docx(state, output_path):
    """Xuất Bản chào giá thương mại chính thức (Official Quotation)"""
    doc = docx.Document()
    phase1 = state['receipt_classification']
    price = state['price_and_discount']
    match = state['solution_match']
    
    create_styled_header(doc, 'BẢN CHÀO GIÁ THƯƠNG MẠI CHÍNH THỨC', f"Số: TMN-BG-{phase1['rfq_code']} | Ngày lập: {datetime.now().strftime('%d/%m/%Y')}")

    p_client = doc.add_paragraph()
    p_client.add_run('Kính gửi: ').bold = True
    p_client.add_run(f"Ban Lãnh đạo & Tổ chuyên gia {phase1['customer_name']}\n")
    p_client.add_run('Về việc: ').bold = True
    p_client.add_run(f"Báo giá cung cấp thiết bị và dịch vụ triển khai cho '{phase1['project_type']}'\n")

    p_intro = doc.add_paragraph('Công ty Cổ phần Công nghệ & Mạng Thiên Minh xin trân trọng gửi tới Quý khách hàng bảng báo giá chi tiết như sau:')

    table = doc.add_table(rows=1, cols=6)
    table.style = 'Table Grid'
    headers = ['STT', 'Tên Hàng hóa / Dịch vụ', 'ĐVT', 'Số lượng', 'Đơn giá (VNĐ)', 'Thành tiền (VNĐ)']
    for idx, text in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = text
        set_cell_background(cell, '0E7490')
        p = cell.paragraphs[0]
        for run in p.runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9.5)

    for item in match['matched_solutions']:
        row = table.add_row().cells
        row[0].text = str(item['stt'])
        row[1].text = f"{item['matched_product_name']}\n({item['matched_specs']})"
        row[2].text = item['unit']
        row[3].text = str(item['quantity'])
        row[4].text = f"{item['unit_price']:,.0f}"
        row[5].text = f"{item['total_price']:,.0f}"
        row[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        row[5].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Bảng tổng kết tài chính
    doc.add_paragraph().paragraph_format.space_before = Pt(8)
    summary_table = doc.add_table(rows=5, cols=2)
    summary_table.style = 'Table Grid'
    summary_rows = [
        ('Tổng giá trị niêm yết (Chưa chiết khấu):', f"{price['list_price_total']:,.0f} VNĐ"),
        (f"Chiết khấu thương mại ({price['proposed_discount_pct']:.1f}%):", f"- {price['discount_amount']:,.0f} VNĐ"),
        ('Tổng tiền sau chiết khấu (Chưa VAT):', f"{price['net_price_before_vat']:,.0f} VNĐ"),
        ('Thuế Giá trị gia tăng (VAT 10%):', f"{price['vat_amount']:,.0f} VNĐ"),
        ('TỔNG CỘNG THANH TOÁN (ĐÃ BAO GỒM VAT):', f"{price['total_with_vat']:,.0f} VNĐ")
    ]
    for idx, (lbl, val) in enumerate(summary_rows):
        cells = summary_table.rows[idx].cells
        cells[0].text = lbl
        cells[1].text = val
        cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if idx == 4:
            set_cell_background(cells[0], 'F1F5F9')
            set_cell_background(cells[1], 'F1F5F9')
            cells[0].paragraphs[0].runs[0].bold = True
            cells[1].paragraphs[0].runs[0].bold = True
            cells[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(14, 116, 144)

    # Điều khoản thương mại
    p_terms = doc.add_paragraph()
    p_terms.paragraph_format.space_before = Pt(12)
    p_terms.add_run('ĐIỀU KHOẢN THƯƠNG MẠI:\n').bold = True
    p_terms.add_run('1. Hiệu lực báo giá: 30 ngày kể từ ngày phát hành.\n')
    p_terms.add_run('2. Thời gian giao hàng & hoàn thành: Theo đúng tiến độ cam kết.\n')
    p_terms.add_run('3. Điều kiện thanh toán: Tạm ứng 40% khi ký HĐ, 40% khi giao hàng, 20% khi nghiệm thu.\n')
    p_terms.add_run('4. Bảo hành: Bảo hành chính hãng 24 - 36 tháng theo tiêu chuẩn nhà sản xuất.\n')

    # Chữ ký
    p_sign = doc.add_paragraph()
    p_sign.add_run('ĐẠI DIỆN CÔNG TY THIÊN MINH NETWORKS\n').bold = True
    p_sign.add_run('TỔNG GIÁM ĐỐC\n\n\n\n')
    p_sign.add_run('(Đã ký & đóng dấu)')
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save(output_path)
    return output_path

def export_approval_form_docx(state, output_path):
    """Xuất Phiếu Chuyển Duyệt (Escalation / Approval Form)"""
    doc = docx.Document()
    phase1 = state['receipt_classification']
    price = state['price_and_discount']
    draft = state['draft_output']
    app_form = draft.get('approval_form')

    create_styled_header(doc, 'PHIẾU CHUYỂN DUYỆT PHƯƠNG ÁN CHÀO GIÁ DỰ ÁN', f"Mã phiếu: PCD-{phase1['rfq_code']} | Ngày lập: {datetime.now().strftime('%d/%m/%Y')}")

    p_info = doc.add_paragraph()
    p_info.add_run('Tên dự án: ').bold = True
    p_info.add_run(f"{phase1['project_type']}\n")
    p_info.add_run('Khách hàng: ').bold = True
    p_info.add_run(f"{phase1['customer_name']}\n")
    p_info.add_run('Tổng giá trị dự toán: ').bold = True
    p_info.add_run(f"{price['list_price_total']:,.0f} VNĐ (Sau chiết khấu: {price['net_price_before_vat']:,.0f} VNĐ)\n")
    p_info.add_run('Đơn vị trình: ').bold = True
    p_info.add_run("Phòng Kinh doanh Khách hàng Doanh nghiệp (Enterprise Sales)\n")

    doc.add_heading('1. Danh Sách Các Yếu Tố Vượt Thẩm Quyền / Tiềm Ẩn Rủi Ro Cần Phê Duyệt', level=2)

    escalations = draft.get('escalation_items', [])
    if escalations:
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        headers = ['STT', 'Nội dung vướng mắc', 'Rủi ro nhận định', 'Đề xuất giải pháp khắc phục']
        for idx, text in enumerate(headers):
            cell = table.rows[0].cells[idx]
            cell.text = text
            set_cell_background(cell, 'DC2626') # Red warning header
            p = cell.paragraphs[0]
            for run in p.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(9.5)

        for idx, esc in enumerate(escalations):
            row = table.add_row().cells
            row[0].text = str(idx + 1)
            row[1].text = esc['issue']
            row[2].text = esc['risk']
            row[3].text = f"{esc['mitigation']}\n[Thẩm quyền: {esc['authority']}]"
    else:
        doc.add_paragraph('Không có nội dung vượt thẩm quyền. Hồ sơ nằm trọn trong hạn mức tự duyệt của Trưởng phòng Kinh doanh.')

    doc.add_heading('2. Ý Kiến & Phê Duyệt Của Hội Đồng / Ban Giám Đốc', level=2)
    p_decision = doc.add_paragraph()
    p_decision.add_run('Trạng thái phê duyệt: ').bold = True
    status = app_form.get('status', 'ĐÃ PHÊ DUYỆT NGOẠI LỆ BỞI HỘI ĐỒNG') if app_form else 'HỢP LỆ'
    p_decision.add_run(f"{status}\n")
    p_decision.add_run('Căn cứ cuộc họp thẩm định liên bộ phận Kỹ thuật - Kinh doanh - Tài chính, Ban Giám Đốc quyết định chấp thuận phương án để kịp tiến độ nộp thầu.')

    # Chữ ký 3 bên
    doc.add_paragraph().paragraph_format.space_before = Pt(20)
    sig_table = doc.add_table(rows=2, cols=3)
    sig_headers = ['TRƯỞNG PHÒNG KD', 'TRƯỞNG PHÒNG KỸ THUẬT', 'TỔNG GIÁM ĐỐC / HỘI ĐỒNG']
    for idx, text in enumerate(sig_headers):
        cell = sig_table.rows[0].cells[idx]
        cell.text = text
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        c2 = sig_table.rows[1].cells[idx]
        c2.text = '\n\n\n(Đã ký xác nhận)'
        c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(output_path)
    return output_path

