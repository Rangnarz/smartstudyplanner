import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import calendar
from datetime import datetime, date
from functools import partial
from ..components.theme import AppTheme


class DashboardView:
    def __init__(self, app):
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        # Header
        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        now = datetime.now()
        header.add(toga.Label(
            f"{now.strftime('%B %Y')}",
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        header.add(toga.Label(
            "Tap a date to add a task",
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        ))
        self.main_box.add(header)

        # Calendar
        self.calendar_wrapper = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.CARD_BG,
                       padding=12, margin=12)
        )
        self.main_box.add(self.calendar_wrapper)

        # Priority list
        self.dash_content = toga.Box(style=Pack(direction=COLUMN, padding=0, padding_top=4))
        self.scroll = toga.ScrollContainer(
            content=self.dash_content,
            style=Pack(flex=1, background_color=AppTheme.BACKGROUND)
        )
        self.main_box.add(self.scroll)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _section_label(self, text):
        box = toga.Box(style=Pack(
            direction=ROW, padding=12, padding_bottom=6, padding_top=16
        ))
        box.add(toga.Label(
            text,
            style=Pack(font_size=13, font_weight='bold', color=AppTheme.TEXT_PRIMARY)
        ))
        return box

    def _divider(self):
        d = toga.Box(style=Pack(
            height=1, background_color=AppTheme.BORDER,
            margin_left=12, margin_right=12
        ))
        return d

    def calculate_priority(self, subject):
        try:
            diff_map = {'Easy': 1, 'Medium': 2, 'Hard': 3}
            diff_val = diff_map.get(subject.get('diff', 'Easy'), 1)
            exam_date = datetime.strptime(subject.get('date', '01/01/2026'), "%d/%m/%Y").date()
            days_left = (exam_date - date.today()).days
            if days_left <= 0:
                return 999
            return diff_val / days_left
        except:
            return 0

    # ── calendar ──────────────────────────────────────────────────────────────

    def refresh(self):
        self.calendar_wrapper.clear()
        self.dash_content.clear()

        now = datetime.now()
        cal_matrix = calendar.monthcalendar(now.year, now.month)

        # Map subjects to day numbers
        subjects_by_day = {}
        for subj in self.app.subjects_data:
            try:
                d, m, y = map(int, subj['date'].split('/'))
                if m == now.month and y == now.year:
                    subjects_by_day.setdefault(d, []).append(subj)
            except:
                pass

        # Day-of-week header
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
                is_today = (day == today.day and now.month == today.month and now.year == today.year)

                if is_today:
                    bg = AppTheme.PRIMARY
                    fg = '#FFFFFF'
                    fw = 'bold'
                elif has_event:
                    bg = AppTheme.PRIMARY_LIGHT
                    fg = AppTheme.PRIMARY_DARK
                    fw = 'bold'
                else:
                    bg = AppTheme.BACKGROUND
                    fg = AppTheme.TEXT_PRIMARY
                    fw = 'normal'

                if has_event:
                    # Clickable — shows popup; also allows "add new task for this day"
                    btn = toga.Button(
                        str(day),
                        on_press=partial(self.on_day_press, day=day,
                                         events=subjects_by_day.get(day, []),
                                         month=now.month, year=now.year),
                        style=Pack(width=44, height=44, background_color=bg,
                                   color=fg, font_weight=fw, font_size=10)
                    )
                    row.add(btn)
                else:
                    # Empty day — clicking opens "add task" form pre-filled with date
                    btn = toga.Button(
                        str(day),
                        on_press=partial(self.on_empty_day_press, day=day,
                                         month=now.month, year=now.year),
                        style=Pack(width=44, height=44, background_color=bg,
                                   color=fg, font_weight=fw, font_size=10)
                    )
                    row.add(btn)

            self.calendar_wrapper.add(row)

        # ── Smart Priority ────────────────────────────────────────────────────
        pending_list = [s for s in self.app.subjects_data if not s.get('completed')]
        completed_list = [s for s in self.app.subjects_data if s.get('completed')]

        self.dash_content.add(self._section_label('💡 Smart Priority'))

        if not pending_list:
            empty = toga.Box(style=Pack(
                direction=COLUMN, background_color=AppTheme.CARD_BG,
                padding=16, margin=12, align_items=CENTER
            ))
            empty.add(toga.Label(
                '🎉 No pending tasks!',
                style=Pack(color=AppTheme.SUCCESS, font_size=13, font_weight='bold')
            ))
            self.dash_content.add(empty)
        else:
            sorted_pending = sorted(pending_list, key=self.calculate_priority, reverse=True)
            for item in sorted_pending:
                self.dash_content.add(self._priority_card(item))

        self.dash_content.add(self._section_label('✅ Completed'))
        for item in completed_list:
            self.dash_content.add(self._completed_card(item))

        # Bottom padding
        self.dash_content.add(toga.Box(style=Pack(height=20)))

    # ── card builders ─────────────────────────────────────────────────────────

    def _priority_card(self, item):
        card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            margin=12, margin_top=0, margin_bottom=8, padding=14,
            align_items=CENTER
        ))

        # Difficulty badge color
        diff_color = {'Easy': AppTheme.SUCCESS, 'Medium': AppTheme.WARNING,
                      'Hard': AppTheme.DANGER}.get(item['diff'], AppTheme.PRIMARY)

        badge = toga.Box(style=Pack(
            width=4, height=40, background_color=diff_color,
            margin_right=12
        ))

        info = toga.Box(style=Pack(direction=COLUMN, flex=1))
        info.add(toga.Label(
            item['name'],
            style=Pack(font_weight='bold', font_size=13, color=AppTheme.TEXT_PRIMARY)
        ))
        info.add(toga.Label(
            f"📅 {item['date']}  ·  {item['diff']}",
            style=Pack(font_size=10, color=AppTheme.TEXT_SECONDARY, margin_top=2)
        ))

        start_btn = toga.Button(
            'Start',
            on_press=partial(self.start_reading, subject=item),
            style=Pack(
                width=60, font_size=10, font_weight='bold',
                background_color=AppTheme.PRIMARY, color='#FFFFFF'
            )
        )

        card.add(badge, info, start_btn)
        return card

    def _completed_card(self, item):
        card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            margin=12, margin_top=0, margin_bottom=6, padding=12,
            align_items=CENTER
        ))
        card.add(toga.Label(
            f"✔  {item['name']}",
            style=Pack(flex=1, color=AppTheme.INACTIVE, font_size=12)
        ))
        return card

    # ── event handlers ────────────────────────────────────────────────────────

    async def on_day_press(self, widget, day, events, month, year):
        """Day that already has tasks — show list, then offer to add another."""
        details = f"Tasks on {day:02d}/{month:02d}/{year}:\n\n"
        for ev in events:
            details += f"• {ev['name']}  [{ev['diff']}]\n"
        details += "\nTap OK to add a new task for this date."
        result = await self.app.main_window.dialog(
            toga.ConfirmDialog("📅 Day Schedule", details)
        )
        if result:
            self._open_form_for_date(day, month, year)

    def on_empty_day_press(self, widget, day, month, year):
        """Empty day — immediately open add-task form with date pre-filled."""
        self._open_form_for_date(day, month, year)

    def _open_form_for_date(self, day, month, year):
        """Navigate to the subjects form pre-filled with the given date."""
        from datetime import date as _date
        self.app.subjects_page.open_form_with_date(_date(year, month, day))

    def start_reading(self, widget, subject):
        """Open timer with custom duration picker."""
        self.app.current_subject = subject['name']
        self.app.timer_page.prepare_timer(subject['name'])
        self.app.show_timer(None)
