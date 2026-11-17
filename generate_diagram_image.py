"""
Script: generate_diagram_image.py
Tạo ảnh infographic độ phân giải cao cho Sơ đồ Quy trình Pipeline Thiên Minh Networks:
Sheets -> Cleaning -> Process -> Verify -> Export
Kèm các luồng xử lý ngoại lệ và hoàn trả lỗi (Error Return Loops).
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def create_pipeline_diagram(output_path='static/so_do_pipeline_thien_minh.png'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 2800 x 1575 px (16:9 ratio, DPI=150)
    fig, ax = plt.subplots(figsize=(26, 14.5), dpi=150)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Palette
    c_bg = '#f8fafc'
    c_primary = '#1e3a8a'      # Xanh navy
    c_purple = '#7c3aed'       # Tím AI Agent
    c_blue = '#0284c7'         # Xanh dương Ingestion
    c_cyan = '#0891b2'         # Xanh ngọc Cleaning
    c_emerald = '#059669'      # Xanh lá Pass/Export
    c_amber = '#d97706'        # Vàng cam Chuyển duyệt
    c_rose = '#e11d48'         # Đỏ Báo lỗi / Loại bỏ
    c_card_bg = '#ffffff'
    font_fam = 'Segoe UI'

    fig.patch.set_facecolor(c_bg)

    # 1. HEADER BANNER
    header_box = FancyBboxPatch((2, 90.5), 96, 8, boxstyle="round,pad=0.5,rounding_size=1.2",
                                facecolor='#0f172a', edgecolor='none')
    ax.add_patch(header_box)

    ax.text(4.2, 95.8, "THIÊN MINH", fontsize=19, fontweight='bold', color='#38bdf8', fontfamily=font_fam, va='center')
    ax.text(4.2, 92.8, "NETWORKS", fontsize=11, fontweight='bold', color='#94a3b8', fontfamily=font_fam, va='center')
    ax.plot([14.5, 14.5], [92, 97], color='#334155', lw=2)

    ax.text(16, 95.7, "SƠ ĐỒ NGUỒN HOẠT ĐỘNG & ĐỊNH TUYẾN PIPELINE AI AGENT", 
            fontsize=17, fontweight='bold', color='#ffffff', fontfamily=font_fam, va='center')
    ax.text(16, 92.8, "Quy trình chuẩn: Sheets -> Cleaning -> AI Process -> Verify -> Export & Cơ chế Hoàn trả Lỗi", 
            fontsize=11.5, color='#cbd5e1', fontfamily=font_fam, va='center')

    # Badge v2.0
    vbadge = FancyBboxPatch((89.5, 92.8), 7.2, 3.4, boxstyle="round,pad=0.3,rounding_size=0.8",
                            facecolor='#1e293b', edgecolor='#38bdf8', lw=1.5)
    ax.add_patch(vbadge)
    ax.text(93.1, 94.5, "PIPELINE v2.0", fontsize=9.5, fontweight='bold', color='#38bdf8', 
            ha='center', va='center', fontfamily=font_fam)

    # 2. COLUMNS HEADERS
    def draw_col_head(x, y, w, h, step, title_vn, title_en, color):
        col_bg = FancyBboxPatch((x, 7), w, 81.5, boxstyle="round,pad=0.4,rounding_size=1.5",
                                facecolor=color, alpha=0.035, edgecolor=color, lw=1.2, ls='--')
        ax.add_patch(col_bg)
        
        h_box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.0",
                               facecolor=color, edgecolor='none')
        ax.add_patch(h_box)
        ax.text(x + w/2, y + h*0.68, f"{step}: {title_vn}", fontsize=11.5, fontweight='bold', 
                color='#ffffff', ha='center', va='center', fontfamily=font_fam)
        ax.text(x + w/2, y + h*0.28, title_en, fontsize=9.5, color='#f1f5f9', 
                ha='center', va='center', fontfamily=font_fam)

    draw_col_head(2, 82.5, 17, 5.5, "BƯỚC 1", "TIẾP NHẬN ĐẦU VÀO", "DATA INGESTION", c_blue)
    draw_col_head(21, 82.5, 17, 5.5, "BƯỚC 2", "LÀM SẠCH & KIỂM ĐỊNH", "CLEANING & VALIDATION", c_cyan)
    draw_col_head(40, 82.5, 19, 5.5, "BƯỚC 3", "AI AGENT XỬ LÝ", "MULTI-STEP PROCESS", c_purple)
    draw_col_head(61, 82.5, 19, 5.5, "BƯỚC 4", "KIỂM TRA & DUYỆT", "HUMAN VERIFICATION", c_amber)
    draw_col_head(82, 82.5, 16, 5.5, "BƯỚC 5", "HOÀN THIỆN BÁO GIÁ", "FINALIZE & EXPORT", c_emerald)

    # Helper Card Drawer
    def draw_card(x, y, w, h, title, items, badge="", badge_color=c_blue, border_color='#e2e8f0'):
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8",
                              facecolor=c_card_bg, edgecolor=border_color, lw=1.5)
        ax.add_patch(card)
        if badge:
            bw = len(badge) * 0.55 + 1.2
            b_patch = FancyBboxPatch((x + w - bw - 0.6, y + h - 2.2), bw, 1.8,
                                     boxstyle="round,pad=0.2,rounding_size=0.4", facecolor=badge_color, edgecolor='none')
            ax.add_patch(b_patch)
            ax.text(x + w - 0.6 - bw/2, y + h - 1.3, badge, fontsize=7.5, fontweight='bold', 
                    color='#ffffff', ha='center', va='center', fontfamily=font_fam)
        
        ax.text(x + 0.8, y + h - 1.5, title, fontsize=10, fontweight='bold', color='#1e293b', fontfamily=font_fam, va='center')
        cur_y = y + h - 3.2
        for it in items:
            ax.text(x + 1.2, cur_y, f"- {it}", fontsize=8.5, color='#475569', fontfamily=font_fam, va='center')
            cur_y -= 1.6

    # BƯỚC 1: CARDS
    draw_card(3, 67.5, 15, 12.5, "1. Link Google Sheets", [
        "Nhận URL bảng tính online",
        "Tự động tách Sheet ID & GID",
        "Chuyển đổi sang link CSV Export",
        "Tải ngầm dữ liệu danh mục"
    ], badge="SHEETS", badge_color='#0284c7')

    draw_card(3, 53, 15, 13, "2. File Word (.docx)", [
        "Đọc văn bản & cấu trúc bảng",
        "Bóc tách danh sách thiết bị",
        "Trích xuất trần ngân sách",
        "Phát hiện deadline & SLA"
    ], badge="DOCX", badge_color='#2563eb')

    draw_card(3, 38.5, 15, 13, "3. Bảng Dữ Liệu (.csv)", [
        "Đọc bảng tính CSV nội bộ",
        "Hỗ trợ chuẩn UTF-8-SIG",
        "Chuẩn hóa danh mục nhiều mã",
        "Đọc cột số lượng, đơn giá"
    ], badge="CSV", badge_color='#059669')

    draw_card(3, 24, 15, 13, "4. Văn Bản / Raw Text", [
        "Copy-paste văn bản tự do",
        "Đọc mô tả dự án từ email/chat",
        "Trợ lý Gemini 3.5 phân giải",
        "Trích xuất điều kiện bắt buộc"
    ], badge="RAW TEXT", badge_color='#6366f1')

    # Mũi tên Bước 1 -> Bước 2
    ax.annotate('', xy=(20.5, 52), xytext=(18.2, 52),
                arrowprops=dict(arrowstyle="-|>", color=c_blue, lw=3, mutation_scale=18))

    # BƯỚC 2: CLEANING & VALIDATION
    draw_card(22, 66, 15, 14, "Chuẩn Hóa Cột (Mapping)", [
        "Tự động ánh xạ tiêu đề cột:",
        " 'hạng mục' / 'item' -> item_name",
        " 'số lượng' / 'qty' -> quantity",
        " 'thông số' / 'specs' -> specs",
        " 'ngân sách' / 'giá' -> budget"
    ], badge="SCHEMA", badge_color=c_cyan)

    draw_card(22, 49, 15, 15, "Làm Sạch & Chuẩn Hóa", [
        "Loại bỏ dòng trống & ký tự rác",
        "Ép kiểu số lượng về integer (int)",
        "Chuẩn hóa định dạng tiền tệ VNĐ",
        "Khởi tạo mã hồ sơ: TMN-RFQ-...",
        "Gán mốc thời gian tiếp nhận"
    ], badge="CLEANING", badge_color='#0284c7')

    # Diamond kiểm tra hợp lệ
    dia_x, dia_y = 29.5, 33
    diamond = patches.Polygon([
        [dia_x, dia_y + 4.5],
        [dia_x + 6.5, dia_y],
        [dia_x, dia_y - 4.5],
        [dia_x - 6.5, dia_y]
    ], closed=True, facecolor='#fef2f2', edgecolor=c_rose, lw=2)
    ax.add_patch(diamond)
    ax.text(dia_x, dia_y + 1.2, "DỮ LIỆU ĐỦ &", fontsize=8.5, fontweight='bold', color=c_rose, ha='center', fontfamily=font_fam)
    ax.text(dia_x, dia_y - 1.2, "HỢP LỆ CHƯA?", fontsize=8.5, fontweight='bold', color=c_rose, ha='center', fontfamily=font_fam)

    # Nối nội bộ Bước 2
    ax.annotate('', xy=(29.5, 64), xytext=(29.5, 66), arrowprops=dict(arrowstyle="->", color='#94a3b8', lw=1.8))
    ax.annotate('', xy=(29.5, 38), xytext=(29.5, 49), arrowprops=dict(arrowstyle="->", color='#94a3b8', lw=1.8))

    # NHÁNH LỖI BƯỚC 2: TRẢ VỀ BƯỚC 1
    err_box = FancyBboxPatch((21.8, 11), 15.4, 15, boxstyle="round,pad=0.3,rounding_size=0.8",
                             facecolor='#fff1f2', edgecolor=c_rose, lw=1.5, ls='--')
    ax.add_patch(err_box)
    ax.text(22.4, 24.2, "[!] ĐIỂM HOÀN TRẢ LỖI (BƯỚC 2):", fontsize=8.5, fontweight='bold', color=c_rose, fontfamily=font_fam)
    ax.text(22.4, 22.2, "- Link Sheets sai / Chưa mở chia sẻ", fontsize=8, color='#9f1239', fontfamily=font_fam)
    ax.text(22.4, 20.4, "- File Word không có bảng thiết bị", fontsize=8, color='#9f1239', fontfamily=font_fam)
    ax.text(22.4, 18.6, "- File CSV trống / Thiếu cột bắt buộc", fontsize=8, color='#9f1239', fontfamily=font_fam)
    ax.text(22.4, 16.8, "- Dữ liệu số lượng không hợp lệ", fontsize=8, color='#9f1239', fontfamily=font_fam)
    ax.text(22.4, 14.5, "-> Hệ thống bật Toast Warning đỏ", fontsize=8, fontweight='bold', color=c_rose, fontfamily=font_fam)
    ax.text(22.4, 12.5, "-> Yêu cầu người dùng nhập lại", fontsize=8, fontweight='bold', color=c_rose, fontfamily=font_fam)

    # Mũi tên từ Diamond xuống Box Lỗi
    ax.annotate('', xy=(29.5, 26.5), xytext=(29.5, 28.5),
                arrowprops=dict(arrowstyle="-|>", color=c_rose, lw=2))
    ax.text(30, 27.5, "LỖI", fontsize=8, fontweight='bold', color=c_rose, fontfamily=font_fam)

    # Mũi tên uốn cong đỏ quay về Bước 1
    ax.annotate('', xy=(18.2, 30), xytext=(21.8, 20),
                arrowprops=dict(arrowstyle="-|>", color=c_rose, lw=2.5,
                                connectionstyle="arc3,rad=-0.25", mutation_scale=16))
    ax.text(19, 21.5, "TRẢ VỀ BƯỚC 1\n(Nhập lại)", fontsize=8.5, fontweight='bold', color=c_rose, ha='center', fontfamily=font_fam)

    # Nhánh HỢP LỆ Bước 2 -> Bước 3
    ax.annotate('', xy=(39.5, 60), xytext=(36, 33),
                arrowprops=dict(arrowstyle="-|>", color='#059669', lw=3,
                                connectionstyle="arc3,rad=-0.15", mutation_scale=18))
    ax.text(37.5, 34.5, "HỢP LỆ", fontsize=9, fontweight='bold', color='#059669', ha='left', fontfamily=font_fam)

    # BƯỚC 3: AI AGENT PROCESS
    draw_card(41, 67, 17, 13.5, "2a. Trích Xuất Thông Tin", [
        "Bóc tách ngân sách trần (Budget Cap)",
        "Đọc hạn chót bàn giao (Deadline)",
        "Nhận diện yêu cầu SLA 24/7/NBD",
        "Phân loại dự án: LAN/WiFi / DC / Nhà xưởng"
    ], badge="EXTRACTION", badge_color=c_purple)

    draw_card(41, 51.5, 17, 13.5, "2b. Đối Chiếu Catalog & Lịch", [
        "Khớp 13 mã chuẩn (Switch, AP, FW...)",
        "Phát hiện thiết bị ngoài danh mục (DDoS...)",
        "Tính Lead-time nhập khẩu + Thi công on-site",
        "So sánh tổng ngày hoàn thành vs Deadline"
    ], badge="MATCHING", badge_color='#8b5cf6')

    draw_card(41, 36, 17, 13.5, "2c. Tính Giá, Chiết Khấu & COGS", [
        "Tính tổng giá niêm yết (List Price)",
        "Áp dụng chính sách 4 Tier chiết khấu",
        "Ước tính giá vốn hàng bán COGS = 68%",
        "Tính Biên lợi nhuận gộp (Gross Margin)",
        "Kiểm tra thâm hụt: Ngân sách < 70% COGS"
    ], badge="PRICING", badge_color='#7c3aed')

    draw_card(41, 20.5, 17, 13.5, "2d. Dự Thảo Ma Trận & Vi Phạm", [
        "Sinh Bảng ma trận đáp ứng yêu cầu",
        "Kích hoạt 5 cờ Escalation Triggers:",
        " Vượt chiết khấu | Lịch gấp | Ngoài catalog",
        " SLA khẩn cấp 1h | Thâm hụt ngân sách nặng",
        "Tạo dự thảo Phiếu chuyển duyệt (PCD)"
    ], badge="MATRIX & FORM", badge_color='#6d28d9')

    # Nối nội bộ Bước 3
    ax.annotate('', xy=(49.5, 65), xytext=(49.5, 67), arrowprops=dict(arrowstyle="->", color=c_purple, lw=1.5))
    ax.annotate('', xy=(49.5, 49.5), xytext=(49.5, 51.5), arrowprops=dict(arrowstyle="->", color=c_purple, lw=1.5))
    ax.annotate('', xy=(49.5, 34), xytext=(49.5, 36), arrowprops=dict(arrowstyle="->", color=c_purple, lw=1.5))

    # Mũi tên Bước 3 -> Bước 4
    ax.annotate('', xy=(61, 54), xytext=(58.2, 27),
                arrowprops=dict(arrowstyle="-|>", color=c_purple, lw=3,
                                connectionstyle="arc3,rad=-0.15", mutation_scale=18))

    # BƯỚC 4: VERIFY & HUMAN CHECKPOINTS
    dia4_x, dia4_y = 70.5, 54
    diamond4 = patches.Polygon([
        [dia4_x, dia4_y + 5.5],
        [dia4_x + 8, dia4_y],
        [dia4_x, dia4_y - 5.5],
        [dia4_x - 8, dia4_y]
    ], closed=True, facecolor='#fffbeb', edgecolor=c_amber, lw=2.5)
    ax.add_patch(diamond4)
    ax.text(dia4_x, dia4_y + 1.8, "KIỂM TRA CỦA CON NGƯỜI", fontsize=8.5, fontweight='bold', color=c_amber, ha='center', fontfamily=font_fam)
    ax.text(dia4_x, dia4_y - 0.2, "Phương Án Hợp Lệ", fontsize=9, fontweight='bold', color='#1e293b', ha='center', fontfamily=font_fam)
    ax.text(dia4_x, dia4_y - 2.0, "& Phù Hợp Không?", fontsize=9, fontweight='bold', color='#1e293b', ha='center', fontfamily=font_fam)

    # Nhánh 1: HỢP LỆ 100% (Pass)
    draw_card(62, 68, 17, 12.5, "1. Phê Duyệt Phương Án", [
        "Hồ sơ chuẩn 100% trong catalog",
        "Tiến độ thi công hoàn toàn khả thi",
        "Chiết khấu trong hạn mức TP Kinh doanh",
        "-> Chuyển thẳng sang BƯỚC 5"
    ], badge="PASS", badge_color=c_emerald, border_color='#a7f3d0')

    ax.annotate('', xy=(70.5, 68), xytext=(70.5, 59.5),
                arrowprops=dict(arrowstyle="-|>", color=c_emerald, lw=2.5, mutation_scale=15))
    ax.text(71, 63.5, "Có (Hợp lệ)", fontsize=8.5, fontweight='bold', color=c_emerald, fontfamily=font_fam)

    # Nhánh 2: HỌP HỘI ĐỒNG CHUYỂN DUYỆT (Escalation)
    draw_card(62, 35.5, 17, 13, "2. Họp Hội Đồng Chuyển Duyệt", [
        "Có ngoại lệ vượt thẩm quyền",
        "Tổng Giám Đốc + Kỹ thuật trưởng họp",
        "Ký biên bản duyệt ngoại lệ (Waiver)",
        "Đồng ý chiết khấu / Bổ sung đối tác",
        "-> Ký xong chuyển sang BƯỚC 5"
    ], badge="ESCALATE", badge_color=c_amber, border_color='#fde68a')

    ax.annotate('', xy=(70.5, 48.5), xytext=(70.5, 48.5), arrowprops=dict(arrowstyle="-|>", color=c_amber))
    ax.plot([70.5, 70.5], [48.5, 48.5], color=c_amber)
    ax.annotate('', xy=(70.5, 48.8), xytext=(70.5, 52), arrowprops=dict(arrowstyle="-|>", color=c_amber, lw=2))
    ax.text(71, 50.5, "Ngoại lệ", fontsize=8, fontweight='bold', color=c_amber, fontfamily=font_fam)

    # Nhánh 3: YÊU CẦU HIỆU CHỈNH (ADJUSTMENT LOOP)
    draw_card(62, 21, 17, 12.5, "3. Yêu Cầu Hiệu Chỉnh", [
        "Quản lý chỉ đạo giảm chiết khấu",
        "Thay đổi thiết bị / Đàm phán lại lịch",
        "-> TRẢ VỀ BƯỚC 3 (PROCESS)",
        "AI tái tính toán lại giá & ma trận"
    ], badge="ADJUST", badge_color='#eab308', border_color='#fef08a')

    ax.annotate('', xy=(62, 27), xytext=(65, 50),
                arrowprops=dict(arrowstyle="-|>", color='#ca8a04', lw=2,
                                connectionstyle="arc3,rad=0.2", mutation_scale=14))

    # MŨI TÊN VÀNG QUAY VỀ BƯỚC 3 (PROCESS)
    ax.annotate('', xy=(58.2, 42.5), xytext=(62, 26),
                arrowprops=dict(arrowstyle="-|>", color='#ca8a04', lw=2.8, ls='--',
                                connectionstyle="arc3,rad=-0.3", mutation_scale=16))
    ax.text(59.5, 33, "VÒNG LẶP HIỆU CHỈNH\n(AI Tái tính toán)", fontsize=8, fontweight='bold', color='#a16207', ha='center', fontfamily=font_fam)

    # Nhánh 4: ĐỀ XUẤT LOẠI BỎ HỒ SƠ (Rejection)
    draw_card(62, 9, 17, 10, "4. Đề Xuất Loại Bỏ", [
        "Ngân sách < 70% COGS (Lỗ nặng)",
        "Lịch trình bất khả thi vật lý",
        "-> DỪNG TIẾN TRÌNH & ĐÓNG HỒ SƠ"
    ], badge="REJECT", badge_color=c_rose, border_color='#fecdd3')

    ax.annotate('', xy=(70.5, 19.2), xytext=(70.5, 21), arrowprops=dict(arrowstyle="-|>", color=c_rose, lw=2))

    # BƯỚC 5: FINALIZE & EXPORT
    ax.annotate('', xy=(82, 74.5), xytext=(79.2, 74.5),
                arrowprops=dict(arrowstyle="-|>", color=c_emerald, lw=3, mutation_scale=18))
    ax.annotate('', xy=(82, 41.5), xytext=(79.2, 41.5),
                arrowprops=dict(arrowstyle="-|>", color=c_emerald, lw=2.5, mutation_scale=16))

    draw_card(83, 67, 14, 13.5, "Giao Diện Điều Hành", [
        "Cập nhật Dashboard 3D",
        "Thẻ Holographic dự toán",
        "Gauge tiến độ & Tuân thủ",
        "Donut COGS & Lợi nhuận",
        "Kích hoạt Gemini 3.5 AI"
    ], badge="DASHBOARD", badge_color='#0284c7')

    draw_card(83, 52.5, 14, 13, "1. Bảng Đáp Ứng YC", [
        "Requirements Matrix .docx",
        "Đối chiếu chi tiết 100%",
        "Ghi chú kỹ thuật hãng",
        "Cam kết tương thích"
    ], badge="FILE .DOCX", badge_color='#059669')

    draw_card(83, 38, 14, 13, "2. Bản Chào Giá", [
        "Official Quotation .docx",
        "Đơn giá niêm yết, VAT",
        "Mức chiết khấu phê duyệt",
        "Điều khoản thanh toán"
    ], badge="FILE .DOCX", badge_color='#059669')

    draw_card(83, 23.5, 14, 13, "3. Phiếu Chuyển Duyệt", [
        "Approval Form .docx",
        "Biên bản họp Hội đồng",
        "Chữ ký Tổng Giám Đốc",
        "Duyệt ngoại lệ chính thức"
    ], badge="FILE .DOCX", badge_color='#d97706')

    draw_card(83, 9, 14, 12.5, "4. Hồ Sơ Đề Xuất", [
        "Proposal Dossier .docx",
        "Kiến trúc giải pháp mạng",
        "Cam kết dịch vụ SLA"
    ], badge="FILE .DOCX", badge_color=c_purple)

    # FOOTER
    footer_box = FancyBboxPatch((2, 1.2), 96, 4.8, boxstyle="round,pad=0.4,rounding_size=0.8",
                                facecolor='#1e293b', edgecolor='none')
    ax.add_patch(footer_box)

    ax.plot([4, 5.5], [3.6, 3.6], color=c_blue, lw=4)
    ax.text(6, 3.6, "Tiếp nhận & Làm sạch", fontsize=8.5, color='#cbd5e1', va='center', fontfamily=font_fam)

    ax.plot([20, 21.5], [3.6, 3.6], color=c_purple, lw=4)
    ax.text(22, 3.6, "AI Agent Xử lý Tự động", fontsize=8.5, color='#cbd5e1', va='center', fontfamily=font_fam)

    ax.plot([38, 39.5], [3.6, 3.6], color=c_amber, lw=4)
    ax.text(40, 3.6, "Điểm Kiểm soát Con người", fontsize=8.5, color='#cbd5e1', va='center', fontfamily=font_fam)

    ax.plot([56, 57.5], [3.6, 3.6], color=c_emerald, lw=4)
    ax.text(58, 3.6, "Phê duyệt & Xuất Tài liệu", fontsize=8.5, color='#cbd5e1', va='center', fontfamily=font_fam)

    ax.plot([74, 75.5], [3.6, 3.6], color=c_rose, lw=4, ls='--')
    ax.text(76, 3.6, "Nhánh Hoàn trả Lỗi / Từ chối", fontsize=8.5, color='#fca5a5', va='center', fontfamily=font_fam)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"Thành công: {output_path}")

if __name__ == '__main__':
    create_pipeline_diagram('static/so_do_pipeline_thien_minh.png')
    create_pipeline_diagram('exports/so_do_pipeline_thien_minh.png')
