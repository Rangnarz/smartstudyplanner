import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from ..components.theme import AppTheme

class FlashcardsView:
    def __init__(self, app):
        self.app = app
        self._subject = None
        self._cards = []
        self._current_idx = 0
        self._showing_front = True
        self.build_ui()

    def build_ui(self):
        self.main_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=AppTheme.BACKGROUND)
        )

        # ── Header ────────────────────────────────────────────────────────────
        header = toga.Box(
            style=Pack(direction=COLUMN, background_color=AppTheme.PRIMARY, padding=16)
        )
        self.title_label = toga.Label(
            'Flashcards',
            style=Pack(font_size=20, font_weight='bold', color='#FFFFFF')
        )
        self.subtitle_label = toga.Label(
            '',
            style=Pack(font_size=11, color='#BDD9FF', margin_top=2)
        )
        header.add(self.title_label, self.subtitle_label)
        
        btn_row = toga.Box(style=Pack(direction=ROW, margin_top=12))
        btn_row.add(toga.Button(
            'Back to Subject',
            on_press=lambda w: self.app.show_subject_list(None),
            style=Pack(flex=1, background_color=AppTheme.PRIMARY_DARK, color='#FFFFFF', font_weight='bold')
        ))
        header.add(btn_row)
        self.main_box.add(header)

        # ── Body Tabs (Study vs Edit) ─────────────────────────────────────────
        self.body_box = toga.Box(style=Pack(direction=COLUMN, flex=1, padding=16))
        self.main_box.add(self.body_box)
        
        # Will dynamically build the view based on whether there are cards
        self._build_study_view()

    def _build_edit_view(self):
        self.body_box.clear()

        # Add new card form
        add_box = toga.Box(style=Pack(direction=COLUMN, background_color=AppTheme.CARD_BG, padding=12, margin_bottom=20))
        add_box.add(toga.Label('Add New Flashcard', style=Pack(font_weight='bold', margin_bottom=8)))
        
        self.new_front = toga.TextInput(placeholder='Front (Question / Concept)', style=Pack(margin_bottom=8))
        self.new_back = toga.MultilineTextInput(placeholder='Back (Answer / Details)', style=Pack(height=60, margin_bottom=8))
        
        add_box.add(self.new_front, self.new_back)
        add_box.add(toga.Button(
            'Add Card',
            on_press=self._add_card,
            style=Pack(background_color=AppTheme.SUCCESS, color='#FFFFFF', font_weight='bold')
        ))
        self.body_box.add(add_box)

        # List existing cards
        list_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        list_box.add(toga.Label('Current Cards', style=Pack(font_weight='bold', margin_bottom=8)))
        
        if not self._cards:
            list_box.add(toga.Label('No flashcards yet. Add one above!', style=Pack(color=AppTheme.INACTIVE, font_style='italic')))
        else:
            scroll_content = toga.Box(style=Pack(direction=COLUMN))
            for i, c in enumerate(self._cards):
                card_row = toga.Box(style=Pack(direction=ROW, background_color=AppTheme.CARD_BG, padding=8, margin_bottom=4, align_items=CENTER))
                card_row.add(toga.Label(f"Q: {c.get('front', '')}", style=Pack(flex=1, font_size=11)))
                card_row.add(toga.Button(
                    '❌', 
                    on_press=lambda w, idx=i: self._delete_card(idx),
                    style=Pack(width=30, background_color='transparent', color=AppTheme.DANGER)
                ))
                scroll_content.add(card_row)
            list_box.add(toga.ScrollContainer(content=scroll_content, style=Pack(flex=1)))
            
            list_box.add(toga.Button(
                'Start Studying',
                on_press=lambda w: self._build_study_view(),
                style=Pack(margin_top=12, background_color=AppTheme.PRIMARY, color='#FFFFFF', font_weight='bold', height=40)
            ))

        self.body_box.add(list_box)

    def _build_study_view(self):
        self.body_box.clear()
        
        if not self._cards:
            self._build_edit_view()
            return
            
        if self._current_idx >= len(self._cards):
            self._current_idx = 0  # reset for now
            
        card = self._cards[self._current_idx]
        
        # Progress
        self.body_box.add(toga.Label(
            f'Card {self._current_idx + 1} of {len(self._cards)}',
            style=Pack(font_size=10, color=AppTheme.TEXT_SECONDARY, margin_bottom=8, text_align=CENTER)
        ))

        # Card UI
        self.card_bg = toga.Box(style=Pack(
            direction=COLUMN, flex=1, background_color=AppTheme.CARD_BG, 
            padding=20, align_items=CENTER
        ))
        
        # Text
        text_val = card.get('front', '') if self._showing_front else card.get('back', '')
        self.card_text = toga.Label(
            text_val,
            style=Pack(font_size=16, font_weight='bold' if self._showing_front else 'normal', 
                       color=AppTheme.TEXT_PRIMARY, text_align=CENTER, flex=1)
        )
        self.card_bg.add(self.card_text)
        self.body_box.add(self.card_bg)

        # Controls
        controls = toga.Box(style=Pack(direction=COLUMN, margin_top=16))
        
        if self._showing_front:
            controls.add(toga.Button(
                'Flip to Answer',
                on_press=self._flip_card,
                style=Pack(background_color=AppTheme.PRIMARY, color='#FFFFFF', font_weight='bold', height=50)
            ))
        else:
            # Self-rating buttons (Spaced Repetition style)
            rate_label = toga.Label('How well did you know this?', style=Pack(text_align=CENTER, font_size=10, color=AppTheme.TEXT_SECONDARY, margin_bottom=4))
            controls.add(rate_label)
            
            rate_row = toga.Box(style=Pack(direction=ROW))
            btn_style = Pack(flex=1, font_weight='bold', color='#FFFFFF', height=40)
            
            rate_row.add(toga.Button('Again', on_press=lambda w: self._next_card('again'), style=btn_style))
            rate_row.add(toga.Button('Hard',  on_press=lambda w: self._next_card('hard'),  style=btn_style))
            rate_row.add(toga.Button('Good',  on_press=lambda w: self._next_card('good'),  style=btn_style))
            rate_row.add(toga.Button('Easy',  on_press=lambda w: self._next_card('easy'),  style=btn_style))
            
            # Simple color assignment by accessing style attributes manually since Pack mapping is tricky
            rate_row.children[0].style.background_color = AppTheme.DANGER
            rate_row.children[1].style.background_color = AppTheme.WARNING
            rate_row.children[2].style.background_color = AppTheme.PRIMARY
            rate_row.children[3].style.background_color = AppTheme.SUCCESS
            
            controls.add(rate_row)

        controls.add(toga.Button(
            'Edit Cards',
            on_press=lambda w: self._build_edit_view(),
            style=Pack(margin_top=12, background_color='transparent', color=AppTheme.TEXT_SECONDARY, font_size=10)
        ))
        
        self.body_box.add(controls)

    def _add_card(self, widget):
        front = self.new_front.value.strip()
        back = self.new_back.value.strip()
        if front and back:
            self._cards.append({'front': front, 'back': back})
            self._save_cards()
            self._build_edit_view()

    def _delete_card(self, idx):
        if 0 <= idx < len(self._cards):
            self._cards.pop(idx)
            if self._current_idx >= len(self._cards):
                self._current_idx = max(0, len(self._cards) - 1)
            self._save_cards()
            self._build_edit_view()

    def _flip_card(self, widget):
        self._showing_front = False
        self._build_study_view()

    def _next_card(self, rating):
        # In a real SRS, we'd adjust intervals here based on rating.
        # For now, just advance the card.
        self._showing_front = True
        self._current_idx += 1
        if self._current_idx >= len(self._cards):
            self._current_idx = 0
            
        self._build_study_view()

    def _save_cards(self):
        if self._subject:
            for s in self.app.subjects_data:
                if s['name'] == self._subject:
                    s['flashcards'] = self._cards
                    break
            self.app.save_data()

    def prepare_study(self, subject_name):
        self._subject = subject_name
        self.subtitle_label.text = f'Studying: {subject_name}'
        
        self._cards = []
        for s in self.app.subjects_data:
            if s['name'] == subject_name:
                self._cards = s.get('flashcards', [])
                break
                
        self._current_idx = 0
        self._showing_front = True
        
        if self._cards:
            self._build_study_view()
        else:
            self._build_edit_view()
