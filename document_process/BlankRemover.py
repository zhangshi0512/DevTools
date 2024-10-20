def remove_blank_lines(file_path):
    # Open the file with UTF-8 encoding
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Remove consecutive blank lines
    with open(file_path, 'w', encoding='utf-8') as file:
        # Write only lines that are not empty or are the first of multiple empty lines
        previous_line = None
        for line in lines:
            if line.strip() != '' or (previous_line and previous_line.strip() != ''):
                file.write(line)
            previous_line = line


# Replace 'yourfile.txt' with the path to your actual file
remove_blank_lines(
    'C:\\Users\\Username\\...\\sample.txt')
