import os
import glob
import argparse

def concatenate_py_files(directory, output_file, exclude_file='_export.py'):
    # Get all .py files in the specified directory
    py_files = glob.glob(os.path.join(directory, '*.py'))
    
    # Open the output file in write mode
    with open(output_file, 'w') as outfile:
        # Iterate through each .py file
        for py_file in py_files:
            # Skip the excluded file
            if os.path.basename(py_file) == exclude_file:
                continue
            
            # Write the file name as a comment
            outfile.write(f"# CONCATENATED FILE - {os.path.basename(py_file)}\n")
            
            # Open and read the contents of the .py file
            with open(py_file, 'r') as infile:
                outfile.write(infile.read())
            
            # Add a newline for separation
            outfile.write('\n\n')

    print(f"Concatenated Python files into {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concatenate Python files in a directory.")
    parser.add_argument("-d", "--directory", default=".", help="Directory to search for .py files (default: current directory)")
    parser.add_argument("-o", "--output", default="concatenated_python_files.py", help="Output file name (default: concatenated_python_files.py)")
    parser.add_argument("-e", "--exclude", default="_export.py", help="File to exclude (default: _export.py)")
    
    args = parser.parse_args()
    
    concatenate_py_files(args.directory, args.output, args.exclude)