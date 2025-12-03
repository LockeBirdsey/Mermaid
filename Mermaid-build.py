import sublime
import sublime_plugin
import os
import sys
import subprocess
import time

class MermaidBuildCommand(sublime_plugin.WindowCommand):
  """Build command for Mermaid"""

  valid_output_types = ['md', 'svg', 'png', 'pdf']

  def init_panel(self):
    """Initialize the output panel."""
    if not hasattr(self, 'output_view'):
        self.output_view = self.window.create_output_panel("mermaid")

  def puts(self, message):
    """Output to panel."""
    message = message + '\n'
    self.output_view.run_command('append', {'characters': message, 'force': True, 'scroll_to_end': True})

  def run(self):
    """Run the build and convert the Mermaid diagram."""
    view = self.window.active_view()
    if not view:
        return
    start_time = time.time()

    self.init_panel()
    settings = sublime.load_settings('mermaid.sublime-settings')

    # TODO how to get this to work and utilise quiet flag
    # show_panel_on_build = settings.get("show_panel_on_build", True)
    # if show_panel_on_build:
    #     self.window.run_command("show_panel", {"panel": "output.mermaid"})

    build_settings = settings.get('build')
    # remove unused settings
    pruned_build_settings = {k: v for k, v in build_settings.items() if v}
    # set input file
    pruned_build_settings["input"] = view.file_name()
    # make output
    output = os.path.splitext(view.file_name())
    outputFile = output[0]
    print(pruned_build_settings)
    if "outputFormat" not in pruned_build_settings:
      outputFormat = "svg"
    else:
      outputFormat = pruned_build_settings["outputFormat"]
    
    outputFile = outputFile + '.' + outputFormat
    pruned_build_settings["output"] = outputFile

    # handle the weird singleton flag
    pdfFit = None
    pdfFit = pruned_build_settings.pop("pdfFit")

    # joined flags
    flags = [['--'+k, str(v)] for k, v in pruned_build_settings.items()]
    print(flags)

    flattened_flags = ["mmdc"] + [x for i in flags for x in i]
    if outputFormat.lower() == 'pdf' and pdfFit:
      flattened_flags += ["--pdfFit"]

    print("running mmdc with flags: " + str(flattened_flags))
    # run mmdc
    # TODO handle Windows
    p = subprocess.Popen(flattened_flags, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # stream stdout and stderr
    handle_popen(p)

    print("mmdc has finished generating. Rendered Mermaid is at "+outputFile)

    will_open = settings.get('open_in_default_app_after_build', False)
    if will_open:
      if sys.platform == 'darwin':
          opener = "open"
      elif sys.platform == 'linux':
          opener += "xdg-open"
      elif sys.platform == 'win32':
          opener = "Invoke-Item"
      # debug
      print("opening in "+str([opener, outputFile]))
      p = subprocess.Popen([opener, outputFile])
      handle_popen(p)

  def handle_popen(handler):
    while True:
      output = handler.stdout.readline()
      if not output:
        err = handler.stderr.readline()
        if not err:
          break
        else:
          print(err.rstrip(), flush=True)
      else:
        print(output.rstrip(), flush=True)

