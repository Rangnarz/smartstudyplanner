import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from ..components.theme import AppTheme

_GOAL_OPTIONS = [30, 60, 90, 120, 150, 180, 240, 300]


class SettingsView:
    def __init__(self, app):
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY, padding=20)
        )
        header.add(toga.Label(
            '⚙️ Settings',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        header.add(toga.Label(
            'Personalise your study experience',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        ))
        self.main_box.add(header)

        scroll_content = toga.Box(style=Pack(direction=COLUMN, padding=16))

        # ── Daily Goal ────────────────────────────────────────────────────
        scroll_content.add(self._section_label('🎯  Daily Study Goal'))
        goal_card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            padding=14, margin_bottom=12, align_items=CENTER
        ))
        goal_card.add(toga.Label(
            'Daily Goal (minutes)',
            style=Pack(flex=1, font_size=13, font_weight='bold',
                       color=AppTheme.TEXT_PRIMARY)
        ))
        self.goal_select = toga.Selection(
            items=[f'{m} min' for m in _GOAL_OPTIONS],
            on_change=self._on_goal_change,
            style=Pack(width=100)
        )
        goal_card.add(self.goal_select)
        scroll_content.add(goal_card)

        self.main_box.add(toga.ScrollContainer(content=scroll_content, style=Pack(flex=1)))

    def _section_label(self, text):
        box = toga.Box(style=Pack(direction=ROW, padding=4, padding_bottom=6, padding_top=14))
        box.add(toga.Label(
            text,
            style=Pack(font_size=12, font_weight='bold', color=AppTheme.TEXT_SECONDARY)
        ))
        return box

    def refresh(self):
        goal_str = f'{self.app.daily_goal_mins} min'
        if goal_str in [f'{m} min' for m in _GOAL_OPTIONS]:
            self.goal_select.value = goal_str
        else:
            self.goal_select.value = '120 min'

    def _on_goal_change(self, widget):
        try:
            self.app.daily_goal_mins = int(widget.value.replace(' min', ''))
            self.app.save_settings()
        except Exception:
            pass
