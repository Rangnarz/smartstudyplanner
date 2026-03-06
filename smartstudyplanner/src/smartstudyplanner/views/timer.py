import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio
from ..components.theme import AppTheme


_DURATIONS = [5, 10, 15, 20, 25, 30, 45, 60]


class TimerView:
    def __init__(self, app):
        self.app = app
        self.time_left            = 0
        self.total_duration_secs  = 0
        self.selected_minutes     = 25
        self.is_running           = False
        self.is_paused            = True
        self._tick_task           = None   # asyncio Task reference
        self.build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        top_bar = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.PRIMARY,
            padding=16, padding_bottom=12, align_items=CENTER
        ))
        back_btn = toga.Button(
            'Back',
            on_press=self._go_back,
            style=Pack(background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_size=13, font_weight='bold')
        )
        top_bar.add(back_btn)
        self.top_running_label = toga.Label(
            '',
            style=Pack(flex=1, font_size=10, color='#BDD9FF', text_align=CENTER)
        )
        top_bar.add(self.top_running_label)
        self.main_box.add(top_bar)

        body = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, padding=20))

        self.timer_subject_label = toga.Label(
            'No Subject',
            style=Pack(font_size=16, font_weight='bold', color=AppTheme.TEXT_PRIMARY,
                       text_align=CENTER, margin_bottom=4)
        )
        self.subtasks_label = toga.Label(
            'Goal: -',
            style=Pack(font_size=11, color=AppTheme.TEXT_SECONDARY,
                       text_align=CENTER, margin_bottom=24)
        )
        body.add(self.timer_subject_label, self.subtasks_label)

        # Duration picker
        self.duration_box = toga.Box(
            style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=20)
        )
        self.duration_box.add(toga.Label(
            'Set Duration',
            style=Pack(font_size=12, font_weight='bold', color=AppTheme.TEXT_SECONDARY,
                       margin_bottom=10)
        ))
        self.duration_select = toga.Selection(
            items=[f"{m} min" for m in _DURATIONS],
            style=Pack(width=130)
        )
        self.duration_select.value = '25 min'
        self.duration_box.add(self.duration_select)
        body.add(self.duration_box)

        # Timer display wrapper
        self.timer_content_wrapper = toga.Box(
            style=Pack(direction=COLUMN, align_items=CENTER)
        )
        self._build_timer_main_view()
        self._build_journal_view()
        self.timer_content_wrapper.add(self.timer_main_view)
        body.add(self.timer_content_wrapper)

        self.main_box.add(
            toga.ScrollContainer(content=body, style=Pack(flex=1))
        )

    def _build_timer_main_view(self):
        self.timer_main_view = toga.Box(
            style=Pack(direction=COLUMN, align_items=CENTER)
        )
        outer = toga.Box(style=Pack(
            direction=COLUMN, background_color=AppTheme.PRIMARY,
            padding=4, margin_bottom=24, align_items=CENTER
        ))
        inner = toga.Box(style=Pack(
            direction=COLUMN, background_color=AppTheme.BACKGROUND,
            padding=4, align_items=CENTER
        ))
        self.time_label = toga.Label(
            '00 : 25 : 00',
            style=Pack(font_size=36, font_weight='bold', color=AppTheme.TEXT_PRIMARY,
                       margin=24, text_align=CENTER)
        )
        inner.add(self.time_label)
        outer.add(inner)
        self.timer_main_view.add(outer)

        self.progress_label = toga.Label(
            '',
            style=Pack(font_size=11, color=AppTheme.TEXT_SECONDARY, margin_bottom=20)
        )
        self.timer_main_view.add(self.progress_label)

        self.start_timer_btn = toga.Button(
            'Start',
            on_press=self.toggle_timer,
            style=Pack(width=140, font_size=15, font_weight='bold',
                       background_color=AppTheme.PRIMARY, color='#FFFFFF')
        )
        self.timer_main_view.add(self.start_timer_btn)

    def _build_journal_view(self):
        self.timer_journal_view = toga.Box(
            style=Pack(direction=COLUMN, align_items=CENTER,
                       background_color=AppTheme.CARD_BG, padding=24)
        )
        self.timer_journal_view.add(toga.Label(
            'Session Complete!',
            style=Pack(font_size=16, font_weight='bold', color=AppTheme.TEXT_PRIMARY,
                       margin_bottom=6)
        ))
        self.timer_journal_view.add(toga.Label(
            'What did you learn today?',
            style=Pack(font_size=11, color=AppTheme.TEXT_SECONDARY, margin_bottom=14)
        ))
        self.journal_input = toga.TextInput(
            placeholder='Write a quick reflection...',
            style=Pack(margin_bottom=20, background_color=AppTheme.BACKGROUND, width=280)
        )
        self.btn_save_journal = toga.Button(
            'Finish and Save',
            on_press=self.finalize_session,
            style=Pack(background_color=AppTheme.SUCCESS, color='#FFFFFF',
                       font_weight='bold', width=180)
        )
        self.timer_journal_view.add(self.journal_input, self.btn_save_journal)

    # ─────────────────────────────────────────────────────────────────────────
    # TIMER LOGIC
    # ─────────────────────────────────────────────────────────────────────────

    def prepare_timer(self, subject_name):
        """Reset UI for a new subject.  Does NOT cancel an existing running timer."""
        subj = next((s for s in self.app.subjects_data if s['name'] == subject_name), None)
        if subj:
            self.timer_subject_label.text = subject_name
            note = subj.get('_session_note') or subj.get('todo', '') or ''
            self.subtasks_label.text = f"Goal: {note}" if note else 'Goal: -'

        self.selected_minutes    = 25
        self.time_left           = 25 * 60
        self.total_duration_secs = 25 * 60
        self.time_label.text     = '00 : 25 : 00'
        self.progress_label.text = ''
        self.top_running_label.text = ''
        self.is_running          = False
        self.is_paused           = True
        self.start_timer_btn.text = 'Start'
        self.duration_select.value = '25 min'

        self.timer_content_wrapper.clear()
        self.timer_content_wrapper.add(self.timer_main_view)

    def _apply_duration(self):
        label = self.duration_select.value
        try:
            mins = int(label.replace(' min', ''))
        except Exception:
            mins = 25
        self.selected_minutes    = mins
        secs                     = mins * 60
        self.time_left           = secs
        self.total_duration_secs = secs
        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        self.time_label.text     = f'{h:02d} : {m:02d} : {s:02d}'
        self.progress_label.text = ''

    async def timer_tick(self):
        self.is_running = True
        while self.time_left > 0 and self.is_running:
            if not self.is_paused:
                hrs, rem  = divmod(self.time_left, 3600)
                mins, scs = divmod(rem, 60)
                elapsed   = self.total_duration_secs - self.time_left
                pct       = int(elapsed / self.total_duration_secs * 100) if self.total_duration_secs else 0

                time_str = f'{hrs:02d}:{mins:02d}:{scs:02d}'
                self.time_label.text     = f'{hrs:02d} : {mins:02d} : {scs:02d}'
                self.progress_label.text = f'{pct}% complete'
                # Mini status in top bar (visible when on timer page)
                self.top_running_label.text = f'{time_str}  {pct}%'

                await asyncio.sleep(1)
                self.time_left -= 1
            else:
                await asyncio.sleep(0.1)

        if self.time_left == 0 and self.is_running:
            self.is_running = False
            self.progress_label.text    = '100% complete!'
            self.top_running_label.text = 'Done!'
            self.timer_content_wrapper.clear()
            self.timer_content_wrapper.add(self.timer_journal_view)

    def toggle_timer(self, widget):
        if not self.app.current_subject:
            return
        if not self.is_running:
            self._apply_duration()
            # hide duration picker
            try:
                self.duration_box.style.update(display='none')
            except Exception:
                pass
            self.is_paused = False
            self.start_timer_btn.text = 'Pause'
            self._tick_task = asyncio.create_task(self.timer_tick())
        else:
            self.is_paused = not self.is_paused
            self.start_timer_btn.text = 'Resume' if self.is_paused else 'Pause'

    def _go_back(self, widget):
        """Go back to dashboard WITHOUT stopping the timer."""
        # Timer keeps running; dashboard refresh will show live time on the card
        self.app.show_dashboard(None)

    # ─────────────────────────────────────────────────────────────────────────
    # FINALIZE
    # ─────────────────────────────────────────────────────────────────────────

    def finalize_session(self, widget):
        self.is_running = False   # stop tick loop
        for s in self.app.subjects_data:
            if s['name'] == self.app.current_subject:
                s['completed'] = True
                s['journal']   = self.journal_input.value

        subj_name = self.app.current_subject
        mins = max(1, self.total_duration_secs // 60)
        if subj_name in self.app.reading_history:
            self.app.reading_history[subj_name]['minutes'] += mins
        else:
            self.app.reading_history[subj_name] = {'minutes': mins}

        self.app.save_data()
        self.journal_input.value = ''
        try:
            self.duration_box.style.update(display='pack')
        except Exception:
            pass
        self.app.show_dashboard(None)