from django.dispatch import Signal


program_begin = Signal(providing_args=['program'])
program_start = Signal(providing_args=['program'])
program_end = Signal(providing_args=['program', 'result'])
update_progress = Signal(providing_args=['program', 'progress'])
