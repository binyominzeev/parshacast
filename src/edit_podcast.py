import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os

XML_PATH = "../data/podcast_input.xml"

class PodcastEditor:
    def __init__(self, master):
        self.master = master
        master.title("Podcast Episode Editor")
        self.episodes = []
        self.load_episodes()

        self.tree = ttk.Treeview(master, columns=("Title", "Rabbi", "Duration"), show="headings", selectmode="extended", height=25)
        self.tree.heading("Title", text="Title")
        self.tree.heading("Rabbi", text="Rabbi")
        self.tree.heading("Duration", text="Duration")
        self.tree.column("Title", width=400)
        self.tree.column("Rabbi", width=200)
        self.tree.column("Duration", width=100)
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.populate_tree()

        btn_frame = tk.Frame(master)
        btn_frame.pack(pady=5)

        self.remove_btn = tk.Button(btn_frame, text="Remove Selected", command=self.remove_selected)
        self.remove_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = tk.Button(btn_frame, text="Save Changes", command=self.save_changes)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.reload_btn = tk.Button(btn_frame, text="Reload", command=self.reload)
        self.reload_btn.pack(side=tk.LEFT, padx=5)

    def load_episodes(self):
        if not os.path.exists(XML_PATH):
            messagebox.showerror("Error", f"File not found: {XML_PATH}")
            self.master.destroy()
            return
        tree = ET.parse(XML_PATH)
        root = tree.getroot()
        self.episodes = []
        for ep in root.findall("episode"):
            # Try to get duration, fallback to empty string if not present
            duration = ep.findtext("duration", "")
            self.episodes.append({
                "element": ep,
                "rabbi": ep.findtext("rabbi", ""),
                "title": ep.findtext("title", ""),
                "duration": duration,
            })

    def populate_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, ep in enumerate(self.episodes):
            self.tree.insert("", "end", iid=i, values=(ep["title"], ep["rabbi"], ep["duration"]))

    def remove_selected(self):
        selected = list(self.tree.selection())
        if not selected:
            messagebox.showinfo("Info", "No episode selected.")
            return
        for iid in reversed([int(i) for i in selected]):
            del self.episodes[iid]
        self.populate_tree()

    def save_changes(self):
        podcast = ET.Element("podcast")
        for ep in self.episodes:
            podcast.append(ep["element"])
        tree = ET.ElementTree(podcast)
        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
        messagebox.showinfo("Saved", "Changes saved to podcast_input.xml.")

    def reload(self):
        self.load_episodes()
        self.populate_tree()

if __name__ == "__main__":
    root = tk.Tk()
    app = PodcastEditor(root)
    root.mainloop()