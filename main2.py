import cv2
import numpy as np
from pyzbar.pyzbar import decode
import streamlit as st
from PIL import Image
import pandas as pd
import os

from streamlit import session_state

if 'done' not in session_state:
    session_state['done'] = False

if 'status' not in session_state:
    session_state['status'] = 0


def scan_qr_code(frame):
    qr_codes = decode(frame)
    if qr_codes:
        for qr_code in qr_codes:
            data = qr_code.data.decode('utf-8')
            return data

    # Rotate frame to check in other orientations
    for angle in [90, 180, 270]:
        rotated_frame = np.rot90(frame, k=angle // 90)
        qr_codes_rotated = decode(rotated_frame)
        if qr_codes_rotated:
            for qr_code in qr_codes_rotated:
                data = qr_code.data.decode('utf-8')
                return data
    return None



st.title("IP Webcam QR Code Scanner - Scan Multiple Items")


ip_url = st.text_input("Enter the IP Webcam URL (e.g., http://192.168.0.101:8080/video)", "")
num_scans = st.number_input("Enter the number of QR codes to scan:", min_value=1, value=1)

excel_file = "track_data.xlsx"  # Updated Excel file name


if os.path.exists(excel_file):
    df = pd.read_excel(excel_file)
else:
    df = pd.DataFrame(columns=["Scan Number", "QR Code Data"])


def get_frame_from_ipcam(ip_url):
    cap = cv2.VideoCapture(ip_url)
    ret, frame = cap.read()
    cap.release()
    return frame

if session_state['status'] < num_scans:
    if st.button("Scan QR"):
        if ip_url:
            all_scanned = False

            st.info(f"Processing Scan {session_state['status'] + 1} of {num_scans}...")
            frame = get_frame_from_ipcam(ip_url)

            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                st.image(img_pil, caption="Video Feed")

                qr_data = scan_qr_code(frame)

                if qr_data:
                    st.success(f"QR Code {session_state['status'] + 1} Content: {qr_data}")
                    session_state['status'] += 1

                    if session_state['status'] == num_scans:
                        all_scanned = True

                    new_data = {"IP": ip_url, "QR Code Data": qr_data}
                    df = df._append(new_data, ignore_index=True)


                    # Save to Excel after each scan
                    df.to_excel(excel_file, index=False)
                else:
                    st.error(f"No QR Code detected for scan {session_state['status'] + 1}. Try again!")
                    all_scanned = False

            else:
                st.error("Unable to capture frame from IP webcam.")
                all_scanned = False


            if all_scanned:
                session_state['done'] = True
                st.success("Response recorded")
        else:
            st.warning("Please enter a valid IP webcam URL.")

# Display the latest scanned data
if session_state['done']:
    if os.path.exists(excel_file):
        st.subheader("Scanned QR Code Data:")
        if st.button("Show Data"):
            df = pd.read_excel(excel_file)
            st.write(df.tail(num_scans))

