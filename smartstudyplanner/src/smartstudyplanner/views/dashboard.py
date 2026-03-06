import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio
import calendar
from datetime import datetime, date
from functools import partial
from ..components.theme import AppTheme


class DashboardView:
    def __init__(self, app):
        self.app = app
        self._selected_day   = None
        self._selected_month = None
        self._selected_year  = None
        self._live_task      = None          # asyncio Task for the ticker
        self._active_time_label  = None      # Label ref for the running time
        self._active_pct_shown   = None      # last pct string shown
        self.build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        now = datetime.now()
        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        header.add(toga.Label(
            now.strftime('%B %Y'),
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        header.add(toga.Label(
            'Tap a date to log a study session',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        ))
        self.main_box.add(header)

        self.calendar_wrapper = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.CARD_BG,
                       padding=12, margin=12)
        )
        self.main_box.add(self.calendar_wrapper)

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
            'Log Study Session',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        self.pick_date_label = toga.Label(
            '', style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        )
        pick_header.add(self.pick_date_label)
        self.picker_box.add(pick_header)

        pick_inner = toga.Box(style=Pack(direction=COLUMN, padding=16))
        pick_inner.add(self._field_label('Choose Subject'))
        self.subject_select = toga.Selection(
            items=['(no subjects yet)'], style=Pack(margin_bottom=16)
        )
        pick_inner.add(self.subject_select)

        pick_inner.add(self._field_label('Session Notes'))
        self.session_notes = toga.TextInput(
            placeholder='e.g. Reading 5 chapters...',
            style=Pack(margin_bottom=24, background_color=AppTheme.CARD_BG)
        )
        pick_inner.add(self.session_notes)

        pick_btn_row = toga.Box(style=Pack(direction=ROW))
        pick_btn_row.add(toga.Button(
            'Start Timer',
            on_press=self.picker_start_timer,
            style=Pack(flex=1, background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_weight='bold', margin_right=8)
        ))
        pick_btn_row.add(toga.Button(
            'Cancel',
            on_press=lambda w: self.stop_live_tick() or self.app.show_dashboard(None),
            style=Pack(flex=1, background_color=AppTheme.CARD_BG,
                       color=AppTheme.DANGER, font_weight='bold')
        ))
        pick_inner.add(pick_btn_row)
        self.picker_box.add(pick_inner)

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

    def calculate_priority(self, subject):
        try:
            diff_map  = {'Easy': 1, 'Medium': 2, 'Hard': 3}
            diff_val  = diff_map.get(subject.get('diff', 'Easy'), 1)
            dl        = subject.get('deadline', subject.get('date', '01/01/2026'))
            exam_date = datetime.strptime(dl, "%d/%m/%Y").date()
            days_left = (exam_date - date.today()).days
            if days_left <= 0:
                return 999
            return diff_val / days_left
        except:
            return 0

    # ─────────────────────────────────────────────────────────────────────────
    # LIVE TICK  – updates only the timer label every second
    # ─────────────────────────────────────────────────────────────────────────

    def start_live_tick(self):
        """Start (or restart) the 1-second ticker that updates the timer label."""
        self.stop_live_tick()
        self._live_task = asyncio.create_task(self._live_loop())

    def stop_live_tick(self):
        if self._live_task and not self._live_task.done():
            self._live_task.cancel()
        self._live_task = None

    async def _live_loop(self):
        """Runs every second while the dashboard is visible.
        Only updates the timer text label — never rebuilds the whole layout."""
        try:
            while True:
                timer = self.app.timer_page
                if (self._active_time_label is not None
                        and self.app.current_subject
                        and timer.is_running
                        and not timer.is_paused):
                    tl    = timer.time_left
                    total = timer.total_duration_secs
                    elapsed = total - tl
                    pct   = int(elapsed / total * 100) if total else 0
                    hrs, rem  = divmod(tl, 3600)
                    mins, scs = divmod(rem, 60)
                    self._active_time_label.text = (
                        f"Running: {hrs:02d}:{mins:02d}:{scs:02d}  {pct}%"
                    )
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # REFRESH  – rebuilds cards once, then starts the ticker
    # ─────────────────────────────────────────────────────────────────────────

    def refresh(self):
        self.stop_live_tick()          # cancel old tick if any
        self._active_time_label = None

        self.calendar_wrapper.clear()
        self.dash_content.clear()

        now        = datetime.now()
        cal_matrix = calendar.monthcalendar(now.year, now.month)

        subjects_by_day = {}
        for subj in self.app.subjects_data:
            dl = subj.get('deadline', subj.get('date', ''))
            try:
                d, m, y = map(int, dl.split('/'))
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
                is_today  = (day == today.day and now.month == today.month
                             and now.year == today.year)
                is_past   = date(now.year, now.month, day) < today

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
                                     month=now.month, year=now.year,
                                     is_past=is_past),
                    style=Pack(width=44, height=44, background_color=bg,
                               color=fg, font_weight=fw, font_size=10)
                ))
            self.calendar_wrapper.add(row)

        # Smart Priority
        pending_list   = [s for s in self.app.subjects_data if not s.get('completed')]
        completed_list = [s for s in self.app.subjects_data if s.get('completed')]

        self.dash_content.add(self._section_label('Smart Priority'))
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
            for item in sorted(pending_list, key=self.calculate_priority, reverse=True):
                self.dash_content.add(self._priority_card(item))

        self.dash_content.add(self._section_label('Completed'))
        for item in completed_list:
            self.dash_content.add(self._completed_card(item))

        self.dash_content.add(toga.Box(style=Pack(height=20)))

        # Start live ticker if a timer is running
        if self.app.current_subject and self.app.timer_page.is_running:
            self.start_live_tick()

    # ─────────────────────────────────────────────────────────────────────────
    # CARDS
    # ─────────────────────────────────────────────────────────────────────────

    def _priority_card(self, item):
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
        info.add(toga.Label(
            item['name'],
            style=Pack(font_weight='bold', font_size=13, color=AppTheme.TEXT_PRIMARY)
        ))
        dl = item.get('deadline', item.get('date', ''))
        info.add(toga.Label(
            f"{dl}  {item.get('diff', '')}",
            style=Pack(font_size=10, color=AppTheme.TEXT_SECONDARY, margin_top=2)
        ))

        # Timer row — always created; text updated by _live_loop
        timer    = self.app.timer_page
        is_active = (self.app.current_subject == item['name'] and timer.is_running)

        if is_active:
            tl      = timer.time_left
            total   = timer.total_duration_secs
            elapsed = total - tl
            pct     = int(elapsed / total * 100) if total else 0
            hrs, rem  = divmod(tl, 3600)
            mins, scs = divmod(rem, 60)
            initial_text = f"Running: {hrs:02d}:{mins:02d}:{scs:02d}  {pct}%"
            timer_label = toga.Label(
                initial_text,
                style=Pack(font_size=10, color=AppTheme.PRIMARY, margin_top=3,
                           font_weight='bold')
            )
            info.add(timer_label)
            # Store reference so the live ticker can update just this label
            self._active_time_label = timer_label

        btn_label = 'Resume' if is_active else 'Start'
        btn_bg    = AppTheme.SUCCESS if is_active else AppTheme.PRIMARY
        card.add(info, toga.Button(
            btn_label,
            on_press=partial(self.start_reading, subject=item),
            style=Pack(width=65, font_size=10, font_weight='bold',
                       background_color=btn_bg, color='#FFFFFF')
        ))
        return card

    def _completed_card(self, item):
        card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            margin=12, margin_top=0, margin_bottom=6, padding=12,
            align_items=CENTER
        ))
        card.add(toga.Label(
            f"Done: {item['name']}",
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
            'Past date - log a session' if is_past
            else f"Date: {day:02d}/{month:02d}/{year}"
        )
        self.session_notes.value = ''

        self.stop_live_tick()   # pause ticker while picker is open
        self.app.content_area.clear()
        self.app.update_nav_style('dash')
        self.app.content_area.add(self.picker_box)

    def picker_start_timer(self, widget):
        chosen = self.subject_select.value
        if not chosen or chosen == '(no subjects yet)':
            return
        for s in self.app.subjects_data:
            if s['name'] == chosen:
                s['_session_note'] = self.session_notes.value
                break
        self.app.current_subject = chosen
        self.app.timer_page.prepare_timer(chosen)
        self.app.show_timer(None)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIORITY START
    # ─────────────────────────────────────────────────────────────────────────

    def start_reading(self, widget, subject):
        timer = self.app.timer_page
        if self.app.current_subject == subject['name'] and timer.is_running:
            self.stop_live_tick()
            self.app.show_timer(None)
        else:
            self.stop_live_tick()
            self.app.current_subject = subject['name']
            timer.prepare_timer(subject['name'])
            self.app.show_timer(None)