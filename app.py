import streamlit as st
import numpy as np
from PIL import Image
import tempfile
import os
import time
import base64

# Try to import OpenCV with fallback
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    st.warning("OpenCV not available. Some features may be limited.")

# Set page configuration
st.set_page_config(
    page_title="ASCII Art Converter",
    page_icon="🎨",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .ascii-art {
        font-family: 'Courier New', monospace;
        line-height: 1;
        white-space: pre;
        overflow-x: auto;
        font-size: 8px;
    }
    .stAlert {
        padding: 10px;
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
    
    def resize_image_pil(self, image, target_width, target_height):
        """Resize image using PIL only (no OpenCV)"""
        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    def image_to_ascii(self, image, width=80, color_mode=True):
        """Convert PIL Image to ASCII art"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_width, original_height = image.size
            if original_width == 0 or original_height == 0:
                return "<pre>Empty image</pre>", 0, 0
            
            aspect_ratio = original_height / original_width
            
            target_width = min(width, 120)
            target_height = int(target_width * aspect_ratio * 0.5)
            target_height = max(10, min(target_height, 80))
            
            # Resize image using PIL
            img_resized = self.resize_image_pil(image, target_width, target_height)
            img_gray = image.convert('L').resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Convert to numpy arrays
            pixels_rgb = np.array(img_resized)
            pixels_gray = np.array(img_gray)
            
            # Create ASCII HTML
            ascii_html = '<pre class="ascii-art">'
            
            for y in range(target_height):
                line_html = ""
                for x in range(target_width):
                    if y < pixels_gray.shape[0] and x < pixels_gray.shape[1]:
                        brightness = pixels_gray[y, x]
                        char = self.char_map[brightness]
                        
                        if color_mode and y < pixels_rgb.shape[0] and x < pixels_rgb.shape[1]:
                            r, g, b = pixels_rgb[y, x]
                            line_html += f"<span style='color: rgb({r},{g},{b})'>{char}</span>"
                        else:
                            line_html += char
                    else:
                        line_html += " "
                
                ascii_html += line_html + "\n"
            
            ascii_html += "</pre>"
            return ascii_html, target_width, target_height
            
        except Exception as e:
            return f"<pre>Error processing image: {str(e)}</pre>", 0, 0

def process_video_without_opencv(uploaded_file):
    """Process video files without OpenCV"""
    st.warning("Video processing requires OpenCV. This feature is not available in the current deployment.")
    st.info("Try the image conversion feature instead!")
    return None

def main():
    st.title("🎨 ASCII Art Converter")
    st.markdown("Convert images to beautiful ASCII art in your browser!")
    
    if not OPENCV_AVAILABLE:
        st.info("🔧 *Running in basic mode - Image conversion available*")
    
    # Initialize converter
    converter = StreamlitASCIIConverter()
    
    # Sidebar for settings
    st.sidebar.title("Settings")
    ascii_width = st.sidebar.slider("ASCII Width", 30, 120, 80)
    color_mode = st.sidebar.checkbox("Color Mode", value=True)
    
    # Main content - simplified without video/webcam
    st.subheader("📷 Image to ASCII")
    
    uploaded_file = st.file_uploader(
        "Choose an image file", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'],
        help="Upload an image to convert to ASCII art"
    )
    
    if uploaded_file is not None:
        try:
            # Display original image
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Image")
                st.image(image, use_column_width=True)
                st.caption(f"Original size: {image.size[0]} x {image.size[1]} pixels")
            
            with col2:
                st.subheader("ASCII Art")
                # Convert to ASCII
                with st.spinner("Converting to ASCII..."):
                    ascii_html, width, height = converter.image_to_ascii(
                        image, ascii_width, color_mode
                    )
                    
                    # Display ASCII art
                    st.markdown(ascii_html, unsafe_allow_html=True)
                    st.caption(f"ASCII dimensions: {width} x {height} characters")
                    
                    # Add download option
                    st.download_button(
                        label="📥 Download ASCII as HTML",
                        data=ascii_html,
                        file_name="ascii_art.html",
                        mime="text/html"
                    )
                    
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            st.info("Try uploading a different image format or smaller file size.")
    
    # Examples section
    with st.expander("🎯 Tips for Best Results"):
        st.markdown("""
        - **Image Size**: Medium-sized images work best (500-2000 pixels)
        - **File Types**: JPG, PNG, BMP are recommended
        - **Contrast**: High-contrast images produce better ASCII art
        - **Width Setting**: 60-100 characters usually works well
        - **Color Mode**: Try both color and B&W to see different effects
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("### 🚀 Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎨 Color Support**")
        st.markdown("Full RGB color in ASCII art")
    
    with col2:
        st.markdown("**📱 Responsive**")
        st.markdown("Works on desktop and mobile")
    
    with col3:
        st.markdown("**⚡ Fast**")
        st.markdown("Real-time conversion")
    
    st.markdown("---")
    st.markdown("Built with Streamlit • Deployed on Streamlit Community Cloud")

if __name__ == "__main__":
    main()