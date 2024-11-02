import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import hashlib
import json
from bs4 import BeautifulSoup
from threading import Thread

class WebsiteMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Change Monitor")
        
        # Initialize site tracking data
        self.url_data = self.load_data()  # Dictionary to store URLs and selectors
        
        # Create UI components
        self.create_widgets()

    def create_widgets(self):
        # URL Entry and Add Button
        self.url_entry = tk.Entry(self.root, width=50)
        self.url_entry.insert(0, "Enter URL")
        self.url_entry.pack(pady=5)

        # Selector Entry
        self.selector_entry = tk.Entry(self.root, width=50)
        self.selector_entry.insert(0, "Enter CSS Selector (e.g., #id, .class)")
        self.selector_entry.pack(pady=5)

        # Buttons
        add_button = tk.Button(self.root, text="Add URL", command=self.add_url)
        add_button.pack()

        # Listbox to display URLs
        self.url_listbox = tk.Listbox(self.root, width=50, height=10)
        self.url_listbox.pack(pady=10)

        # Check Changes Button
        check_button = tk.Button(self.root, text="Check for Changes", command=self.start_monitoring)
        check_button.pack(pady=5)

        # Delete Selected URL Button
        delete_button = tk.Button(self.root, text="Delete Selected URL", command=self.delete_url)
        delete_button.pack(pady=5)

    def add_url(self):
        url = self.url_entry.get().strip()
        selector = self.selector_entry.get().strip()
        if url and selector:
            self.url_data[url] = {"selector": selector, "hash": None, "previous_content": None}
            self.url_listbox.insert(tk.END, f"{url} - {selector}")
            self.url_entry.delete(0, tk.END)
            self.selector_entry.delete(0, tk.END)
            self.save_data()
            messagebox.showinfo("Success", f"URL '{url}' added with selector '{selector}'.")

    def delete_url(self):
        selected = self.url_listbox.curselection()
        if selected:
            index = selected[0]
            url = list(self.url_data.keys())[index]
            del self.url_data[url]  # Remove from data
            self.url_listbox.delete(index)
            self.save_data()
            messagebox.showinfo("Success", f"URL '{url}' removed from monitor list.")

    def start_monitoring(self):
        monitor_thread = Thread(target=self.check_website_changes)
        monitor_thread.daemon = True
        monitor_thread.start()

    def get_content(self, url, selector):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            target_content = soup.select_one(selector)
            return target_content.get_text(strip=True) if target_content else None
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def check_website_changes(self):
        for url, data in self.url_data.items():
            selector = data["selector"]
            current_content = self.get_content(url, selector)
            if current_content is not None:
                previous_content = data["previous_content"]
                if previous_content and current_content != previous_content:
                    self.show_changes(url, previous_content, current_content)
                # Update the content and hash for the next comparison
                self.url_data[url]["previous_content"] = current_content
        # Save updated data after each check
        self.save_data()

    def show_changes(self, url, old_content, new_content):
        changes = f"Changes detected for '{url}':\n\nOld Content:\n{old_content}\n\nNew Content:\n{new_content}"
        messagebox.showinfo("Website Changed", changes)

    def save_data(self):
        with open("url_data.json", "w") as file:
            json.dump(self.url_data, file)

    def load_data(self):
        try:
            with open("url_data.json", "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

# Create the Tkinter app
root = tk.Tk()
app = WebsiteMonitorApp(root)
root.mainloop()
