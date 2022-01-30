import base64
import json
import sublime
import sublime_plugin


class JwtCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        if text:
            try:
                decoded_jwt = decode_jwt(text)
                new_file = self.view.window().new_file()
                new_file.run_command('append', {"characters": decoded_jwt})
                new_file.assign_syntax(sublime.find_syntax_by_name("JSON")[0])
            except (UnicodeDecodeError, base64.binascii.Error):
                sublime.error_message("Invalid JWT")

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