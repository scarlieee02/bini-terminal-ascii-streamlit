import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import time

# Set page configuration
st.set_page_config(
    page_title="ASCII Art Converter",
    page_icon="🎨",
    layout="wide"
)

class StreamlitASCIIConverter:
    def __init__(self):
        self.chars = "@%#*+=-:. "
        self.precompute_char_mapping()
    
    def precompute_char_mapping(self):
        self.char_map = {}
        for pixel_value in range(256):
            scale = len(self.chars) - 1
            char_index = min(int(pixel_value / 255 * scale), scale)
            self.char_map[pixel_value] = self.chars[char_index]
    
    def frame_to_ascii(self, frame, width=100, color_mode=True):
        """Convert frame to ASCII art for Streamlit"""
        try:
            original_height, original_width = frame.shape[:2]
            aspect_ratio = original_height / original_width
            
            target_width = width
            target_height = int(target_width * aspect_ratio * 0.5)
            
            # Resize frame
            frame_resized = cv2.resize(frame, (target_width, target_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            
            # Convert to ASCII with HTML formatting for color
            ascii_html = "<pre style='font-family: monospace; line-height: 1;'>"
            
            for y in range(target_height):
                line_html = ""
                for x in range(target_width):
                    brightness = frame_gray[y, x]
                    char = self.char_map[brightness]
                    r, g, b = frame_rgb[y, x]
                    
                    if color_mode:
                        # Use HTML span with color
                        line_html += f"<span style='color: rgb({r},{g},{b})'>{char}</span>"
                    else:
                        line_html += char
                
                ascii_html += line_html + "\n"
            
            ascii_html += "</pre>"
            return ascii_html, target_width, target_height
            
        except Exception as e:
            return f"<pre>Error: {e}</pre>", 0, 0
    
    def image_to_ascii(self, image, width=100, color_mode=True):
        """Convert PIL Image to ASCII art"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate dimensions
            original_width, original_height = image.size
            aspect_ratio = original_height / original_width
            
            target_width = width
            target_height = int(target_width * aspect_ratio * 0.5)
            
            # Resize image
            img_resized = image.resize((target_width, target_height))
            img_gray = image.convert('L').resize((target_width, target_height))
            
            # Convert to numpy arrays
            pixels_rgb = np.array(img_resized)
            pixels_gray = np.array(img_gray)
            
            # Create ASCII HTML
            ascii_html = "<pre style='font-family: monospace; line-height: 1;'>"
            
            for y in range(target_height):
                line_html = ""
                for x in range(target_width):
                    r, g, b = pixels_rgb[y, x]
                    brightness = pixels_gray[y, x]
                    char = self.char_map[brightness]
                    
                    if color_mode:
                        line_html += f"<span style='color: rgb({r},{g},{b})'>{char}</span>"
                    else:
                        line_html += char
                
                ascii_html += line_html + "\n"
            
            ascii_html += "</pre>"
            return ascii_html, target_width, target_height
            
        except Exception as e:
            return f"<pre>Error: {e}</pre>", 0, 0

def main():
    st.title("🎨 ASCII Art Converter")
    st.markdown("Convert images, videos, and webcam feed to ASCII art!")
    
    # Initialize converter
    converter = StreamlitASCIIConverter()
    
    # Sidebar for settings
    st.sidebar.title("Settings")
    ascii_width = st.sidebar.slider("ASCII Width", 50, 200, 100)
    color_mode = st.sidebar.checkbox("Color Mode", value=True)
    
    # Main content - choose input type
    input_type = st.radio(
        "Choose input type:",
        ["Image", "Video", "Webcam"],
        horizontal=True
    )
    
    if input_type == "Image":
        handle_image_input(converter, ascii_width, color_mode)
    
    elif input_type == "Video":
        handle_video_input(converter, ascii_width, color_mode)
    
    elif input_type == "Webcam":
        handle_webcam_input(converter, ascii_width, color_mode)

def handle_image_input(converter, ascii_width, color_mode):
    st.subheader("Image to ASCII")
    
    uploaded_file = st.file_uploader(
        "Choose an image...", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff']
    )
    
    if uploaded_file is not None:
        # Display original image
        image = Image.open(uploaded_file)
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Image")
            st.image(image, use_column_width=True)
        
        with col2:
            st.subheader("ASCII Art")
            # Convert to ASCII
            ascii_html, width, height = converter.image_to_ascii(
                image, ascii_width, color_mode
            )
            st.markdown(ascii_html, unsafe_allow_html=True)
            
            st.info(f"ASCII Dimensions: {width} x {height}")

def handle_video_input(converter, ascii_width, color_mode):
    st.subheader("Video to ASCII")
    
    uploaded_file = st.file_uploader(
        "Choose a video...", 
        type=['mp4', 'avi', 'mov', 'mkv']
    )
    
    if uploaded_file is not None:
        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name
        
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                st.error("Error: Could not open video file")
                return
            
            # Get video info
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            st.info(f"Video Info: {total_frames} frames, {fps:.1f} FPS")
            
            # Frame selector
            frame_number = st.slider("Select Frame", 0, total_frames-1, 0)
            
            # Display controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⏮️ First Frame"):
                    frame_number = 0
                    st.rerun()
            
            with col2:
                if st.button("▶️ Play Animation"):
                    play_video_animation(cap, converter, ascii_width, color_mode)
            
            with col3:
                if st.button("⏭️ Last Frame"):
                    frame_number = total_frames - 1
                    st.rerun()
            
            # Display selected frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Original Frame")
                    # Convert BGR to RGB for display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st.image(frame_rgb, use_column_width=True)
                
                with col2:
                    st.subheader("ASCII Art")
                    ascii_html, width, height = converter.frame_to_ascii(
                        frame, ascii_width, color_mode
                    )
                    st.markdown(ascii_html, unsafe_allow_html=True)
            
        finally:
            cap.release()
            os.unlink(video_path)

def handle_webcam_input(converter, ascii_width, color_mode):
    st.subheader("Webcam to ASCII")
    
    if not st.button("🎥 Start Webcam"):
        st.info("Click the button above to start webcam capture")
        return
    
    # Create placeholder for webcam feed
    ascii_placeholder = st.empty()
    info_placeholder = st.empty()
    stop_button = st.button("🛑 Stop Webcam")
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        st.error("❌ Error: Could not access webcam")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while not stop_button:
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to capture frame from webcam")
                break
            
            # Convert frame to ASCII
            ascii_html, width, height = converter.frame_to_ascii(
                frame, ascii_width, color_mode
            )
            
            # Calculate FPS
            frame_count += 1
            current_time = time.time()
            elapsed_time = current_time - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            
            # Update display
            ascii_placeholder.markdown(ascii_html, unsafe_allow_html=True)
            info_placeholder.info(
                f"Frame: {frame_count} | FPS: {fps:.1f} | "
                f"Size: {width}x{height} | Color: {'ON' if color_mode else 'OFF'}"
            )
            
            # Check if stop button was pressed
            if stop_button:
                break
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.03)
            
    except Exception as e:
        st.error(f"Webcam error: {e}")
    finally:
        cap.release()
        st.success("Webcam stopped")

def play_video_animation(cap, converter, ascii_width, color_mode):
    """Play video as animation in Streamlit"""
    st.info("Playing video animation...")
    
    # Reset video to beginning
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    # Create placeholder for animation
    animation_placeholder = st.empty()
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = 1.0 / fps if fps > 0 else 1.0 / 24
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert frame to ASCII
            ascii_html, width, height = converter.frame_to_ascii(
                frame, ascii_width, color_mode
            )
            
            # Update animation
            animation_placeholder.markdown(ascii_html, unsafe_allow_html=True)
            
            # Small delay
            time.sleep(frame_delay)
            
    except Exception as e:
        st.error(f"Animation error: {e}")

if __name__ == "__main__":
    main()