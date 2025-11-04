import streamlit as st
import numpy as np
from PIL import Image
import tempfile
import os
import time
import io
import base64

# Try to import OpenCV with specific version
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError as e:
    OPENCV_AVAILABLE = False
    st.sidebar.warning("⚠️ OpenCV not available - video features disabled")

# Set page configuration
st.set_page_config(
    page_title="ASCII Art Converter",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .ascii-art {
        font-family: 'Courier New', monospace;
        line-height: 1;
        white-space: pre;
        overflow-x: auto;
        font-size: 8px;
    }
    .video-container {
        max-width: 100%;
        border-radius: 10px;
    }
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

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
    
    def frame_to_ascii(self, frame, width=80, color_mode=True):
        """Convert frame to ASCII art"""
        try:
            if frame is None:
                return "<pre>No frame</pre>", 0, 0
                
            original_height, original_width = frame.shape[:2]
            aspect_ratio = original_height / original_width
            
            target_width = min(width, 120)
            target_height = int(target_width * aspect_ratio * 0.5)
            target_height = max(10, min(target_height, 80))
            
            # Resize frame
            frame_resized = cv2.resize(frame, (target_width, target_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            
            # Convert to ASCII
            ascii_html = '<pre class="ascii-art">'
            
            for y in range(target_height):
                line_html = ""
                for x in range(target_width):
                    brightness = frame_gray[y, x]
                    char = self.char_map[brightness]
                    
                    if color_mode:
                        r, g, b = frame_rgb[y, x]
                        line_html += f"<span style='color: rgb({r},{g},{b})'>{char}</span>"
                    else:
                        line_html += char
                
                ascii_html += line_html + "\n"
            
            ascii_html += "</pre>"
            return ascii_html, target_width, target_height
            
        except Exception as e:
            return f"<pre>Error: {str(e)}</pre>", 0, 0
    
    def image_to_ascii(self, image, width=80, color_mode=True):
        """Convert PIL Image to ASCII art"""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_width, original_height = image.size
            aspect_ratio = original_height / original_width
            
            target_width = min(width, 120)
            target_height = int(target_width * aspect_ratio * 0.5)
            target_height = max(10, min(target_height, 80))
            
            img_resized = image.resize((target_width, target_height))
            img_gray = image.convert('L').resize((target_width, target_height))
            
            pixels_rgb = np.array(img_resized)
            pixels_gray = np.array(img_gray)
            
            ascii_html = '<pre class="ascii-art">'
            
            for y in range(target_height):
                line_html = ""
                for x in range(target_width):
                    brightness = pixels_gray[y, x]
                    char = self.char_map[brightness]
                    
                    if color_mode:
                        r, g, b = pixels_rgb[y, x]
                        line_html += f"<span style='color: rgb({r},{g},{b})'>{char}</span>"
                    else:
                        line_html += char
                
                ascii_html += line_html + "\n"
            
            ascii_html += "</pre>"
            return ascii_html, target_width, target_height
            
        except Exception as e:
            return f"<pre>Error: {str(e)}</pre>", 0, 0

def main():
    st.title("🎨 ASCII Art Converter")
    st.markdown("Convert images, videos, and access webcam to create ASCII art!")
    
    # Initialize converter
    converter = StreamlitASCIIConverter()
    
    # Sidebar settings
    st.sidebar.title("⚙️ Settings")
    ascii_width = st.sidebar.slider("ASCII Width", 30, 120, 80)
    color_mode = st.sidebar.checkbox("Color Mode", value=True)
    
    # Main app
    input_type = st.radio(
        "Choose input type:",
        ["Image", "Video", "Webcam"],
        horizontal=True
    )
    
    if input_type == "Image":
        handle_image_input(converter, ascii_width, color_mode)
    elif input_type == "Video":
        if OPENCV_AVAILABLE:
            handle_video_input(converter, ascii_width, color_mode)
        else:
            st.error("❌ Video processing requires OpenCV. This feature is not available in the current deployment.")
            st.info("🔧 Try deploying with the compatible OpenCV version in requirements.txt")
    elif input_type == "Webcam":
        if OPENCV_AVAILABLE:
            handle_webcam_input(converter, ascii_width, color_mode)
        else:
            st.error("❌ Webcam access requires OpenCV. This feature is not available in the current deployment.")
            st.info("🔧 Try running this app locally for full webcam support")

def handle_image_input(converter, ascii_width, color_mode):
    st.subheader("📷 Image to ASCII")
    
    uploaded_file = st.file_uploader(
        "Choose an image file", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']
    )
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Image")
                st.image(image, use_column_width=True)
                st.caption(f"Size: {image.size[0]} x {image.size[1]}")
            
            with col2:
                st.subheader("ASCII Art")
                with st.spinner("Converting..."):
                    ascii_html, width, height = converter.image_to_ascii(
                        image, ascii_width, color_mode
                    )
                    st.markdown(ascii_html, unsafe_allow_html=True)
                    st.caption(f"ASCII: {width} x {height} chars")
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")

def handle_video_input(converter, ascii_width, color_mode):
    st.subheader("🎥 Video to ASCII")
    
    uploaded_file = st.file_uploader(
        "Choose a video file", 
        type=['mp4', 'avi', 'mov', 'mkv']
    )
    
    if uploaded_file is not None:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                st.error("❌ Could not open video file")
                return
            
            # Get video info
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames > 0:
                st.info(f"📊 Video Info: {total_frames} frames, {fps:.1f} FPS")
                
                # Frame navigation
                frame_number = st.slider("Select Frame", 0, total_frames-1, 0, key="video_frame")
                
                # Navigation buttons
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
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        st.image(frame_rgb, use_column_width=True)
                        st.caption(f"Frame {frame_number}/{total_frames-1}")
                    
                    with col2:
                        st.subheader("ASCII Art")
                        ascii_html, width, height = converter.frame_to_ascii(
                            frame, ascii_width, color_mode
                        )
                        st.markdown(ascii_html, unsafe_allow_html=True)
                        st.caption(f"ASCII: {width} x {height} chars")
            
        except Exception as e:
            st.error(f"Video processing error: {str(e)}")
        finally:
            if 'cap' in locals():
                cap.release()
            if os.path.exists(video_path):
                os.unlink(video_path)

def handle_webcam_input(converter, ascii_width, color_mode):
    st.subheader("📹 Webcam to ASCII")
    
    st.info("""
    **Webcam Access Notes:**
    - Works best in local deployment
    - Cloud deployment may have limited camera access
    - Grant camera permissions when prompted
    - Use Chrome/Firefox for best compatibility
    """)
    
    # Webcam access using OpenCV
    if st.button("🎥 Start Webcam"):
        webcam_placeholder = st.empty()
        info_placeholder = st.empty()
        stop_button = st.button("🛑 Stop Webcam")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ Could not access webcam")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while not stop_button:
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ Failed to capture frame")
                    break
                
                # Convert to ASCII
                ascii_html, width, height = converter.frame_to_ascii(
                    frame, ascii_width, color_mode
                )
                
                # Calculate FPS
                frame_count += 1
                current_time = time.time()
                elapsed_time = current_time - start_time
                fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                
                # Update display
                webcam_placeholder.markdown(ascii_html, unsafe_allow_html=True)
                info_placeholder.info(
                    f"📊 Frame: {frame_count} | FPS: {fps:.1f} | "
                    f"Size: {width}x{height} | Color: {'ON' if color_mode else 'OFF'}"
                )
                
                # Check for stop
                if stop_button:
                    break
                
                # Control frame rate
                time.sleep(0.05)
                
        except Exception as e:
            st.error(f"Webcam error: {str(e)}")
        finally:
            cap.release()
            st.success("✅ Webcam stopped")

def play_video_animation(cap, converter, ascii_width, color_mode):
    """Play video as animation"""
    st.info("🎬 Playing video animation...")
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    animation_placeholder = st.empty()
    stop_animation = st.button("⏹️ Stop Animation")
    
    try:
        while not stop_animation:
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
            time.sleep(0.1)
            
            if stop_animation:
                break
                
    except Exception as e:
        st.error(f"Animation error: {str(e)}")

if __name__ == "__main__":
    main()