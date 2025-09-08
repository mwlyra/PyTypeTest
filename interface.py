import tkinter as tk
import random


class AppInterface:
    """Manages the entire UI and logic for the Typing Speed Test application."""

    TEST_DURATION = 30

    # --- INITIALIZATION AND SETUP ---

    def __init__(self, master):
        """Initializes the main application window and components."""
        self.master = master
        self._initialize_state_variables()
        self._setup_ui()

        self.master.after(50, self._initial_setup)

    def _initialize_state_variables(self):
        """Initializes or resets all state-tracking variables for the test."""
        self.original_text = ""
        self.current_index = 0
        self.correct_chars = 0
        self.total_typed_chars = 0

        self.time_left = self.TEST_DURATION
        self.timer_running = False
        self.timer_id = None

        self.is_scrolling = False
        self.line_height_px = 1
        self.scroll_threshold_px = 0

    def _setup_ui(self):
        """Creates and places all the widgets on the screen."""
        self.master.title("Typing Speed Test")
        self.master.geometry("800x600")
        self.master.config(bg="grey10")

        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=0)
        self.master.columnconfigure(2, weight=1)

        self.title_label = tk.Label(
            self.master,
            text="Test your typing speed!",
            font=("JetBrains Mono", 16, "bold"),
            bg="grey10",
            fg="white",
        )
        self.title_label.grid(row=0, column=1, padx=10, pady=10)

        self.timer_label = tk.Label(
            self.master,
            text=f"Time: {self.time_left}",
            font=("JetBrains Mono", 14),
            bg="grey10",
            fg="white",
        )
        self.timer_label.grid(row=1, column=0, sticky="e", padx=20)

        self.wpm_label = tk.Label(
            self.master,
            text="WPM: 0",
            font=("JetBrains Mono", 14),
            bg="grey10",
            fg="white",
        )
        self.wpm_label.grid(row=1, column=2, sticky="w", padx=20)

        self.text_area = tk.Text(
            self.master,
            font=("JetBrains Mono", 16),
            bg="grey10",
            fg="white",
            borderwidth=0,
            height=5,
            width=50,
            wrap="word",
            padx=20,
            pady=10,
            spacing2=10,
        )
        self.text_area.grid(row=2, column=0, columnspan=3, pady=10)
        self._configure_text_tags()

    def _configure_text_tags(self):
        """Configures the color and style tags for the text widget."""
        self.text_area.tag_config("untouched", foreground="grey50")
        self.text_area.tag_config("correct", foreground="white")
        self.text_area.tag_config("incorrect", foreground="#ff0000")
        self.text_area.tag_config("cursor", background="gold2")

    def _initial_setup(self):
        """Performs setup tasks after the main window is stable."""
        self._setup_new_test()
        self.master.bind("<KeyPress>", self.on_key_press)
        self.master.update_idletasks()
        self._calculate_stable_geometry()

    # --- TEST LIFECYCLE ---

    def _start_test(self):
        """Starts the timer if it's not already running."""
        if not self.timer_running:
            self.timer_running = True
            self._update_timer()

    def _end_test(self):
        """Ends the test, stops the timer, and calculates results."""
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
        self.master.unbind("<KeyPress>")

        minutes = self.TEST_DURATION / 60.0
        wpm = (self.correct_chars / 5) / minutes if minutes > 0 else 0

        self.wpm_label.config(text=f"WPM: {wpm:.2f}")
        self.title_label.config(text="Time's Up! Press Restart.")

    def _setup_new_test(self):
        """Loads a new phrase and resets the text area for a new test."""
        try:
            with open("phrases.txt", "r", encoding="utf-8") as file:
                phrases = file.readlines()
            self.original_text = random.choice(phrases).strip()
        except (FileNotFoundError, IndexError):
            self.original_text = "Error: Could not load text from phrases.txt."

        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", self.original_text)
        self.text_area.tag_add("untouched", "1.0", tk.END)
        self.text_area.config(state="disabled")

        self.current_index = 0
        self._update_cursor_position()

    # --- EVENT HANDLING ---

    def on_key_press(self, event):
        """Main dispatcher for key press events."""
        self._start_test()

        if event.keysym in (
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
            "Caps_Lock",
            "Tab",
        ):
            return

        if event.keysym == "BackSpace":
            self._handle_backspace()
        elif self.current_index < len(self.original_text):
            self._handle_character(event)

        self._update_cursor_position()
        self._update_scroll_position()

    def _handle_backspace(self):
        """Handles the logic for a backspace key press."""
        if self.current_index > 0:
            self.current_index -= 1
            if self.total_typed_chars > 0:
                self.total_typed_chars -= 1

            index_str = f"1.{self.current_index}"
            self.text_area.tag_remove("correct", index_str, f"{index_str}+1c")
            self.text_area.tag_remove("incorrect", index_str, f"{index_str}+1c")
            self.text_area.tag_add("untouched", index_str, f"{index_str}+1c")

    def _handle_character(self, event):
        """Handles the logic for a regular character key press."""
        typed_char = " " if event.keysym == "space" else event.char
        expected_char = self.original_text[self.current_index]

        index_str = f"1.{self.current_index}"
        self.text_area.tag_remove("untouched", index_str, f"{index_str}+1c")

        if typed_char == expected_char:
            self.text_area.tag_add("correct", index_str, f"{index_str}+1c")
            self.correct_chars += 1
        else:
            self.text_area.tag_add("incorrect", index_str, f"{index_str}+1c")

        self.total_typed_chars += 1
        self.current_index += 1

    # --- UI UPDATES & SCROLLING ---

    def _update_timer(self):
        """Updates the timer label every second."""
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=f"Time: {self.time_left}")
            self.timer_id = self.master.after(1000, self._update_timer)
        else:
            self._end_test()

    def _update_cursor_position(self):
        """Moves the cursor highlight to the current character index."""
        self.text_area.tag_remove("cursor", "1.0", tk.END)
        if self.current_index < len(self.original_text):
            cursor_index = f"1.{self.current_index}"
            self.text_area.tag_add("cursor", cursor_index, f"{cursor_index}+1c")

    def _update_scroll_position(self):
        """Scrolls the text area proactively based on cursor's pixel geometry."""
        if self.is_scrolling:
            return
        try:
            cursor_index = self.text_area.index(f"1.0 + {self.current_index} chars")
            cursor_bbox = self.text_area.bbox(cursor_index)

            if not cursor_bbox:
                self.text_area.see(cursor_index)
                return

            cursor_y = cursor_bbox[1]
            if cursor_y >= self.scroll_threshold_px:
                self.is_scrolling = True
                self.text_area.yview_scroll(1, "pages")
                self.master.after(100, self._enable_scrolling)
        except Exception:
            pass

    def _enable_scrolling(self):
        """Callback to re-enable scrolling after a short cooldown."""
        self.is_scrolling = False

    def _calculate_stable_geometry(self):
        """Calculates and stores widget geometry after the UI is stable."""
        try:
            widget_height_in_lines = int(self.text_area.cget("height"))
            bbox = self.text_area.bbox("1.0")
            if bbox:
                self.line_height_px = bbox[3]
                widget_height_px = self.line_height_px * widget_height_in_lines
                self.scroll_threshold_px = widget_height_px - (
                    self.line_height_px * 1.5
                )
        except (tk.TclError, TypeError):
            self.line_height_px = 25
            self.scroll_threshold_px = 50
