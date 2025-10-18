import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
#import matlab.engine
import threading
import os
import time
from PIL import Image, ImageTk, ImageGrab
from pathlib import Path
import pyautogui
from datetime import datetime
import mss
import mss.tools
import matplotlib.pyplot as plt


class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReaPT")
        self.root.geometry("600x700")

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, font=('Helvetica', 10))
        self.style.configure("TLabel", font=('Helvetica', 11))
        self.style.configure("Accent.TButton", foreground="black")

        # Two possible modes: "process" or "draw".
        self.mode_var = tk.StringVar(value="process")

        self.participants = []  
        self.points = {}       
        self.original_points = {}
        self.annotations = {}   
        self.trace_sources = {} 
        self.finalized = {}     
        self.selected_trace = 1
        self.trace_var = tk.IntVar(value=1)

        self.line_ids = {}
        self.drawing = False
        self.current_line_points = []

        self.mode = None
        self.animation_id = None
        self.filename_label_id = None
        self.add_participant_label = None

        self.setup_selection_interface()

    def setup_selection_interface(self):
        """Set up the initial participant selection interface."""
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill="both", expand=True)

        ttk.Label(self.main_frame, text="ReaPT", font=('Helvetica', 16, 'bold')).pack(pady=(0, 20))

        mode_frame = ttk.Frame(self.main_frame)
        mode_frame.pack(fill="x", pady=10)
        ttk.Label(mode_frame, text="Select mode:").pack(side="left", padx=5)

        
        ttk.Radiobutton(
            mode_frame, text="Process Videos",
            variable=self.mode_var, value="process",
            command=self.update_mode
        ).pack(side="left", padx=5)

        ttk.Radiobutton(
            mode_frame, text="Draw Traces (or Import CSV)",
            variable=self.mode_var, value="draw",
            command=self.update_mode
        ).pack(side="left", padx=5)

        self.selection_frame = ttk.LabelFrame(self.main_frame, text="Participants", padding="10")
        self.selection_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas_frame = tk.Canvas(self.selection_frame)
        self.scrollbar = ttk.Scrollbar(self.selection_frame, orient="vertical", command=self.canvas_frame.yview)
        self.scrollable_frame = ttk.Frame(self.canvas_frame)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_frame.configure(scrollregion=self.canvas_frame.bbox("all"))
        )

        self.canvas_frame.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_frame.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.trace_frame = ttk.LabelFrame(self.main_frame, text="Start with", padding="10")
        self.trace_frame.pack(fill="x", padx=10, pady=10)

        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(fill="x", pady=10)
        ttk.Button(self.buttons_frame, text="Start", command=self.start_action,
                   style="Accent.TButton").pack(side="left", padx=5)

        self.add_participant()
        self.root.update_idletasks()
        self.update_mode()

    def add_participant(self):
        """Add a new participant entry field."""
        participant_id = len(self.participants) + 1
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=5)

        label_text = f"Participant {participant_id}:"
        ttk.Label(frame, text=label_text).pack(side="left", padx=5)
        entry = ttk.Entry(frame)
        entry.pack(side="left", fill="x", expand=True, padx=5)

        browse_button = ttk.Button(
            frame,
            text="Browse",
            command=lambda: self.browse_file(entry)
        )
        browse_button.pack(side="left")

        # Init data for this participant
        self.participants.append((entry, None))
        self.points[participant_id] = []
        self.original_points[participant_id] = []
        self.annotations[participant_id] = []
        self.trace_sources[participant_id] = None
        self.finalized[participant_id] = False

        if self.add_participant_label:
            self.add_participant_label.destroy()

        self.add_participant_label = ttk.Label(
            self.scrollable_frame,
            text="Add Participant",
            foreground="blue",
            font=('Helvetica', 10, 'underline'),
            cursor="hand2"
        )
        self.add_participant_label.pack(pady=5)
        self.add_participant_label.bind("<Button-1>", lambda e: self.add_participant())

        self.update_trace_selection()

    def update_mode(self):
        """Switch between 'Process Videos' and 'Draw' modes."""
        mode = self.mode_var.get()
        if mode == "process":
            self.selection_frame.config(text="Videos")
        else:
            self.selection_frame.config(text="Traces or Keys")

    def update_trace_selection(self):
        for widget in self.trace_frame.winfo_children():
            widget.destroy()
        for i in range(1, len(self.participants) + 1):
            ttk.Radiobutton(
                self.trace_frame,
                text=f"Participant {i}",
                variable=self.trace_var,
                value=i
            ).pack(side="left", padx=10)
        if self.participants:
            self.trace_var.set(1)

    def browse_file(self, entry):
        """Open a file dialog to select either a video (process mode) or CSV (draw mode)."""
        mode = self.mode_var.get()
        if mode == "process":
            file_types = [("Video files", "*.mov *.mp4 *.avi")]
        else:
            file_types = [("CSV files", "*.csv"), ("All files", "*.*")]

        filename = filedialog.askopenfilename(filetypes=file_types)
        if filename:
          
            base_name = os.path.splitext(os.path.basename(filename))[0]
            entry.delete(0, tk.END)
            entry.insert(0, base_name)

            participant_id = None
            for idx, (ent, _) in enumerate(self.participants, start=1):
                if ent is entry:
                    participant_id = idx
                    break
            if participant_id is not None:
               
                self.participants[participant_id - 1] = (entry, filename)
                self.trace_sources[participant_id] = filename

    def start_action(self):
        """Initiate processing or drawing/importing based on the mode."""
        self.mode = self.mode_var.get()
        valid_participants = [(entry, path) for entry, path in self.participants if entry.get()]

        if self.mode == "draw":
            # In "draw" mode, if a CSV is provided for a participant, automatically load & finalize it.
            for i, (entry, path) in enumerate(valid_participants, 1):
                if path and os.path.isfile(path):  
                    try:
                        coords = pd.read_csv(path, header=None)
                        coords_list = list(zip(coords[0].values, coords[1].values))
                        
                      
                        if len(coords_list) >= 2:
                            if coords_list[0][0] > coords_list[-1][0]:
                                coords_list.reverse()
                       
                        
                        self.points[i] = coords_list
                        self.original_points[i] = self.points[i].copy()
                        self.trace_sources[i] = path
                        self.finalized[i] = True
                    except Exception as e:
                        messagebox.showerror(
                            "Error",
                            f"Failed to load CSV for participant {i}:\n{str(e)}"
                        )
                # If no path was given, points[i] remains empty => user can draw freely

            self.selected_trace = self.trace_var.get()
            self.main_frame.pack_forget()
            self.launch_drawing_interface()
            return
        if not valid_participants:
            messagebox.showerror("Error", "Please select at least one file.")
            return

        self.selected_trace = self.trace_var.get()
        self.main_frame.pack_forget()

        if self.mode == "process":
            self.setup_loading_interface()
            threading.Thread(target=self.process_videos, args=(valid_participants,), daemon=True).start()
        else:  # import
            try:
                for i, (entry, path) in enumerate(valid_participants, 1):
                    coords = pd.read_csv(path, header=None)
                    self.points[i] = list(zip(coords[0].values, coords[1].values))
                    self.original_points[i] = self.points[i].copy()
                    self.trace_sources[i] = path
                self.launch_drawing_interface()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV files: {str(e)}")

       

    def setup_loading_interface(self):
        """
        self.loading_frame = ttk.Frame(self.root)
        self.loading_frame.pack(fill="both", expand=True)

        self.loading_container = ttk.Frame(self.loading_frame)
        self.loading_container.place(relx=0.5, rely=0.5, anchor="center")

        self.canvas_loading = tk.Canvas(self.loading_container, width=120, height=120, highlightthickness=0)
        self.canvas_loading.pack()

        cx, cy, r = 60, 60, 40
        self.loading_angle = 0
        self.arc = self.canvas_loading.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=0, extent=90, width=5, style="arc", outline="green"
        )

        self.loading_label = ttk.Label(
            self.loading_container,
            text="Starting MATLAB engine...",
            font=('Helvetica', 12, 'bold')
        )
        self.loading_label.pack(pady=(10, 0))

        self.subtext_label = ttk.Label(
            self.loading_container,
            text="In the meantime, go to EchoWave",
            font=('Helvetica', 10, 'italic')
        )
        self.subtext_label.pack(pady=(5, 0))

        self.animate_loading()
"""
    def animate_loading(self):
        if hasattr(self, 'canvas_loading') and self.canvas_loading.winfo_exists():
            self.loading_angle = (self.loading_angle + 10) % 360
            self.canvas_loading.delete(self.arc)
            cx, cy, r = 60, 60, 40
            self.arc = self.canvas_loading.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=self.loading_angle, extent=90,
                width=5, style="arc", outline="green"
            )
            self.animation_id = self.root.after(50, self.animate_loading)
        else:
            self.animation_id = None

    def stop_animation(self):
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def update_loading_text(self, text):
        self.root.after(0, lambda: self.loading_label.config(text=text))

    def process_videos(self, participants):
        """
        try:
            self.update_loading_text("Starting MATLAB engine...")
            self.eng = matlab.engine.start_matlab()
            matlab_script_path = "tracePalateCES.m"
            self.eng.addpath(matlab_script_path, nargout=0)

            for i, (entry, video_path) in enumerate(participants, 1):
                video_name = os.path.basename(video_path)
                self.update_loading_text(f"Processing {video_name}...")
                self.eng.tracePalateCES(video_path, nargout=0)
                time.sleep(1)

                video_base = os.path.splitext(video_name)[0]
                csv_filename = os.path.join("participants_palates", f"{video_base}_palate.csv")
                coords = pd.read_csv(csv_filename, header=None)
                self.points[i] = list(zip(coords[0].values, coords[1].values))
                self.original_points[i] = self.points[i].copy()
                self.trace_sources[i] = video_path
                self.annotations[i] = []
             
                self.finalized[i] = True

            self.update_loading_text("Done")
            #self.root.after(0, self.launch_drawing_interface)
        except Exception as e:
            self.update_loading_text(f"Error: {str(e)}")
"""


    def launch_drawing_interface(self):
       
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.stop_animation()
            self.loading_frame.destroy()

        self.points['manual'] = []
        self.annotations['manual'] = []

        self.root.attributes('-alpha', 0.25)
        self.root.attributes('-topmost', True)
        self.root.state('zoomed')

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main_frame, bg='black', highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)

        self.line_ids = {i: None for i in self.points.keys()}
        self.line_ids['manual'] = None

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)

        for i in range(1, len(self.participants) + 1):
            self.root.bind(str(i), lambda event, num=i: self.switch_trace(num))

        self.root.bind("<Return>", lambda event: self.align_lines())

        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(side="bottom", fill="x", pady=5)

        self.root.bind("<Delete>", lambda event: self.clear())

        ttk.Button(self.button_frame, text="Clear Annotations", command=self.clear).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="Screenshot", command=self.take_screenshot).pack(side="left", padx=5)

        if self.mode == "process":
            ttk.Button(
                self.button_frame, text="Re-run MATLAB",
                command=self.rerun_matlab
            ).pack(side="left", padx=5)

        if self.mode == "draw":
            self.root.bind("p", lambda event: self.save_current_trace())

        self.root.update_idletasks()
        self.root.after(100, self.update_visualization)

    def save_current_trace(self):
        if self.mode != "draw":
            return

        participant_id = self.selected_trace
        p_line = self.points.get(participant_id, [])
        if not p_line:
            messagebox.showinfo("Info", "No palate trace to save for this participant.")
            return

        matching_key = self.participants[participant_id - 1][0].get()
        if not matching_key:
            matching_key = f"participant_{participant_id}"

        save_dir = "participants_palates"
        os.makedirs(save_dir, exist_ok=True)

        filename = os.path.join(save_dir, f"{matching_key}.csv")

        df = pd.DataFrame(p_line)
        df.to_csv(filename, header=False, index=False)

        self.finalized[participant_id] = True
        self.original_points[participant_id] = p_line.copy()


    def start_drawing(self, event):
        self.drawing = True
        self.current_line_points = [(event.x, event.y)]

    def draw(self, event):
        if self.drawing:
            self.current_line_points.append((event.x, event.y))
            self.canvas.delete("current_line")
            self.canvas.create_line(
                self.current_line_points, fill="white", width=5, tags="current_line"
            )

    def stop_drawing(self, event):
        self.drawing = False
        self.canvas.delete("current_line")

        if len(self.current_line_points) < 2:
            self.current_line_points = []
            return
        
        x_vals = [p[0] for p in self.current_line_points]
        y_vals = [p[1] for p in self.current_line_points]
        first_x, last_x = x_vals[0], x_vals[-1]
        width = max(x_vals) - min(x_vals)
        height = max(y_vals) - min(y_vals)

        # Right->left => participant's trace (unless finalized) or "manual" if finalized
        # Left->right => annotation
        if last_x < first_x and width >= 2 * height:
            if not self.finalized[self.selected_trace]:
                self.points[self.selected_trace] = self.current_line_points
            else:
                self.points['manual'] = self.current_line_points
        else:
            self.annotations.setdefault(self.selected_trace, []).append(self.current_line_points)

        self.current_line_points = []
        self.update_visualization()

    def switch_trace(self, trace_num):
        if trace_num in self.points:
            self.selected_trace = trace_num
            self.update_visualization()

    def clear(self):
        """Remove annotations for the selected participant (not the main palate line)."""
        if self.selected_trace in self.annotations:
            self.annotations[self.selected_trace].clear()
        if 'manual' in self.points:
            self.points['manual'].clear()
        self.update_visualization()

    def reset(self):
        """Reset participant’s line to its original state (if in process mode)."""
        if (self.mode == "process" and
                self.selected_trace in self.original_points and
                self.original_points[self.selected_trace]):
            self.points[self.selected_trace] = self.original_points[self.selected_trace].copy()
            self.annotations[self.selected_trace].clear()
            self.update_visualization()

    def update_visualization(self):
        self.canvas.delete("all")
        colors = {i: "yellow" for i in range(1, len(self.participants) + 1)}
        colors['manual'] = "blue"

        if self.selected_trace in self.points and self.points[self.selected_trace]:
            self.line_ids[self.selected_trace] = self.canvas.create_line(
                self.points[self.selected_trace],
                fill=colors.get(self.selected_trace, "yellow"),
                width=10
            )

        if 'manual' in self.points and self.points['manual']:
            self.line_ids['manual'] = self.canvas.create_line(
                self.points['manual'],
                fill=colors['manual'],
                width=10
            )

        for annotation in self.annotations.get(self.selected_trace, []):
            if annotation:
                self.canvas.create_line(annotation, fill="red", width=5)

        if self.filename_label_id:
            self.canvas.delete(self.filename_label_id)

        if self.mode == "process":
            if self.selected_trace in self.trace_sources and self.trace_sources[self.selected_trace]:
                filename = os.path.basename(self.trace_sources[self.selected_trace])
                filename = Path(filename).stem
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:
                    self.filename_label_id = self.canvas.create_text(
                        canvas_width - 10, 10,
                        text=filename,
                        fill="white",
                        font=('Helvetica', 50),
                        anchor="ne"
                    )
        else:
            p_label = self.participants[self.selected_trace - 1][0].get()
            canvas_width = self.canvas.winfo_width()
            if p_label and canvas_width > 1:
                self.filename_label_id = self.canvas.create_text(
                    canvas_width - 10, 10,
                    text=p_label,
                    fill="white",
                    font=('Helvetica', 50),
                    anchor="ne"
                )

        self.root.title(f"Showing Participant {self.selected_trace}")


    def resample_points(self, points, n_points):
        points = np.array(points)
        if len(points) <= 1:
            return points
        diffs = np.diff(points, axis=0)
        distances = np.sqrt(np.sum(diffs ** 2, axis=1))
        cum_distances = np.concatenate(([0], np.cumsum(distances)))
        total_length = cum_distances[-1]
        if total_length == 0:
            return points
        new_distances = np.linspace(0, total_length, n_points)
        new_points = []
        for d in new_distances:
            idx = np.searchsorted(cum_distances, d)
            if idx == 0:
                new_points.append(points[0])
            elif idx >= len(points):
                new_points.append(points[-1])
            else:
                t = (d - cum_distances[idx - 1]) / (cum_distances[idx] - cum_distances[idx - 1])
                interpolated = points[idx - 1] + t * (points[idx] - points[idx - 1])
                new_points.append(interpolated)
        return new_points

    def align_lines(self):
        """
        Align the currently selected participant’s line (src) to the “manual” line (tgt).
        This version tries both normal and reversed src to avoid unwanted flipping.
        """
        if 'manual' not in self.points or not self.points['manual']:
            return
        if self.selected_trace not in self.points or not self.points[self.selected_trace]:
            return

        src_original = np.array(self.points[self.selected_trace])
        tgt = np.array(self.points['manual'])

        if len(src_original) < 2 or len(tgt) < 2:
            return

        def do_alignment(src_points, tgt_points):
            n_points = min(len(src_points), len(tgt_points), 50)
            src_resampled = np.array(self.resample_points(src_points, n_points))
            tgt_resampled = np.array(self.resample_points(tgt_points, n_points))

            src_mean = np.mean(src_resampled, axis=0)
            tgt_mean = np.mean(tgt_resampled, axis=0)
            src_centered = src_resampled - src_mean
            tgt_centered = tgt_resampled - tgt_mean

            H = np.dot(src_centered.T, tgt_centered)
            U, _, Vt = np.linalg.svd(H)
            R = np.dot(Vt.T, U.T)

            if np.linalg.det(R) < 0:
                Vt[-1, :] *= -1
                R = np.dot(Vt.T, U.T)

            t = tgt_mean - np.dot(R, src_mean)
            transformed_src = np.dot(src_points, R.T) + t
            return transformed_src, R, t

       
        transformedA, RA, tA = do_alignment(src_original, tgt)

      
        n_len = min(len(transformedA), len(tgt))
        if len(transformedA) != n_len:
            transformedA = np.array(self.resample_points(transformedA, n_len))
        if len(tgt) != n_len:
            tgt = np.array(self.resample_points(tgt, n_len))

        errorA = np.sum(np.sqrt(np.sum((transformedA - tgt) ** 2, axis=1)))

        src_reversed = np.flipud(src_original) 
        transformedB, RB, tB = do_alignment(src_reversed, tgt)

  
        if len(transformedB) != n_len:
            transformedB = np.array(self.resample_points(transformedB, n_len))

        errorB = np.sum(np.sqrt(np.sum((transformedB - tgt) ** 2, axis=1)))

       
        if errorA <= errorB:
           
            final_transformed = transformedA
            R, t = RA, tA
        else:
            final_transformed = transformedB
            R, t = RB, tB
            src_original = src_reversed

        self.points[self.selected_trace] = final_transformed.tolist()

       
        if self.selected_trace in self.annotations:
            for annotation in self.annotations[self.selected_trace]:
                arr = np.array(annotation)
                
                transformed_annotation = np.dot(arr, R.T) + t
                annotation[:] = transformed_annotation.tolist()
     
        self.points['manual'].clear()
        self.update_visualization()


    def take_screenshot(self):
        base_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with mss.mss() as sct:
            monitor = {"top": 120, "left": 320, "width": 1280, "height": 720}
            screenshot = sct.grab(monitor)
            filename = f"screenshot_{base_timestamp}.png"
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
            print(f"Screenshot saved as {filename}")

        self.root.deiconify()
        self.root.state('zoomed')
        self.root.attributes('-alpha', 0.25)
        self.root.attributes('-topmost', True)

        main_frame = self.canvas.master
        main_frame.pack_forget()
        main_frame.pack(fill="both", expand=True)
        self.canvas.pack_forget()
        self.canvas.pack(side="top", fill="both", expand=True)
        self.root.update_idletasks()
        self.update_visualization()

    def rerun_matlab(self):
        self.canvas.delete("all")
        self.button_frame.pack_forget()
        self.setup_loading_interface()
        valid_participants = [(entry, path) for entry, path in self.participants if path]
        threading.Thread(target=self.process_videos, args=(valid_participants,), daemon=True).start()

    def back_to_selection(self):
        self.canvas.delete("all")
        self.button_frame.pack_forget()
        self.root.state('normal')
        self.root.attributes('-alpha', 1.0)
        self.root.attributes('-topmost', False)
        self.main_frame.pack(fill="both", expand=True)

    def __del__(self):
        if hasattr(self, 'eng'):
            self.eng.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()


