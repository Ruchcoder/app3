import streamlit as st
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import io

st.title("Infrastructure Health Monitoring System")
st.write("Detects cracks and rust on pipes/concrete surfaces with severity levels.")

uploaded_file = st.file_uploader("Upload Image", type=["jpg","png","jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    # -------------------------
    # RESIZE FOR PERFORMANCE
    # -------------------------
    max_width = 600
    w_percent = max_width / float(image.width)
    new_height = int(float(image.height) * w_percent)
    image_resized = image.resize((max_width, new_height))

    # -------------------------
    # CRACK DETECTION (EDGE)
    # -------------------------
    gray = image_resized.convert("L")
    gray_enhanced = ImageEnhance.Contrast(gray).enhance(2.5)

    edges = gray_enhanced.filter(ImageFilter.FIND_EDGES)
    edge_array = np.array(edges)

    threshold = np.percentile(edge_array, 90)
    edge_binary = edge_array > threshold

    visited = np.zeros_like(edge_binary, dtype=bool)
    crack_mask = np.zeros_like(edge_binary, dtype=bool)

    min_region_size = 20
    openings = []
    opening_sizes = []

    def flood_fill(y, x):
        stack = [(y, x)]
        region_pixels = []
        while stack:
            cy, cx = stack.pop()
            if cy < 0 or cy >= edge_binary.shape[0] or cx < 0 or cx >= edge_binary.shape[1]:
                continue
            if visited[cy, cx] or not edge_binary[cy, cx]:
                continue
            visited[cy, cx] = True
            region_pixels.append((cy, cx))
            stack.extend([(cy-1, cx), (cy+1, cx), (cy, cx-1), (cy, cx+1)])
        return region_pixels

    height, width = edge_binary.shape
    for y in range(height):
        for x in range(width):
            if edge_binary[y, x] and not visited[y, x]:
                pixels = flood_fill(y, x)
                if len(pixels) >= min_region_size:
                    openings.append(pixels)
                    ys = [p[0] for p in pixels]
                    xs = [p[1] for p in pixels]
                    opening_width = max(xs) - min(xs) + 1
                    opening_sizes.append(opening_width)
                    for py, px in pixels:
                        crack_mask[py, px] = True

    crack_pixels = np.sum(crack_mask)

    # -------------------------
    # RUST DETECTION (COLOR)
    # -------------------------
    img_array = np.array(image_resized)

    R = img_array[:, :, 0]
    G = img_array[:, :, 1]
    B = img_array[:, :, 2]

    rust_mask = (R > 100) & (G < 100) & (B < 80) & (R > G) & (R > B)
    rust_pixels = np.sum(rust_mask)

    # -------------------------
    # DRAW RESULTS
    # -------------------------
    draw = ImageDraw.Draw(image_resized)

    # Draw cracks in red
    if crack_pixels > 200:
        for y in range(height):
            x_positions = np.where(crack_mask[y, :])[0]
            if len(x_positions) > 0:
                start = x_positions[0]
                prev = x_positions[0]
                for x in x_positions[1:]:
                    if x == prev + 1:
                        prev = x
                    else:
                        draw.line((start, y, prev, y), fill="red", width=3)
                        start = x
                        prev = x
                draw.line((start, y, prev, y), fill="red", width=3)

    # Draw rust in orange
    for y in range(height):
        for x in range(width):
            if rust_mask[y, x]:
                draw.point((x, y), fill=(255, 165, 0))  # orange

    # Display the processed image
    st.subheader("Detection Overlay")
    st.image(image_resized, use_container_width=True)

    # -------------------------
    # SEVERITY ANALYSIS
    # -------------------------
    if opening_sizes:
        max_width_opening = max(opening_sizes)
        if max_width_opening < 50:
            crack_severity = "Low"
        elif max_width_opening < 150:
            crack_severity = "Moderate"
        else:
            crack_severity = "High"
    else:
        crack_severity = "None"

    if rust_pixels < 500:
        rust_severity = "Low"
    elif rust_pixels < 2000:
        rust_severity = "Moderate"
    else:
        rust_severity = "High"

    # -------------------------
    # INSPECTION REPORT
    # -------------------------
    st.subheader("Inspection Report")
    actions = []

    # Crack report
    if crack_pixels > 200:
        st.success("Cracks Detected")
        st.write(f"Crack Severity: {crack_severity}")
        actions.append("- Immediate inspection and maintenance required. Repair cracks detected")
    else:
        st.info("No Cracks Detected")

    # Rust report
    if rust_pixels > 100:
        st.warning("Rust Detected")
        st.write(f"Rust Severity: {rust_severity}")
        actions.append("- Apply anti-corrosion treatment if rust is present")
    else:
        st.info("No Significant Rust Detected")

    # Recommended actions only for detected defects
    if actions:
        st.write("Recommended Action:")
        for action in actions:
            st.write(action)

    # -------------------------
    # DOWNLOAD PROCESSED IMAGE
    # -------------------------
    buffer = io.BytesIO()
    image_resized.save(buffer, format="PNG")
    buffer.seek(0)

    st.download_button(
        label="Download Processed Image",
        data=buffer,
        file_name="crack_rust_detection.png",
        mime="image/png"
    )
