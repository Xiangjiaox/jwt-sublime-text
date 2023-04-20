import base64
import json
import sublime
import sublime_plugin

SETTINGS_FILE = 'JWTDecode.sublime-settings'

class JwtCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        if text:
            try:
                decoded_jwt = decode_jwt(text)
                new_file = self.view.window().new_file()
                new_file.run_command('append', {"characters": decoded_jwt})
                new_file.assign_syntax(sublime.find_syntax_by_name("JSON")[0])
                post_processing(new_file)
            except (UnicodeDecodeError, base64.binascii.Error):
                sublime.error_message("Invalid JWT")
            return

        for selected_text in self.view.sel():
            lines = self.view.split_by_newlines(selected_text)
            errors = []
            any_success = False

            for selected_line in reversed(lines):
                if selected_line.empty():
                    continue

                words = [txt.strip() for txt in self.view.substr(selected_line).split()]
                try:
                    self.view.replace(edit, selected_line, " ".join([decode_jwt(encoded) for encoded in words]))
                    any_success = True
                except (UnicodeDecodeError, base64.binascii.Error):
                    errors.append(self.view.rowcol(selected_line.a)[0] + 1)
                    continue
            if errors:
                sublime.error_message("Invalid JWT(s) on line(s): {}".format(errors))
            if any_success:
                self.view.assign_syntax(sublime.find_syntax_by_name("JSON")[0])
                post_processing(self.view)

    def input(self, args):
        return EncodedInputHandler()


class EncodedInputHandler(sublime_plugin.TextInputHandler):
    def name(self):
        return "text"

    def placeholder(self):
        return "Encoded JWT"


def decode_jwt(encoded_token):
    components = [part for part in encoded_token.rsplit(".", 2) if part]

    dict = {"header": sublime.decode_value(base64_url_decode(components.pop(0)))}

    if components:
        dict["payload"] = sublime.decode_value(base64_url_decode(components.pop(0)))
    if components:
        dict["signature"] = components.pop(0)

    return json.dumps(dict)

def base64_url_decode(encoded_string):
    return base64.urlsafe_b64decode(encoded_string + '=' * (4 - len(encoded_string) % 4)).decode("UTF-8")

def post_processing(view):
    if sublime.load_settings(SETTINGS_FILE).get("format_on_decode"):
        format_output(view)

def format_output(view):
    formatter_command = get_json_formatter_command()
    if formatter_command is not None:
        view.run_command(formatter_command)

def get_json_formatter_command():
    formatter = 'Pretty JSON'
    installed_packages = sublime.load_settings('Package Control.sublime-settings').get('installed_packages', [])
    ignored_packages = sublime.load_settings('Preferences.sublime-settings').get('ignored_packages', [])

    if formatter not in installed_packages:
        sublime.status_message('Unable to format decoded output: package "Pretty JSON" is not installed')
        return None

    if formatter in ignored_packages:
        sublime.status_message('Unable to format decoded output: package "Pretty JSON" is installed, but in your "ignored_packages"')
        return None
    
    return "pretty_json"
