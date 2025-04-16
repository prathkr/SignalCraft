import streamlit as st
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import tempfile
import os
from collections import defaultdict
import time

# Page configuration
st.set_page_config(
    page_title="Vehicle Counter with YOLOv8",
    page_icon="🚗",
    layout="wide"
)

# Title and description
st.title("🚗 Vehicle Counter with YOLOv8")
st.markdown("""
Upload a video file to count cars and trucks using YOLOv8 object detection.
The app will process the video and display the total count of detected vehicles.
""")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.5, 0.01)
    selected_classes = st.multiselect(
        "Select Vehicle Classes to Count",
        options=["car", "truck", "bus", "motorcycle"],
        default=["car", "truck"]
    )
    process_every_nth_frame = st.slider("Process every Nth frame", 1, 10, 3)
    show_live_results = st.checkbox("Show live processing", value=True)

# Class mappings for YOLOv8
CLASS_MAPPINGS = {
    "car": 2,
    "truck": 7,
    "bus": 5,
    "motorcycle": 3
}

# Load YOLOv8 model
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

# Video upload
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

if uploaded_file is not None:
    # Save uploaded file to a temporary file
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    # Open the video file
    cap = cv2.VideoCapture(tfile.name)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    st.info(f"Video Info: {total_frames} frames, {fps:.2f} FPS, Resolution: {width}x{height}")
    
    # Prepare for processing
    st_frame = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize counters
    frame_count = 0
    processed_frame_count = 0
    vehicle_counts = defaultdict(int)
    total_counts = defaultdict(int)
    
    # Process video
    start_time = time.time()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Skip frames based on processing setting
        if frame_count % process_every_nth_frame != 0:
            continue
        
        processed_frame_count += 1
        
        # Perform detection
        results = model.predict(
            frame,
            conf=confidence_threshold,
            classes=[CLASS_MAPPINGS[cls] for cls in selected_classes],
            verbose=False
        )
        
        # Update counts
        current_frame_counts = defaultdict(int)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)
                for cls_name, cls_idx in CLASS_MAPPINGS.items():
                    if class_id == cls_idx and cls_name in selected_classes:
                        current_frame_counts[cls_name] += 1
                        total_counts[cls_name] += 1
        
        # Update vehicle_counts with the maximum counts per class in the current frame
        for cls in selected_classes:
            if current_frame_counts[cls] > vehicle_counts[cls]:
                vehicle_counts[cls] = current_frame_counts[cls]
        
        # Display results
        if show_live_results:
            # Annotate the frame with detections
            annotated_frame = results[0].plot()
            
            # Add counters to the frame
            counter_text = "Current Frame: "
            for cls in selected_classes:
                counter_text += f"{cls.capitalize()}: {current_frame_counts[cls]} | "
            
            cv2.putText(
                annotated_frame,
                counter_text[:-3],
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            # Display in Streamlit
            st_frame.image(annotated_frame, channels="BGR", use_column_width=True)
        
        # Update progress
        progress = frame_count / total_frames
        progress_bar.progress(min(progress, 1.0))
        status_text.text(f"Processing frame {frame_count} of {total_frames}...")
    
    # Release resources
    cap.release()
    os.unlink(tfile.name)
    
    processing_time = time.time() - start_time
    status_text.text(f"Processing complete! Time taken: {processing_time:.2f} seconds")
    
    # Display results
    st.success("Video processing completed!")
    
    # Create a DataFrame for the results
    results_df = pd.DataFrame({
        "Vehicle Type": selected_classes,
        "Max Count in Single Frame": [vehicle_counts[cls] for cls in selected_classes],
        "Total Detections": [total_counts[cls] for cls in selected_classes]
    })
    
    # Display the DataFrame
    st.dataframe(results_df, use_container_width=True)
    
    # Display summary
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Frames Processed", processed_frame_count)
        st.metric("Processing Speed", f"{processed_frame_count/processing_time:.2f} FPS")
    
    with col2:
        st.metric("Max Vehicles in Frame", sum(vehicle_counts.values()))
        st.metric("Total Vehicle Detections", sum(total_counts.values()))
    
    # Show a bar chart of the results
    st.subheader("Vehicle Counts")
    st.bar_chart(results_df.set_index("Vehicle Type")["Max Count in Single Frame"])
    
else:
    st.warning("Please upload a video file to get started.")