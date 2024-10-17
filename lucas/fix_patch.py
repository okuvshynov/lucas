import re
import sys

# while at least sonnet 3.5 is pretty good, it makes mistakes
# when counting lines in a hunk. Let's manually fix it. Let's assume
# starting lines and +/- sizes are correct, but size might be off
def fix_patch(patch_content):
    # Regular expression to match hunk headers
    hunk_header_pattern = re.compile(r'@@ -(\d+),\d+ \+(\d+),\d+ @@(.*)')
    
    # Split the patch into lines
    lines = patch_content.split('\n')
    
    fixed_lines = []

    # this is index in 'diff' file
    current_hunk_start = 0

    # and this is index in 'original' file
    current_hunk_line = 0
    current_hunk_size = 0
    new_hunk_size = 0
    rest_of_header = ''

    # first line is never start of a hunk
    for i, line in enumerate(lines):
        if line.startswith('@@'):
            # If we're processing a new hunk, fix the previous one (if any)
            if current_hunk_start > 0:
                fixed_header = f'@@ -{current_hunk_line},{current_hunk_size} +{new_hunk_start},{new_hunk_size} @@{rest_of_header}'
                fixed_lines[current_hunk_start] = fixed_header

            # Reset counters for the new hunk
            match = hunk_header_pattern.match(line)
            if match:
                current_hunk_start = i
                current_hunk_line = match.group(1)
                new_hunk_start = match.group(2)
                current_hunk_size = 0
                new_hunk_size = 0
                rest_of_header = match.group(3)
            
        elif line.startswith('-'):
            current_hunk_size += 1
        elif line.startswith('+'):
            new_hunk_size += 1
        elif line.startswith(' '):
            current_hunk_size += 1
            new_hunk_size += 1
        
        fixed_lines.append(line)

    # Fix the last hunk
    if current_hunk_start > 0:
        fixed_header = f'@@ -{current_hunk_line},{current_hunk_size} +{new_hunk_start},{new_hunk_size} @@{rest_of_header}'
        fixed_lines[current_hunk_start] = fixed_header

    return '\n'.join(fixed_lines)


def main():
    with open(sys.argv[1], 'r') as f:
        print(fix_patch(f.read()))

if __name__ == '__main__':
    main()
