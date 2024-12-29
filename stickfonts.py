import tkinter as tk
from tkinter import filedialog
from fontTools.ttLib import TTFont
import svgwrite
import os

# Global variables for document settings
DOC_SIZE = (595, 842)  # Default A4 portrait size in pixels (72 DPI)
TOP_BORDER = 20
BOTTOM_BORDER = 20
LEFT_BORDER = 20
RIGHT_BORDER = 20
TEXT_SIZE = 12  # Default text size in points
FONT_NAME = "1CamBam_Stick_1"  # Default font name
FONT_FOLDER = "StickFonts"  # Folder containing TTF fonts

PAPER_SIZES = {
    "A4 Portrait": (595.3 * 1.333, 841.9 * 1.333),
    "A4 Landscape": (841.9 * 1.333, 595.3 * 1.333),
    "A5 Portrait": (420.9 * 1.333, 595.3 * 1.333),
    "A5 Landscape": (595.3 * 1.333, 420.9 * 1.333),
    "A6 Portrait": (297.6 * 1.333, 420.9 * 1.333),
    "A6 Landscape": (420.9 * 1.333, 297.6 * 1.333),
    "100x150 Portrait": (283.5 * 1.333, 425.2 * 1.333),
    "100x150 Landscape": (425.2 * 1.333, 283.5 * 1.333),
    "A1 Portrait": (1684.2 * 1.333, 2384.3 * 1.333),
    "A1 Landscape": (2384.3 * 1.333, 1684.2 * 1.333),
    "A2 Portrait": (1190.6 * 1.333, 1684.2 * 1.333),
    "A2 Landscape": (1684.2 * 1.333, 1190.6 * 1.333),
    "A3 Portrait": (841.9 * 1.333, 1190.6 * 1.333),
    "A3 Landscape": (1190.6 * 1.333, 841.9 * 1.333),
}

TEXT_SIZES = [10, 12, 24, 36, 48, 72, 96]  # Available text sizes

# Get all fonts from the StickFonts folder
FONT_NAMES = [f.split(".")[0] for f in os.listdir(FONT_FOLDER) if f.endswith(".ttf")]


def set_doc_size(event):
    """Update DOC_SIZE based on selected paper size and orientation."""
    global DOC_SIZE
    selected_size = paper_size_var.get()
    DOC_SIZE = PAPER_SIZES[selected_size]
    status_label.config(text=f"Selected paper size: {selected_size} ({DOC_SIZE[0]} x {DOC_SIZE[1]})")


def set_text_size(event):
    """Update global text size."""
    global TEXT_SIZE
    TEXT_SIZE = int(text_size_var.get())
    status_label.config(text=f"Text size set to: {TEXT_SIZE}")


def set_font_name(event):
    """Update global font name."""
    global FONT_NAME
    FONT_NAME = font_name_var.get()
    status_label.config(text=f"Font set to: {FONT_NAME}")


def convert_text_to_svg(text, font_path, output_file, font_size, position, letter_spacing, line_spacing):
    """Convert text to single-stroke paths and save to SVG, ensuring no word splits on wrapping."""
    try:
        font = TTFont(font_path)
        glyf_table = font["glyf"]
        cmap = font.getBestCmap()
        dwg = svgwrite.Drawing(output_file, profile="tiny", size=DOC_SIZE)
        x, y = position
        scale = font_size / font["head"].unitsPerEm  # type: ignore

        # Calculate maximum width for wrapping
        max_width = DOC_SIZE[0] - LEFT_BORDER - RIGHT_BORDER
        default_space_width = font_size / 2  # Fallback space width

        paragraphs = text.split("\n")  # Split text into paragraphs
        for paragraph in paragraphs:
            words = paragraph.split()  # Split the paragraph into words

            for word in words:
                word_width = 0
                for char in word:
                    glyph_name = cmap.get(ord(char))
                    if glyph_name:
                        glyph = glyf_table[glyph_name]  # type: ignore
                        char_width = glyph.advanceWidth * scale if hasattr(glyph, "advanceWidth") else (glyph.xMax - glyph.xMin) * scale
                        word_width += char_width + letter_spacing
                word_width -= letter_spacing  # Remove the trailing letter spacing for the word

                # Check if the word fits on the current line
                if x + word_width > max_width:
                    # Move to the next line
                    x = LEFT_BORDER
                    y += font_size * line_spacing

                # Render the word
                for char in word:
                    if char == " ":  # Spaces handled below; skip here
                        continue

                    glyph_name = cmap.get(ord(char))
                    if not glyph_name:
                        continue
                    glyph = glyf_table[glyph_name]  # type: ignore
                    if glyph.isComposite():
                        print(f"Composite glyphs not supported: {char}")
                        continue
                    if glyph.numberOfContours > 0:
                        coordinates = glyph.coordinates
                        contours = glyph.endPtsOfContours

                        start = 0
                        for end in contours:
                            path_data = [f"M {x + coordinates[start][0] * scale} {y - coordinates[start][1] * scale}"]
                            for i in range(start + 1, end + 1):
                                path_data.append(f"L {x + coordinates[i][0] * scale} {y - coordinates[i][1] * scale}")
                            path_data.append("Z")
                            dwg.add(dwg.path(" ".join(path_data), fill="none", stroke="black"))
                            start = end + 1

                    # Advance x position for the next character
                    if hasattr(glyph, "advanceWidth"):
                        x += glyph.advanceWidth * scale + letter_spacing
                    else:
                        x += (glyph.xMax - glyph.xMin) * scale + letter_spacing

                # Add a space after the word
                x += default_space_width
                if x > max_width:  # Avoid leftover trailing spaces exceeding max width
                    x = LEFT_BORDER
                    y += font_size * line_spacing

            # After finishing a paragraph, move to the next line with additional spacing
            x = LEFT_BORDER
            y += font_size * line_spacing * 2  # Double line spacing between paragraphs

        dwg.save()
        return True
    except Exception as e:
        print(f"Error generating SVG: {e}")
        return False


def generate_svg():
    global TOP_BORDER, BOTTOM_BORDER, LEFT_BORDER, RIGHT_BORDER
    try:
        # Update borders from user input
        TOP_BORDER = float(top_border_entry.get())
        BOTTOM_BORDER = float(bottom_border_entry.get())
        LEFT_BORDER = float(left_border_entry.get())
        RIGHT_BORDER = float(right_border_entry.get())

        # Fetch the text input
        text = text_box.get("1.0", tk.END).strip()
        if not text:
            status_label.config(text="Please enter some text.")
            return

        # Fetch the file path for saving the SVG
        filepath = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        if not filepath:
            status_label.config(text="Save operation canceled.")
            return

        # Fetch font and spacing values
        font_path = os.path.join(FONT_FOLDER, f"{FONT_NAME}.ttf")
        letter_spacing = float(letter_spacing_entry.get())
        line_spacing = float(line_spacing_entry.get())

        # Generate the SVG
        success = convert_text_to_svg(
            text, font_path, filepath, TEXT_SIZE, (LEFT_BORDER, TOP_BORDER), letter_spacing, line_spacing
        )
        if success:
            status_label.config(text=f"SVG saved successfully: {filepath}")
        else:
            status_label.config(text="Error generating SVG.")
    except ValueError:
        status_label.config(text="Please enter valid numeric values for borders, letter spacing, and line spacing.")
    except Exception as e:
        status_label.config(text=f"An unexpected error occurred: {e}")


# GUI setup
root = tk.Tk()
root.title("StickFont Text to SVG")

# Text Box
text_label = tk.Label(root, text="Enter text:")
text_label.pack(pady=5)
text_box = tk.Text(root, width=60, height=10)
text_box.pack(pady=5)

# Paper size selection
paper_size_label = tk.Label(root, text="Select paper size:")
paper_size_label.pack(pady=5)
paper_size_var = tk.StringVar(root)
paper_size_var.set("A4 Portrait")
paper_size_menu = tk.OptionMenu(root, paper_size_var, *PAPER_SIZES.keys(), command=set_doc_size)
paper_size_menu.pack(pady=5)

# Text size selection
text_size_label = tk.Label(root, text="Select text size:")
text_size_label.pack(pady=5)
text_size_var = tk.StringVar(root)
text_size_var.set(TEXT_SIZE) # type: ignore
text_size_menu = tk.OptionMenu(root, text_size_var, *TEXT_SIZES, command=set_text_size) # type: ignore
text_size_menu.pack(pady=5)

# Font selection
font_name_label = tk.Label(root, text="Select font:")
font_name_label.pack(pady=5)
font_name_var = tk.StringVar(root)
font_name_var.set(FONT_NAME)
font_name_menu = tk.OptionMenu(root, font_name_var, *FONT_NAMES, command=set_font_name)
font_name_menu.pack(pady=5)

# Letter spacing
letter_spacing_label = tk.Label(root, text="Letter spacing:")
letter_spacing_label.pack(pady=5)
letter_spacing_entry = tk.Entry(root, width=10)
letter_spacing_entry.insert(0, "2")  # Default value
letter_spacing_entry.pack(pady=5)

# Line spacing
line_spacing_label = tk.Label(root, text="Line spacing:")
line_spacing_label.pack(pady=5)
line_spacing_entry = tk.Entry(root, width=10)
line_spacing_entry.insert(0, "1.2")  # Default value
line_spacing_entry.pack(pady=5)

# Border settings
border_label = tk.Label(root, text="Set border sizes:")
border_label.pack(pady=5)
top_border_entry = tk.Entry(root, width=10)
top_border_entry.insert(0, TOP_BORDER)
top_border_entry.pack(pady=2)
bottom_border_entry = tk.Entry(root, width=10)
bottom_border_entry.insert(0, BOTTOM_BORDER)
bottom_border_entry.pack(pady=2)
left_border_entry = tk.Entry(root, width=10)
left_border_entry.insert(0, LEFT_BORDER)
left_border_entry.pack(pady=2)
right_border_entry = tk.Entry(root, width=10)
right_border_entry.insert(0, RIGHT_BORDER)
right_border_entry.pack(pady=2)

# Generate button
generate_button = tk.Button(root, text="Generate SVG", command=generate_svg)
generate_button.pack(pady=10)

# Status label
status_label = tk.Label(root, text="", fg="blue")
status_label.pack(pady=5)

# Start the GUI event loop
root.mainloop()
