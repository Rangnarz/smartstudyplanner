import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from datetime import date, timedelta
from ..components.theme import AppTheme


class AnalyticsView:
    def __init__(self, app):
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        header.add(toga.Label(
            '📊 Analytics',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        header.add(toga.Label(
            'Track your study progress',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        ))
        self.main_box.add(header)

        self.content = toga.Box(style=Pack(direction=COLUMN))
        self.main_box.add(
            toga.ScrollContainer(content=self.content, style=Pack(flex=1))
        )

    def refresh(self):
        self.content.clear()
        inner = toga.Box(style=Pack(direction=COLUMN, padding=16))

        # ── Weekly Summary ────────────────────────────────────────────────────
        inner.add(self._section_label('📅 This Week'))

        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_mins_by_day = {i: 0 for i in range(7)}  # Mon=0 … Sun=6

        total_week_mins = 0
        best_subject = None
        best_subject_mins = 0

        for subj_name, data in self.app.reading_history.items():
            mins = data.get('minutes', 0)
            total_week_mins += mins          # simplification: all history counted as week
            if mins > best_subject_mins:
                best_subject_mins = mins
                best_subject = subj_name

        # Week stat cards row
        week_row = toga.Box(style=Pack(direction=ROW, margin_bottom=12))
        week_row.add(self._stat_card('Total Time', f'{total_week_mins} min', AppTheme.PRIMARY))
        week_row.add(self._stat_card(
            'Best Subject', best_subject or '—', AppTheme.SUCCESS
        ))
        pending_tasks = len([s for s in self.app.subjects_data if not s.get('completed')])
        completed_tasks = len([s for s in self.app.subjects_data if s.get('completed')])
        week_row.add(self._stat_card('Pending', str(pending_tasks), AppTheme.WARNING))
        inner.add(week_row)

        # Completion ratio bar
        total_tasks = pending_tasks + completed_tasks
        if total_tasks > 0:
            comp_pct = int(completed_tasks / total_tasks * 100)
            bar_box = toga.Box(style=Pack(direction=COLUMN,
                                         background_color=AppTheme.CARD_BG,
                                         padding=12, margin_bottom=12))
            bar_hdr = toga.Box(style=Pack(direction=ROW, margin_bottom=6))
            bar_hdr.add(toga.Label(
                'Task Completion',
                style=Pack(flex=1, font_size=11, font_weight='bold',
                           color=AppTheme.TEXT_SECONDARY)
            ))
            bar_hdr.add(toga.Label(
                f'{completed_tasks}/{total_tasks}  ({comp_pct}%)',
                style=Pack(font_size=11, color=AppTheme.PRIMARY, font_weight='bold')
            ))
            bar_box.add(bar_hdr)
            # Text-based progress bar
            filled = int(comp_pct / 5)
            bar_str = '█' * filled + '░' * (20 - filled)
            bar_box.add(toga.Label(
                bar_str,
                style=Pack(font_size=9, color=AppTheme.SUCCESS, margin_top=4)
            ))
            inner.add(bar_box)

        # ── Per-Subject chart ─────────────────────────────────────────────────
        inner.add(self._section_label('📖 Study Time by Subject'))

        if not self.app.reading_history:
            inner.add(toga.Label(
                'No study history yet. Start a timer to begin!',
                style=Pack(font_size=12, color=AppTheme.TEXT_SECONDARY,
                           margin=20, text_align=CENTER)
            ))
        else:
            max_mins = max(d.get('minutes', 0) for d in self.app.reading_history.values())
            colors = AppTheme.SUBJECT_COLORS
            for idx, (subj, data) in enumerate(self.app.reading_history.items()):
                mins = data.get('minutes', 0)
                pomodoros = data.get('pomodoros', 0)
                row = toga.Box(style=Pack(direction=COLUMN,
                                         background_color=AppTheme.CARD_BG,
                                         padding=10, margin_bottom=8))
                lbl_row = toga.Box(style=Pack(direction=ROW))
                lbl_row.add(toga.Label(
                    subj,
                    style=Pack(flex=1, font_size=12, font_weight='bold',
                               color=AppTheme.TEXT_PRIMARY)
                ))
                detail_str = f'{mins} min'
                if pomodoros:
                    detail_str += f'  🍅 {pomodoros}'
                lbl_row.add(toga.Label(
                    detail_str,
                    style=Pack(font_size=11, color=AppTheme.TEXT_SECONDARY)
                ))
                row.add(lbl_row)
                # Text-based bar
                bar_filled = int((mins / max_mins) * 20) if max_mins > 0 else 0
                bar_empty  = 20 - bar_filled
                bar_str    = '█' * bar_filled + '░' * bar_empty
                row.add(toga.Label(
                    bar_str,
                    style=Pack(font_size=9, color=colors[idx % len(colors)], margin_top=4)
                ))
                inner.add(row)

        # ── AI Insight ────────────────────────────────────────────────────────
        inner.add(self._section_label('🤖 AI Insight'))
        total_mins = sum(d.get('minutes', 0) for d in self.app.reading_history.values())
        if total_mins < 30:
            msg = f"Good start! {total_mins} min logged.\nKeep building the habit!"
        elif total_mins < 120:
            msg = f"Great progress! {total_mins} min of focus.\nConsistency is key!"
        else:
            msg = f"Outstanding! {total_mins} min studied.\nYou're definitely ready!"

        insight = toga.Box(style=Pack(
            direction=COLUMN, background_color=AppTheme.INSIGHT_BG,
            padding=14, margin_bottom=16
        ))
        insight.add(toga.Label(
            msg, style=Pack(font_size=12, color=AppTheme.TEXT_PRIMARY, text_align=CENTER)
        ))
        if pending_tasks > 0:
            insight.add(toga.Label(
                f'\n📌 {pending_tasks} tasks still pending — you can do this!',
                style=Pack(font_size=10, color=AppTheme.DANGER, text_align=CENTER)
            ))
        elif completed_tasks > 0:
            insight.add(toga.Label(
                '\n🎉 All tasks complete! Enjoy your free time.',
                style=Pack(font_size=10, color=AppTheme.SUCCESS, text_align=CENTER)
            ))
        inner.add(insight)

        inner.add(toga.Box(style=Pack(height=20)))
        self.content.add(inner)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section_label(self, text):
        box = toga.Box(style=Pack(direction=ROW, padding=4, padding_bottom=6, padding_top=12))
        box.add(toga.Label(
            text,
            style=Pack(font_size=13, font_weight='bold', color=AppTheme.TEXT_PRIMARY)
        ))
        return box

    def _stat_card(self, label, value, color):
        card = toga.Box(style=Pack(
            direction=COLUMN, flex=1, background_color=AppTheme.CARD_BG,
            padding=10, margin_right=6, align_items=CENTER
        ))
        card.add(toga.Label(
            value,
            style=Pack(font_size=14, font_weight='bold', color=color, text_align=CENTER)
        ))
        card.add(toga.Label(
            label,
            style=Pack(font_size=9, color=AppTheme.TEXT_SECONDARY, text_align=CENTER,
                       margin_top=2)
        ))
        return card