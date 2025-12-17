import cv2
import numpy as np
import os
from datetime import datetime
from PIL import Image
import svgwrite
from pathlib import Path


def create_output_folder():
    """Create a unique timestamped folder for output"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f"static/processed_frames_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(f"{output_folder}/images", exist_ok=True)
    os.makedirs(f"{output_folder}/vectors", exist_ok=True)
    return output_folder


def extract_frames(video_path, output_folder, fps=1):
    """Extract frames from video at specified fps (1 frame per second by default)"""
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps)
    
    frame_count = 0
    saved_count = 0
    frames_paths = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            frame_path = f"{output_folder}/images/frame_{saved_count:04d}.png"
            cv2.imwrite(frame_path, frame)
            frames_paths.append(frame_path)
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    print(f"Extracted {saved_count} frames from video")
    return frames_paths


def convert_to_line_drawing(image_path):
    """Convert image to black and white line drawing"""
    # Read image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detect edges using Canny edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Invert so lines are black on white background
    inverted = cv2.bitwise_not(edges)
    
    return inverted, edges


def edges_to_svg(edges, svg_path, width, height):
    """Convert edge image to SVG vector format"""
    # Create SVG drawing
    dwg = svgwrite.Drawing(svg_path, size=(width, height), profile='tiny')
    
    # Find contours in the edge image
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw each contour as a polyline in SVG
    for contour in contours:
        if len(contour) > 2:  # Only draw contours with at least 3 points
            points = [(int(point[0][0]), int(point[0][1])) for point in contour]
            dwg.add(dwg.polyline(points, stroke='black', fill='none', stroke_width=1))
    
    dwg.save()


def process_frame(frame_path, output_folder, frame_number):
    """Process a single frame: convert to line drawing and save as both PNG and SVG"""
    # Convert to line drawing
    line_drawing, edges = convert_to_line_drawing(frame_path)
    
    # Save as PNG
    png_output = f"{output_folder}/images/line_frame_{frame_number:04d}.png"
    cv2.imwrite(png_output, line_drawing)
    
    # Save as SVG
    height, width = edges.shape
    svg_output = f"{output_folder}/vectors/frame_{frame_number:04d}.svg"
    edges_to_svg(edges, svg_output, width, height)
    
    print(f"Processed frame {frame_number:04d}")
    return png_output, svg_output


def main():
    video_path = "static/video.mp4"
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    
    print("Starting video processing...")
    
    # Create output folder
    output_folder = create_output_folder()
    print(f"Output folder: {output_folder}")
    
    # Extract frames (1 per second)
    frame_paths = extract_frames(video_path, output_folder, fps=1)
    
    # Process each frame
    print("\nConverting frames to line drawings and vectors...")
    for i, frame_path in enumerate(frame_paths):
        process_frame(frame_path, output_folder, i)
    
    print(f"\n✓ Processing complete!")
    print(f"✓ Total frames processed: {len(frame_paths)}")
    print(f"✓ PNG line drawings: {output_folder}/images/")
    print(f"✓ SVG vectors: {output_folder}/vectors/")
    
    # Create a summary file
    summary_path = f"{output_folder}/summary.txt"
    with open(summary_path, 'w') as f:
        f.write(f"Video Processing Summary\n")
        f.write(f"========================\n\n")
        f.write(f"Source video: {video_path}\n")
        f.write(f"Frames extracted: {len(frame_paths)}\n")
        f.write(f"Frame rate: 1 frame per second\n")
        f.write(f"Output location: {output_folder}\n")
        f.write(f"\nProcessing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"✓ Summary saved: {summary_path}")


if __name__ == "__main__":
    main()
