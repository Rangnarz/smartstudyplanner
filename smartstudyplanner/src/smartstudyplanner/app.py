import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import json

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

        # ── Views ──────────────────────────────────────────────────────────
        self.dashboard_page = DashboardView(self)
        self.subjects_page  = SubjectsView(self)
        self.timer_page     = TimerView(self)
        self.analytics_page = AnalyticsView(self)

        # ── Root layout ────────────────────────────────────────────────────
        self.main_box     = toga.Box(style=Pack(direction=COLUMN, background_color=AppTheme.BACKGROUND))
        self.content_area = toga.Box(style=Pack(flex=1, direction=COLUMN, background_color=AppTheme.BACKGROUND))

        # ── Bottom nav ─────────────────────────────────────────────────────
        nav_border = toga.Box(style=Pack(height=1, background_color=AppTheme.BORDER))

        self.nav_bar = toga.Box(style=Pack(
            direction=ROW, height=60, background_color=AppTheme.NAV_BG
        ))

        # Nav button style (inactive)
        def _nav_btn(emoji, label, handler):
            btn = toga.Button(
                f'{emoji}\n{label}',
                on_press=handler,
                style=Pack(
                    flex=1, font_size=9, font_weight='bold',
                    background_color=AppTheme.NAV_BG, color=AppTheme.INACTIVE
                )
            )
            return btn

        self.btn_dash = _nav_btn('🏠', 'Home',     self.show_dashboard)
        self.btn_subj = _nav_btn('📚', 'Subjects', self.show_subject_list)
        self.btn_stat = _nav_btn('📊', 'Stats',    self.show_analytic)

        self.nav_bar.add(self.btn_dash, self.btn_subj, self.btn_stat)
        self.main_box.add(self.content_area, nav_border, self.nav_bar)

        # ── Window ─────────────────────────────────────────────────────────
        self.main_window = toga.MainWindow(title=self.formal_name, size=(400, 750))
        self.main_window.content = self.main_box

        self.show_dashboard(None)
        self.main_window.show()

    # ── Data persistence ────────────────────────────────────────────────────

    def load_data(self):
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subjects_data   = data.get('subjects', [])
                    self.reading_history = data.get('history',  {})
            else:
                self.subjects_data   = []
                self.reading_history = {}
        except Exception:
            self.subjects_data   = []
            self.reading_history = {}

    def save_data(self):
        try:
            if not self.paths.data.exists():
                self.paths.data.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'subjects': self.subjects_data, 'history': self.reading_history},
                    f, ensure_ascii=False, indent=4
                )
        except Exception as e:
            print(f'[save_data] Error: {e}')

    # ── Nav helpers ─────────────────────────────────────────────────────────

    def update_nav_style(self, active_tab):
        tabs = {
            'dash': self.btn_dash,
            'subj': self.btn_subj,
            'stat': self.btn_stat,
        }
        for key, btn in tabs.items():
            btn.style.color = AppTheme.PRIMARY if key == active_tab else AppTheme.INACTIVE
            btn.style.background_color = (
                AppTheme.PRIMARY_LIGHT if key == active_tab else AppTheme.NAV_BG
            )

    # ── Navigation ──────────────────────────────────────────────────────────

    def show_dashboard(self, widget):
        self.content_area.clear()
        self.update_nav_style('dash')
        self.dashboard_page.refresh()
        self.content_area.add(self.dashboard_page.main_box)

    def show_subject_list(self, widget):
        self.dashboard_page.stop_live_tick()
        self.content_area.clear()
        self.update_nav_style('subj')
        self.subjects_page.refresh()
        self.content_area.add(self.subjects_page.main_box)

    def show_timer(self, widget):
        self.dashboard_page.stop_live_tick()
        self.content_area.clear()
        self.update_nav_style('none')
        self.content_area.add(self.timer_page.main_box)

    def show_analytic(self, widget):
        self.dashboard_page.stop_live_tick()
        self.content_area.clear()
        self.update_nav_style('stat')
        self.analytics_page.refresh()
        self.content_area.add(self.analytics_page.main_box)


def main():
    return SmartStudyPlanner('Smart Study Planner', 'org.example.smartstudyplanner')