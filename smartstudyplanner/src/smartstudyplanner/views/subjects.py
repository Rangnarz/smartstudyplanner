import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from functools import partial
from ..components.theme import AppTheme


class SubjectsView:
    def __init__(self, app):
        self.app = app
        self._detail_subject = None
        self.build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def build_ui(self):
        # ── List view ─────────────────────────────────────────────────────────
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        header.add(toga.Label(
            'Subjects',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        header.add(toga.Label(
            'Manage your assignments and tasks',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        ))
        self.main_box.add(header)

        self.subj_list_container = toga.Box(style=Pack(direction=COLUMN))
        self.subj_scroll = toga.ScrollContainer(
            content=self.subj_list_container,
            style=Pack(flex=1, background_color=AppTheme.BACKGROUND)
        )

        # Add New Subject button at the bottom
        add_btn = toga.Button(
            '+ Add New Subject',
            on_press=self.show_add_form,
            style=Pack(background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_weight='bold', padding=14, margin=12)
        )

        self.main_box.add(self.subj_scroll, add_btn)

        # ── Add form view ─────────────────────────────────────────────────────
        self.form_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        form_header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        form_header.add(toga.Label(
            'New Subject',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        ))
        form_header.add(toga.Label(
            'Fill in the details below',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        ))
        self.form_box.add(form_header)

        form_scroll_content = toga.Box(style=Pack(direction=COLUMN, padding=16))

        # 1. Assignment Topic
        form_scroll_content.add(self._field_label('1. Assignment Topic'))
        self.topic_input = toga.TextInput(
            placeholder='e.g. Mathematics - Chapter 3',
            style=Pack(margin_bottom=14, background_color=AppTheme.CARD_BG)
        )
        form_scroll_content.add(self.topic_input)

        # 2. Assignment Details
        form_scroll_content.add(self._field_label('2. Assignment Details'))
        self.details_input = toga.TextInput(
            placeholder='e.g. Solve exercises 1-20, review formulas',
            style=Pack(margin_bottom=14, background_color=AppTheme.CARD_BG)
        )
        form_scroll_content.add(self.details_input)

        # 3. To Do List
        form_scroll_content.add(self._field_label('3. To Do List'))
        self.todo_input = toga.TextInput(
            placeholder='e.g. Read notes, practice problems, review',
            style=Pack(margin_bottom=14, background_color=AppTheme.CARD_BG)
        )
        form_scroll_content.add(self.todo_input)

        # 4. Deadline
        form_scroll_content.add(self._field_label('4. Deadline'))
        self.deadline_input = toga.DateInput(style=Pack(margin_bottom=14))
        form_scroll_content.add(self.deadline_input)

        # Difficulty (kept for priority calc)
        form_scroll_content.add(self._field_label('Difficulty'))
        self.diff_input = toga.Selection(
            items=['Easy', 'Medium', 'Hard'],
            style=Pack(margin_bottom=24)
        )
        form_scroll_content.add(self.diff_input)

        btn_row = toga.Box(style=Pack(direction=ROW))
        save_btn = toga.Button(
            'Save Subject',
            on_press=self.save_subject,
            style=Pack(flex=1, background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_weight='bold', margin_right=8)
        )
        cancel_btn = toga.Button(
            'Cancel',
            on_press=self.cancel_form,
            style=Pack(flex=1, background_color=AppTheme.CARD_BG,
                       color=AppTheme.DANGER, font_weight='bold')
        )
        btn_row.add(save_btn, cancel_btn)
        form_scroll_content.add(btn_row)
        form_scroll_content.add(toga.Box(style=Pack(height=20)))

        self.form_box.add(
            toga.ScrollContainer(content=form_scroll_content, style=Pack(flex=1))
        )

        # ── Detail view ───────────────────────────────────────────────────────
        self.detail_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        self.detail_header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY,
                       padding=20, padding_bottom=16)
        )
        self.detail_title = toga.Label(
            '',
            style=Pack(font_size=18, font_weight='bold', color='#FFFFFF')
        )
        self.detail_sub = toga.Label(
            '',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        )
        self.detail_header.add(self.detail_title, self.detail_sub)
        self.detail_box.add(self.detail_header)

        self.detail_content = toga.Box(style=Pack(direction=COLUMN))
        self.detail_box.add(
            toga.ScrollContainer(content=self.detail_content, style=Pack(flex=1))
        )

        detail_btn_row = toga.Box(style=Pack(direction=ROW, padding=12))
        back_btn = toga.Button(
            'Back',
            on_press=lambda w: self.app.show_subject_list(None),
            style=Pack(flex=1, background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       font_weight='bold', margin_right=8)
        )
        self.detail_delete_btn = toga.Button(
            'Delete',
            on_press=self._delete_current_detail,
            style=Pack(flex=1, background_color=AppTheme.DANGER, color='#FFFFFF',
                       font_weight='bold')
        )
        detail_btn_row.add(back_btn, self.detail_delete_btn)
        self.detail_box.add(detail_btn_row)

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
        box = toga.Box(style=Pack(
            direction=ROW, padding=12, padding_bottom=4, padding_top=16
        ))
        box.add(toga.Label(
            text,
            style=Pack(font_size=12, font_weight='bold', color=AppTheme.TEXT_SECONDARY)
        ))
        return box

    # ─────────────────────────────────────────────────────────────────────────
    # REFRESH LIST
    # ─────────────────────────────────────────────────────────────────────────

    def refresh(self):
        self.subj_list_container.clear()

        # ── Subjects section header ───────────────────────────────────────────
        sec_hdr = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY_LIGHT,
                       padding=12, margin_bottom=4)
        )
        sec_hdr.add(toga.Label(
            'Your Subjects',
            style=Pack(font_size=14, font_weight='bold', color=AppTheme.PRIMARY)
        ))
        self.subj_list_container.add(sec_hdr)

        if not self.app.subjects_data:
            empty = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, padding=40))
            empty.add(toga.Label(
                'No subjects yet.',
                style=Pack(font_size=13, color=AppTheme.TEXT_SECONDARY,
                           text_align=CENTER)
            ))
            empty.add(toga.Label(
                'Tap "+ Add New Subject" to get started.',
                style=Pack(font_size=11, color=AppTheme.INACTIVE,
                           text_align=CENTER, margin_top=6)
            ))
            self.subj_list_container.add(empty)
            return

        pending = [s for s in self.app.subjects_data if not s.get('completed')]
        done    = [s for s in self.app.subjects_data if s.get('completed')]

        if pending:
            self.subj_list_container.add(self._section_label('Pending'))
            for item in pending:
                self.subj_list_container.add(self._subject_card(item))

        if done:
            self.subj_list_container.add(self._section_label('Completed'))
            for item in done:
                self.subj_list_container.add(self._subject_card(item))

        self.subj_list_container.add(toga.Box(style=Pack(height=20)))

    def _subject_card(self, item):
        diff_color = {
            'Easy':   AppTheme.SUCCESS,
            'Medium': AppTheme.WARNING,
            'Hard':   AppTheme.DANGER
        }.get(item.get('diff', 'Easy'), AppTheme.PRIMARY)

        card = toga.Box(style=Pack(
            direction=ROW, background_color=AppTheme.CARD_BG,
            margin=12, margin_top=0, margin_bottom=8, padding=14,
            align_items=CENTER
        ))

        badge = toga.Box(style=Pack(
            width=4, height=44, background_color=diff_color, margin_right=12
        ))

        info = toga.Box(style=Pack(direction=COLUMN, flex=1))
        status = ' [Done]' if item.get('completed') else ''
        info.add(toga.Label(
            f"{item['name']}{status}",
            style=Pack(font_weight='bold', font_size=13, color=AppTheme.TEXT_PRIMARY)
        ))
        dl = item.get('deadline', item.get('date', ''))
        info.add(toga.Label(
            f"Deadline: {dl}  |  {item.get('diff', '')}",
            style=Pack(font_size=10, color=AppTheme.TEXT_SECONDARY, margin_top=2)
        ))

        view_btn = toga.Button(
            'View',
            on_press=partial(self.show_detail, item=item),
            style=Pack(width=50, font_size=10, font_weight='bold',
                       background_color=AppTheme.PRIMARY, color='#FFFFFF',
                       margin_right=6)
        )

        card.add(badge, info, view_btn)
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # DETAIL VIEW
    # ─────────────────────────────────────────────────────────────────────────

    def show_detail(self, widget, item):
        self._detail_subject = item['name']

        self.detail_title.text = item['name']
        dl = item.get('deadline', item.get('date', ''))
        self.detail_sub.text   = f"Deadline: {dl}  |  {item.get('diff', '')}"

        self.detail_content.clear()
        inner = toga.Box(style=Pack(direction=COLUMN, padding=16))

        def _row(label, value):
            box = toga.Box(style=Pack(direction=COLUMN, margin_bottom=16))
            box.add(toga.Label(
                label,
                style=Pack(font_size=11, font_weight='bold', color=AppTheme.TEXT_SECONDARY,
                           margin_bottom=4)
            ))
            box.add(toga.Label(
                value or '—',
                style=Pack(font_size=13, color=AppTheme.TEXT_PRIMARY)
            ))
            box.add(toga.Box(style=Pack(height=1, background_color=AppTheme.BORDER,
                                        margin_top=10)))
            return box

        inner.add(_row('1. Assignment Topic',   item.get('name', '')))
        inner.add(_row('2. Assignment Details', item.get('details', '')))
        inner.add(_row('3. To Do List',         item.get('todo', '')))
        inner.add(_row('4. Deadline',           dl))
        inner.add(_row('Difficulty',            item.get('diff', '')))

        if item.get('journal'):
            inner.add(_row('Study Journal', item['journal']))

        status_label = 'Completed' if item.get('completed') else 'In Progress'
        status_color = AppTheme.SUCCESS if item.get('completed') else AppTheme.WARNING
        status_box = toga.Box(style=Pack(direction=COLUMN, margin_bottom=16))
        status_box.add(toga.Label(
            'Status',
            style=Pack(font_size=11, font_weight='bold', color=AppTheme.TEXT_SECONDARY,
                       margin_bottom=4)
        ))
        status_box.add(toga.Label(
            status_label,
            style=Pack(font_size=13, font_weight='bold', color=status_color)
        ))
        inner.add(status_box)

        self.detail_content.add(inner)

        self.app.content_area.clear()
        self.app.update_nav_style('subj')
        self.app.content_area.add(self.detail_box)

    def _delete_current_detail(self, widget):
        if self._detail_subject:
            self.app.subjects_data = [
                s for s in self.app.subjects_data
                if s['name'] != self._detail_subject
            ]
            self.app.save_data()
            self._detail_subject = None
        self.app.show_subject_list(None)

    # ─────────────────────────────────────────────────────────────────────────
    # FORM
    # ─────────────────────────────────────────────────────────────────────────

    def show_add_form(self, widget):
        self.topic_input.value   = ''
        self.details_input.value = ''
        self.todo_input.value    = ''
        self.app.content_area.clear()
        self.app.update_nav_style('subj')
        self.app.content_area.add(self.form_box)

    def cancel_form(self, widget):
        self.app.show_subject_list(None)

    def save_subject(self, widget):
        topic = self.topic_input.value.strip()
        if not topic:
            return
        d_val    = self.deadline_input.value
        date_str = f"{d_val.day:02d}/{d_val.month:02d}/{d_val.year}"
        self.app.subjects_data.append({
            'name':     topic,
            'details':  self.details_input.value,
            'todo':     self.todo_input.value,
            'deadline': date_str,
            'date':     date_str,           # kept for backward compat
            'diff':     self.diff_input.value,
            'completed': False,
            'journal':  ''
        })
        self.app.save_data()
        self.app.show_subject_list(None)

    def delete_subject(self, widget, name_to_del):
        self.app.subjects_data = [
            s for s in self.app.subjects_data if s['name'] != name_to_del
        ]
        self.app.save_data()
        self.refresh()