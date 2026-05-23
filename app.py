"""
Веб-приложение с REST API для учёта мероприятий
АНО МЦИ "ШАГ НАВСТРЕЧУ"
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect
from datetime import datetime, date, time
import os
import json

from db import db
from pdf_export import pdf_exporter

app = Flask(__name__)


def serialize_event(event):
    """Преобразует объект мероприятия в JSON-сериализуемый словарь"""
    if not event:
        return None

    result = {}
    for key, value in event.items():
        if isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, time):
            result[key] = value.strftime('%H:%M:%S')
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def serialize_events(events):
    return [serialize_event(e) for e in events]


def serialize_participant(participant):
    if not participant:
        return None
    result = {}
    for key, value in participant.items():
        if isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def serialize_participants(participants):
    return [serialize_participant(p) for p in participants]


# ==================== СТРАНИЦЫ ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calendar')
def calendar_page():
    return render_template('calendar.html')

@app.route('/events-page')
def events_page():
    return render_template('events.html')

@app.route('/participants-page')
def participants_page():
    return render_template('participants.html')

@app.route('/registrations')
def registrations_page():
    """Страница управления записью участников на мероприятия"""
    events = db.get_events()
    participants = db.get_participants()
    return render_template('registrations.html',
                         events=events,
                         participants=participants,
                         title="Запись на мероприятия")

@app.route('/reports-page')
def reports_page():
    today = date.today()
    return render_template('reports.html', today=today)

@app.route('/logs-page')
def logs_page():
    return render_template('logs.html')

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = db.get_event(event_id)
    if not event:
        return "Мероприятие не найдено", 404
    participants = db.get_event_participants(event_id)
    all_participants = db.get_participants()
    return render_template('event_detail.html',
                         event=serialize_event(event),
                         participants=serialize_participants(participants),
                         all_participants=serialize_participants(all_participants))

@app.route('/participant/<int:participant_id>')
def participant_detail(participant_id):
    participant = db.get_participant(participant_id)
    if not participant:
        return "Участник не найден", 404
    events = db.get_participant_events(participant_id)
    return render_template('participant_detail.html',
                         participant=serialize_participant(participant),
                         events=serialize_events(events))

@app.route('/events/<int:event_id>/register', methods=['POST'])
def register_post(event_id):
    participant_id = request.form.get('participant_id')
    if participant_id:
        db.register(event_id, int(participant_id))
    return redirect(f'/event/{event_id}')


# ==================== API: МЕРОПРИЯТИЯ ====================

@app.route('/api/events', methods=['GET'])
def api_get_events():
    try:
        events = db.get_events()
        return jsonify({'success': True, 'data': serialize_events(events)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/<int:eid>', methods=['GET'])
def api_get_event(eid):
    try:
        event = db.get_event(eid)
        if event:
            return jsonify({'success': True, 'data': serialize_event(event)})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events', methods=['POST'])
def api_create_event():
    try:
        data = request.json
        eid = db.create_event(
            title=data['title'],
            description=data.get('description', ''),
            event_date=datetime.strptime(data['event_date'], '%Y-%m-%d').date(),
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            event_type=data['event_type'],
            location=data.get('location', ''),
            status=data.get('status', 'запланировано')
        )
        return jsonify({'success': True, 'data': {'id': eid}}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/events/<int:eid>', methods=['PUT'])
def api_update_event(eid):
    try:
        data = request.json
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'event_date' in data:
            update_data['event_date'] = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
        if 'start_time' in data:
            update_data['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'location' in data:
            update_data['location'] = data['location']
        if 'status' in data:
            update_data['status'] = data['status']
        db.update_event(eid, **update_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/events/<int:eid>', methods=['DELETE'])
def api_delete_event(eid):
    try:
        db.delete_event(eid)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/events/range', methods=['GET'])
def api_events_range():
    try:
        start = datetime.strptime(request.args.get('start'), '%Y-%m-%d').date()
        end = datetime.strptime(request.args.get('end'), '%Y-%m-%d').date()
        events = db.get_events_by_range(start, end)
        return jsonify({'success': True, 'data': serialize_events(events)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/event-types', methods=['GET'])
def api_event_types():
    try:
        return jsonify({'success': True, 'data': db.get_event_types()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== API: УЧАСТНИКИ ====================

@app.route('/api/participants', methods=['GET'])
def api_get_participants():
    try:
        participants = db.get_participants()
        return jsonify({'success': True, 'data': serialize_participants(participants)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/participants/<int:pid>', methods=['GET'])
def api_get_participant(pid):
    try:
        p = db.get_participant(pid)
        if p:
            return jsonify({'success': True, 'data': serialize_participant(p)})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/participants', methods=['POST'])
def api_create_participant():
    try:
        data = request.json
        pid = db.create_participant(
            last_name=data['last_name'],
            first_name=data['first_name'],
            category=data['category'],
            phone=data.get('phone', ''),
            email=data.get('email', '')
        )
        return jsonify({'success': True, 'data': {'id': pid}}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/participants/<int:pid>', methods=['PUT'])
def api_update_participant(pid):
    try:
        data = request.json
        update_data = {}
        if 'last_name' in data:
            update_data['last_name'] = data['last_name']
        if 'first_name' in data:
            update_data['first_name'] = data['first_name']
        if 'category' in data:
            update_data['category'] = data['category']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'email' in data:
            update_data['email'] = data['email']
        db.update_participant(pid, **update_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/participants/<int:pid>', methods=['DELETE'])
def api_delete_participant(pid):
    try:
        db.delete_participant(pid)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/participants/search', methods=['GET'])
def api_search_participants():
    try:
        q = request.args.get('q', '')
        results = db.search_participants(q)
        return jsonify({'success': True, 'data': serialize_participants(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: ЗАПИСЬ ====================

@app.route('/api/events/<int:eid>/register', methods=['POST'])
def api_register(eid):
    try:
        data = request.json
        success = db.register(eid, data['participant_id'])
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/events/<int:eid>/unregister/<int:pid>', methods=['DELETE'])
def api_unregister(eid, pid):
    try:
        db.unregister(eid, pid)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/events/<int:eid>/participants', methods=['GET'])
def api_event_participants(eid):
    try:
        participants = db.get_event_participants(eid)
        return jsonify({'success': True, 'data': serialize_participants(participants)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/participants/<int:pid>/events', methods=['GET'])
def api_participant_events(pid):
    try:
        events = db.get_participant_events(pid)
        return jsonify({'success': True, 'data': serialize_events(events)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/registrations', methods=['GET'])
def api_get_registrations():
    """Получить все записи на мероприятия"""
    try:
        events = db.get_events()
        result = []
        for event in events:
            participants = db.get_event_participants(event['id'])
            result.append({
                'event_id': event['id'],
                'event_title': event['title'],
                'event_date': str(event['event_date']),
                'participants': serialize_participants(participants)
            })
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== API: СТАТИСТИКА ====================

@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    try:
        stats = db.get_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== API: ЛОГИ ====================

def serialize_log(log):
    if not log:
        return None
    result = {}
    for key, value in log.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result

@app.route('/api/logs', methods=['GET'])
def api_logs():
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = db.get_logs(limit)
        return jsonify({'success': True, 'data': [serialize_log(l) for l in logs]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== API: ОТЧЁТЫ PDF ====================

@app.route('/api/reports/events/pdf', methods=['GET'])
def api_events_pdf():
    try:
        start_str = request.args.get('start')
        end_str = request.args.get('end')

        print(f"Получены параметры: start={start_str}, end={end_str}")  # Отладка

        if not start_str or not end_str:
            return jsonify({'success': False, 'error': 'Не указаны даты'}), 400

        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()

        events = db.get_events_by_range(start, end)
        filename = pdf_exporter.export_events(events, start, end)
        return send_file(filename, as_attachment=True, download_name=f"events_{start}_{end}.pdf")
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reports/statistics/pdf', methods=['GET'])
def api_statistics_pdf():
    try:
        stats = db.get_statistics()
        filename = pdf_exporter.export_statistics(stats)
        return send_file(filename, as_attachment=True, download_name=f"statistics_{date.today()}.pdf")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reports/events/with-participants/pdf', methods=['GET'])
def api_events_with_participants_pdf():
    """Экспорт мероприятий с участниками в PDF (таблица)"""
    try:
        start = datetime.strptime(request.args.get('start'), '%Y-%m-%d').date()
        end = datetime.strptime(request.args.get('end'), '%Y-%m-%d').date()
        events = db.get_events_by_range(start, end)
        # Фильтруем только запланированные и проведённые
        filtered_events = [e for e in events if e['status'] in ('запланировано', 'проведено')]
        filename = pdf_exporter.export_events_with_participants_table(filtered_events, db, start, end)
        return send_file(filename, as_attachment=True, download_name=f"events_with_participants_{start}_{end}.pdf")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='127.0.0.1', port=port, threaded=True)