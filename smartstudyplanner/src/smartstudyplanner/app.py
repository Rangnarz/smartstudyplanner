import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import json

# ดึงคลาสจากไฟล์ที่เราแยกไว้
from .components.theme import AppTheme
from .views.dashboard import DashboardView
from .views.subjects import SubjectsView
from .views.timer import TimerView
from .views.analytics import AnalyticsView

class SmartStudyPlanner(toga.App):
    def startup(self):
        # Global State
        self.current_subject = None
        self.data_file = self.paths.data / 'planner_data.json'
        self.load_data()

        # สร้าง Views ทั้งหมดเก็บไว้ในตัวแปร
        self.dashboard_page = DashboardView(self)
        self.subjects_page = SubjectsView(self)
        self.timer_page = TimerView(self)
        self.analytics_page = AnalyticsView(self)

        # Build Main Layout
        self.main_box = toga.Box(style=Pack(direction=COLUMN))
        self.content_area = toga.Box(style=Pack(flex=1, direction=COLUMN, background_color=AppTheme.BACKGROUND))
        
        # Bottom Navbar
        self.nav_bar = toga.Box(style=Pack(direction=ROW, height=65, background_color=AppTheme.BACKGROUND))
        nav_border = toga.Box(style=Pack(height=1, background_color='#ecf0f1'))
        
        btn_style = Pack(flex=1, font_size=11, background_color=AppTheme.BACKGROUND, font_weight='bold')
        self.btn_dash = toga.Button('🏠 Home', on_press=self.show_dashboard, style=btn_style)
        self.btn_subj = toga.Button('📚 Subjects', on_press=self.show_subject_list, style=btn_style)
        self.btn_stat = toga.Button('📊 Stats', on_press=self.show_analytic, style=btn_style)
        
        self.nav_bar.add(self.btn_dash, self.btn_subj, self.btn_stat)
        self.main_box.add(self.content_area, nav_border, self.nav_bar)

        self.main_window = toga.MainWindow(title=self.formal_name, size=(400, 700))
        self.main_window.content = self.main_box
        
        # เปิดมาเข้าหน้า Home ก่อนเลย
        self.show_dashboard(None)
        self.main_window.show()

    def load_data(self):
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subjects_data = data.get('subjects', [])
                    self.reading_history = data.get('history', {})
            else:
                self.subjects_data = []
                self.reading_history = {}
        except:
            self.subjects_data = []
            self.reading_history = {}

    def save_data(self):
        try:
            if not self.paths.data.exists(): self.paths.data.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({'subjects': self.subjects_data, 'history': self.reading_history}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def update_nav_style(self, active_tab):
        self.btn_dash.style.color = AppTheme.PRIMARY if active_tab == 'dash' else AppTheme.INACTIVE
        self.btn_subj.style.color = AppTheme.PRIMARY if active_tab == 'subj' else AppTheme.INACTIVE
        self.btn_stat.style.color = AppTheme.PRIMARY if active_tab == 'stat' else AppTheme.INACTIVE

    def show_dashboard(self, widget):
        self.content_area.clear()
        self.update_nav_style('dash')
        self.dashboard_page.refresh()
        self.content_area.add(self.dashboard_page.main_box)

    def show_subject_list(self, widget):
        self.content_area.clear()
        self.update_nav_style('subj')
        self.subjects_page.refresh()
        self.content_area.add(self.subjects_page.main_box)

    def show_timer(self, widget):
        self.content_area.clear()
        self.update_nav_style('none')
        self.content_area.add(self.timer_page.main_box)

    def show_analytic(self, widget):
        self.content_area.clear()
        self.update_nav_style('stat')
        self.analytics_page.refresh()
        self.content_area.add(self.analytics_page.main_box)

def main():
    return SmartStudyPlanner('Smart Study Planner', 'org.example.smartstudyplanner')