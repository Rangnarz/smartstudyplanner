import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio
from ..components.theme import AppTheme

class TimerView:
    def __init__(self, app):
        self.app = app
        self.time_left = 0
        self.total_duration_secs = 0 
        self.is_running = False
        self.is_paused = True
        self.build_ui()

    def build_ui(self):
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=20, align_items=CENTER, flex=1))
        
        top_bar = toga.Box(style=Pack(direction=ROW, width=360, margin_bottom=20))
        back_btn = toga.Button('❮ Back', on_press=self.app.show_dashboard, style=Pack(background_color='transparent', color=AppTheme.PRIMARY, font_size=14))
        top_bar.add(back_btn)
        
        self.timer_subject_label = toga.Label('Subject: None', style=Pack(margin_bottom=5, font_weight='bold', font_size=14))
        self.subtasks_label = toga.Label('Goal: N/A', style=Pack(margin_bottom=20, color='gray', font_size=11))
        
        self.timer_content_wrapper = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER))

        self.timer_main_view = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER))
        self.time_border = toga.Box(style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY, margin_bottom=30, align_items=CENTER))
        self.time_frame = toga.Box(style=Pack(direction=COLUMN, background_color=AppTheme.BACKGROUND, margin=4, align_items=CENTER))
        self.time_label = toga.Label('00 : 25 : 00', style=Pack(font_size=40, font_weight='bold', margin=30, text_align=CENTER))
        self.time_frame.add(self.time_label)
        self.time_border.add(self.time_frame)
        
        self.start_timer_btn = toga.Button('▶', on_press=self.toggle_timer, style=Pack(font_size=24, width=70, height=70, background_color=AppTheme.PRIMARY, color='white'))
        self.timer_main_view.add(self.time_border, self.start_timer_btn)

        self.timer_journal_view = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, background_color=AppTheme.NAV_BG, padding=20))
        self.timer_journal_view.add(toga.Label('📔 Study Journal', style=Pack(font_weight='bold', margin_bottom=10)))
        self.journal_input = toga.TextInput(placeholder='What did you learn today?...', style=Pack(margin_bottom=15))
        self.btn_save_journal = toga.Button('Finish Session', on_press=self.finalize_session, style=Pack(background_color=AppTheme.SUCCESS, color='white', width=150))
        self.timer_journal_view.add(self.journal_input, self.btn_save_journal)

        self.timer_content_wrapper.add(self.timer_main_view)
        self.main_box.add(top_bar, self.timer_subject_label, self.subtasks_label, self.timer_content_wrapper)

    def prepare_timer(self, subject_name):
        subj = next((s for s in self.app.subjects_data if s['name'] == subject_name), None)
        if subj:
            self.timer_subject_label.text = f'Subject: {subject_name}'
            self.subtasks_label.text = f"Goal: {subj.get('subtasks', 'N/A')}"
            self.time_left = 25 * 60
            self.total_duration_secs = 25 * 60
            self.time_label.text = '00 : 25 : 00'
            self.is_running = False
            self.start_timer_btn.text = '▶'
        self.timer_content_wrapper.clear()
        self.timer_content_wrapper.add(self.timer_main_view)

    async def timer_tick(self):
        self.is_running = True
        while self.time_left > 0 and self.is_running:
            if not self.is_paused:
                hrs, rem = divmod(self.time_left, 3600)
                mins, secs = divmod(rem, 60)
                self.time_label.text = f'{hrs:02d} : {mins:02d} : {secs:02d}'
                await asyncio.sleep(1)
                self.time_left -= 1
            else: await asyncio.sleep(0.1)
                
        if self.time_left == 0 and self.is_running:
            self.is_running = False
            self.timer_content_wrapper.clear()
            self.timer_content_wrapper.add(self.timer_journal_view)

    def toggle_timer(self, widget):
        if not self.app.current_subject: return
        if not self.is_running:
            self.is_paused = False
            self.start_timer_btn.text = '⏸'
            asyncio.create_task(self.timer_tick())
        else:
            self.is_paused = not self.is_paused
            self.start_timer_btn.text = '▶' if self.is_paused else '⏸'

    def finalize_session(self, widget):
        for s in self.app.subjects_data:
            if s['name'] == self.app.current_subject:
                s['completed'] = True
                s['journal'] = self.journal_input.value
        
        subj_name = self.app.current_subject
        mins = max(1, self.total_duration_secs // 60)
        if subj_name in self.app.reading_history:
            self.app.reading_history[subj_name]['minutes'] += mins
        else:
            self.app.reading_history[subj_name] = {'minutes': mins}
            
        self.app.save_data()
        self.journal_input.value = ""
        self.app.show_dashboard(None)