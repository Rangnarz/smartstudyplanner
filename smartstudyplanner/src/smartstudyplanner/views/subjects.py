import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from functools import partial
from ..components.theme import AppTheme

class SubjectsView:
    def __init__(self, app):
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=15, flex=1))
        self.main_box.add(toga.Label('📚 Subject Management', style=Pack(font_weight='bold', font_size=16, margin_bottom=10)))
        
        self.subj_list_container = toga.Box(style=Pack(direction=COLUMN))
        scroll_subj = toga.ScrollContainer(content=self.subj_list_container, style=Pack(flex=1, margin_bottom=10))
        add_fab = toga.Button('+ New Task', on_press=self.show_subject_form, style=Pack(background_color=AppTheme.PRIMARY, color='white', font_weight='bold', margin=10))
        self.main_box.add(scroll_subj, add_fab)

        # ฟอร์มเพิ่มข้อมูล
        self.form_box = toga.Box(style=Pack(direction=COLUMN, margin=15, flex=1))
        self.form_box.add(toga.Label('✨ Subject Details', style=Pack(font_weight='bold', font_size=16, margin_bottom=15)))
        self.sub_input = toga.TextInput(placeholder='Subject Name...', style=Pack(margin_bottom=10))
        self.diff_input = toga.Selection(items=['Easy', 'Medium', 'Hard'], style=Pack(margin_bottom=10))
        self.subtasks_input = toga.TextInput(placeholder='Sub-tasks (e.g. Chap 1, Chap 2)...', style=Pack(margin_bottom=10))
        self.form_box.add(toga.Label('Exam Date:', style=Pack(margin_bottom=5, font_size=10, color='gray')))
        self.date_input = toga.DateInput(style=Pack(margin_bottom=20))
        btn_box = toga.Box(style=Pack(direction=ROW))
        save_btn = toga.Button('Save', on_press=self.save_subject, style=Pack(flex=1, background_color=AppTheme.PRIMARY, color='white', margin_right=5))
        cancel_btn = toga.Button('Cancel', on_press=self.cancel_form, style=Pack(flex=1, background_color=AppTheme.DANGER, color='white'))
        btn_box.add(save_btn, cancel_btn)
        self.form_box.add(self.sub_input, self.diff_input, self.subtasks_input, self.date_input, btn_box)

    def refresh(self):
        self.subj_list_container.clear()
        if not self.app.subjects_data:
            self.subj_list_container.add(toga.Label('No subjects yet.', style=Pack(color='gray', margin=10)))
            return
        for item in self.app.subjects_data:
            card = toga.Box(style=Pack(direction=ROW, margin_bottom=10, background_color='#f8f9fa', align_items=CENTER))
            info = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=10))
            status = " ✅" if item.get('completed') else ""
            info.add(toga.Label(f"📖 {item['name']}{status}", style=Pack(font_weight='bold')))
            info.add(toga.Label(f"Due: {item['date']} | {item['diff']}", style=Pack(font_size=10, color='gray')))
            del_btn = toga.Button('🗑️', on_press=partial(self.delete_subject, name_to_del=item['name']), style=Pack(width=40, color=AppTheme.DANGER, background_color='transparent', margin_right=10))
            card.add(info, del_btn)
            self.subj_list_container.add(card)

    def show_subject_form(self, widget):
        self.app.content_area.clear()
        self.app.content_area.add(self.form_box)

    def cancel_form(self, widget):
        self.app.show_subject_list(None)

    def save_subject(self, widget):
        name = self.sub_input.value
        if name:
            d_val = self.date_input.value
            date_str = f"{d_val.day:02d}/{d_val.month:02d}/{d_val.year}"
            self.app.subjects_data.append({
                'name': name, 'diff': self.diff_input.value, 
                'date': date_str, 'completed': False,
                'subtasks': self.subtasks_input.value,
                'journal': ""
            })
            self.app.save_data()
            self.sub_input.value = ""
            self.subtasks_input.value = ""
            self.app.show_subject_list(None)

    def delete_subject(self, widget, name_to_del):
        self.app.subjects_data = [s for s in self.app.subjects_data if s['name'] != name_to_del]
        self.app.save_data()
        self.refresh()