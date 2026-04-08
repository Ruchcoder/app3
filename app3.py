# -------------------------
# INSPECTION REPORT
# -------------------------
st.subheader("Inspection Report")
actions = []

# Crack report
if crack_pixels > 200:
    st.success("Cracks Detected")
    st.write(f"Crack Severity: {crack_severity}")
    actions.append("- Repair cracks if detected")
else:
    st.info("No Cracks Detected")

# Rust report
if rust_pixels > 100:
    st.warning("Rust Detected")
    st.write(f"Rust Severity: {rust_severity}")
    actions.append("- Apply anti-corrosion treatment if rust is present")
else:
    st.info("No Rust Detected")

# Recommended actions only for detected defects
if actions:
    st.write("Recommended Action:")
    for action in actions:
        st.write(action)
