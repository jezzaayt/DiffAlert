import tkinter as tk
import requests
import json
import base64
from tkinter import messagebox
from bs4 import BeautifulSoup
from threading import Thread
from datetime import datetime
from tkinter import PhotoImage
from PIL import Image, ImageTk

class DiffAlerterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Diff Alerter") 
        # Set the icon using an .ico file located in the same folder
        try:
            # Attempt to load the icon
            icon_image = PhotoImage(file="icon.png")  # Ensure this matches your filename
            root.wm_iconphoto(False, icon_image)  # Set the icon
        except Exception as e:
            print("Error loading icon:", e)
        # Initialize site tracking data
        self.url_data = self.load_data()  # Dictionary to store URLs and selectors
        
        # Create UI components
        self.create_widgets()
        
        # Populate Listbox with loaded data
        self.populate_listbox()
        

    def create_widgets(self):
        # URL Entry and Add Button
        self.url_entry = tk.Entry(self.root, width=50)
        self.url_entry.insert(0, "Enter URL")
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.set_placeholder)
        self.url_entry.pack(pady=5)

        # Selector Entry
        self.selector_entry = tk.Entry(self.root, width=50)
        self.selector_entry.insert(0, "Enter CSS Selector (e.g., #id, .class)")
        self.selector_entry.bind("<FocusIn>", self.clear_placeholder_selector)
        self.selector_entry.bind("<FocusOut>", self.set_placeholder_selector)
        self.selector_entry.pack(pady=5)

        # Buttons
        add_button = tk.Button(self.root, text="Add URL", command=self.add_url)
        add_button.pack()
        listbox_frame = tk.Frame(self.root)
        listbox_frame.pack(pady=10)
        # Listbox to display URLs
        self.url_listbox = tk.Listbox(listbox_frame, width=70, height=10)
        self.url_listbox.pack(pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(listbox_frame, command=self.url_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.url_listbox['yscrollcommand'] = scrollbar.set
        scrollbar.config(command=self.url_listbox.yview)
        # Check Changes Button
        check_button = tk.Button(self.root, text="Check for Changes", command=self.start_monitoring)
        check_button.pack(pady=5)

        # Delete Selected URL Button
        delete_button = tk.Button(self.root, text="Delete Selected URL", command=self.delete_url)
        delete_button.pack(pady=5)

    def clear_placeholder(self, event):
        if self.url_entry.get() == "Enter URL":
            self.url_entry.delete(0, tk.END)

    def set_placeholder(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "Enter URL")

    def clear_placeholder_selector(self, event):
        if self.selector_entry.get() == "Enter CSS Selector (e.g., #id, .class)":
            self.selector_entry.delete(0, tk.END)

    def set_placeholder_selector(self, event):
        if not self.selector_entry.get():
            self.selector_entry.insert(0, "Enter CSS Selector (e.g., #id, .class)")

    def add_url(self):
        url = self.url_entry.get().strip()
        selector = self.selector_entry.get().strip()
        if url and selector and url != "Enter URL" and selector != "Enter CSS Selector (e.g., #id, .class)":
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")  # Format date without seconds
            self.url_data[url] = {
                "selector": selector,
                "hash": None,
                "previous_content": None,
                "added_date": current_time,
                "last_checked": None
            }
            self.url_listbox.insert(tk.END, f"{url} - {selector} (Added: {current_time}) ")
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
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
            
            # Check for specific status codes
            if response.status_code == 429:
                return None, "Error 429: Too Many Requests. Please try again later."
            soup = BeautifulSoup(response.text, 'html.parser')
            target_content = soup.select_one(selector)
            return target_content.get_text(strip=True) if target_content else None, None
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None, f"Error fetching {url}: {e}"

    def check_website_changes(self):
        
    # Get the current selection index
        selected = self.url_listbox.curselection()
        selected_index = selected[0] if selected else None  # Store the selected index
        # Only proceed if an item is selected
        if selected_index is not None:
            # Get the URL corresponding to the selected index
            url = list(self.url_data.keys())[selected_index]
            data = self.url_data[url]  # Get the corresponding data for the selected URL

            selector = data["selector"]
            current_content, error_message = self.get_content(url, selector)
            
            if current_content is not None:
                previous_content = data["previous_content"]
                data["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M")  # Format last checked without seconds
                
                if previous_content and current_content != previous_content:
                    self.show_changes(url, previous_content, current_content, data["added_date"], data["last_checked"])
                else:
                    self.show_changes(url, "", "No Changes", data["added_date"], data["last_checked"])
                    
                # Update the content for the next comparison
                data["previous_content"] = current_content  # Update the previous content
            else:
                # Handle case where content could not be fetched
                if error_message:
                
                    self.show_changes(url, error_message, "", data["added_date"], data["last_checked"])
                data["content_changed"] = False  # No change detected due to error


        # Save updated data after each check
        self.save_data()

        # Clear the Listbox before updating with new content
        self.url_listbox.delete(0, tk.END)

        # Second loop to insert items into the Listbox
        for url, data in self.url_data.items():
            added_date = datetime.fromisoformat(data['added_date']).date()  # Adjust format if necessary

            if data['last_checked'] is not None:
                entry = f"{url} {data['selector']} (Added: {added_date}) - {data['last_checked']}"
            else:
                entry = f"{url} - {data['selector']} (Added: {added_date})"

            # Insert the entry into the Listbox
            self.url_listbox.insert(tk.END, entry)

        # Reselect the previous selection, if it exists
        if selected_index is not None and selected_index < self.url_listbox.size():
            self.url_listbox.selection_set(selected_index)  # Reselect the previous index
            self.url_listbox.activate(selected_index)

            
            

    def show_changes(self, url, old_content, new_content, added_date, last_checked):
        old_lines = set(old_content.splitlines())
        new_lines = set(new_content.splitlines())
        
        added_lines = new_lines - old_lines
        removed_lines = old_lines - new_lines

        changes_window = tk.Toplevel(self.root)
        changes_window.title("Website Changes")
        changes_window.geometry("600x400")  # Set initial window size (width x height)
        changes_window.bind("<Escape>", lambda event: changes_window.destroy())


        # Create a frame to hold the Text widget and scrollbar
        frame = tk.Frame(changes_window)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create the Text widget
        text_widget = tk.Text(frame, wrap="word", height=15, width=70)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a scrollbar and link it to the Text widget
        scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget['yscrollcommand'] = scrollbar.set

        # Adding metadata
        
        text_widget.insert(tk.END, f"Changes detected for '{url}':\n\n")
        text_widget.insert(tk.END, f"• Added Date: {added_date}\n")
        text_widget.insert(tk.END, f"• Last Checked: {last_checked}\n\n")
       
        # Highlight differences
        if removed_lines:
            if new_content != "":
                text_widget.insert(tk.END, "• Removed Content:\n")
            for line in removed_lines:
                text_widget.insert(tk.END, f"- {line}\n", "removed")
            text_widget.insert(tk.END, "\n")
        
        if added_lines:
            if new_content != "No Changes" or new_content == "": 
                text_widget.insert(tk.END, "• Added Content:\n")
            for line in added_lines:
                text_widget.insert(tk.END, f"+ {line}\n", "added")
            text_widget.insert(tk.END, "\n")

        # Tag configurations for highlighting
        text_widget.tag_config("removed", foreground="red")
        text_widget.tag_config("added", foreground="green")

        text_widget.config(state=tk.DISABLED)  # Make the text widget read-only

    def save_data(self):
        with open("url_data.json", "w") as file:
            json.dump(self.url_data, file)

    def load_data(self):
        try:
            with open("url_data.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def populate_listbox(self):
        """ Populate the Listbox with the URLs and selectors from the loaded data. """
        for url, data in self.url_data.items():
            added_date = datetime.fromisoformat(data['added_date']).date()  # Adjust format if necessary

            if data['last_checked'] is not None:
                entry = f"{url} {data['selector']} (Added {added_date}) - {data['last_checked']}"
            else:
                entry = f"{url} - {data['selector']} (Added: {added_date})"

            # Insert the entry into the Listbox
            self.url_listbox.insert(tk.END, entry)

# Create the Tkinter app
root = tk.Tk()
app = DiffAlerterApp(root)
root.mainloop()
