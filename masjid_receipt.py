import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from urllib.parse import quote
from datetime import datetime
import pandas as pd
import re
import uuid
from streamlit_gsheets import GSheetsConnection


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Masjid Sharief Welfare Receipt",
    page_icon="🕌",
    layout="wide",
)

# ============================================================
# PASSWORD PROTECTION
# ============================================================

import hmac


def check_password():
    """Show login screen and return True only after successful login."""

    if st.session_state.get("authenticated", False):
        return True

    st.title("🕌 Al Rehman Masjid Sharief")
    st.subheader("Welfare Receipt System")

    st.info("🔐 Please enter the collector password to continue.")

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter collector password",
    )

    if st.button("🔓 Login", type="primary", width="stretch"):
        correct_password = st.secrets["auth"]["password"]

        if hmac.compare_digest(password, correct_password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password.")

    return False


# Stop the rest of the application until authenticated
if not check_password():
    st.stop()

st.markdown(
    """
    <style>
    [data-testid="InputInstructions"] {
        display: none !important;
    }
    .receipt-card {
        border: 1px solid #d0d0d0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# MASJID SETTINGS
# Based on the supplied physical welfare receipt
# ============================================================

MASJID_NAME = "AL Rehman Masjid Sharief"
MASJID_ADDRESS = "Sir Syed Colony, Upper Soura, Srinagar, J&K"
MASJID_BANK = "J&K Bank, Soura"
MASJID_ACCOUNT = "0204040100000553"
MASJID_IFSC = "JAKA0SOURA"

# The supplied receipt visibly shows "S.No. M 559".
# The system starts from 559 and increments automatically.
RECEIPT_PREFIX = "M"
STARTING_RECEIPT_NO = 559

# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================

conn = st.connection("gsheets", type=GSheetsConnection)

# ============================================================
# GOOGLE SHEETS HELPERS
# ============================================================


@st.cache_data(ttl=30)
def get_receipts():
    try:
        df = conn.read(worksheet="Receipts", ttl=30)

        if df.empty:
            return pd.DataFrame()

        text_columns = [
            "Receipt No",
            "Transaction ID",
            "Date",
            "Received From",
            "House No",
            "Purpose",
            "Month From",
            "Month To",
            "Payment Mode",
            "Phone",
            "Status",
        ]

        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Fix phone numbers that Google Sheets/pandas may return as 10-digit floats
        if "Phone" in df.columns:
            df["Phone"] = (
                df["Phone"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            )

        # Fix numeric-looking House No values
        if "House No" in df.columns:
            df["House No"] = (
                df["House No"]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
            )

        if "Amount" in df.columns:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)

        return df

    except Exception:
        return pd.DataFrame()


def get_next_receipt_serial():
    """
    Returns the next numeric receipt serial.
    Existing receipts are expected to use values such as M-559 or M 559.
    """
    try:
        df = get_receipts()

        if df.empty or "Receipt No" not in df.columns:
            return STARTING_RECEIPT_NO

        numbers = df["Receipt No"].astype(str).str.extract(r"(\d+)", expand=False)

        numbers = pd.to_numeric(numbers, errors="coerce").dropna()

        if numbers.empty:
            return STARTING_RECEIPT_NO

        return max(STARTING_RECEIPT_NO, int(numbers.max()) + 1)

    except Exception:
        return STARTING_RECEIPT_NO


def receipt_display_no(serial):
    return f"{RECEIPT_PREFIX}-{int(serial)}"


# ============================================================
# VALIDATION
# ============================================================


def validate_name(name):
    name = name.strip()

    if not name:
        return False, "Name cannot be empty."

    # Allows English letters, spaces, dots, apostrophes and hyphens.
    if not re.fullmatch(r"[A-Za-z .'\-]+", name):
        return (
            False,
            "Name can contain letters, spaces, dots, apostrophes and hyphens only.",
        )

    return True, ""


def validate_phone(phone):
    phone = phone.strip()

    if not phone:
        return True, ""

    if not phone.isdigit():
        return False, "Phone number can contain numbers only."

    if len(phone) != 10:
        return False, "Phone number must contain exactly 10 digits."

    return True, ""


# ============================================================
# NUMBER TO WORDS - INDIAN NUMBERING
# ============================================================


def number_to_words(number):
    ones = [
        "",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]

    tens = [
        "",
        "",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety",
    ]

    def under_thousand(n):
        words = ""

        if n >= 100:
            words += ones[n // 100] + " Hundred"
            n %= 100
            if n:
                words += " "

        if n >= 20:
            words += tens[n // 10]
            n %= 10
            if n:
                words += " " + ones[n]
        elif n > 0:
            words += ones[n]

        return words

    number = round(float(number), 2)
    rupees = int(number)
    paise = int(round((number - rupees) * 100))

    if rupees == 0:
        rupees_words = "Zero"
    else:
        parts = []

        crore = rupees // 10000000
        rupees %= 10000000

        lakh = rupees // 100000
        rupees %= 100000

        thousand = rupees // 1000
        rupees %= 1000

        if crore:
            parts.append(under_thousand(crore) + " Crore")
        if lakh:
            parts.append(under_thousand(lakh) + " Lakh")
        if thousand:
            parts.append(under_thousand(thousand) + " Thousand")
        if rupees:
            parts.append(under_thousand(rupees))

        rupees_words = " ".join(parts)

    if paise:
        return f"{rupees_words} Rupees and {under_thousand(paise)} Paise Only"

    return f"{rupees_words} Rupees Only"


# ============================================================
# PDF RECEIPT GENERATOR
# ============================================================


def generate_receipt_pdf(
    receipt_serial,
    received_from,
    house_no,
    amount,
    purpose,
    month_from,
    month_to,
    payment_mode,
    date_value,
):
    buffer = BytesIO()

    receipt_width = 190 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=(receipt_width, 135 * mm),
        rightMargin=7 * mm,
        leftMargin=7 * mm,
        topMargin=6 * mm,
        bottomMargin=6 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=19,
        alignment=TA_CENTER,
        spaceAfter=1,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
    )

    small_center = ParagraphStyle(
        "SmallCenter",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        alignment=TA_CENTER,
    )

    normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
    )

    normal_right = ParagraphStyle(
        "NormalRight",
        parent=normal,
        alignment=TA_RIGHT,
    )

    label = ParagraphStyle(
        "Label",
        parent=normal,
        fontName="Helvetica-Bold",
    )

    amount_style = ParagraphStyle(
        "Amount",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_RIGHT,
    )

    words_style = ParagraphStyle(
        "Words",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
    )

    story = []

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    receipt_no = receipt_display_no(receipt_serial)

    header_data = [
        [
            Paragraph("<b>Welfare Receipt No.:</b>", normal),
            Paragraph(receipt_no, label),
        ]
    ]

    header_table = Table(header_data, colWidths=[45 * mm, 35 * mm])

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    story.append(header_table)
    story.append(Spacer(1, 1))

    story.append(Paragraph(MASJID_NAME, title_style))
    story.append(Paragraph(MASJID_ADDRESS, subtitle_style))
    story.append(
        Paragraph(
            f"{MASJID_BANK} | A/C No. {MASJID_ACCOUNT} | IFSC: {MASJID_IFSC}",
            small_center,
        )
    )

    story.append(Spacer(1, 3))

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.black,
            spaceBefore=1,
            spaceAfter=4,
        )
    )

    # --------------------------------------------------------
    # MAIN RECEIPT CONTENT
    # --------------------------------------------------------

    content = [
        [
            Paragraph("<b>S.No.</b>", normal),
            Paragraph(receipt_no, label),
            Paragraph("<b>Dated:</b>", normal),
            Paragraph(date_value, normal),
        ],
        [
            Paragraph("<b>Received with Thanks From</b>", normal),
            Paragraph(received_from, normal),
            Paragraph("<b>House No.</b>", normal),
            Paragraph(house_no or "—", normal),
        ],
        [
            Paragraph("<b>The Sum of Rupees</b>", normal),
            Paragraph(f"₹ {amount:,.2f}", amount_style),
            "",
            "",
        ],
        [
            Paragraph("<b>On Account of</b>", normal),
            Paragraph(purpose, normal),
            "",
            "",
        ],
        [
            Paragraph("<b>For the Month of</b>", normal),
            Paragraph(month_from, normal),
            Paragraph("<b>To</b>", normal),
            Paragraph(month_to, normal),
        ],
        [
            Paragraph("<b>Payment Mode</b>", normal),
            Paragraph(payment_mode, normal),
            "",
            "",
        ],
    ]

    content_table = Table(
        content,
        colWidths=[35 * mm, 78 * mm, 25 * mm, 45 * mm],
    )

    content_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            # Merge cells for long fields.
            ("SPAN", (1, 2), (3, 2)),
            ("SPAN", (1, 3), (3, 3)),
            ("SPAN", (1, 5), (3, 5)),
        ])
    )

    story.append(content_table)
    story.append(Spacer(1, 3))

    # --------------------------------------------------------
    # AMOUNT IN WORDS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            f"<b>Amount in Words:</b> {number_to_words(amount)}",
            words_style,
        )
    )

    story.append(Spacer(1, 3))

    # --------------------------------------------------------
    # SIGNATURE + BANK DETAILS
    # --------------------------------------------------------

    footer_table = Table(
        [
            [
                Paragraph(
                    f"<b>Bank Details:</b> {MASJID_BANK}<br/>"
                    f"A/C No.: {MASJID_ACCOUNT}<br/>"
                    f"IFSC: {MASJID_IFSC}",
                    small_center,
                ),
                Paragraph(
                    "Signature<br/><br/>________________________",
                    small_center,
                ),
            ]
        ],
        colWidths=[105 * mm, 78 * mm],
    )

    footer_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ])
    )

    story.append(footer_table)

    story.append(Spacer(1, 2))

    story.append(
        Paragraph(
            "This receipt is issued for Masjid welfare / contribution records.",
            small_center,
        )
    )

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# SAVE RECEIPT TO GOOGLE SHEETS
# ============================================================


def save_receipt(
    receipt_serial,
    transaction_id,
    received_from,
    house_no,
    amount,
    purpose,
    month_from,
    month_to,
    payment_mode,
    phone,
    date_value,
):
    receipt_no = receipt_display_no(receipt_serial)

    existing = conn.read(worksheet="Receipts", ttl=0)

    if not existing.empty:
        if "Transaction ID" in existing.columns:
            if existing["Transaction ID"].astype(str).eq(str(transaction_id)).any():
                return False, "This receipt has already been saved."

        if "Receipt No" in existing.columns:
            if existing["Receipt No"].astype(str).eq(receipt_no).any():
                return False, f"Receipt No. {receipt_no} already exists."

    new_row = pd.DataFrame([
        {
            "Receipt No": receipt_no,
            "Transaction ID": transaction_id,
            "Date": date_value,
            "Received From": received_from,
            "House No": house_no,
            "Amount": float(amount),
            "Purpose": purpose,
            "Month From": month_from,
            "Month To": month_to,
            "Payment Mode": payment_mode,
            "Phone": phone,
            "Status": "Saved",
        }
    ])

    if existing.empty:
        final_data = new_row
    else:
        final_data = pd.concat([existing, new_row], ignore_index=True)

    columns = [
        "Receipt No",
        "Transaction ID",
        "Date",
        "Received From",
        "House No",
        "Amount",
        "Purpose",
        "Month From",
        "Month To",
        "Payment Mode",
        "Phone",
        "Status",
    ]

    for col in columns:
        if col not in final_data.columns:
            final_data[col] = ""

    final_data = final_data[columns]

    conn.update(worksheet="Receipts", data=final_data)
    get_receipts.clear()

    return True, "Receipt saved successfully."


# ============================================================
# SESSION STATE
# ============================================================

if "receipt_serial" not in st.session_state:
    st.session_state.receipt_serial = get_next_receipt_serial()

if "transaction_id" not in st.session_state:
    st.session_state.transaction_id = str(uuid.uuid4())

if "receipt_saved" not in st.session_state:
    st.session_state.receipt_saved = False

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

if "generated_receipt_no" not in st.session_state:
    st.session_state.generated_receipt_no = None


# ============================================================
# HEADER
# ============================================================

st.title("🕌 Al Rehman Welfare Receipt System")
st.caption(
    "Digital receipt generation, Google Sheets records and printable PDF receipts"
)


# ============================================================
# SIDEBAR - MASJID + RECEIPT SETTINGS
# ============================================================
with st.sidebar:
    st.header("🔐 Collector")

    if st.button("🔒 Logout", width="stretch"):
        st.session_state.authenticated = False
        st.rerun()

    st.divider()
    st.header("🕌 Masjid Details")

    st.text_input("Masjid Name", value=MASJID_NAME, disabled=True)
    st.text_input("Address", value=MASJID_ADDRESS, disabled=True)
    st.text_input("Bank", value=MASJID_BANK, disabled=True)
    st.text_input("A/C No.", value=MASJID_ACCOUNT, disabled=True)
    st.text_input("IFSC", value=MASJID_IFSC, disabled=True)

    st.divider()

    st.header("🧾 Receipt")
    st.info(f"Next Receipt: **{receipt_display_no(st.session_state.receipt_serial)}**")

    st.caption(
        "The supplied physical receipt shows S.No. M 559, so the digital system "
        "starts from M-559 unless existing Google Sheet records require a higher number."
    )


# ============================================================
# RECEIPT FORM
# ============================================================

st.header("Create Welfare Receipt")

col1, col2 = st.columns(2)

with col1:
    received_from = st.text_input(
        "Received with Thanks From *",
        placeholder="e.g. Mohammad Amaan",
    )

    house_no = st.text_input(
        "House No.",
        placeholder="e.g. 42",
    )

    amount = st.number_input(
        "Amount (₹) *",
        min_value=0.0,
        value=0.0,
        step=100.0,
    )

    phone = st.text_input(
        "Phone / WhatsApp Number",
        max_chars=10,
        placeholder="10-digit number",
    )

with col2:
    purpose = st.selectbox(
        "On Account of *",
        [
            "Monthly Contribution",
            "Donation",
            "Fire Wood",
            "Masjid Welfare",
            "Other",
        ],
    )

    if purpose == "Other":
        purpose_other = st.text_input("Specify Purpose")
        selected_purpose = purpose_other.strip()
    else:
        selected_purpose = purpose

    month_from = st.date_input(
        "For the Month - From",
        value=datetime.now().date(),
        format="DD/MM/YYYY",
    )

    month_to = st.date_input(
        "To",
        value=datetime.now().date(),
        format="DD/MM/YYYY",
    )

    payment_mode = st.selectbox(
        "Payment Mode",
        ["Cash", "UPI", "Bank Transfer", "Cheque", "Other"],
    )

date_value = st.date_input(
    "Receipt Date",
    value=datetime.now().date(),
    format="DD/MM/YYYY",
)

# ============================================================
# LIVE PREVIEW
# ============================================================

st.divider()
st.subheader("Receipt Summary")

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric("Receipt No.", receipt_display_no(st.session_state.receipt_serial))

with summary_col2:
    st.metric("Amount", f"₹{amount:,.2f}")

with summary_col3:
    st.metric("Purpose", selected_purpose or "—")

with summary_col4:
    st.metric("Payment", payment_mode)


st.write(
    f"**Amount in Words:** {number_to_words(amount) if amount > 0 else 'Zero Rupees Only'}"
)


# ============================================================
# GENERATE RECEIPT
# ============================================================

st.divider()
st.header("Generate Receipt")

generate_receipt = st.button(
    "🧾 Generate & Save Receipt",
    type="primary",
    width="stretch",
)

if generate_receipt:
    name_ok, name_error = validate_name(received_from)
    phone_ok, phone_error = validate_phone(phone)

    if not name_ok:
        st.error(f"❌ {name_error}")

    elif not phone_ok:
        st.error(f"❌ {phone_error}")

    elif amount <= 0:
        st.error("❌ Please enter an amount greater than ₹0.")

    elif not selected_purpose:
        st.error("❌ Please select or enter the purpose.")

    elif month_to < month_from:
        st.error("❌ 'To' date cannot be earlier than 'From' date.")

    elif st.session_state.receipt_saved:
        st.warning(
            f"Receipt {receipt_display_no(st.session_state.receipt_serial)} "
            "has already been generated."
        )

    else:
        try:
            serial = st.session_state.receipt_serial
            receipt_no = receipt_display_no(serial)

            pdf_bytes = generate_receipt_pdf(
                receipt_serial=serial,
                received_from=received_from.strip(),
                house_no=house_no.strip(),
                amount=amount,
                purpose=selected_purpose,
                month_from=month_from.strftime("%d/%m/%Y"),
                month_to=month_to.strftime("%d/%m/%Y"),
                payment_mode=payment_mode,
                date_value=date_value.strftime("%d/%m/%Y"),
            )

            saved, message = save_receipt(
                receipt_serial=serial,
                transaction_id=st.session_state.transaction_id,
                received_from=received_from.strip(),
                house_no=house_no.strip(),
                amount=amount,
                purpose=selected_purpose,
                month_from=month_from.strftime("%d/%m/%Y"),
                month_to=month_to.strftime("%d/%m/%Y"),
                payment_mode=payment_mode,
                phone=phone.strip(),
                date_value=date_value.strftime("%d/%m/%Y"),
            )

            if saved:
                st.session_state.pdf_bytes = pdf_bytes
                st.session_state.generated_receipt_no = receipt_no
                st.session_state.receipt_saved = True

                st.success(
                    f"✅ Receipt {receipt_no} generated and saved to Google Sheets."
                )

            else:
                st.error(f"❌ {message}")

        except Exception as e:
            st.error("❌ Receipt generation failed.")
            st.error(f"Details: {e}")


# ============================================================
# RECEIPT READY / DOWNLOAD
# ============================================================

if st.session_state.pdf_bytes:
    st.divider()
    st.subheader("📄 Receipt Ready")

    safe_name = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        received_from.strip() or "Donor",
    ).strip("_")

    filename = f"Masjid_Receipt_{st.session_state.generated_receipt_no}_{safe_name}.pdf"

    st.download_button(
        "⬇️ Download Receipt PDF",
        data=st.session_state.pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        width="stretch",
    )

    # --------------------------------------------------------
    # WHATSAPP
    # --------------------------------------------------------

    whatsapp_number = "".join(c for c in phone if c.isdigit())

    if len(whatsapp_number) == 10:
        whatsapp_number = "91" + whatsapp_number

    if whatsapp_number:
        whatsapp_message = (
            f"Assalamu Alaikum {received_from},\n\n"
            f"Thank you for your contribution to {MASJID_NAME}.\n\n"
            f"Welfare Receipt: {st.session_state.generated_receipt_no}\n"
            f"Amount: ₹{amount:,.2f}\n"
            f"Purpose: {selected_purpose}\n"
            f"Date: {date_value.strftime('%d/%m/%Y')}\n\n"
            f"JazakAllah Khair."
        )

        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={quote(whatsapp_message)}"

        st.markdown(
            f"""
            <a href="{whatsapp_url}" target="_blank">
                <button style="
                    width: 100%;
                    padding: 12px;
                    background-color: #25D366;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                ">
                    📱 Open WhatsApp Message
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "WhatsApp opens with the message prepared. "
            "Download the PDF above, attach it in WhatsApp and send it."
        )


# ============================================================
# RECEIPT HISTORY
# ============================================================

st.divider()
st.header("📊 Receipt History")

history_col1, history_col2 = st.columns([1, 1])

with history_col1:
    refresh_history = st.button(
        "🔄 Refresh Receipt History",
        width="stretch",
    )

if refresh_history:
    get_receipts.clear()

receipts_df = get_receipts()

if receipts_df.empty:
    st.info("No receipts found in the Google Sheets 'Receipts' worksheet yet.")
else:
    display_df = receipts_df.copy()

    if "Amount" in display_df.columns:
        display_df["Amount"] = pd.to_numeric(
            display_df["Amount"], errors="coerce"
        ).fillna(0.0)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )

    excel_buffer = BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        display_df.to_excel(
            writer,
            index=False,
            sheet_name="Receipts",
        )

    excel_buffer.seek(0)

    st.download_button(
        "⬇️ Download Receipt Databook",
        data=excel_buffer,
        file_name="Masjid_Sharief_Receipt_Databook.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )


# ============================================================
# SUMMARY
# ============================================================

if not receipts_df.empty:
    st.divider()
    st.subheader("📈 Collection Summary")

    total_collection = (
        pd
        .to_numeric(
            receipts_df.get("Amount", pd.Series(dtype=float)),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )

    total_receipts = len(receipts_df)

    summary1, summary2 = st.columns(2)

    with summary1:
        st.metric("Total Receipts", total_receipts)

    with summary2:
        st.metric("Total Collection", f"₹{total_collection:,.2f}")


# ============================================================
# NEW RECEIPT
# ============================================================

st.divider()


def reset_new_receipt():
    st.session_state.receipt_serial = get_next_receipt_serial()
    st.session_state.transaction_id = str(uuid.uuid4())
    st.session_state.receipt_saved = False
    st.session_state.pdf_bytes = None
    st.session_state.generated_receipt_no = None


st.button(
    "🔄 Start New Receipt",
    on_click=reset_new_receipt,
    width="stretch",
)
