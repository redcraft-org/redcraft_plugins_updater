import re

# Filters containing backslash escapes or groups are treated as regular
# expressions (like the sodium or lithium filters), everything else is a
# plain glob where only "*" is a wildcard
regex_filter_markers = re.compile(r"[\\()]")


def compile_file_filter(file_filter):
    if regex_filter_markers.search(file_filter):
        # Historical behavior for regex filters, "*" still acts as a ".+" wildcard
        pattern = file_filter.replace("*", ".+")
    else:
        # Escape everything else so characters like "." and "+" match literally
        pattern = ".+".join(re.escape(part) for part in file_filter.split("*"))

    # Anchor the pattern so filters match the whole file name
    return re.compile(r"\A{}\Z".format(pattern))
