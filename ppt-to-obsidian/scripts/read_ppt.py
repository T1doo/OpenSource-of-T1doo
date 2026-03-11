"""
PPT Content & Image Extractor for Obsidian Notes

Reads a PowerPoint file (.ppt/.pptx) via COM automation, extracts all text content
and embedded images, and outputs a structured text file with slide boundaries.

Requirements:
  - Windows with Microsoft PowerPoint installed
  - Python 3 with comtypes (pip install comtypes)

Usage:
  python read_ppt.py <ppt_path> <output_path> <image_dir> <note_name> [--offset N]

Arguments:
  ppt_path    - Path to the .ppt or .pptx file
  output_path - Path for the output text file (temporary, will be cleaned up)
  image_dir   - Directory to save extracted images (typically Pictures/ next to the note)
  note_name   - Note filename without extension, used for image naming
                e.g., "第1讲 2026.3.6" produces "image from 第1讲 2026.3.6.png"

Options:
  --offset N  - Start image numbering from N (default: 0).
                Use this when extracting multiple PPTs for the same note
                to avoid filename collisions. Set N to the total number of
                images already extracted by previous PPTs.
"""

import comtypes.client
import sys
import os
import json


def read_ppt(ppt_path, output_path, image_dir, note_name, image_offset=0):
    # Ensure paths are absolute (COM requires absolute paths)
    ppt_path = os.path.abspath(ppt_path)
    output_path = os.path.abspath(output_path)
    image_dir = os.path.abspath(image_dir)

    # Initialize PowerPoint COM object
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    powerpoint.Visible = 1

    try:
        presentation = powerpoint.Presentations.Open(ppt_path, WithWindow=False)
    except Exception as e:
        powerpoint.Quit()
        print(f"Error opening {ppt_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Create image output directory
    os.makedirs(image_dir, exist_ok=True)

    slides_content = []
    image_count = 0
    total_slides = presentation.Slides.Count

    print(f"Processing {total_slides} slides from: {os.path.basename(ppt_path)}")
    if image_offset > 0:
        print(f"Image numbering offset: {image_offset}")

    for i, slide in enumerate(presentation.Slides, 1):
        slide_text = f"\n{'=' * 60}\nSlide {i}/{total_slides}\n{'=' * 60}\n"

        for shape in slide.Shapes:
            # Extract text content
            if shape.HasTextFrame:
                try:
                    if shape.TextFrame.HasText:
                        text = shape.TextFrame.TextRange.Text.strip()
                        if text:
                            slide_text += f"\n{text}\n"
                except Exception:
                    pass  # Some shapes may error on text access

            # Extract images (Type 13 = msoPicture / msoLinkedPicture)
            if shape.Type == 13:
                idx = image_count + image_offset
                if idx == 0:
                    img_name = f"image from {note_name}.png"
                else:
                    img_name = f"image from {note_name}-{idx}.png"
                image_count += 1

                img_path = os.path.join(image_dir, img_name)
                try:
                    shape.Export(img_path, 2)  # 2 = PNG format
                    slide_text += f"\n[IMAGE: {img_name}]\n"
                    print(f"  Exported image: {img_name}")
                except Exception as e:
                    print(f"  Warning: Failed to export image on slide {i}: {e}",
                          file=sys.stderr)

        slides_content.append(slide_text)

    presentation.Close()
    powerpoint.Quit()

    # Write extracted content to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(slides_content))

    # Print summary as JSON on the last line for easy parsing by the caller
    summary = {"slides": total_slides, "images": image_count,
               "next_offset": image_offset + image_count}
    print(f"\nDone! Extracted {total_slides} slides, {image_count} images.")
    print(f"Content saved to: {output_path}")
    if image_count > 0:
        print(f"Images saved to: {image_dir}")
    print(f"SUMMARY:{json.dumps(summary)}")


def parse_args(argv):
    """Parse positional args and --offset option."""
    positional = []
    offset = 0
    i = 0
    while i < len(argv):
        if argv[i] == "--offset" and i + 1 < len(argv):
            offset = int(argv[i + 1])
            i += 2
        else:
            positional.append(argv[i])
            i += 1
    return positional, offset


if __name__ == "__main__":
    positional, offset = parse_args(sys.argv[1:])

    if len(positional) < 4:
        print("Usage: python read_ppt.py <ppt_path> <output_path> <image_dir> <note_name> [--offset N]")
        print()
        print("Arguments:")
        print("  ppt_path    - Path to the .ppt or .pptx file")
        print("  output_path - Path for the output text file")
        print("  image_dir   - Directory to save extracted images")
        print("  note_name   - Note filename without extension (for image naming)")
        print()
        print("Options:")
        print("  --offset N  - Start image numbering from N (default: 0)")
        print("                Use when extracting multiple PPTs for one note")
        sys.exit(1)

    read_ppt(positional[0], positional[1], positional[2], positional[3], offset)
