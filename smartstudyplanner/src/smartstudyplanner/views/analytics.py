import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from ..components.theme import AppTheme
 
class AnalyticsView:
    def __init__(self, app):
        self.app = app
        self.build_ui()
 
    def build_ui(self):
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=15, flex=1))
        self.main_box.add(toga.Label('📊 Learning Progress', style=Pack(font_weight='bold', font_size=16, margin_bottom=10)))
       
        # --- FIX: ส่วนกราฟ 50% ด้านบน (ให้ flex=1) ---
        self.chart_container = toga.Box(style=Pack(direction=COLUMN))
        scroll = toga.ScrollContainer(content=self.chart_container, style=Pack(flex=1))
       
        # --- FIX: ส่วนวิเคราะห์ 50% ด้านล่าง (ให้ flex=1) และจัดให้อยู่ตรงกลาง ---
        self.insight_box = toga.Box(style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND, padding=10, align_items=CENTER))
       
        self.main_box.add(scroll, self.insight_box)
 
    def refresh(self):
        self.chart_container.clear()
        self.insight_box.clear()
       
        self.insight_box.add(toga.Label('🤖 AI Analysis:', style=Pack(font_weight='bold', margin_top=15, margin_bottom=10, color=AppTheme.PRIMARY)))
       
        if not self.app.reading_history:
            self.chart_container.add(toga.Label("No study history yet.", style=Pack(margin=20, color='gray')))
            self.insight_box.add(toga.Label("You haven't started studying yet.\nLet's pick an easy subject and begin!", style=Pack(font_size=11, color='#2c3e50', text_align=CENTER)))
            return
 
        max_mins = max([d['minutes'] for d in self.app.reading_history.values()])
        total_mins = sum([d['minutes'] for d in self.app.reading_history.values()])
       
        for subj, data in self.app.reading_history.items():
            row = toga.Box(style=Pack(direction=COLUMN, margin_bottom=10))
            row.add(toga.Label(f"{subj}: {data['minutes']} mins"))
            bar_w = int((data['minutes']/max_mins)*200) if max_mins > 0 else 10
            row.add(toga.Box(style=Pack(height=10, width=max(10, bar_w), background_color=AppTheme.PRIMARY)))
            self.chart_container.add(row)
       
        pending_tasks = len([s for s in self.app.subjects_data if not s.get('completed')])
        completed_tasks = len([s for s in self.app.subjects_data if s.get('completed')])
       
        # --- FIX: ใช้ \n เพื่อขึ้นบรรทัดใหม่ ป้องกันข้อความล้นทะลุจอ Android ---
        if total_mins < 30:
            analysis_msg = f"Good start! You've studied for {total_mins} mins.\nKeep building the habit."
        elif total_mins < 120:
            analysis_msg = f"Great progress! {total_mins} mins of focus.\nYou're showing great consistency!"
        else:
            analysis_msg = f"Outstanding! {total_mins} mins of studying.\nYou're definitely ready for your exams!"
           
        self.insight_box.add(toga.Label(analysis_msg, style=Pack(font_size=11, color='#2c3e50', text_align=CENTER)))
       
        if pending_tasks > 0:
            self.insight_box.add(toga.Label(f"📌 {pending_tasks} tasks remaining.\nYou can do this!", style=Pack(font_size=10, color=AppTheme.DANGER, margin_top=10, text_align=CENTER)))
        else:
            if completed_tasks > 0:
                self.insight_box.add(toga.Label("🎉 All scheduled tasks are completed!\nEnjoy your free time.", style=Pack(font_size=10, color=AppTheme.SUCCESS, margin_top=10, text_align=CENTER)))