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
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=15, flex=1))
        self.main_box.add(toga.Label('📅 Monthly Calendar', style=Pack(font_weight='bold', font_size=14, margin_bottom=10)))
        
        self.calendar_outer = toga.Box(style=Pack(direction=ROW, margin_bottom=20))
        self.calendar_wrapper = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER))
        self.calendar_outer.add(toga.Box(style=Pack(flex=1)), self.calendar_wrapper, toga.Box(style=Pack(flex=1)))
        self.main_box.add(self.calendar_outer)

        self.dash_content = toga.Box(style=Pack(direction=COLUMN))
        self.scroll = toga.ScrollContainer(content=self.dash_content, style=Pack(flex=1))
        self.main_box.add(self.scroll)

    def calculate_priority(self, subject):
        try:
            diff_map = {'Easy': 1, 'Medium': 2, 'Hard': 3}
            diff_val = diff_map.get(subject.get('diff', 'Easy'), 1)
            d_str = subject.get('date', '01/01/2026')
            exam_date = datetime.strptime(d_str, "%d/%m/%Y").date()
            days_left = (exam_date - date.today()).days
            if days_left <= 0: return 999
            return diff_val / days_left
        except: return 0

    def refresh(self):
        self.calendar_wrapper.clear()
        self.dash_content.clear()
        
        now = datetime.now()
        cal_matrix = calendar.monthcalendar(now.year, now.month)
        cal_box = toga.Box(style=Pack(direction=COLUMN))
        
        subjects_by_day = {}
        for subj in self.app.subjects_data:
            try:
                d, m, y = map(int, subj['date'].split('/'))
                if m == now.month and y == now.year:
                    if d not in subjects_by_day:
                        subjects_by_day[d] = []
                    subjects_by_day[d].append(subj)
            except: pass

        header = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        for day_name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            header.add(toga.Label(day_name, style=Pack(width=45, text_align=CENTER, font_size=10, font_weight='bold', color=AppTheme.INACTIVE)))
        cal_box.add(header)
        
        for week in cal_matrix:
            row = toga.Box(style=Pack(direction=ROW))
            for day in week:
                if day != 0:
                    if day in subjects_by_day:
                        btn = toga.Button(str(day), on_press=partial(self.show_calendar_popup, day=day, events=subjects_by_day[day]), style=Pack(width=45, height=45, background_color=AppTheme.PRIMARY, color='#ffffff', font_weight='bold', font_size=10, margin=1))
                        row.add(btn)
                    else:
                        cell = toga.Box(style=Pack(width=45, height=45, background_color=AppTheme.NAV_BG, margin=1, align_items=CENTER))
                        cell.add(toga.Label(str(day), style=Pack(font_size=10, margin_top=15)))
                        row.add(cell)
                else:
                    row.add(toga.Box(style=Pack(width=45, height=45, margin=1)))
            cal_box.add(row)
            
        self.calendar_wrapper.add(cal_box)

        pending_list = [s for s in self.app.subjects_data if not s.get('completed')]
        completed_list = [s for s in self.app.subjects_data if s.get('completed')]

        self.dash_content.add(toga.Label('💡 Smart Priority', style=Pack(font_weight='bold', font_size=16, margin_bottom=10)))
        if not pending_list:
            self.dash_content.add(toga.Label("Hooray! No pending tasks.", style=Pack(margin=10, color='gray')))
        else:
            sorted_pending = sorted(pending_list, key=self.calculate_priority, reverse=True)
            for item in sorted_pending:
                card = toga.Box(style=Pack(direction=ROW, margin_bottom=10, background_color='#f0f8ff', align_items=CENTER))
                info = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=10))
                info.add(toga.Label(item['name'], style=Pack(font_weight='bold')))
                info.add(toga.Label(f"Target: {item['date']} | Priority: {item['diff']}", style=Pack(font_size=9, color='#34495e')))
                
                # --- FIX: ปรับ width เป็น 65 เพื่อให้คำว่า START ไม่ล้นตกบรรทัด ---
                btn = toga.Button('START', on_press=partial(self.start_reading, subject_name=item['name']), 
                                  style=Pack(width=65, font_size=9, background_color=AppTheme.PRIMARY, color='white', margin_right=5))
                card.add(info, btn)
                self.dash_content.add(card)

        self.dash_content.add(toga.Label('✅ Finished Sessions', style=Pack(font_weight='bold', font_size=16, margin_top=20, margin_bottom=10, color=AppTheme.SUCCESS)))
        for item in completed_list:
            card = toga.Box(style=Pack(direction=ROW, margin_bottom=5, background_color='#f9f9f9', align_items=CENTER))
            card.add(toga.Label(f" ✔ {item['name']}", style=Pack(flex=1, color='gray', margin=10)))
            self.dash_content.add(card)

    async def show_calendar_popup(self, widget, day, events):
        details_text = f"Schedule for {day}:\n\n"
        for ev in events:
            details_text += f"- {ev['name']}\n  Level: {ev['diff']}\n"
        await self.app.main_window.dialog(toga.InfoDialog("Calendar Detail", details_text))

    def start_reading(self, widget, subject_name):
        self.app.current_subject = subject_name
        self.app.timer_page.prepare_timer(subject_name)
        self.app.show_timer(None)