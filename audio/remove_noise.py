import os

import cv2
import numpy as np
from tqdm import tqdm


def remove_video_noise(input_path, output_path, 
                      spatial_luma=4.0, spatial_chroma=4.0,
                      temporal_luma=6.0, temporal_chroma=6.0,
                      method='hqdn3d'):
    """
    Remove noise from video using various denoising methods.
    
    Args:
        input_path (str): Path to input video file
        output_path (str): Path to output video file
        spatial_luma (float): Spatial luma strength (1-15)
        spatial_chroma (float): Spatial chroma strength (1-15)
        temporal_luma (float): Temporal luma strength (1-20)
        temporal_chroma (float): Temporal chroma strength (1-20)
        method (str): Denoising method - 'hqdn3d', 'nlmeans', 'fastnl', 'bilateral'
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' not found")
            return False
        
        # Open input video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print("Error: Could not open input video")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Setup video writer - use X264 for better compatibility
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print("Error: Could not create output video")
            cap.release()
            return False
        
        print(f"Processing video: {width}x{height}, {fps:.1f} FPS, {total_frames} frames")
        print(f"Using method: {method}")
        print(f"Parameters: spatial_luma={spatial_luma}, temporal_luma={temporal_luma}")
        
        # Initialize variables for temporal denoising
        prev_frame = None
        frame_count = 0
        
        # Create progress bar
        pbar = tqdm(total=total_frames, desc="Denoising frames")
        
        # Process each frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            denoised_frame = apply_denoising(frame, prev_frame, method,
                                           spatial_luma, spatial_chroma,
                                           temporal_luma, temporal_chroma)
            
            out.write(denoised_frame)
            prev_frame = frame.copy()
            frame_count += 1
            pbar.update(1)
        
        pbar.close()
        
        # Cleanup
        cap.release()
        out.release()
        
        print(f"Successfully processed {frame_count} frames")
        print(f"Output saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()
        return False

def apply_denoising(frame, prev_frame, method, spatial_luma, spatial_chroma,
                   temporal_luma, temporal_chroma):
    """Apply specific denoising method to frame"""
    
    if method == 'hqdn3d':
        return hqdn3d_denoise(frame, prev_frame, spatial_luma, spatial_chroma,
                            temporal_luma, temporal_chroma)
    elif method == 'nlmeans':
        return nlmeans_denoise(frame, spatial_luma)
    elif method == 'fastnl':
        return fast_nlmeans_denoise(frame, spatial_luma)
    elif method == 'bilateral':
        return bilateral_denoise(frame, spatial_luma)
    else:
        # Default to bilateral filter
        return bilateral_denoise(frame, spatial_luma)

def hqdn3d_denoise(frame, prev_frame, spatial_luma, spatial_chroma,
                  temporal_luma, temporal_chroma):
    """HQDN3D-like denoising implementation"""
    
    # Convert to YUV color space
    yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    y, u, v = cv2.split(yuv)
    
    # Apply spatial denoising with safe kernel sizes
    # Ensure kernel size is odd and reasonable
    kernel_size = max(3, min(int(spatial_luma), 15))
    if kernel_size % 2 == 0:  # Ensure odd number
        kernel_size += 1
    
    y_denoised = cv2.medianBlur(y, kernel_size)
    
    # Chroma denoising with Gaussian blur
    sigma_u = max(0.5, spatial_chroma / 3.0)
    sigma_v = max(0.5, spatial_chroma / 3.0)
    
    u_denoised = cv2.GaussianBlur(u, (0, 0), sigma_u)
    v_denoised = cv2.GaussianBlur(v, (0, 0), sigma_v)
    
    # Apply temporal denoising if previous frame exists
    if prev_frame is not None and temporal_luma > 0:
        prev_yuv = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2YUV)
        prev_y, prev_u, prev_v = cv2.split(prev_yuv)
        
        # Temporal blending (0-1 range)
        alpha_y = min(0.5, temporal_luma / 40.0)
        alpha_uv = min(0.5, temporal_chroma / 40.0)
        
        y_denoised = cv2.addWeighted(y_denoised, 1-alpha_y, prev_y, alpha_y, 0)
        u_denoised = cv2.addWeighted(u_denoised, 1-alpha_uv, prev_u, alpha_uv, 0)
        v_denoised = cv2.addWeighted(v_denoised, 1-alpha_uv, prev_v, alpha_uv, 0)
    
    # Merge channels and convert back
    merged = cv2.merge([y_denoised, u_denoised, v_denoised])
    result = cv2.cvtColor(merged, cv2.COLOR_YUV2BGR)
    
    # Ensure we don't return invalid data
    return np.clip(result, 0, 255).astype(np.uint8)

def nlmeans_denoise(frame, strength):
    """Non-local means denoising"""
    h = max(3.0, min(strength, 25.0))  # denoising strength
    hColor = max(3.0, min(strength, 25.0))
    
    # Resize if frame is too large for performance
    h_orig, w_orig = frame.shape[:2]
    if w_orig > 1920 or h_orig > 1080:
        scale = min(1920.0/w_orig, 1080.0/h_orig)
        frame_small = cv2.resize(frame, None, fx=scale, fy=scale)
        denoised_small = cv2.fastNlMeansDenoisingColored(frame_small, None, h, hColor, 7, 21)
        return cv2.resize(denoised_small, (w_orig, h_orig))
    else:
        return cv2.fastNlMeansDenoisingColored(frame, None, h, hColor, 7, 21)

def fast_nlmeans_denoise(frame, strength):
    """Faster non-local means denoising"""
    h = max(3.0, min(strength, 15.0))
    return cv2.fastNlMeansDenoisingColored(frame, None, h, h, 5, 11)

def bilateral_denoise(frame, strength):
    """Bilateral filter denoising"""
    d = int(max(1, min(strength * 2, 15)))
    sigma_color = max(10.0, strength * 10)
    sigma_space = max(10.0, strength * 10)
    
    return cv2.bilateralFilter(frame, d, sigma_color, sigma_space)

def simple_gaussian_denoise(frame, strength):
    """Simple Gaussian denoising as fallback"""
    sigma = max(0.5, strength / 4.0)
    kernel_size = max(3, int(strength))
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    return cv2.GaussianBlur(frame, (kernel_size, kernel_size), sigma)

# Alternative simple usage function
def quick_denoise(input_path, output_path, strength='medium'):
    """
    Quick denoising with preset strengths
    """
    presets = {
        'light': {'spatial_luma': 2.0, 'temporal_luma': 3.0, 'method': 'bilateral'},
        'medium': {'spatial_luma': 4.0, 'temporal_luma': 6.0, 'method': 'hqdn3d'},
        'strong': {'spatial_luma': 8.0, 'temporal_luma': 10.0, 'method': 'nlmeans'},
        'heavy': {'spatial_luma': 12.0, 'temporal_luma': 15.0, 'method': 'nlmeans'}
    }
    
    if strength not in presets:
        print(f"Invalid strength '{strength}'. Using 'medium'")
        strength = 'medium'
    
    params = presets[strength]
    return remove_video_noise(input_path, output_path, **params)

# Example usage
if __name__ == "__main__":
    # Test with different methods
    input_video = "/home/zaya/Videos/me-imtheone.mp4"
    output_video = "/home/zaya/Videos/denoised_video.mp4"
    
    # Make sure input file exists
    if not os.path.exists(input_video):
        print(f"Please create a test video first or update the input_video path")
        print(f"Current path: {os.path.abspath(input_video)}")
    else:
        # Quick denoising with medium strength
        quick_denoise(input_video, output_video, strength='medium')
        
        # Or use custom parameters:
        # remove_video_noise(input_video, output_video, 
        #                   spatial_luma=5.0, temporal_luma=8.0,
        #                   method='hqdn3d')