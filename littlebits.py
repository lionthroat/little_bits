import datetime  # grab the date!
import json  # to save and load user data
import math
import os  # to clear terminal screen when timer updates
import random
import sys  # to allow sys.exit(), the signal to end program when user chooses to quit
import threading  # to allow user input while task timer is counting down, without stopping timer or blocking input
import time
import winsound

# for GUI
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# Initialize global timer variable
timer = 0
timer_seconds = 0

have_active_task = False
current_task = ''

freq=1000
dur=300

# Load the custom font from a font file
font_path = "assets/Lora-Regular.ttf"  # Even if you have the file, you have to install the font
lora_font = QFont("Lora", 12)  # Replace "Lora" with the font name and 12 with the desired size

# Set the custom font as the default font for the application
QApplication.setFont(lora_font)

# Set the stylesheet for list widgets
list_widget_stylesheet = """
    QListWidget {
        background-color: #D4DFC7;
        border-radius: 10px;
        padding: 5px;
    }
"""

# Set the stylesheet for list widgets
widget_stylesheet = """
    QWidget {
        background-color: #E2E9D9;
    }
"""

button_stylesheet = """
    QPushButton {
        background-color: #D4DFC7;
        font-size: 15px;
        border-radius: 5px;
        padding: 2px;
    }
"""

def timer_thread(task):
    global timerList
    while timer > 0:
        time.sleep(60)  # Sleep for 1 minute
        timer -= 1

def times_up_alert():
    print("\n\tTime\'s up!", flush=True)
    winsound.Beep(880,dur)
    winsound.Beep(932,dur)
    winsound.Beep(988,dur)
    winsound.Beep(1047,900)

class TaskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        global timer_seconds

        # Connect the aboutToQuit signal to the save_notes_on_exit slot
        QApplication.instance().aboutToQuit.connect(self.save_notes_on_exit)

        self.current_date = datetime.datetime.now()
        self.display_date = datetime.datetime.now()

        self.up_next = []
        self.done_today = []
        self.current_activity_assigned = False # either a break or a task

        self.setWindowTitle("Little Bits - The Task Tracker & Timer")
        self.setGeometry(100, 100, 600, 600)

        self.setup_ui()              # Define UI elements
        self.load_lists()            # Load in user data, if available
        self.populate_list_widgets() # After UI is fully initialized, can fill w/data

    # Initialize the UI
    def setup_ui(self):
        global current_task
        global have_active_task

        # Container widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Widget for the date and current task
        date_and_task_widget = QWidget()
        date_and_task_layout = QVBoxLayout(date_and_task_widget)
        
        # Add the date and current task labels to the widget
        pick_day_widget = QWidget()
        pick_day_layout = QHBoxLayout(pick_day_widget)

        # Today's date will always be displayed by default when opening program
        default_date_formatted = datetime.datetime.now().strftime('%A, %B %d, %Y')
        self.prev_day_button = QPushButton("←")
        self.prev_day_button.setStyleSheet("padding: 5px; border: 0;")
        self.date_label = QLabel(f"{default_date_formatted}")
        self.next_day_button = QPushButton("→")
        self.next_day_button.setStyleSheet("padding: 5px; border: 0;")

        pick_day_layout.addWidget(self.prev_day_button)
        pick_day_layout.addWidget(self.date_label)
        pick_day_layout.addWidget(self.next_day_button)

        if have_active_task:
            self.current_task_label = QLabel(f"Current Task: {self.current_task}")
        else:
            self.current_task_label = QLabel(f"Current Task: (button here!)")

        # Set the stylesheet for the date and current task labels
        self.date_label.setStyleSheet("background-color: #D4DFC7; font-size: 18px; text-align: center;")
        self.current_task_label.setStyleSheet("background-color: #96C0B7; font-size: 16px; border-radius: 10px; padding: 5px; text-align: center;")

        date_and_task_layout.addWidget(pick_day_widget)
        date_and_task_layout.addWidget(self.current_task_label)

        # Add the new widget to the layout
        layout.addWidget(date_and_task_widget)

        # Create a splitter
        splitter = QSplitter()

        # Left pane
        left_pane = QWidget()
        left_pane.setStyleSheet(widget_stylesheet)
        left_pane.setMinimumWidth(125)  # Set the minimum width you prefer
        left_layout = QVBoxLayout(left_pane)
        splitter.addWidget(left_pane)

        # Hourglass class
        self.hourglass = Hourglass()
        left_layout.addWidget(self.hourglass)

        # Timer
        self.timer_label = QLabel('00:00')
        self.timer_label.setStyleSheet("background-color: #D4DFC7; font-size: 18px;")
        self.timer_label.setAlignment(Qt.AlignCenter)  # Center align the text
        self.timer_label.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.timer_label)
        left_layout.addStretch(1)

        # Default buttons
        self.assign_task_button = QPushButton("Assign task")
        self.take_break_button = QPushButton("Take a break!")
        left_layout.addWidget(self.assign_task_button)
        left_layout.addWidget(self.take_break_button)

        # Create buttons for switching views
        self.tasks_view_button = QPushButton("Tasks")
        self.notes_view_button = QPushButton("Notes")
        left_layout.addWidget(self.tasks_view_button)
        left_layout.addWidget(self.notes_view_button)
        self.tasks_view_button.clicked.connect(self.switch_to_tasks_view)
        self.notes_view_button.clicked.connect(self.switch_to_notes_view)

        # Contextual buttons (only display if doing a task or on a timed break)
        self.complete_task_button = QPushButton("Done")
        self.add_time_button = QPushButton("Add Time")
        self.pause_timer_button = QPushButton("Pause Timer")
        left_layout.addWidget(self.complete_task_button)
        left_layout.addWidget(self.add_time_button)
        left_layout.addWidget(self.pause_timer_button)

        # Connect left pane buttons to functions
        self.assign_task_button.clicked.connect(self.assign_task)
        self.take_break_button.clicked.connect(self.take_break)

        self.complete_task_button.clicked.connect(self.complete_task)
        self.add_time_button.clicked.connect(self.add_time)
        self.pause_timer_button.clicked.connect(self.pause_timer)

        # Decide which buttons to show
        self.display_control_buttons()

        # Apply button styles
        self.assign_task_button.setStyleSheet(button_stylesheet)
        self.take_break_button.setStyleSheet(button_stylesheet)
        self.tasks_view_button.setStyleSheet(button_stylesheet)
        self.notes_view_button.setStyleSheet(button_stylesheet)
        self.complete_task_button.setStyleSheet(button_stylesheet)
        self.add_time_button.setStyleSheet(button_stylesheet)
        self.pause_timer_button.setStyleSheet(button_stylesheet)

        # Right pane setup
        right_pane = QWidget()
        right_pane.setStyleSheet(widget_stylesheet)   
        right_layout = QVBoxLayout(right_pane)
        splitter.addWidget(right_pane)

        # Create stacked widget in right pane
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)
        self.tasks_view = QWidget() # blank container for tasks UI elements
        self.notes_view = QWidget() # blank container for notes UI elements

        # Create widgets for tasks and notes views
        self.create_tasks_view()  # Add UI elements for tasks
        self.create_notes_view()  # Add UI elements for notes

        # Add both views to stack, set task view as default
        self.stacked_widget.addWidget(self.tasks_view)
        self.stacked_widget.addWidget(self.notes_view)

        # can use setCurrentIndex, but this way initializes correct buttons for default view
        self.switch_to_tasks_view()

        # Set up QTimer for saving notes
        self.notes_save_timer = QTimer(self)
        self.notes_save_timer.timeout.connect(self.save_notes)
        self.notes_save_timer.start(30000)  # Every 30 seconds

        # Set the stretch factors for the panes
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        self.prev_day_button.clicked.connect(self.move_to_prev_day)
        self.next_day_button.clicked.connect(self.move_to_next_day)

    def move_to_prev_day(self):
        # Save user data
        self.save_notes()
    
        # Clear user data (python lists and widget data)
        self.up_next.clear()
        self.done_today.clear()
        self.up_next_list.clear()
        self.done_today_list.clear()
        self.notes_edit.setPlainText("")

        # Decrement display date
        self.display_date -= datetime.timedelta(days=1)

        # Update GUI
        self.update_displayed_date()

    def move_to_next_day(self):
        # Save user data
        self.save_notes()

        # Clear user data (python lists and widget data)
        self.up_next.clear()
        self.done_today.clear()
        self.up_next_list.clear()
        self.done_today_list.clear()
        self.notes_edit.setPlainText("")

        # Increment display date
        self.display_date += datetime.timedelta(days=1)

        # Update displayed date and load associated data
        self.update_displayed_date()

    def update_displayed_date(self):
        self.load_lists()
        self.load_notes()
        self.populate_list_widgets()

        days_difference = (self.display_date - self.current_date).days

        if days_difference == 0:
            # Today
            self.date_label.setText(self.current_date.strftime(f'Today: %A, %B %d, %Y'))
        elif days_difference == -1:
            # Yesterday
            self.date_label.setText(self.display_date.strftime(f'Yesterday: %A, %B %d, %Y'))
        elif days_difference == 1:
            # Tomorrow
            self.date_label.setText(self.display_date.strftime(f'Tomorrow: %A, %B %d, %Y'))
        elif days_difference >= 2 and days_difference < 7:
            # This week
            day_name = self.display_date.strftime('%A')
            self.date_label.setText(self.display_date.strftime(f'This %A, %B %d, %Y'))
        elif days_difference >= 7:
            # Next week
            self.date_label.setText(self.display_date.strftime(f'Next week: %A, %B %d, %Y'))
        elif days_difference >= -7 and days_difference < 0:
            # Last week
            self.date_label.setText(self.display_date.strftime(f'Last week: %A, %B %d, %Y'))
        else:
            # Default case
            self.date_label.setText(self.display_date.strftime('%A, %B %d, %Y'))

    # Textbox for your notes!
    def create_notes_view(self):
        self.notes_edit = QTextEdit()
        notes_layout = QVBoxLayout(self.notes_view)
        notes_layout.addWidget(self.notes_edit)

        # If notes exist for today, load them up!
        self.load_notes()

    def create_tasks_view(self):
        tasks_layout = QVBoxLayout(self.tasks_view)

        # Right pane: upcoming tasks
        up_next_label = QLabel("Upcoming tasks:")
        self.up_next_list = TaskList()

        # Right pane: add a task (input field and Add Task button)
        add_task_container = QWidget()
        add_task_layout = QHBoxLayout(add_task_container)

        self.new_task_input = QLineEdit()
        add_task_button = QPushButton("→")
        add_task_button.setStyleSheet("padding: 5px; border: 0;")

        add_task_layout.addWidget(self.new_task_input)
        add_task_layout.addWidget(add_task_button)

        # Enabled drag and drop
        self.up_next_list.setDragDropMode(QAbstractItemView.DragDrop) # can also use InternalMove
        self.up_next_list.setDefaultDropAction(Qt.MoveAction) # default is copy, makes a mess of duplicates
        self.up_next_list.setDropIndicatorShown(True)
        #########################################################

        # Right pane: completed tasks
        done_today_label = QLabel("Done so far today:")
        self.done_today_list = TaskList()

        # Right pane: add objects to layout
        tasks_layout.addWidget(up_next_label)
        tasks_layout.addWidget(self.up_next_list)
        tasks_layout.addWidget(add_task_container)
        tasks_layout.addWidget(done_today_label)
        tasks_layout.addWidget(self.done_today_list)

        # Apply the stylesheet to your list widgets
        self.up_next_list.setStyleSheet(list_widget_stylesheet)
        self.done_today_list.setStyleSheet(list_widget_stylesheet)

        # Drag and drop for Done Today
        self.done_today_list.setDragDropMode(QAbstractItemView.DragDrop)
        self.up_next_list.setDefaultDropAction(Qt.MoveAction) # default is copy, makes a mess of duplicates
        self.done_today_list.setDropIndicatorShown(True)

        # Right pane: connect button(s) to functions
        self.new_task_input.returnPressed.connect(self.add_task)
        add_task_button.clicked.connect(self.add_task)

        # Right pane: for up_next list items, register enterEvent (hover) and leaveEvent (stop hover)
        for task in self.up_next:
            item = QListWidgetItem(task)
            self.up_next_list.addItem(item)

            # Add hover background color change
            item.enterEvent = lambda event, item=item: self.hover_enter(item)
            item.leaveEvent = lambda event, item=item: self.hover_leave(item)

        # Right pane: for done_today list items, register enterEvent (hover) and leaveEvent (stop hover)
        for task in self.up_next:
            item = QListWidgetItem(task)
            self.up_next_list.addItem(item)
            item.enterEvent = lambda event, item=item: self.hover_enter(item)
            item.leaveEvent = lambda event, item=item: self.hover_leave(item)

        # Right pane: handle when list items in Up Next and Done Today are clicked
        self.up_next_list.itemClicked.connect(self.handle_up_next_item_click)
        self.done_today_list.itemClicked.connect(self.handle_done_today_item_click)

        # Connect custom signal from TaskList to save_lists method (save list order after drag and drop)
        self.done_today_list.task_dropped.connect(self.save_lists)
        self.up_next_list.task_dropped.connect(self.save_lists)

    def switch_to_tasks_view(self):
        self.stacked_widget.setCurrentIndex(0)
        self.tasks_view_button.hide()
        self.notes_view_button.show()

    def switch_to_notes_view(self):
        self.stacked_widget.setCurrentIndex(1)
        self.tasks_view_button.show()
        self.notes_view_button.hide()

    def save_notes(self):
        notes_content = self.notes_edit.toPlainText()
        with open("data/notes.json", "r+") as f:
            data = json.load(f)
            data[self.display_date.strftime('%Y-%m-%d')] = notes_content
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    # Even if you X out of the program without manually saving, and have recent changes
    # since the last 30-second interval auto-save, your notes will be saved!
    def save_notes_on_exit(self):
        notes_content = self.notes_edit.toPlainText()
        with open("data/notes.json", "r+") as f:
            data = json.load(f)
            data[self.display_date.strftime('%Y-%m-%d')] = notes_content
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    # Get the correct order of list items for saving
    def get_list_items(self, list_widget):
        items = []
        for index in range(list_widget.count()):
            items.append(list_widget.item(index).text())
        return items

    def hover_enter(self, item):
        item.setBackground(QColor(200, 200, 200))  # Change background color on hover

    def hover_leave(self, item):
        item.setBackground(QColor(255, 255, 255))  # Restore background color on hover exit

    def handle_up_next_item_click(self, item):
        menu = QMenu(self)
        mark_done_action = menu.addAction("Mark as Done")
        delete_action = menu.addAction("Delete")

        global_pos = self.up_next_list.mapToGlobal(self.up_next_list.pos())
        action = menu.exec(global_pos)

        if action == mark_done_action:
            self.mark_task_done(item)
        elif action == delete_action:
            self.remove_up_next_item(item)

    def mark_task_done(self, item):
        task = item.text()
        self.up_next_list.takeItem(self.up_next_list.row(item))
        self.up_next.remove(task)

        # must add to list widget FIRST as they're considered
        # the master copy of the list. adding to the Python list
        # will get overwritten in save_lists method
        self.done_today_list.addItem(task)
        self.save_lists()              # Update JSON file
        self.populate_list_widgets()   # Update list widgets

    def remove_up_next_item(self, item):
        task = item.text()

        self.up_next_list.takeItem(self.up_next_list.row(item))
        self.up_next.remove(task)
        self.save_lists()              # Update JSON file
        self.populate_list_widgets()   # Update list widgets

    def handle_done_today_item_click(self, item):
        menu = QMenu(self)

        edit_action = menu.addAction("Edit")
        remove_action = menu.addAction("Remove")

        global_pos = self.done_today_list.mapToGlobal(self.done_today_list.pos())
        action = menu.exec(global_pos)

        if action == edit_action:
            self.edit_done_today_item(item)
        elif action == remove_action:
            self.remove_done_today_item()

    def edit_done_today_item(self, item):
        index = self.done_today_list.row(item)  # Get the index of the clicked item
        new_text, ok = QInputDialog.getText(self, "Edit Task", "Edit task name:", QLineEdit.Normal, item.text())

        if ok and new_text:
            self.done_today[index] = new_text       # Update the list element's text
            self.save_lists()                       # Update JSON file
            self.populate_list_widgets()            # Reload the list widget

    def remove_done_today_item(self):
        # currentIndex() returns a QModelIndex (model item index), not an integer
        selection = self.done_today_list.currentIndex()
        row = selection.row()
        data = selection.data()

        # Delete from "Done Today" list widget (GUI)
        self.done_today_list.takeItem(row)

        # Delete from "Done Today" list (data)
        self.done_today.remove(data)

        # Update JSON file
        self.save_lists()
   
    def populate_list_widgets(self):
        self.up_next_list.clear()  # Clear the list widget before adding items
        for task in self.up_next:
            self.up_next_list.addItem(task)

        self.done_today_list.clear()  # Clear the list widget before adding items
        for task in sorted(self.done_today):
            self.done_today_list.addItem(task)

    def complete_task(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"Are you done with: {self.current_task}?")

        yes_button = msg_box.addButton("Done", QMessageBox.YesRole)
        more_time_button = msg_box.addButton("More Time", QMessageBox.ActionRole)
        skip_button = msg_box.addButton("Skip", QMessageBox.RejectRole)
        msg_box.exec()

        # Task complete
        if msg_box.clickedButton() == yes_button:
            global have_active_task

            self.current_task_label.setText(f"Current Task: ^_^") # Change in-progress task display
            self.up_next.remove(self.current_task)                # Remove task from Upcoming Tasks list
            self.done_today.append(self.current_task)             # Add task to Done Today list
            self.save_lists()                                     # Save updated lists to JSON file
            self.populate_list_widgets()                          # Update GUI task list Widgets

            have_active_task = False                              # Switch our busy flag to off
            self.stop_timer()                                     # Stop the QTimer and set self.timer_seconds to 0
            self.display_control_buttons()                        # Swap displayed buttons

        # Task not complete, need more time
        elif msg_box.clickedButton() == more_time_button:
            self.start_task_timer()                              # Start over w/15 mins on the clock

        # Task not complete, want to move on for now
        elif msg_box.clickedButton() == skip_button:
            have_active_task = False                              # Switch our busy flag to off
            self.stop_timer()                                     # Stop the QTimer and set self.timer_seconds to 0
            self.display_control_buttons()                        # Swap displayed buttons

    def display_control_buttons(self):
        global have_active_task

        # If user has an active task (or is on a timed break)
        if have_active_task:
            # Hide general menu buttons
            self.assign_task_button.hide()
            self.take_break_button.hide()

            # Show task control buttons
            self.complete_task_button.show()
            self.add_time_button.show()
            self.pause_timer_button.show()

        else:
            # Show general menu buttons
            self.assign_task_button.show()
            self.take_break_button.show()

            # Hide task control button
            self.complete_task_button.hide()
            self.add_time_button.hide()
            self.pause_timer_button.hide()

    # Left nav pane option: Get assigned a new task
    def assign_task(self):
        global have_active_task

        # Program will pick a task at random from your to-do list
        self.current_task = random.choice(self.up_next)

        # Instead of a pop-up, I want a wheel that spins or a lotto ball picker, etc.
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"Do you accept the task: {self.current_task}?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec()

        if result == QMessageBox.Yes:
            # Set global var to true
            have_active_task = True

            # Display assigned task
            self.current_task_label.setText(f"Current Task: {self.current_task}")

            # Display task control buttons, hide general menu buttons
            self.display_control_buttons()

            # Put 15mins on the block, start countdown
            self.start_task_timer()

    def flash_current_task_label(self):
        # Create and start the first animation thread
        thread1 = threading.Thread(target=self.animate_font_size_thread, args=(18, 24, 'black', 'green'))
        thread1.start()

        # Wait for the first animation to finish
        thread1.join()
        print(f'joined first thread, now shrinking text', flush=True)

        # Start the second animation
        thread2 = threading.Thread(target=self.animate_font_size_thread, args=(24, 18, 'green', 'black'))
        thread2.start()

    def animate_font_size_thread(self, start_size, end_size, start_color, end_color):
        size_range = abs(start_size - end_size)
        sleep_amt = 0.5
        self.font_size = start_size
        for x in range(size_range):
            if start_size > end_size:
                print(f"shrinking text from font size: {self.font_size} to {self.font_size - 1}", flush=True)
                self.font_size -= 1
                sleep_amt = max(sleep_amt - 0.11, 0.03)
            else:
                print(f"enlarging text from font size: {self.font_size} to {self.font_size + 1}", flush=True)
                self.font_size += 1
                sleep_amt = max(sleep_amt + 0.11, .9)
            self.current_task_label.setStyleSheet(f"color: {start_color}; font-size: {self.font_size}px;")
            time.sleep(sleep_amt)
        self.current_task_label.setStyleSheet(f"font-size: {end_size}px; color: {end_color};")

    def flash_timer_label(self):
        self.timer_label.setStyleSheet("color: green; background-color: #D4DFC7; font-size: 24px;")

        self.flash_timer_timer = QTimer(self)
        self.flash_timer_timer.timeout.connect(self.restore_timer_label)
        self.flash_timer_timer.start(500)  # Flash for 0.5 seconds

    def restore_timer_label(self):
        self.timer_label.setStyleSheet("color: black; background-color: #D4DFC7; font-size: 18px")  # Restore original font size
        self.flash_timer_timer.stop()

    def start_task_timer(self):
        global have_active_task
        
        have_active_task = True
        self.add_time()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every 1 second

    def update_timer(self):
        global timer_seconds

        if timer_seconds > 0:
            timer_seconds -= 1
            timer = datetime.timedelta(seconds=timer_seconds)
            self.timer_label.setText(f"{timer}")
        else:
            self.timer.stop()
            self.complete_task() # Ask user if they're done, need more time, etc.

    def take_break(self):
        global have_active_task
        have_active_task = True

        self.add_time()
        self.current_task_label.setText("Currently: taking a break")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every 1 second
        #times_up_alert()

    def add_time(self):
        global have_active_task
        global timer_seconds

        if have_active_task:
            # Start with empty hourglass
            self.hourglass.show_empty_hourglass()
            # Rotate hourglass
            self.hourglass.rotate_hourglass()

            # Add 15 minutes to the clock
            timer_seconds += 15 * 60
            self.timer_label.setText(f"{datetime.timedelta(seconds=timer_seconds)}")
            winsound.Beep(880, dur)

            # Show the updated time for 3 seconds before starting the countdown
            QTimer.singleShot(3000, self.update_timer)
            self.flash_timer_label()

            # Show hourglass as full again
            QTimer.singleShot(2000, self.hourglass.show_full_hourglass)
            # 1 second later, show running hourglass image
            QTimer.singleShot(2500, self.hourglass.show_running_hourglass)
            QTimer.singleShot(4000, self.hourglass.pulse_hourglass)

    def add_task(self):
        new_task = self.new_task_input.text()
        if new_task != '':
            self.up_next.append(new_task)
            self.up_next_list.addItem(new_task)
            self.new_task_input.clear()
            self.save_lists()
        else:
            print("Cannot add empty task", flush=True)

    def stop_timer(self):
        global timer_seconds

        self.timer.stop()
        timer_seconds = 0
        self.hourglass.show_empty_hourglass()

    def pause_timer(self):
        #self.timer.stop()
        pass

    # Save up_next and done_today listwidget tasks to their Python lists, and to a JSON file
    def save_lists(self):
        date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Return widget elements, because they get out of sync with Python lists after drag and drop
        up_next_items = self.get_list_items(self.up_next_list)
        done_today_items = self.get_list_items(self.done_today_list)

        # Clear Python lists
        self.up_next.clear()
        self.done_today.clear()

        # Update the Python lists
        self.up_next = up_next_items
        self.done_today = done_today_items

        # Update the JSON file
        with open("data/task_lists.json", "r+") as f:
            data = json.load(f)
            data[date] = {"up_next": up_next_items, "done_today": done_today_items}
            #data[date] = {date: {"up_next": up_next_items, "done_today": done_today_items}}
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    def load_notes(self):
        date = self.display_date.strftime('%Y-%m-%d')  # Use the display date
        try:
            with open("data/notes.json", "r") as f:
                data = json.load(f)
                if date in data:
                    # Load notes for the current day
                    todays_data = data[date]
                    self.notes_edit.setPlainText(todays_data)
        except FileNotFoundError:
            pass  # Handle if the notes.json file doesn't exist

    # Load up_next and done_today lists from the JSON file
    def load_lists(self):
        date = self.display_date.strftime('%Y-%m-%d')  # Use the display date
        try:
            with open("data/task_lists.json", "r") as f:
                data = json.load(f)
                if data.get(date):
                    # Load lists for the current day
                    todays_data = data[date]
                    self.up_next = todays_data.get("up_next", [])
                    self.done_today = todays_data.get("done_today", [])
                else:
                    # Look for the most recent existing date with data
                    existing_dates = sorted(data.keys())
                    existing_dates.reverse()  # To get the most recent date first

                    for day in existing_dates:
                        if day < date:
                            previous_day_data = data[day]
                            self.up_next = previous_day_data.get("up_next", [])
                            break

        except FileNotFoundError:
            pass

class Hourglass(QGraphicsView):
    def __init__(self):
        super().__init__()
        self._scale_factor = 1.0  # Initial scale factor
        self.setFixedSize(QSize(105, 141))  # Can adjust rect size here
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("border: 0; background-color: #D4DFC7;")

        # Create a QGraphicsScene
        scene = QGraphicsScene(self)
        self.setScene(scene)

        # Load the hourglass pixmaps
        self.hourglass_empty_pixmap = QPixmap("assets/hourglass_empty.png")
        self.hourglass_full_pixmap = QPixmap("assets/hourglass_full.png")
        self.hourglass_pixmap = QPixmap("assets/hourglass.png")

        # Create QGraphicsPixmapItems
        self.hourglass_empty_item = scene.addPixmap(self.hourglass_empty_pixmap)
        self.hourglass_full_item = scene.addPixmap(self.hourglass_full_pixmap)
        self.hourglass_item = scene.addPixmap(self.hourglass_pixmap)

        # Set default opacity
        self.hourglass_full_item.setOpacity(0)  # Start with full hourglass hidden
        self.hourglass_item.setOpacity(0)  # Start with running hourglass also hidden

        self._rotation = 0

    @Property(float)
    def rotation(self):
        return self._rotation

    @Property(float)
    def scale_factor(self):
        return self._scale_factor

    @rotation.setter
    def rotation(self, angle):
        self._rotation = angle
        transform = QTransform()
        transform.translate(self.hourglass_empty_item.pixmap().width() / 2, self.hourglass_empty_item.pixmap().height() / 2)
        transform.rotate(self._rotation)
        transform.translate(-self.hourglass_empty_item.pixmap().width() / 2, -self.hourglass_empty_item.pixmap().height() / 2)
        self.hourglass_empty_item.setTransform(transform)

    @scale_factor.setter
    def scale_factor(self, value):
        self._scale_factor = value
        self.hourglass_item.setScale(self._scale_factor)

    def rotate_hourglass(self):
        self.animation = QPropertyAnimation(self, b'rotation')
        self.animation.setDuration(2000)  # Duration in milliseconds (adjust as needed)
        self.animation.setStartValue(0)
        self.animation.setEndValue(180)
        self.animation.start()

    def show_full_hourglass(self):
        self.hourglass_empty_item.setOpacity(0)  # Hide the empty hourglass
        self.hourglass_full_item.setOpacity(1)   # Show the full hourglass
        self.hourglass_item.setOpacity(0)

    def show_running_hourglass(self):
        self.hourglass_empty_item.setOpacity(0)  # Hide the empty hourglass
        self.hourglass_full_item.setOpacity(0)   # hide the full hourglass
        self.hourglass_item.setOpacity(1)   # Show the running hourglass

    def show_empty_hourglass(self):
        self.hourglass_empty_item.setOpacity(1)  # show the empty hourglass
        self.hourglass_full_item.setOpacity(0)   # hide the full hourglass
        self.hourglass_item.setOpacity(0)

    def pulse_hourglass(self):
        pass
        #print(f'pulse', flush=True)
        # pulse_animation = QPropertyAnimation(self.hourglass_item, b'scale')
        # pulse_animation.setDuration(1000)  # Duration in milliseconds
        # pulse_animation.setKeyValueAt(0, 1)
        # pulse_animation.setKeyValueAt(0.5, 1.1)  # Scale up to 10% larger
        # pulse_animation.setKeyValueAt(1, 1)
        # pulse_animation.setLoopCount(1)
        # pulse_animation.start()

# Custom subclass to override default dropEvent method of QListWidget,
# to allow users to save their task list orders properly (to Python list and JSON save file)
# Also emits signal to call save_lists method in parent app
class TaskList(QListWidget):
    task_dropped = Signal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.task_dropped.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskApp()
    window.show()

    # global stylesheet for app
    padding_top = 2  # Adjust as needed
    padding_bottom = 2  # Adjust as needed
    app.setStyleSheet(f"* {{ padding-top: {padding_top}px; padding-bottom: {padding_bottom}px; }}")


    sys.exit(app.exec())