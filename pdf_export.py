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

# Пытаемся зарегистрировать русский шрифт
FONT_NAME = 'Helvetica'  # шрифт по умолчанию

# Вариант 1: Шрифт Roboto в папке проекта
roboto_path = os.path.join(BASE_DIR, 'fonts', 'Roboto-Regular.ttf')
if os.path.exists(roboto_path):
    try:
        pdfmetrics.registerFont(TTFont('Roboto', roboto_path))
        FONT_NAME = 'Roboto'
        print(f"✅ Загружен шрифт Roboto из {roboto_path}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки Roboto: {e}")

# Вариант 2: Шрифт DejaVuSans в папке проекта
if FONT_NAME == 'Helvetica':
    dejavu_path = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    if os.path.exists(dejavu_path):
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_path))
            FONT_NAME = 'DejaVuSans'
            print(f"✅ Загружен шрифт DejaVuSans из {dejavu_path}")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки DejaVuSans: {e}")

# Вариант 3: Шрифт из системы Windows
if FONT_NAME == 'Helvetica':
    system_fonts = [
        ('Arial', 'C:/Windows/Fonts/arial.ttf'),
        ('Times New Roman', 'C:/Windows/Fonts/times.ttf'),
        ('Courier New', 'C:/Windows/Fonts/cour.ttf'),
    ]
    for name, path in system_fonts:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                FONT_NAME = name
                print(f"✅ Загружен системный шрифт {name}")
                break
            except:
                continue

if FONT_NAME == 'Helvetica':
    print("⚠️ ВНИМАНИЕ: Кириллический шрифт не найден! Текст в PDF будет квадратиками.")
    print(f"   Поместите файл Roboto-Regular.ttf в папку {os.path.join(BASE_DIR, 'fonts')}")


class PDFExporter:
    """Класс для экспорта отчётов в PDF с поддержкой русского языка"""

    def __init__(self):
        self.output_dir = os.path.join(BASE_DIR, "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Отчёты будут сохраняться в: {self.output_dir}")

    def export_events(self, events: List[Dict], start_date: date, end_date: date, filename: str = None) -> str:
        """Экспорт мероприятий в PDF за период"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"events_{start_date}_{end_date}_{timestamp}.pdf")

        # Проверяем, есть ли данные
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

        # Создаём стили с русским шрифтом
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

        # Сборка документа
        elements = []

        # Заголовок
        elements.append(Paragraph("Журнал мероприятий", title_style))
        elements.append(Paragraph(f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}", subtitle_style))
        elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 10*mm))

        # Заголовки таблицы
        headers = ['№', 'Дата', 'Время', 'Название', 'Тип', 'Место', 'Участников', 'Статус']

        # Данные для таблицы
        table_data = []

        # Добавляем заголовки
        header_row = []
        for h in headers:
            header_row.append(Paragraph(f"<b>{h}</b>", header_cell_style))
        table_data.append(header_row)

        # Добавляем строки с данными
        for i, event in enumerate(events, 1):
            # Преобразуем дату
            if hasattr(event.get('event_date'), 'strftime'):
                date_str = event['event_date'].strftime('%d.%m.%Y')
            else:
                date_str = str(event.get('event_date', '-'))

            # Преобразуем время
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

        # Создаём таблицу
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Стиль таблицы
        table.setStyle(TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Все ячейки
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

        # Итоговая строка
        elements.append(Spacer(1, 10*mm))
        footer_text = f"<font name='{FONT_NAME}' size='8'>Всего мероприятий за период: {len(events)}</font>"
        elements.append(Paragraph(footer_text, cell_style))

        # Подпись
        elements.append(Spacer(1, 15*mm))
        signature_style = ParagraphStyle(
            'Signature',
            parent=cell_style,
            fontSize=8,
            textColor=colors.HexColor('#95a5a6'),
            alignment=2
        )
        elements.append(Paragraph("© АНО МЦИ «ШАГ НАВСТРЕЧУ»", signature_style))

        # Сборка PDF
        doc.build(elements)
        print(f"✅ PDF создан: {filename}")
        return filename

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

        # Заголовок
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

        # Подпись
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


# Создаём глобальный экземпляр
pdf_exporter = PDFExporter()