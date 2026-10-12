from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import anvil.users


class Main(MainTemplate):
    """Secure Student Registration System.
    All components are created in code, so you only need to create ONE empty
    form named Main (Blank Panel) and paste this file over its code."""

    def __init__(self, **properties):
        self.init_components(**properties)
        self.role = None
        self.records_loaded = False
        self.build_ui()
        self.show_logged_out("Please log in to continue.")
        self.add_event_handler("show", self.form_show)

    # ------------------------------------------------------------------
    # UI construction (component names follow the activity's Task 2 table)
    # ------------------------------------------------------------------
    def build_ui(self):
        self.title_label = Label(text="Secure Student Registration System",
                                 bold=True, font_size=22)
        self.user_label = Label(text="Not logged in", italic=True)
        self.status_label = Label(text="", bold=True, foreground="#1a5fb4")
        self.login_button = Button(text="Log In", icon="fa:sign-in",
                                   role="primary-color")
        self.logout_button = Button(text="Log Out", icon="fa:sign-out",
                                    role="secondary-color")
        for c in (self.title_label, self.user_label, self.status_label,
                  self.login_button, self.logout_button):
            self.add_component(c)

        self.app_panel = ColumnPanel()
        self.add_component(self.app_panel)

        p = self.app_panel
        p.add_component(Label(text="Register a Student", bold=True, font_size=18))

        self.student_id_box = TextBox(placeholder="Student ID, e.g. 2024-0001")
        self.name_box = TextBox(placeholder="Full name")
        self.course_dropdown = DropDown(items=["BSIT", "BSCS", "BSIS"],
                                        include_placeholder=True,
                                        placeholder="Select course")
        self.year_dropdown = DropDown(items=[1, 2, 3, 4],
                                      include_placeholder=True,
                                      placeholder="Select year level")
        self.register_button = Button(text="Register Student", icon="fa:user-plus",
                                      role="primary-color")
        for c in (self.student_id_box, self.name_box, self.course_dropdown,
                  self.year_dropdown, self.register_button):
            p.add_component(c)

        p.add_component(Label(text="Registrations", bold=True, font_size=18))
        self.view_button = Button(text="View Records", icon="fa:list",
                                  role="secondary-color")
        p.add_component(self.view_button)

        self.records_area = DataGrid(
            columns=[
                {"id": "c_id", "title": "Student ID", "data_key": "student_id"},
                {"id": "c_name", "title": "Name", "data_key": "name"},
                {"id": "c_course", "title": "Course", "data_key": "course"},
                {"id": "c_year", "title": "Year Level", "data_key": "year_level"},
            ],
            rows_per_page=10, show_page_controls=True, auto_header=True)
        p.add_component(self.records_area)

        p.add_component(Label(text="Delete a Registration (Admin only)",
                              bold=True, font_size=18))
        self.delete_id_box = TextBox(placeholder="Student ID to delete")
        self.delete_button = Button(text="Delete Registration", icon="fa:trash",
                                    role="secondary-color")
        p.add_component(self.delete_id_box)
        p.add_component(self.delete_button)

        self.login_button.set_event_handler("click", self.login_button_click)
        self.logout_button.set_event_handler("click", self.logout_button_click)
        self.register_button.set_event_handler("click", self.register_button_click)
        self.view_button.set_event_handler("click", self.view_button_click)
        self.delete_button.set_event_handler("click", self.delete_button_click)

    # ------------------------------------------------------------------
    # Login / logout
    # ------------------------------------------------------------------
    def form_show(self, **event_args):
        if anvil.users.get_user() is None:
            self.do_login()
        else:
            self.show_logged_in()

    def login_button_click(self, **event_args):
        self.do_login()

    def do_login(self):
        try:
            user = anvil.users.login_with_form(allow_cancel=True)
            if user is None:
                self.show_logged_out("Login is required to use this application.")
            else:
                self.show_logged_in()
        except Exception as e:
            self.show_logged_out(str(e))

    def show_logged_in(self):
        try:
            anvil.server.call("ensure_default_role")
            self.role = anvil.server.call("get_my_role")
            user = anvil.users.get_user()
            self.user_label.text = "Logged in as {} ({})".format(
                user["email"], self.role)
        except Exception:
            self.user_label.text = "Logged in"
        self.app_panel.visible = True
        self.login_button.visible = False
        self.logout_button.visible = True
        self.status_label.text = "Welcome! You may register students and view records."

    def show_logged_out(self, message):
        self.role = None
        self.records_loaded = False
        self.clear_records()
        self.app_panel.visible = False
        self.login_button.visible = True
        self.logout_button.visible = False
        self.user_label.text = "Not logged in"
        self.status_label.text = message

    def logout_button_click(self, **event_args):
        anvil.users.logout()
        self.student_id_box.text = ""
        self.name_box.text = ""
        self.delete_id_box.text = ""
        self.course_dropdown.selected_value = None
        self.year_dropdown.selected_value = None
        self.show_logged_out("You have been logged out. Please log in to continue.")

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------
    def register_button_click(self, **event_args):
        try:
            result = anvil.server.call(
                "register_student",
                self.student_id_box.text,
                self.name_box.text,
                self.course_dropdown.selected_value,
                self.year_dropdown.selected_value
            )
            self.status_label.text = result
            self.student_id_box.text = ""
            self.name_box.text = ""
            self.course_dropdown.selected_value = None
            self.year_dropdown.selected_value = None
            if self.records_loaded:
                self.load_records(show_message=False)
        except Exception as e:
            self.status_label.text = str(e)

    # ------------------------------------------------------------------
    # View
    # ------------------------------------------------------------------
    def clear_records(self):
        for row in list(self.records_area.get_components()):
            row.remove_from_parent()

    def view_button_click(self, **event_args):
        self.load_records(show_message=True)

    def load_records(self, show_message=True):
        try:
            user = anvil.users.get_user()
            if user is None:
                self.status_label.text = "Please log in first."
                return

            # Display choice only. The SERVER enforces who may see what.
            role = anvil.server.call("get_my_role")
            if role == "Admin":
                records = anvil.server.call("get_all_registrations")
            else:
                records = anvil.server.call("get_my_registrations")

            self.clear_records()
            for rec in records:
                row = DataRowPanel()
                row.add_component(Label(text=rec["student_id"]), column="c_id")
                row.add_component(Label(text=rec["name"]), column="c_name")
                row.add_component(Label(text=rec["course"]), column="c_course")
                row.add_component(Label(text=str(rec["year_level"])), column="c_year")
                self.records_area.add_component(row)

            self.records_loaded = True
            if show_message:
                self.status_label.text = "Loaded {} registration(s).".format(len(records))
        except Exception as e:
            self.status_label.text = str(e)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def delete_button_click(self, **event_args):
        try:
            result = anvil.server.call("delete_registration", self.delete_id_box.text)
            self.status_label.text = result
            self.delete_id_box.text = ""
            if self.records_loaded:
                self.load_records(show_message=False)
        except Exception as e:
            self.status_label.text = str(e)
