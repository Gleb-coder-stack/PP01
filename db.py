"""
Модуль работы с базой данных PostgreSQL
"""

import psycopg2
from psycopg2 import extras
from typing import List, Dict, Optional
from datetime import datetime, date, time
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Класс для работы с БД"""

    def __init__(self):
        self.conn = None
        self._connect()

    def _connect(self):
        """Установить соединение"""
        try:
            password = os.getenv('DB_PASSWORD', '')
            if password:
                self.conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', 5432),
                    database=os.getenv('DB_NAME', 'step_toward_events'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=password
                )
            else:
                self.conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', 5432),
                    database=os.getenv('DB_NAME', 'step_toward_events'),
                    user=os.getenv('DB_USER', 'postgres')
                )
            self.conn.autocommit = False
            print("✅ Подключение к PostgreSQL установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            raise

    def _cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _execute(self, query: str, params: tuple = None) -> List[Dict]:
        with self._cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            self.conn.commit()
            return []

    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        result = self._execute(query, params)
        return result[0] if result else None

    def _execute_insert(self, query: str, params: tuple = None) -> int:
        with self._cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()
            if cur.description:
                row = cur.fetchone()
                return row.get('id') if row else None
            return None

    def close(self):
        if self.conn:
            self.conn.close()
            print("🔌 Соединение с БД закрыто")

    # ========== МЕРОПРИЯТИЯ ==========

    def get_events(self) -> List[Dict]:
        """Все мероприятия"""
        return self._execute("""
            SELECT 
                e.id, e.title, e.description, e.event_date, e.start_time, e.end_time,
                et.name as event_type, e.location, e.status, e.created_at,
                COALESCE((SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id), 0) as participants_count
            FROM events e
            LEFT JOIN event_types et ON e.event_type_id = et.id
            ORDER BY e.event_date, e.start_time
        """)

    def get_events_by_date(self, d: date) -> List[Dict]:
        """Мероприятия на дату"""
        return self._execute("""
            SELECT 
                e.id, e.title, e.event_date, e.start_time, e.end_time,
                et.name as event_type, e.location, e.status,
                COALESCE((SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id), 0) as participants_count
            FROM events e
            LEFT JOIN event_types et ON e.event_type_id = et.id
            WHERE e.event_date = %s
            ORDER BY e.start_time
        """, (d,))

    def get_events_by_range(self, start: date, end: date) -> List[Dict]:
        """Мероприятия за период"""
        return self._execute("""
            SELECT 
                e.id, e.title, e.event_date, e.start_time, e.end_time,
                et.name as event_type, e.location, e.status,
                COALESCE((SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id), 0) as participants_count
            FROM events e
            LEFT JOIN event_types et ON e.event_type_id = et.id
            WHERE e.event_date BETWEEN %s AND %s
            ORDER BY e.event_date, e.start_time
        """, (start, end))

    def get_event(self, event_id: int) -> Optional[Dict]:
        """Мероприятие по ID"""
        return self._execute_one("""
            SELECT 
                e.*, et.name as event_type_name
            FROM events e
            LEFT JOIN event_types et ON e.event_type_id = et.id
            WHERE e.id = %s
        """, (event_id,))

    def create_event(self, title: str, description: str, event_date: date,
                     start_time: time, event_type: str, location: str, status: str) -> int:
        """Создать мероприятие"""
        type_row = self._execute_one("SELECT id FROM event_types WHERE name = %s", (event_type,))
        event_type_id = type_row['id'] if type_row else None

        return self._execute_insert("""
            INSERT INTO events (title, description, event_date, start_time, event_type_id, location, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (title, description, event_date, start_time, event_type_id, location, status))

    def update_event(self, event_id: int, **kwargs) -> bool:
        """Обновить мероприятие"""
        allowed = ['title', 'description', 'event_date', 'start_time', 'location', 'status']
        updates = []
        values = []
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                updates.append(f"{k} = %s")
                values.append(v)
        if not updates:
            return False
        values.append(event_id)
        self._execute(f"UPDATE events SET {', '.join(updates)} WHERE id = %s", tuple(values))
        return True

    def delete_event(self, event_id: int) -> bool:
        """Удалить мероприятие"""
        self._execute("DELETE FROM events WHERE id = %s", (event_id,))
        return True

    def get_event_types(self) -> List[str]:
        """Типы мероприятий"""
        rows = self._execute("SELECT name FROM event_types ORDER BY id")
        return [r['name'] for r in rows]

    # ========== УЧАСТНИКИ ==========

    def get_participants(self) -> List[Dict]:
        """Все участники"""
        return self._execute("""
            SELECT 
                p.id, p.last_name, p.first_name, p.category, p.phone, p.email, p.registration_date,
                COALESCE((SELECT COUNT(*) FROM event_registrations WHERE participant_id = p.id), 0) as events_count
            FROM participants p
            WHERE p.is_active = TRUE
            ORDER BY p.last_name, p.first_name
        """)

    def get_participant(self, pid: int) -> Optional[Dict]:
        """Участник по ID"""
        return self._execute_one("SELECT * FROM participants WHERE id = %s", (pid,))

    def create_participant(self, last_name: str, first_name: str, category: str,
                           phone: str = "", email: str = "") -> int:
        """Создать участника"""
        return self._execute_insert("""
            INSERT INTO participants (last_name, first_name, category, phone, email)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (last_name, first_name, category, phone, email))

    def update_participant(self, pid: int, **kwargs) -> bool:
        """Обновить участника"""
        allowed = ['last_name', 'first_name', 'category', 'phone', 'email', 'is_active']
        updates = []
        values = []
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                updates.append(f"{k} = %s")
                values.append(v)
        if not updates:
            return False
        values.append(pid)
        self._execute(f"UPDATE participants SET {', '.join(updates)} WHERE id = %s", tuple(values))
        return True

    def delete_participant(self, pid: int) -> bool:
        """Удалить участника"""
        self._execute("DELETE FROM participants WHERE id = %s", (pid,))
        return True

    def search_participants(self, query: str) -> List[Dict]:
        """Поиск участников"""
        pattern = f"%{query}%"
        return self._execute("""
            SELECT 
                p.id, p.last_name, p.first_name, p.category, p.phone, p.email,
                COALESCE((SELECT COUNT(*) FROM event_registrations WHERE participant_id = p.id), 0) as events_count
            FROM participants p
            WHERE p.last_name ILIKE %s OR p.first_name ILIKE %s OR p.phone ILIKE %s
            ORDER BY p.last_name, p.first_name
        """, (pattern, pattern, pattern))

    # ========== ЗАПИСЬ НА МЕРОПРИЯТИЯ ==========

    def register(self, event_id: int, participant_id: int) -> bool:
        """Записать участника на мероприятие"""
        try:
            self._execute("""
                INSERT INTO event_registrations (event_id, participant_id, registration_date)
                VALUES (%s, %s, CURRENT_DATE)
            """, (event_id, participant_id))
            return True
        except Exception:
            self.conn.rollback()
            return False

    def unregister(self, event_id: int, participant_id: int) -> bool:
        """Отменить запись участника"""
        self._execute("""
            DELETE FROM event_registrations 
            WHERE event_id = %s AND participant_id = %s
        """, (event_id, participant_id))
        return True

    def get_event_participants(self, event_id: int) -> List[Dict]:
        """Участники мероприятия"""
        return self._execute("""
            SELECT p.id, p.last_name, p.first_name, p.category, p.phone, 
                   er.attendance_status, er.registration_date
            FROM event_registrations er
            JOIN participants p ON er.participant_id = p.id
            WHERE er.event_id = %s
            ORDER BY p.last_name, p.first_name
        """, (event_id,))

    def get_participant_events(self, participant_id: int) -> List[Dict]:
        """Мероприятия участника"""
        return self._execute("""
            SELECT e.id, e.title, e.event_date, e.start_time, e.location, er.attendance_status
            FROM event_registrations er
            JOIN events e ON er.event_id = e.id
            WHERE er.participant_id = %s
            ORDER BY e.event_date DESC
        """, (participant_id,))

    # ========== СТАТИСТИКА ==========

    def get_statistics(self) -> Dict:
        """Получить статистику"""
        stats = {}

        total_events = self._execute_one("SELECT COUNT(*) as cnt FROM events")
        stats['total_events'] = total_events['cnt'] if total_events else 0

        total_participants = self._execute_one("SELECT COUNT(*) as cnt FROM participants WHERE is_active = TRUE")
        stats['total_participants'] = total_participants['cnt'] if total_participants else 0

        upcoming = self._execute_one("""
            SELECT COUNT(*) as cnt FROM events 
            WHERE event_date >= CURRENT_DATE AND status = 'запланировано'
        """)
        stats['upcoming_events'] = upcoming['cnt'] if upcoming else 0

        # Статистика по статусам мероприятий
        status_stats = self._execute("SELECT status, COUNT(*) as cnt FROM events GROUP BY status")
        stats['events_by_status'] = {r['status']: r['cnt'] for r in status_stats}

        # Статистика по категориям участников
        category_stats = self._execute("SELECT category, COUNT(*) as cnt FROM participants GROUP BY category")
        stats['participants_by_category'] = {r['category']: r['cnt'] for r in category_stats if r['category']}

        return stats

    # ========== ЛОГИ ==========

    def get_logs(self, limit: int = 100) -> List[Dict]:
        """Получить логи"""
        return self._execute("""
            SELECT * FROM logs 
            ORDER BY operation_time DESC 
            LIMIT %s
        """, (limit,))


db = Database()