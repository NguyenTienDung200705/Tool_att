import csv
import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


# ============================================================
# CONFIG
# ============================================================

APP_DIR = Path.home() / ".person_attribute_editor"
STATE_FILE = APP_DIR / "state.json"
APP_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
TRUE_VALUES = {"1", "true", "yes", "y", "x", "checked", "tick", "on"}


def is_true(value):
    return str(value).strip().lower() in TRUE_VALUES


class AttributeAnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Attribute Annotation Tool")
        self.root.geometry("1450x850")
        self.root.minsize(1200, 720)

        self.csv_path = ""
        self.image_dir = ""
        self.image_col = ""
        self.headers = []
        self.attribute_cols = []
        self.rows = []
        self.image_paths = []
        self.current_index = 0

        self.vars = {}
        self.photo = None
        self.dirty = False

        self.load_state()
        self.build_style()
        self.build_ui()

        if (
            self.csv_path
            and self.image_dir
            and os.path.isfile(self.csv_path)
            and os.path.isdir(self.image_dir)
        ):
            try:
                self.load_data()
            except Exception as e:
                messagebox.showwarning(
                    "Restore session",
                    f"Không thể khôi phục dữ liệu cũ:\n\n{e}"
                )

    # ========================================================
    # STATE
    # ========================================================

    def load_state(self):
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(
                STATE_FILE.read_text(encoding="utf-8")
            )
            self.csv_path = data.get("csv_path", "")
            self.image_dir = data.get("image_dir", "")
            self.current_index = int(
                data.get("current_index", 0)
            )
        except Exception:
            pass

    def save_state(self):
        try:
            STATE_FILE.write_text(
                json.dumps(
                    {
                        "csv_path": self.csv_path,
                        "image_dir": self.image_dir,
                        "current_index": self.current_index,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ========================================================
    # STYLE
    # ========================================================

    def build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Main.TLabelframe", padding=4)
        style.configure(
            "Main.TLabelframe.Label",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Nav.TButton",
            font=("Segoe UI", 9),
            padding=(8, 3)
        )
        style.configure(
            "Save.TButton",
            font=("Segoe UI", 9),
            padding=(8, 4)
        )

        style.configure(
            "Attribute.TCheckbutton",
            background="white",
            foreground="#202020",
            font=("Segoe UI", 8),
            padding=(0, 0),
        )

        style.map(
            "Attribute.TCheckbutton",
            background=[
                ("active", "white"),
                ("pressed", "white"),
                ("selected", "white"),
            ],
            foreground=[
                ("disabled", "#999999"),
                ("active", "#202020"),
            ],
        )

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):
        root_frame = ttk.Frame(self.root, padding=6)
        root_frame.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # FILE SELECTION
        # Compact top bar: do not let the long image path
        # consume unnecessary space.
        # ----------------------------------------------------
        file_group = ttk.LabelFrame(
            root_frame,
            text="File Selection",
            style="Main.TLabelframe"
        )
        file_group.pack(fill="x", pady=(0, 5))

        ttk.Button(
            file_group,
            text="Load CSV",
            command=self.choose_csv
        ).pack(side="left", padx=(3, 5))

        self.csv_name_label = ttk.Label(
            file_group,
            text="No CSV loaded",
            width=24,
            anchor="w"
        )
        self.csv_name_label.pack(side="left", padx=(0, 8))

        ttk.Button(
            file_group,
            text="Load Image Folder",
            command=self.choose_image_folder
        ).pack(side="left", padx=(0, 5))

        # Show only the folder name in the top bar.
        # The complete path is shown in the bottom status bar.
        self.image_folder_label = ttk.Label(
            file_group,
            text="No image folder loaded",
            width=30,
            anchor="w"
        )
        self.image_folder_label.pack(side="left")

        # ----------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------
        nav_group = ttk.LabelFrame(
            root_frame,
            text="Navigation",
            style="Main.TLabelframe"
        )
        nav_group.pack(fill="x", pady=(0, 5))

        ttk.Button(
            nav_group,
            text="Previous",
            style="Nav.TButton",
            command=self.previous_image
        ).pack(side="left", padx=(3, 4))

        ttk.Button(
            nav_group,
            text="Next",
            style="Nav.TButton",
            command=self.next_image
        ).pack(side="left", padx=(0, 12))

        self.position_label = ttk.Label(
            nav_group,
            text="0 / 0",
            width=10,
            anchor="center"
        )
        self.position_label.pack(side="left", padx=(0, 7))

        ttk.Label(
            nav_group,
            text="Go to:"
        ).pack(side="left", padx=(0, 4))

        self.goto_entry = ttk.Entry(
            nav_group,
            width=7,
            justify="center"
        )
        self.goto_entry.pack(side="left", padx=(0, 5))
        self.goto_entry.bind("<Return>", self.goto_image)

        ttk.Button(
            nav_group,
            text="Go",
            style="Nav.TButton",
            command=self.goto_image
        ).pack(side="left")

        self.checked_label = ttk.Label(
            nav_group,
            text="Checked: 0",
            foreground="#006dcc"
        )
        self.checked_label.pack(side="right", padx=8)

        # ----------------------------------------------------
        # MAIN
        # Image area is narrower: 280 px.
        # Attribute area gets all remaining width.
        # ----------------------------------------------------
        main = ttk.Frame(root_frame)
        main.pack(fill="both", expand=True, pady=(0, 5))

        main.grid_columnconfigure(0, weight=0, minsize=280)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # IMAGE
        image_group = ttk.LabelFrame(
            main,
            text="Image",
            style="Main.TLabelframe"
        )
        image_group.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5)
        )

        self.image_canvas = tk.Canvas(
            image_group,
            background="white",
            highlightthickness=1,
            highlightbackground="#d0d0d0",
            width=265
        )
        self.image_canvas.pack(
            fill="both",
            expand=True,
            padx=2,
            pady=2
        )

        self.image_canvas.bind(
            "<Configure>",
            lambda e: self.refresh_image()
        )

        self.image_info_label = ttk.Label(
            image_group,
            text="",
            anchor="w"
        )
        self.image_info_label.pack(
            fill="x",
            padx=3,
            pady=(2, 0)
        )

        # ATTRIBUTES
        attr_group = ttk.LabelFrame(
            main,
            text="Attributes (120)",
            style="Main.TLabelframe"
        )
        attr_group.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        # Search bar is compact.
        search = ttk.Frame(attr_group)
        search.pack(fill="x", pady=(0, 3))

        ttk.Label(
            search,
            text="Search:"
        ).pack(side="left", padx=(2, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace_add(
            "write",
            lambda *_: self.render_attributes()
        )

        ttk.Entry(
            search,
            textvariable=self.search_var
        ).pack(
            side="left",
            fill="x",
            expand=True
        )

        ttk.Button(
            search,
            text="Clear",
            command=lambda: self.search_var.set("")
        ).pack(side="left", padx=(4, 0))

        # ----------------------------------------------------
        # ATTRIBUTE GRID
        #
        # IMPORTANT CHANGE:
        # 4 columns instead of 5.
        #
        # This gives each attribute substantially more width,
        # so names such as upperBodyShortSleeve,
        # carryingMessengerBag, personalLarger60, etc.
        # are not clipped.
        #
        # 120 attributes / 4 columns = 30 rows.
        # With compact 8px text and 720+ px window height,
        # all 120 fit without a scrollbar.
        # ----------------------------------------------------
        self.attr_frame = tk.Frame(
            attr_group,
            background="white"
        )
        self.attr_frame.pack(
            fill="both",
            expand=True,
            padx=2,
            pady=2
        )

        for c in range(4):
            self.attr_frame.grid_columnconfigure(
                c,
                weight=1,
                uniform="attribute_columns"
            )

        # No scrollbar intentionally.

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------
        ttk.Button(
            root_frame,
            text="Save CSV",
            style="Save.TButton",
            command=self.save_csv
        ).pack(fill="x")

        self.status_label = ttk.Label(
            root_frame,
            text="Ready",
            anchor="w",
            relief="sunken"
        )
        self.status_label.pack(
            fill="x",
            pady=(3, 0)
        )

        self.root.bind(
            "<Left>",
            lambda e: self.previous_image()
        )
        self.root.bind(
            "<Right>",
            lambda e: self.next_image()
        )
        self.root.bind(
            "<Control-s>",
            lambda e: self.save_csv()
        )
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.update_file_labels()

    # ========================================================
    # FILE
    # ========================================================

    def choose_csv(self):
        path = filedialog.askopenfilename(
            title="Load CSV",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self.csv_path = path

        try:
            self.load_data()
        except Exception as e:
            messagebox.showerror(
                "CSV Error",
                str(e)
            )
            return

        self.save_state()

    def choose_image_folder(self):
        path = filedialog.askdirectory(
            title="Select image folder"
        )

        if not path:
            return

        self.image_dir = path

        if self.csv_path:
            try:
                self.load_data()
            except Exception as e:
                messagebox.showerror(
                    "Image Error",
                    str(e)
                )
                return

        self.save_state()
        self.update_file_labels()

    def read_csv(self):
        with open(
            self.csv_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            sample = f.read(8192)
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(
                    sample,
                    delimiters=",;\t"
                )
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(
                f,
                dialect=dialect
            )

            rows = list(reader)
            headers = reader.fieldnames or []

        if not headers:
            raise ValueError(
                "CSV không có header."
            )

        return headers, rows

    def detect_image_column(
        self,
        headers,
        rows
    ):
        candidates = {
            "image",
            "img",
            "image_path",
            "imagepath",
            "path",
            "filename",
            "file_name",
            "file",
            "image_name"
        }

        for header in headers:
            if header.strip().lower() in candidates:
                return header

        best_header = None
        best_score = 0

        for header in headers:
            score = 0

            for row in rows[:100]:
                value = str(
                    row.get(header, "")
                ).strip()

                if (
                    Path(value)
                    .suffix
                    .lower()
                    in IMAGE_EXTS
                ):
                    score += 1

            if score > best_score:
                best_score = score
                best_header = header

        return best_header or headers[0]

    # ========================================================
    # IMAGE MATCHING
    # ========================================================

    def build_image_index(self):
        root = Path(self.image_dir)

        files = [
            p for p in root.rglob("*")
            if p.is_file()
            and p.suffix.lower() in IMAGE_EXTS
        ]

        by_relative = {}
        by_name = {}

        for p in files:
            try:
                rel = (
                    p.relative_to(root)
                    .as_posix()
                    .lower()
                )
                by_relative[rel] = p
            except ValueError:
                pass

            by_name.setdefault(
                p.name.lower(),
                p
            )

        result = []

        for row in self.rows:
            raw = str(
                row.get(
                    self.image_col,
                    ""
                )
            ).strip()

            raw = raw.replace(
                "\\",
                "/"
            ).lstrip("./")

            found = None

            if os.path.isabs(raw):
                p = Path(raw)
                if p.is_file():
                    found = p

            if found is None:
                p = root / raw
                if p.is_file():
                    found = p

            if found is None:
                found = by_relative.get(
                    raw.lower()
                )

            if found is None:
                found = by_name.get(
                    Path(raw).name.lower()
                )

            result.append(found)

        return result

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_data(self):
        if not self.csv_path:
            return

        if not self.image_dir:
            raise ValueError(
                "Hãy chọn folder ảnh."
            )

        self.headers, self.rows = (
            self.read_csv()
        )

        self.image_col = (
            self.detect_image_column(
                self.headers,
                self.rows
            )
        )

        # ====================================================
        # EXACTLY 120 ATTRIBUTES
        #
        # The CSV also contains *_score columns. Those are
        # prediction confidence values, NOT annotation
        # attributes, so they must never become checkboxes.
        # ====================================================
        candidates = [
            h for h in self.headers
            if h != self.image_col
            and not h.lower().endswith("_score")
            and h.strip().lower() not in {
                "filename",
                "file_name",
                "image",
                "img",
                "image_path",
                "imagepath",
                "path",
                "file",
                "image_name",
            }
        ]

        if len(candidates) < 120:
            raise ValueError(
                f"CSV chỉ tìm thấy {len(candidates)} thuộc tính "
                f"sau khi loại bỏ các cột *_score. Cần đúng 120."
            )

        # If the CSV has extra non-score columns, only the first
        # 120 actual attributes are used.
        self.attribute_cols = candidates[:120]

        if len(self.attribute_cols) != 120:
            raise ValueError(
                f"Tool phải có đúng 120 checkbox, "
                f"nhưng hiện có {len(self.attribute_cols)}."
            )

        self.image_paths = (
            self.build_image_index()
        )

        if not self.rows:
            raise ValueError(
                "CSV không có dữ liệu."
            )

        self.current_index = max(
            0,
            min(
                self.current_index,
                len(self.rows) - 1
            )
        )

        if len(self.attribute_cols) != 120:
            raise ValueError(
                f"Lỗi: tool phải hiển thị đúng 120 thuộc tính, "
                f"nhưng đang xác định được {len(self.attribute_cols)}."
            )

        self.create_attribute_variables()
        self.update_file_labels()
        self.show_current()
        self.save_state()

    # ========================================================
    # ATTRIBUTES
    # ========================================================

    def create_attribute_variables(self):
        self.vars = {
            attr: tk.BooleanVar(value=False)
            for attr in self.attribute_cols
        }

        self.render_attributes()

    def render_attributes(self):
        for widget in self.attr_frame.winfo_children():
            widget.destroy()

        if not self.attribute_cols:
            return

        query = (
            self.search_var
            .get()
            .strip()
            .lower()
        )

        visible = [
            attr
            for attr in self.attribute_cols
            if not query
            or query in attr.lower()
        ]

        # EXACTLY 120 attributes:
        # 4 columns x 30 rows = 120 checkboxes.
        column_count = 4

        for c in range(column_count):
            self.attr_frame.grid_columnconfigure(
                c,
                weight=1,
                uniform="attribute_columns"
            )

        for i, attr in enumerate(visible):
            column = i % column_count
            row = i // column_count

            cb = ttk.Checkbutton(
                self.attr_frame,
                text=attr,
                variable=self.vars[attr],
                style="Attribute.TCheckbutton",
                command=self.attribute_changed
            )

            cb.grid(
                row=row,
                column=column,
                sticky="w",
                padx=(4, 12),
                pady=0
            )

    def attribute_changed(self):
        # Save immediately whenever a checkbox changes.
        # This writes directly to the ORIGINAL CSV file.
        self.dirty = True
        self.update_checked_count()

        try:
            self.save_current_to_memory()
            self.save_csv(show_message=False)
            self.status_label.config(
                text=f"Auto-saved: {Path(self.csv_path).name}"
            )
        except Exception as e:
            self.status_label.config(
                text=f"Auto-save error: {e}"
            )

    def update_checked_count(self):
        count = sum(
            var.get()
            for var in self.vars.values()
        )

        self.checked_label.config(
            text=f"Checked: {count}"
        )

    # ========================================================
    # IMAGE
    # ========================================================

    def show_current(self):
        if not self.rows:
            return

        row = self.rows[
            self.current_index
        ]

        for attr in self.attribute_cols:
            self.vars[attr].set(
                is_true(
                    row.get(attr, "")
                )
            )

        self.dirty = False
        self.update_checked_count()

        total = len(self.rows)

        self.position_label.config(
            text=(
                f"{self.current_index + 1}"
                f" / {total}"
            )
        )

        self.goto_entry.delete(
            0,
            "end"
        )
        self.goto_entry.insert(
            0,
            str(self.current_index + 1)
        )

        path = self.image_paths[
            self.current_index
        ]

        self.image_canvas.delete("all")

        if path is None:
            name = str(
                row.get(
                    self.image_col,
                    ""
                )
            )

            self.image_canvas.create_text(
                140,
                250,
                text=(
                    "Image not found:\n"
                    f"{name}"
                ),
                fill="#444444",
                font=("Segoe UI", 10),
                justify="center"
            )

            self.image_info_label.config(
                text=name
            )

            self.status_label.config(
                text="Image not found"
            )
            return

        self.image_info_label.config(
            text=str(path)
        )

        self.status_label.config(
            text="Ready"
        )

        self.refresh_image()

    def refresh_image(self):
        if not self.rows:
            return

        path = self.image_paths[
            self.current_index
        ]

        if path is None or not path.exists():
            return

        try:
            image = Image.open(
                path
            ).convert("RGB")

            cw = max(
                self.image_canvas.winfo_width(),
                100
            )
            ch = max(
                self.image_canvas.winfo_height(),
                100
            )

            scale = min(
                (cw - 10) / image.width,
                (ch - 10) / image.height,
                1.0
            )

            nw = max(
                1,
                int(image.width * scale)
            )
            nh = max(
                1,
                int(image.height * scale)
            )

            image = image.resize(
                (nw, nh),
                Image.Resampling.LANCZOS
            )

            self.photo = ImageTk.PhotoImage(
                image
            )

            self.image_canvas.delete("all")

            self.image_canvas.create_image(
                cw // 2,
                ch // 2,
                image=self.photo,
                anchor="center"
            )

        except Exception as e:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(
                self.image_canvas.winfo_width() // 2,
                self.image_canvas.winfo_height() // 2,
                text=f"Cannot open image:\n{e}",
                fill="#444444",
                font=("Segoe UI", 10),
                justify="center"
            )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def save_current_to_memory(self):
        if not self.rows:
            return

        row = self.rows[
            self.current_index
        ]

        for attr in self.attribute_cols:
            row[attr] = (
                "1"
                if self.vars[attr].get()
                else "0"
            )

        self.dirty = False

    def ask_save(self):
        if not self.dirty:
            return True

        result = messagebox.askyesnocancel(
            "Unsaved changes",
            "Bạn đã thay đổi thuộc tính.\n\n"
            "Lưu trước khi chuyển ảnh?"
        )

        if result is None:
            return False

        if result:
            self.save_csv(
                show_message=False
            )
        else:
            self.show_current()

        return True

    def previous_image(self):
        if not self.rows:
            return
        if not self.ask_save():
            return

        self.current_index = max(
            0,
            self.current_index - 1
        )

        self.show_current()
        self.save_state()

    def next_image(self):
        if not self.rows:
            return
        if not self.ask_save():
            return

        self.current_index = min(
            len(self.rows) - 1,
            self.current_index + 1
        )

        self.show_current()
        self.save_state()

    def goto_image(self, event=None):
        if not self.rows:
            return

        try:
            index = (
                int(
                    self.goto_entry.get()
                ) - 1
            )
        except ValueError:
            messagebox.showwarning(
                "Go to",
                "Hãy nhập số ảnh hợp lệ."
            )
            return

        if not self.ask_save():
            return

        self.current_index = max(
            0,
            min(
                len(self.rows) - 1,
                index
            )
        )

        self.show_current()
        self.save_state()

    # ========================================================
    # SAVE
    # ========================================================

    def save_csv(self, show_message=True):
        if not self.csv_path or not self.rows:
            return

        self.save_current_to_memory()

        with open(
            self.csv_path,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self.headers,
                extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(self.rows)

        self.save_state()

        self.status_label.config(
            text=f"Saved: {self.csv_path}"
        )

        if show_message:
            messagebox.showinfo(
                "Save CSV",
                "Đã lưu thay đổi vào CSV."
            )

    # ========================================================
    # CLOSE
    # ========================================================

    def on_close(self):
        if self.dirty:
            result = messagebox.askyesnocancel(
                "Exit",
                "Bạn còn thay đổi chưa lưu.\n\n"
                "Lưu trước khi thoát?"
            )

            if result is None:
                return

            if result:
                try:
                    self.save_csv(
                        show_message=False
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Save error",
                        str(e)
                    )
                    return

        self.save_state()
        self.root.destroy()

    # ========================================================
    # LABELS
    # ========================================================

    def update_file_labels(self):
        if self.csv_path:
            self.csv_name_label.config(
                text=Path(
                    self.csv_path
                ).name
            )
        else:
            self.csv_name_label.config(
                text="No CSV loaded"
            )

        if self.image_dir:
            self.image_folder_label.config(
                text=Path(
                    self.image_dir
                ).name
            )
        else:
            self.image_folder_label.config(
                text="No image folder loaded"
            )


def main():
    root = tk.Tk()
    AttributeAnnotationTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()