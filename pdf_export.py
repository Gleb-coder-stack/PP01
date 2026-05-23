"""
Экспорт отчётов в PDF с поддержкой кириллицы
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, date
import os
from typing import List, Dict

# Определяем путь к проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Регистрация кириллического шрифта
FONT_NAME = 'Helvetica'

# Пробуем загрузить Roboto
roboto_path = os.path.join(BASE_DIR, 'fonts', 'Roboto-Regular.ttf')
if os.path.exists(roboto_path):
    try:
        pdfmetrics.registerFont(TTFont('Roboto', roboto_path))
        FONT_NAME = 'Roboto'
        print(f"✅ Загружен шрифт Roboto")
    except:
        pass

# Если Roboto не загрузился, пробуем Arial из системы
if FONT_NAME == 'Helvetica':
    arial_path = 'C:/Windows/Fonts/arial.ttf'
    if os.path.exists(arial_path):
        try:
            pdfmetrics.registerFont(TTFont('Arial', arial_path))
            FONT_NAME = 'Arial'
            print(f"✅ Загружен шрифт Arial")
        except:
            pass

if FONT_NAME == 'Helvetica':
    print("⚠️ ВНИМАНИЕ: Кириллический шрифт не найден!")


class PDFExporter:
    """Класс для экспорта отчётов в PDF"""

    def __init__(self):
        self.output_dir = os.path.join(BASE_DIR, "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Отчёты будут сохраняться в: {self.output_dir}")

    # ==================== ОБЫЧНЫЙ ОТЧЁТ (БЕЗ УЧАСТНИКОВ) ====================

    def export_events(self, events: List[Dict], start_date: date, end_date: date, filename: str = None) -> str:
        """Экспорт мероприятий в PDF (таблица без участников)"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"events_{start_date}_{end_date}_{timestamp}.pdf")

        if not events:
            print("⚠️ Нет данных для экспорта")
            return None

        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=20*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=16,
            alignment=1,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=0,
            textColor=colors.HexColor('#7f8c8d')
        )

        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=9,
            alignment=0
        )

        header_cell_style = ParagraphStyle(
            'HeaderCellStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=1,
            textColor=colors.white
        )

        elements = []

        # Заголовок
        elements.append(Paragraph("Журнал мероприятий", title_style))
        elements.append(Paragraph(f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}", subtitle_style))
        elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 10*mm))

        # Заголовки таблицы
        headers = ['№', 'Дата', 'Время', 'Название', 'Тип', 'Место', 'Участников', 'Статус']

        table_data = []

        # Строка заголовков
        header_row = []
        for h in headers:
            header_row.append(Paragraph(f"<b>{h}</b>", header_cell_style))
        table_data.append(header_row)

        # Строки с данными
        for i, event in enumerate(events, 1):
            # Дата
            if hasattr(event.get('event_date'), 'strftime'):
                date_str = event['event_date'].strftime('%d.%m.%Y')
            else:
                date_str = str(event.get('event_date', '-'))

            # Время
            start_time = event.get('start_time', '-')
            if hasattr(start_time, 'strftime'):
                time_str = start_time.strftime('%H:%M')
            else:
                time_str = str(start_time)[:5] if start_time else '-'

            row = [
                Paragraph(str(i), cell_style),
                Paragraph(date_str, cell_style),
                Paragraph(time_str, cell_style),
                Paragraph(str(event.get('title', '-'))[:50], cell_style),
                Paragraph(str(event.get('event_type', '-')), cell_style),
                Paragraph(str(event.get('location', '-'))[:40], cell_style),
                Paragraph(str(event.get('participants_count', 0)), cell_style),
                Paragraph(str(event.get('status', '-')), cell_style)
            ]
            table_data.append(row)

        # Ширина колонок
        col_widths = [15*mm, 35*mm, 25*mm, 60*mm, 35*mm, 50*mm, 30*mm, 35*mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Стиль таблицы
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('ALIGN', (6, 1), (7, -1), 'CENTER'),
            ('ALIGN', (3, 1), (5, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(f"<font name='{FONT_NAME}' size='8'>Всего мероприятий за период: {len(events)}</font>", cell_style))
        elements.append(Spacer(1, 15*mm))

        signature_style = ParagraphStyle(
            'Signature',
            parent=cell_style,
            fontSize=8,
            textColor=colors.HexColor('#95a5a6'),
            alignment=2
        )
        elements.append(Paragraph("© АНО МЦИ «ШАГ НАВСТРЕЧУ»", signature_style))

        doc.build(elements)
        print(f"✅ PDF создан: {filename}")
        return filename

    # ==================== СТАТИСТИЧЕСКИЙ ОТЧЁТ ====================

    def export_statistics(self, statistics: Dict, filename: str = None) -> str:
        """Экспорт статистического отчёта в PDF"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"statistics_{timestamp}.pdf")

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=16,
            alignment=1,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        )

        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=12,
            alignment=0,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        )

        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=0,
            spaceAfter=6
        )

        elements = []

        elements.append(Paragraph("Статистический отчёт", title_style))
        elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
        elements.append(Spacer(1, 10*mm))

        # Общая статистика
        elements.append(Paragraph("<b>Общая статистика</b>", heading_style))
        elements.append(Paragraph(f"• Всего мероприятий: {statistics.get('total_events', 0)}", normal_style))
        elements.append(Paragraph(f"• Всего участников: {statistics.get('total_participants', 0)}", normal_style))
        elements.append(Paragraph(f"• Запланировано на ближайшее время: {statistics.get('upcoming_events', 0)}", normal_style))
        elements.append(Spacer(1, 10*mm))

        # По статусам
        elements.append(Paragraph("<b>Мероприятия по статусам</b>", heading_style))
        events_by_status = statistics.get('events_by_status', {})
        if events_by_status:
            status_names = {
                'запланировано': 'Запланировано',
                'проведено': 'Проведено',
                'отменено': 'Отменено'
            }
            for status, count in events_by_status.items():
                status_text = status_names.get(status, status)
                elements.append(Paragraph(f"• {status_text}: {count}", normal_style))
        else:
            elements.append(Paragraph("• Нет данных", normal_style))
        elements.append(Spacer(1, 10*mm))

        # По категориям участников
        elements.append(Paragraph("<b>Участники по категориям</b>", heading_style))
        participants_by_category = statistics.get('participants_by_category', {})
        if participants_by_category:
            category_names = {
                'ребёнок': 'Дети',
                'взрослый': 'Взрослые',
                'волонтёр': 'Волонтёры',
                'особенный гость': 'Особенные гости'
            }
            for category, count in participants_by_category.items():
                category_text = category_names.get(category, category)
                elements.append(Paragraph(f"• {category_text}: {count}", normal_style))
        else:
            elements.append(Paragraph("• Нет данных", normal_style))

        elements.append(Spacer(1, 20*mm))
        signature_style = ParagraphStyle(
            'Signature',
            parent=normal_style,
            fontSize=8,
            textColor=colors.HexColor('#95a5a6'),
            alignment=2
        )
        elements.append(Paragraph("© АНО МЦИ «ШАГ НАВСТРЕЧУ»", signature_style))

        doc.build(elements)
        print(f"✅ PDF статистики создан: {filename}")
        return filename

    # ==================== ОТЧЁТ С УЧАСТНИКАМИ (ТАБЛИЦА) ====================

    def export_events_with_participants_table(self, events_data: List[Dict], db, start_date: date, end_date: date, filename: str = None) -> str:
        """Экспорт мероприятий с участниками в PDF (таблица)"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"events_with_participants_{start_date}_{end_date}_{timestamp}.pdf")

        if not events_data:
            print("⚠️ Нет данных для экспорта")
            return None

        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=20*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=16,
            alignment=1,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=0,
            textColor=colors.HexColor('#7f8c8d')
        )

        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=9,
            alignment=0
        )

        header_cell_style = ParagraphStyle(
            'HeaderCellStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=1,
            textColor=colors.white
        )

        elements = []

        # Заголовок
        elements.append(Paragraph("Отчёт о мероприятиях с участниками", title_style))
        elements.append(Paragraph(f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}", subtitle_style))
        elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 10*mm))

        # Заголовки таблицы
        headers = ['№', 'Дата', 'Время', 'Название', 'Место', 'Статус', 'Участники']

        table_data = []

        # Строка заголовков
        header_row = []
        for h in headers:
            header_row.append(Paragraph(f"<b>{h}</b>", header_cell_style))
        table_data.append(header_row)

        # Строки с данными
        for i, event in enumerate(events_data, 1):
            # Дата
            if hasattr(event.get('event_date'), 'strftime'):
                date_str = event['event_date'].strftime('%d.%m.%Y')
            else:
                date_str = str(event.get('event_date', '-'))

            # Время
            start_time = event.get('start_time', '-')
            if hasattr(start_time, 'strftime'):
                time_str = start_time.strftime('%H:%M')
            else:
                time_str = str(start_time)[:5] if start_time else '-'

            # Получаем участников мероприятия
            participants = db.get_event_participants(event['id'])
            # Фильтруем только со статусом "записан" или "посетил"
            filtered_participants = [p for p in participants if p['attendance_status'] in ('записан', 'посетил')]

            # Формируем строку с участниками (каждый с новой строки)
            if filtered_participants:
                participants_lines = []
                for p in filtered_participants:
                    participants_lines.append(f"• {p['last_name']} {p['first_name']} ({p['category']})")
                participants_text = "<br/>".join(participants_lines)
            else:
                participants_text = "Нет записанных участников"

            row = [
                Paragraph(str(i), cell_style),
                Paragraph(date_str, cell_style),
                Paragraph(time_str, cell_style),
                Paragraph(str(event.get('title', '-')), cell_style),
                Paragraph(str(event.get('location', '-')), cell_style),
                Paragraph(str(event.get('status', '-')), cell_style),
                Paragraph(participants_text, cell_style)
            ]
            table_data.append(row)

        # Ширина колонок
        col_widths = [15*mm, 30*mm, 25*mm, 50*mm, 45*mm, 30*mm, 60*mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Стиль таблицы
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(f"<font name='{FONT_NAME}' size='8'>Всего мероприятий за период: {len(events_data)}</font>", cell_style))
        elements.append(Spacer(1, 15*mm))

        signature_style = ParagraphStyle(
            'Signature',
            parent=cell_style,
            fontSize=8,
            textColor=colors.HexColor('#95a5a6'),
            alignment=2
        )
        elements.append(Paragraph("© АНО МЦИ «ШАГ НАВСТРЕЧУ»", signature_style))

        doc.build(elements)
        print(f"✅ PDF с участниками создан: {filename}")
        return filename


# Создаём глобальный экземпляр
pdf_exporter = PDFExporter()