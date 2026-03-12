import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio
import calendar
import random
from datetime import datetime, date
from functools import partial
from ..components.theme import AppTheme

QUOTES = [
    "The secret of getting ahead is getting started. – Mark Twain",
    "Don't watch the clock; do what it does. Keep going. – Sam Levenson",
    "Push yourself, because no one else is going to do it for you.",
    "Great things never come from comfort zones.",
    "Success is the sum of small efforts, repeated day in and day out.",
    "Believe you can and you're halfway there. – Theodore Roosevelt",
    "The expert in anything was once a beginner.",
    "Dream big. Work hard. Stay focused.",
]


class DashboardView:
    def __init__(self, app):
        self.app = app
        now = datetime.now()
        self._view_month = now.month
        self._view_year  = now.year
        self._selected_day   = None
        self._selected_month = None
        self._selected_year  = None
        self._live_task          = None
        self._active_time_label  = None
        self.build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        # ── Header with month navigation ─────────────────────────────────────
        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=16, padding_bottom=14)
        )

        # Motivational quote
        self.quote_label = toga.Label(
            random.choice(QUOTES),
            style=Pack(font_size=9, color='#D0E8FF', text_align=CENTER,
                       margin_bottom=8)
        )
        header.add(self.quote_label)

        # Month nav row: < [Month Year] >
        nav_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        self.btn_prev = toga.Button(
            '<',
            on_press=self.prev_month,
            style=Pack(width=40, height=40, background_color=AppTheme.PRIMARY_DARK,
                       color='#FFFFFF', font_weight='bold', font_size=16)
        )
        self.month_label = toga.Label(
            '',
            style=Pack(flex=1, font_size=18, font_weight='bold',
                       color='#FFFFFF', text_align=CENTER)
        )
        self.btn_next = toga.Button(
            '>',
            on_press=self.next_month,
            style=Pack(width=40, height=40, background_color=AppTheme.PRIMARY_DARK,
                       color='#FFFFFF', font_weight='bold', font_size=16)
        )
        nav_row.add(self.btn_prev, self.month_label, self.btn_next)
        header.add(nav_row)

        # Exam countdown
        self.countdown_label = toga.Label(
            '',
            style=Pack(font_size=11, color='#FFE0A0', text_align=CENTER, margin_top=6)
        )
        header.add(self.countdown_label)

        header.add(toga.Label(
            'Tap a date to log a study session',
            style=Pack(font_size=10, color='#BDD9FF', margin_top=4, text_align=CENTER)
        ))
        self.main_box.add(header)

        # ── Daily goal bar ────────────────────────────────────────────────────
        self.goal_box = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.CARD_BG,
                       margin=12, margin_bottom=0)
        )
        goal_inner = toga.Box(style=Pack(direction=COLUMN, padding=10))
        goal_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        self.goal_text = toga.Label(
            '',
            style=Pack(flex=1, font_size=10, color=AppTheme.TEXT_SECONDARY)
        )
        self.goal_pct_label = toga.Label(
            '',
            style=Pack(font_size=10, font_weight='bold', color=AppTheme.PRIMARY)
        )
        goal_row.add(self.goal_text, self.goal_pct_label)
        goal_inner.add(goal_row)
        self.goal_bar_label = toga.Label(
            '',
            style=Pack(font_size=9, color=AppTheme.SUCCESS, margin_top=4)
        )
        goal_inner.add(self.goal_bar_label)
        self.goal_box.add(goal_inner)
        self.main_box.add(self.goal_box)

        # ── Calendar grid ─────────────────────────────────────────────────────
        self.calendar_wrapper = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.CARD_BG,
                       padding=12, margin=12)
        )
        self.main_box.add(self.calendar_wrapper)

        # ── Priority scroll area ──────────────────────────────────────────────
        self.dash_content = toga.Box(style=Pack(direction=COLUMN))
        self.scroll = toga.ScrollContainer(
            content=self.dash_content,
            style=Pack(flex=1, background_color=AppTheme.BACKGROUND)
        )
        self.main_box.add(self.scroll)

        # ── Subject-picker form ───────────────────────────────────────────────
        self.picker_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )
        pick_header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        pick_header.add(toga.Label(
            'Plan To-Do',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        self.pick_date_label = toga.Label(
            '', style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        )
        pick_header.add(self.pick_date_label)
        self.picker_box.add(pick_header)

        pick_inner = toga.Box(style=Pack(direction=COLUMN, flex=1, padding=16))
        
        # Select Subject
        pick_inner.add(self._field_label('Choose Subject'))
        self.subject_select = toga.Selection(
            items=['(no subjects yet)'], style=Pack(margin_bottom=16)
        )
        pick_inner.add(self.subject_select)

        # To-Do Input
        pick_inner.add(self._field_label('What to do?'))
        self.session_notes = toga.TextInput(
            placeholder='e.g. Read Chapter 4 and complete exercises...',
            style=Pack(margin_bottom=16, background_color=AppTheme.CARD_BG)
        )
        pick_inner.add(self.session_notes)

        # Buttons
        pick_btn_row = toga.Box(style=Pack(direction=ROW))
        pick_btn_row.add(toga.Button(
            'Add to Subject Todo',
            on_press=self.picker_save_todo,
            style=Pack(flex=1, background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_weight='bold', margin_right=8)
        ))
        pick_btn_row.add(toga.Button(
            'Cancel',
            on_press=self.goto_day_details,
            style=Pack(flex=1, background_color=AppTheme.CARD_BG,
                       color=AppTheme.DANGER, font_weight='bold')
        ))
        pick_inner.add(pick_btn_row)
        
        # Spacer
        pick_inner.add(toga.Box(style=Pack(height=16)))
        
        # Scroll container for the form
        self.picker_box.add(toga.ScrollContainer(content=pick_inner, style=Pack(flex=1)))

        # ── Day Details View ──────────────────────────────────────────────────
        self.day_details_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )
        detail_header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        self.detail_date_label = toga.Label(
            'Day Details', style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        )
        detail_header.add(self.detail_date_label)
        self.day_details_box.add(detail_header)

        detail_inner = toga.Box(style=Pack(direction=COLUMN, padding=16))
        
        # Subjects Studied
        detail_inner.add(self._field_label('Subjects Studied on this Date:'))
        self.studied_box = toga.Box(style=Pack(direction=COLUMN, margin_bottom=16))
        detail_inner.add(self.studied_box)

        # Existing Todos
        detail_inner.add(self._field_label('Existing Tasks/Todos:'))
        self.existing_todos_box = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_bottom=16))
        detail_inner.add(self.existing_todos_box)
        
        # Buttons
        detail_btn_row = toga.Box(style=Pack(direction=ROW))
        detail_btn_row.add(toga.Button(
            'Add New Task',
            on_press=self.show_plan_todo,
            style=Pack(flex=1, background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_weight='bold', margin_right=8)
        ))
        detail_btn_row.add(toga.Button(
            'Back to Dashboard',
            on_press=lambda w: self.app.show_dashboard(None),
            style=Pack(flex=1, background_color=AppTheme.CARD_BG,
                       color=AppTheme.TEXT_SECONDARY, font_weight='bold')
        ))
        detail_inner.add(detail_btn_row)

        self.day_details_box.add(toga.ScrollContainer(content=detail_inner, style=Pack(flex=1)))

    # ─────────────────────────────────────────────────────────────────────────
    # MONTH NAVIGATION
    # ─────────────────────────────────────────────────────────────────────────

    def prev_month(self, widget):
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._rebuild_calendar()

    def next_month(self, widget):
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._rebuild_calendar()

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _field_label(self, text):
        return toga.Label(
            text,
            style=Pack(font_size=11, font_weight='bold', color=AppTheme.TEXT_SECONDARY,
                       margin_bottom=4)
        )

    def _section_label(self, text):
        box = toga.Box(style=Pack(direction=ROW, padding=12, padding_bottom=6, padding_top=16))
        box.add(toga.Label(
            text,
            style=Pack(font_size=13, font_weight='bold', color=AppTheme.TEXT_PRIMARY)
        ))
        return box

    def _auto_escalate(self, subject):
        """Auto-set difficulty to Hard if deadline <= 3 days away."""
        try:
            dl = subject.get('deadline', subject.get('date', ''))
            exam_date = datetime.strptime(dl, '%d/%m/%Y').date()
            days_left = (exam_date - date.today()).days
            if 0 < days_left <= 3 and subject.get('diff', 'Easy') != 'Hard':
                subject['diff'] = 'Hard'
        except Exception:
            pass

    def _smart_schedule_score(self, subject):
        """
        AI-like scheduler:
        - Base score from deadline & difficulty
        - Penalty for subjects already studied heavily recently
        """
        try:
            # 1. Base Deadline Score
            diff_map  = {'Easy': 1.0, 'Medium': 1.5, 'Hard': 2.0}
            diff_val  = diff_map.get(subject.get('diff', 'Easy'), 1.0)
            
            dl        = subject.get('deadline', subject.get('date', ''))
            exam_date = datetime.strptime(dl, "%d/%m/%Y").date()
            days_left = (exam_date - date.today()).days
            
            if days_left < 0:
                base_score = 1000  # Overdue
            elif days_left == 0:
                base_score = 500   # Due today
            else:
                base_score = (100.0 / days_left) * diff_val
                
            # 2. Study History Penalty
            # Find how many minutes studied in the last 7 days for this subject
            recent_mins = 0
            now = datetime.now()
            for key, data in self.app.reading_history.items():
                if data.get('subject') == subject['name']:
                    try:
                        session_date_str = key.split('_')[0] # 'YYYY-MM-DD'
                        session_date = datetime.strptime(session_date_str, '%Y-%m-%d')
                        if (now - session_date).days <= 7:
                            recent_mins += data.get('today_mins', 0)
                    except Exception:
                        pass
                        
            # Penalize the score by reducing it based on recent study time
            # e.g., if studied 120 mins recently, reduce score by ~20%
            penalty_factor = max(0.5, 1.0 - (recent_mins / 600.0))
            
            return base_score * penalty_factor
            
        except Exception:
            return 0

    def _nearest_deadline_countdown(self):
        best_days = None
        best_name = ''
        for s in self.app.subjects_data:
            if s.get('completed'):
                continue
            try:
                dl = s.get('deadline', s.get('date', ''))
                exam_date = datetime.strptime(dl, '%d/%m/%Y').date()
                days_left = (exam_date - date.today()).days
                if days_left >= 0 and (best_days is None or days_left < best_days):
                    best_days = days_left
                    best_name = s['name']
            except Exception:
                pass
        if best_days is None:
            return ''
        if best_days == 0:
            return f'🚨 {best_name} is DUE TODAY!'
        if best_days == 1:
            return f'⚠️ {best_name} — 1 day left!'
        return f'📅 Next: {best_name} in {best_days} days'

    def _today_studied_mins(self):
        """Total minutes studied across all sessions saved today."""
        total = 0
        for data in self.app.reading_history.values():
            total += data.get('today_mins', 0)
        return total

    # ─────────────────────────────────────────────────────────────────────────
    # LIVE TICK
    # ─────────────────────────────────────────────────────────────────────────

    def start_live_tick(self):
        self.stop_live_tick()
        self._live_task = asyncio.create_task(self._live_loop())

    def stop_live_tick(self):
        if self._live_task and not self._live_task.done():
            self._live_task.cancel()
        self._live_task = None

    async def _live_loop(self):
        try:
            while True:
                timer = self.app.timer_page
                if (self._active_time_label is not None
                        and self.app.current_subject
                        and timer.is_running
                        and not timer.is_paused):
                    tl      = timer.time_left
                    total   = timer.total_duration_secs
                    elapsed = total - tl
                    pct     = int(elapsed / total * 100) if total else 0
                    hrs, rem  = divmod(tl, 3600)
                    mins, scs = divmod(rem, 60)
                    status_text = 'Break' if getattr(timer, 'is_break', False) else 'Running'
                    self._active_time_label.text = (
                        f"{status_text}: {hrs:02d}:{mins:02d}:{scs:02d}  {pct}%"
                    )
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # CALENDAR BUILDER
    # ─────────────────────────────────────────────────────────────────────────

    def _rebuild_calendar(self):
        m, y = self._view_month, self._view_year
        self.month_label.text = date(y, m, 1).strftime('%B %Y')

        self.calendar_wrapper.clear()

        cal_matrix = calendar.monthcalendar(y, m)

        subjects_by_day = {}
        for subj in self.app.subjects_data:
            dl = subj.get('deadline', subj.get('date', ''))
            try:
                sd, sm, sy = map(int, dl.split('/'))
                if sm == m and sy == y:
                    subjects_by_day.setdefault(sd, []).append(subj)
            except Exception:
                pass

        dow_row = toga.Box(style=Pack(direction=ROW, margin_bottom=6))
        for name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            dow_row.add(toga.Label(
                name,
                style=Pack(width=44, text_align=CENTER, font_size=10,
                           font_weight='bold', color=AppTheme.INACTIVE)
            ))
        self.calendar_wrapper.add(dow_row)

        today = date.today()
        for week in cal_matrix:
            row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
            for day in week:
                if day == 0:
                    row.add(toga.Box(style=Pack(width=44, height=44)))
                    continue

                has_event = day in subjects_by_day
                is_today  = (day == today.day and m == today.month and y == today.year)
                cell_date = date(y, m, day)
                is_past   = cell_date < today

                if is_today:
                    bg, fg, fw = AppTheme.PRIMARY, '#FFFFFF', 'bold'
                elif has_event:
                    bg, fg, fw = AppTheme.PRIMARY_LIGHT, AppTheme.PRIMARY_DARK, 'bold'
                elif is_past:
                    bg, fg, fw = AppTheme.CARD_BG, AppTheme.INACTIVE, 'normal'
                else:
                    bg, fg, fw = AppTheme.BACKGROUND, AppTheme.TEXT_PRIMARY, 'normal'

                row.add(toga.Button(
                    str(day),
                    on_press=partial(self.on_day_press, day=day,
                                     month=m, year=y, is_past=is_past),
                    style=Pack(width=44, height=44, background_color=bg,
                               color=fg, font_weight=fw, font_size=10)
                ))
            self.calendar_wrapper.add(row)

    # ─────────────────────────────────────────────────────────────────────────
    # REFRESH  (full page rebuild)
    # ─────────────────────────────────────────────────────────────────────────

    def refresh(self):
        self.stop_live_tick()
        self._active_time_label = None

        # Rotate quote each refresh
        self.quote_label.text = random.choice(QUOTES)

        # Exam countdown
        self.countdown_label.text = self._nearest_deadline_countdown()

        # Auto-escalate difficulties
        for s in self.app.subjects_data:
            if not s.get('completed'):
                self._auto_escalate(s)

        now = datetime.now()
        self._view_month = now.month
        self._view_year  = now.year

        self._rebuild_calendar()

        # Daily goal bar
        goal_mins = getattr(self.app, 'daily_goal_mins', 120)
        today_mins = self._today_studied_mins()
        pct = min(100, int(today_mins / goal_mins * 100)) if goal_mins else 0
        self.goal_text.text = f'🎯 Today: {today_mins}/{goal_mins} min'
        self.goal_pct_label.text = f'{pct}%'
        # Text-based progress bar
        filled = int(pct / 5)   # 20 chars = 100%
        bar_str = '█' * filled + '░' * (20 - filled)
        self.goal_bar_label.text = bar_str
        self.goal_bar_label.style.color = AppTheme.SUCCESS if pct >= 100 else AppTheme.PRIMARY

        # Smart Priority -> Recommended Today
        self.dash_content.clear()
        pending_list   = [s for s in self.app.subjects_data if not s.get('completed')]
        completed_list = [s for s in self.app.subjects_data if s.get('completed')]

        self.dash_content.add(self._section_label('🤖 Recommended Today (Smart Schedule)'))
        if not pending_list:
            empty = toga.Box(style=Pack(
                direction=COLUMN, background_color=AppTheme.CARD_BG,
                padding=16, margin=12, align_items=CENTER
            ))
            empty.add(toga.Label(
                'No pending tasks!',
                style=Pack(color=AppTheme.SUCCESS, font_size=13, font_weight='bold')
            ))
            self.dash_content.add(empty)
        else:
            # Score and sort them
            scored_list = []
            for item in pending_list:
                score = self._smart_schedule_score(item)
                scored_list.append((score, item))
                
            scored_list.sort(key=lambda x: x[0], reverse=True)
            
            for score, item in scored_list:
                self.dash_content.add(self._priority_card(item, score))

        if completed_list:
            self.dash_content.add(self._section_label('Completed'))
            for item in completed_list:
                self.dash_content.add(self._completed_card(item))

        self.dash_content.add(toga.Box(style=Pack(height=20)))

        if self.app.current_subject and self.app.timer_page.is_running:
            self.start_live_tick()

    # ─────────────────────────────────────────────────────────────────────────
    # CARDS
    # ─────────────────────────────────────────────────────────────────────────

    def _priority_card(self, item, score=0):
        card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            margin=12, margin_top=0, margin_bottom=8, padding=14,
            align_items=CENTER
        ))

        diff_color = {
            'Easy': AppTheme.SUCCESS, 'Medium': AppTheme.WARNING,
            'Hard': AppTheme.DANGER
        }.get(item.get('diff', 'Easy'), AppTheme.PRIMARY)
        card.add(toga.Box(style=Pack(
            width=4, height=48, background_color=diff_color, margin_right=12
        )))

        info = toga.Box(style=Pack(direction=COLUMN, flex=1))
        
        # Determine Smart Tag
        tag = ''
        if score >= 1000: tag = '🔥 Overdue'
        elif score >= 500: tag = '⚡ Due Today'
        elif score > 50: tag = '🤖 Focus'
        
        title_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        title_row.add(toga.Label(item['name'], style=Pack(font_weight='bold', font_size=13, color=AppTheme.TEXT_PRIMARY)))
        if tag:
            title_row.add(toga.Label(tag, style=Pack(font_size=9, font_weight='bold', color=AppTheme.PRIMARY, margin_left=8)))
        info.add(title_row)
        dl = item.get('deadline', item.get('date', ''))
        # Show days left
        days_str = ''
        try:
            exam_date = datetime.strptime(dl, '%d/%m/%Y').date()
            days_left = (exam_date - date.today()).days
            if days_left == 0:
                days_str = '  🔴 DUE TODAY'
            elif days_left < 0:
                days_str = f'  ⚠️ {-days_left}d overdue'
            else:
                days_str = f'  · {days_left}d left'
        except Exception:
            pass
        info.add(toga.Label(
            f"{dl}  {item.get('diff', '')}{days_str}",
            style=Pack(font_size=10, color=AppTheme.TEXT_SECONDARY, margin_top=2)
        ))

        timer    = self.app.timer_page
        is_active = (self.app.current_subject == item['name'] and timer.is_running)
        if is_active:
            tl      = timer.time_left
            total   = timer.total_duration_secs
            elapsed = total - tl
            pct     = int(elapsed / total * 100) if total else 0
            hrs, rem  = divmod(tl, 3600)
            mins, scs = divmod(rem, 60)
            status_text = 'Break' if getattr(timer, 'is_break', False) else 'Running'
            timer_label = toga.Label(
                f"{status_text}: {hrs:02d}:{mins:02d}:{scs:02d}  {pct}%",
                style=Pack(font_size=10, color=AppTheme.PRIMARY, margin_top=3,
                           font_weight='bold')
            )
            info.add(timer_label)
            self._active_time_label = timer_label

        if is_active:
            btn_col = toga.Box(style=Pack(direction=COLUMN))
            btn_col.add(toga.Button(
                'Resume',
                on_press=partial(self.start_reading, subject=item),
                style=Pack(width=85, font_size=9, font_weight='bold',
                           background_color=AppTheme.SUCCESS, color='#FFFFFF',
                           margin_bottom=4)
            ))
            btn_col.add(toga.Button(
                'Cancel',
                on_press=partial(self.cancel_timer, subject_name=item['name']),
                style=Pack(width=85, font_size=9, font_weight='bold',
                           background_color=AppTheme.DANGER, color='#FFFFFF')
            ))
            card.add(info, btn_col)
        else:
            card.add(info, toga.Button(
                'Start',
                on_press=partial(self.start_reading, subject=item),
                style=Pack(width=75, font_size=9, font_weight='bold',
                           background_color=AppTheme.PRIMARY, color='#FFFFFF')
            ))
        return card

    def _completed_card(self, item):
        card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            margin=12, margin_top=0, margin_bottom=6, padding=12,
            align_items=CENTER
        ))
        card.add(toga.Label(
            f"✅ {item['name']}",
            style=Pack(flex=1, color=AppTheme.INACTIVE, font_size=12)
        ))
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # CALENDAR HANDLERS
    # ─────────────────────────────────────────────────────────────────────────

    def on_day_press(self, widget, day, month, year, is_past=False):
        self._selected_day   = day
        self._selected_month = month
        self._selected_year  = year

        if is_past:
            names = [s['name'] for s in self.app.subjects_data]
        else:
            names = [s['name'] for s in self.app.subjects_data if not s.get('completed')]
        if not names:
            names = ['(no subjects yet)']
        self.subject_select.items = names
        self.subject_select.value = names[0]

        self.pick_date_label.text = (
            f"Past date: {day:02d}/{month:02d}/{year}" if is_past
            else f"Date: {day:02d}/{month:02d}/{year}"
        )
        self.detail_date_label.text = f"{day:02d}/{month:02d}/{year} ({'Past' if is_past else 'Upcoming'})"
        
        self.picker_refresh_todos(day, month, year)

        self.stop_live_tick()
        self.app.content_area.clear()
        self.app.update_nav_style('dash')
        self.app.content_area.add(self.day_details_box)

    def show_plan_todo(self, widget):
        self.app.content_area.clear()
        self.app.content_area.add(self.picker_box)

    def goto_day_details(self, widget):
        self.app.content_area.clear()
        self.app.content_area.add(self.day_details_box)

    def picker_refresh_todos(self, day, month, year):
        target_date_str = f"{day:02d}/{month:02d}/{year}"
        self.existing_todos_box.clear()
        self.studied_box.clear()

        # Render Study History for this date
        # reading_history keys look like "2024-03-07_Math"
        target_db_date = f"{year}-{month:02d}-{day:02d}"
        studied_any = False
        
        for key, data in self.app.reading_history.items():
            if key.startswith(target_db_date):
                studied_any = True
                subj = data.get('subject', 'Unknown Form')
                mins = data.get('minutes', data.get('today_mins', 0))
                poms = data.get('pomodoros', 0)
                
                row = toga.Box(style=Pack(direction=ROW, background_color=AppTheme.CARD_BG, padding=8, margin_bottom=4, align_items=CENTER))
                row.add(toga.Label(f"📚 {subj}", style=Pack(font_size=11, font_weight='bold', color=AppTheme.SUCCESS, flex=1)))
                row.add(toga.Label(f"{mins} mins | {poms} poms", style=Pack(font_size=10, color=AppTheme.TEXT_SECONDARY)))
                self.studied_box.add(row)
                
        if not studied_any:
             self.studied_box.add(toga.Label(
                'No recorded study sessions for this date.',
                style=Pack(font_size=10, color=AppTheme.INACTIVE, font_style='italic')
            ))

        # Render Existing Todos
        has_todos = False
        for s in self.app.subjects_data:
            dl = s.get('deadline', s.get('date', ''))
            if dl == target_date_str:
                has_todos = True
                todo_text = s.get('todo', '')
                if not todo_text:
                    todo_text = '(No specific to-do text set)'
                
                row = toga.Box(style=Pack(direction=ROW, background_color=AppTheme.CARD_BG, padding=8, margin_bottom=4, align_items=CENTER))
                
                info_col = toga.Box(style=Pack(direction=COLUMN, flex=1))
                info_col.add(toga.Label(s['name'], style=Pack(font_size=10, font_weight='bold', color=AppTheme.PRIMARY)))
                # Show truncated version in the list if it's long
                display_text = todo_text if len(todo_text) < 40 else todo_text[:37] + '...'
                info_col.add(toga.Label(display_text, style=Pack(font_size=11, color=AppTheme.TEXT_PRIMARY)))
                
                row.add(info_col)
                
                view_btn = toga.Button(
                    'View',
                    on_press=partial(self.picker_view_todo, subject_name=s['name'], todo_text=todo_text),
                    style=Pack(font_size=9, background_color=AppTheme.PRIMARY, color='#FFFFFF', font_weight='bold')
                )
                row.add(view_btn)
                
                self.existing_todos_box.add(row)
                
        if not has_todos:
            self.existing_todos_box.add(toga.Label(
                'No subjects or to-dos set for this date.',
                style=Pack(font_size=10, color=AppTheme.INACTIVE, font_style='italic')
            ))

    async def picker_view_todo(self, widget, subject_name, todo_text):
        await self.app.main_window.dialog(
            toga.InfoDialog(f"To-Do: {subject_name}", todo_text)
        )

    async def picker_save_todo(self, widget):
        chosen = self.subject_select.value
        todo_text = self.session_notes.value.strip()
        if not chosen or chosen == '(no subjects yet)' or not todo_text:
            return
            
        target_date_str = f"{self._selected_day:02d}/{self._selected_month:02d}/{self._selected_year}"
        
        for s in self.app.subjects_data:
            if s['name'] == chosen:
                existing_todo = s.get('todo', '').strip()
                if existing_todo:
                    s['todo'] = existing_todo + f"\n- {todo_text}"
                else:
                    s['todo'] = todo_text
                
                s['deadline'] = target_date_str
                s['date'] = target_date_str # backward compat
                break
                
        self.app.save_data()
        self.session_notes.value = ''
        
        # Refresh the day details view with the newly added task seamlessly
        self.picker_refresh_todos(self._selected_day, self._selected_month, self._selected_year)
        
        # Show success popup then go back to the Day Details view
        await self.app.main_window.dialog(
            toga.InfoDialog('Success', 'The task has been added!')
        )
        self.app.content_area.clear()
        self.app.content_area.add(self.day_details_box)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIORITY START
    # ─────────────────────────────────────────────────────────────────────────

    def start_reading(self, widget, subject):
        timer = self.app.timer_page
        self.stop_live_tick()
        if self.app.current_subject == subject['name'] and timer.is_running:
            self.app.show_timer(None)
        else:
            self.app.current_subject = subject['name']
            timer.prepare_timer(subject['name'])
            self.app.show_timer(None)

    def cancel_timer(self, widget, subject_name):
        """Stop the running timer and clear state without saving a session."""
        timer = self.app.timer_page
        timer.is_running = False
        timer.is_paused  = True
        timer.time_left  = 0
        self.app.current_subject = None
        self.stop_live_tick()
        self._active_time_label = None
        self.refresh()