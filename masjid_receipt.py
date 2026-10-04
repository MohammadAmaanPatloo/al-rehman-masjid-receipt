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
    Image as RLImage,
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
from xml.sax.saxutils import escape


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Masjid Sharief Receipt",
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
    st.subheader("Masjid Receipt System")

    st.info("🔐 Please enter the collector password to continue.")

    # Login form
    with st.form("login_form"):
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter collector password",
        )

        login = st.form_submit_button(
            "🔓 Login",
            type="primary",
            width="stretch",
        )

    if login:
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

    /* =========================================================
       GLOBAL UI
       ========================================================= */

    [data-testid="InputInstructions"] {
        display: none !important;
    }

    .receipt-card {
        padding: 0;
        border: none;
        border-radius: 0;
        margin-bottom: 12px;
    }    
    
    .expense-card {
        padding: 0;
        border: none;
        border-radius: 0;
        margin-bottom: 12px;
    }
    
    /* ============================================================
    MONTHLY ACCOUNTS
    ============================================================ */

    .account-card {
        padding: 0;
        border: none;
        border-radius: 0;
        margin-bottom: 12px;
    }

    .account-section-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .account-total {
        padding: 10px 12px;
        border-radius: 8px;
        font-weight: 600;
        margin-top: 8px;
    }

    @media (max-width: 768px) {

        .account-card {
            padding: 0;
            border: none;
            border-radius: 0;
            margin-bottom: 10px;
        }

        .account-section-title {
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }

        .account-total {
            padding: 9px 10px;
        }
    }

    .expense-section-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    @media (max-width: 768px) {
        .expense-card {
            padding: 0;
            border: none;
            border-radius: 0;
            margin-bottom: 10px;
        }

        .expense-section-title {
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }
    }

    .receipt-section-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    @media (max-width: 768px) {
        .receipt-card {
            padding: 0;
            border: none;
            border-radius: 0;
            margin-bottom: 10px;
        }

        .receipt-section-title {
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }
    }


    /* =========================================================
       MOBILE
       ========================================================= */

    @media (max-width: 768px) {

        /* -----------------------------------------------------
           Main page spacing
           ----------------------------------------------------- */

        .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
            padding-top: 0.75rem;
            padding-bottom: 2rem;
        }


        /* -----------------------------------------------------
           Headings
           ----------------------------------------------------- */

        h1 {
            font-size: 1.55rem !important;
            line-height: 1.3 !important;
            margin-top: 0.25rem !important;
            margin-bottom: 0.75rem !important;
            padding-top: 0.15rem !important;
            overflow: visible !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }

        h2 {
            font-size: 1.3rem !important;
            line-height: 1.25 !important;
        }

        h3 {
            font-size: 1.15rem !important;
            line-height: 1.25 !important;
        }


        /* -----------------------------------------------------
           Buttons
           ----------------------------------------------------- */

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            min-height: 46px;
            font-size: 15px;
        }


        /* -----------------------------------------------------
           Inputs
           
           16px prevents automatic zooming on many phones.
           ----------------------------------------------------- */

        input,
        textarea,
        [data-baseweb="select"] {
            font-size: 16px !important;
        }


        /* -----------------------------------------------------
           Reduce excessive vertical spacing
           ----------------------------------------------------- */

        [data-testid="stVerticalBlock"] {
            gap: 0.65rem;
        }


        /* -----------------------------------------------------
           Metrics
           ----------------------------------------------------- */

        [data-testid="stMetric"] {
            padding: 5px;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.15rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }

        [data-testid="stMetric"] {
            padding: 5px;
            margin-bottom: 8px;
        }

        /* -----------------------------------------------------
        Dataframes / tables
        ----------------------------------------------------- */

        [data-testid="stDataFrame"] {
            font-size: 12px;
        }




        /* -----------------------------------------------------
           Dividers
           ----------------------------------------------------- */

        hr {
            margin-top: 0.75rem;
            margin-bottom: 0.75rem;
        }


        /* -----------------------------------------------------
           Sidebar
           ----------------------------------------------------- */

        section[data-testid="stSidebar"] {
            width: 85vw !important;
            max-width: 340px !important;
        }


        /* -----------------------------------------------------
           Receipt card
           ----------------------------------------------------- */

        .receipt-card {
            padding: 12px;
            border-radius: 8px;
        }
    }


    /* =========================================================
       SMALL PHONES
       ========================================================= */

    @media (max-width: 480px) {

        .block-container {
            padding-left: 0.55rem;
            padding-right: 0.55rem;
        }

        h1 {
            font-size: 1.4rem !important;
            line-height: 1.3 !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.65rem !important;
            padding-top: 0.1rem !important;
            overflow: visible !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }

        h2 {
            font-size: 1.2rem !important;
        }

        h3 {
            font-size: 1.05rem !important;
        }


        [data-testid="stMetricValue"] {
            font-size: 1rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
        }


        .stButton > button,
        .stDownloadButton > button {
            min-height: 48px;
            font-size: 14px;
        }
    }
    /* =========================================================
    RECEIPT ACTION BUTTONS
    ========================================================= */

    .receipt-whatsapp-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        min-height: 48px;
        padding: 12px 16px;
        background-color: #25D366;
        color: #ffffff !important;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        text-align: center;
        text-decoration: none !important;
        box-sizing: border-box;
    }

    .receipt-whatsapp-button:hover {
        background-color: #1DA851;
        color: #ffffff !important;
    }

    @media (max-width: 480px) {
        .receipt-whatsapp-button {
            min-height: 50px;
            font-size: 15px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)
# ============================================================
# MASJID SETTINGS
# Based on the supplied physical masjid receipt
# ============================================================

MASJID_NAME = "AL Rehman Masjid Sharief"
MASJID_ADDRESS = "Sir Syed Colony, Upper Soura, Srinagar, J&K"
MASJID_BANK = "J&K Bank, Soura"
MASJID_ACCOUNT = "0204040100000553"
MASJID_IFSC = "JAKA0SOOURA"

# The supplied receipt visibly shows "S.No. M 1001".
# The system starts from 515 and increments automatically.
RECEIPT_PREFIX = "M"
STARTING_RECEIPT_NO = 515

# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================

conn = st.connection("gsheets", type=GSheetsConnection)

# ============================================================
# CACHE SYNC TRACKING
# ============================================================

CACHE_SYNC_TIMES = {}


def mark_cache_synced(name):
    CACHE_SYNC_TIMES[name] = datetime.now()


def get_last_synced():
    if not CACHE_SYNC_TIMES:
        return "Not synced yet"

    latest = max(CACHE_SYNC_TIMES.values())

    return latest.strftime("%d-%m-%Y %I:%M:%S %p")


# ============================================================
# CACHE MANAGEMENT
# ============================================================


def refresh_google_sheets():
    """
    Clear all Google Sheets data caches.

    Use this only when a complete manual refresh is required.
    Normal save operations should clear only the cache
    related to the sheet that was changed.
    """

    try:
        get_receipts.clear()
    except Exception:
        pass

    try:
        get_masjid_residents.clear()
    except Exception:
        pass

    try:
        get_expenses.clear()
    except Exception:
        pass

    try:
        get_monthly_accounts.clear()
    except Exception:
        pass

    try:
        get_monthly_receipts.clear()
    except Exception:
        pass

    try:
        get_monthly_expenses.clear()
    except Exception:
        pass

    try:
        calculate_monthly_income.clear()
    except Exception:
        pass

    try:
        calculate_monthly_expenses.clear()
    except Exception:
        pass


def clear_receipt_cache():
    """
    Clear only caches affected by a receipt change.
    """

    try:
        get_receipts.clear()
    except Exception:
        pass

    try:
        get_monthly_receipts.clear()
    except Exception:
        pass

    try:
        calculate_monthly_income.clear()
    except Exception:
        pass


def clear_resident_cache():
    """
    Clear only caches affected by resident changes.
    """

    try:
        get_masjid_residents.clear()
    except Exception:
        pass


def clear_expense_cache():
    """
    Clear only caches affected by an expense change.
    """

    try:
        get_expenses.clear()
    except Exception:
        pass

    try:
        get_monthly_expenses.clear()
    except Exception:
        pass

    try:
        calculate_monthly_expenses.clear()
    except Exception:
        pass


def clear_monthly_account_cache():
    """
    Clear only caches affected by monthly account changes.
    """

    try:
        get_monthly_accounts.clear()
    except Exception:
        pass


# ============================================================
# GOOGLE SHEETS HELPERS
# ============================================================


@st.cache_data(ttl=120)
def get_receipts():
    try:
        df = conn.read(worksheet="Receipts", ttl=120)
        mark_cache_synced("Receipts")

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
            "Monthly Contribution Paid Upto",
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

        if "Date" in df.columns:
            df["_Parsed Date"] = pd.to_datetime(
                df["Date"],
                dayfirst=True,
                errors="coerce",
            )

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120)
def get_masjid_residents():
    try:
        df = conn.read(
            worksheet="Masjid Residents",
            ttl=120,
        )
        mark_cache_synced("Masjid Residents")

        if df.empty:
            return pd.DataFrame()

        # Clean column names
        df.columns = df.columns.astype(str).str.strip()

        # Clean values
        for col in [
            "H No.",
            "Name",
            "Phone Number",
            "Monthly Contribution Paid Upto",
            "Fire Wood Contribution Paid Upto",
        ]:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .fillna("")
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

        return df

    except Exception as e:
        st.error(f"Could not load Masjid Residents: {e}")
        return pd.DataFrame()


residents_df = get_masjid_residents()

# ============================================================
# Masjid Monthly - GOOGLE SHEETS STATEMENT
# ============================================================

MASJID_MONTHY_SHEET = "Masjid Monthly"


def save_masjid_monthy_statement(
    month_name,
    year,
    opening_cash,
    opening_bank,
    additions_during_month,
    monthly_contribution,
    friday_idd,
    donation,
    recovery,
    fire_wood,
    salary_khadim,
    salary_imam,
    masjid_electricity,
    darasgah_electricity,
    other_expenses,
    deposits_credits,
    withdrawals_debits,
    closing_bank,
    closing_cash,
):
    try:
        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet(MASJID_MONTHY_SHEET)

        month_text = f"{month_name} {year}"

        title = f"Income Expenditure details for month of {month_text}"

        # ---------------------------------------------------------
        # TOTALS
        # ---------------------------------------------------------

        total_income = opening_cash + additions_during_month + opening_bank

        total_expenses = (
            salary_khadim
            + salary_imam
            + masjid_electricity
            + darasgah_electricity
            + other_expenses
        )

        total_statement = total_expenses + closing_bank + closing_cash

        # ---------------------------------------------------------
        # HEADER
        # New layout:
        #
        # A = Income Particulars
        # B = Income Amount
        # C = Separator
        # D = Expense Particulars
        # E = Expense Amount
        # ---------------------------------------------------------

        worksheet.update(
            values=[[title]],
            range_name="A1",
        )

        worksheet.update(
            values=[["Income Side"]],
            range_name="A2",
        )

        worksheet.update(
            values=[["Expenses Side"]],
            range_name="D2",
        )

        worksheet.update(
            values=[["Particulars", "Amount"]],
            range_name="A3:B3",
        )

        worksheet.update(
            values=[["Particulars", "Amount"]],
            range_name="D3:E3",
        )

        # ---------------------------------------------------------
        # INCOME SIDE
        # A = Particulars
        # B = Amount
        # ---------------------------------------------------------

        income_values = [
            ["Last Months Cash in Hand", opening_cash],  # Row 4
            ["Additions During the month", additions_during_month],  # Row 5
            ["", ""],  # Row 6
            ["a) Monthly Contribution", monthly_contribution],  # Row 7
            ["b) Friday Collections", friday_idd],  # Row 8
            ["c) Donation", donation],  # Row 9
            ["", ""],  # Row 10
            ["Recovery from Imaam Sahib", recovery],  # Row 11
            ["Fire Wood Contribution", fire_wood],  # Row 12
            [
                "Last Months Balance in Bank excluding Interest",
                opening_bank,
            ],  # Row 13
            ["Total", total_income],  # Row 14
        ]

        worksheet.update(
            values=income_values,
            range_name="A4:B14",
        )

        # ---------------------------------------------------------
        # EXPENSE SIDE
        # D = Particulars
        # E = Amount
        # ---------------------------------------------------------

        expense_values = [
            ["Salary Paid to Khadim Sahib.", salary_khadim],  # Row 4
            ["Salary Paid to Imam Sahib.", salary_imam],  # Row 5
            ["a) Masjid Electricity Paid", masjid_electricity],  # Row 6
            ["b) Darasgah Electricity Paid", darasgah_electricity],  # Row 7
            ["Amount Credited to Bank", deposits_credits],  # Row 8
            ["Amount Debited from Bank", withdrawals_debits],  # Row 9
            ["", ""],  # Row 10
            ["", ""],  # Row 11
            [
                "Balance with J&K Bank excluding Interest",
                closing_bank,
            ],  # Row 12
            ["Cash in Hand", closing_cash],  # Row 13
            ["Total", total_statement],  # Row 14
        ]

        worksheet.update(
            values=expense_values,
            range_name="D4:E14",
        )

        # ---------------------------------------------------------
        # BOLD HEADINGS
        # ---------------------------------------------------------

        worksheet.format(
            "A2",
            {"textFormat": {"bold": True}},
        )

        worksheet.format(
            "D2",
            {"textFormat": {"bold": True}},
        )

        worksheet.format(
            "A3:B3",
            {"textFormat": {"bold": True}},
        )

        worksheet.format(
            "D3:E3",
            {"textFormat": {"bold": True}},
        )

        # Bold Income Total
        worksheet.format(
            "A14:B14",
            {"textFormat": {"bold": True}},
        )

        # Bold Expenses Total
        worksheet.format(
            "D14:E14",
            {"textFormat": {"bold": True}},
        )
        # Make title bold as well
        worksheet.format(
            "A1",
            {"textFormat": {"bold": True}},
        )

        return True, f"{month_text} saved successfully to Masjid Monthly."

    except Exception as e:
        return False, f"Failed to save Masjid Monthly statement: {e}"


def select_resident_by_name():
    selected_name = st.session_state.selected_resident_name

    # ----------------------------------------------------
    # NON RESIDENT
    # ----------------------------------------------------
    if selected_name == "➕ Non Resident":
        st.session_state.selected_resident_house = "-- Select House No. --"
        st.session_state.resident_phone = ""
        st.session_state.resident_paid_upto = ""
        st.session_state.resident_firewood_paid_upto = ""
        return

    # ----------------------------------------------------
    # NO RESIDENT SELECTED
    # ----------------------------------------------------
    if selected_name == "-- Select Resident --":
        st.session_state.selected_resident_house = "-- Select House No. --"
        st.session_state.resident_phone = ""
        st.session_state.resident_paid_upto = ""
        st.session_state.resident_firewood_paid_upto = ""
        return

    # ----------------------------------------------------
    # NORMAL RESIDENT
    # ----------------------------------------------------
    match = residents_df[residents_df["Name"].astype(str).str.strip() == selected_name]

    if not match.empty:
        resident = match.iloc[0]

        st.session_state.selected_resident_house = str(resident["H No."]).strip()

        st.session_state.resident_phone = str(resident["Phone Number"]).strip()

        st.session_state.resident_paid_upto = str(
            resident.get("Monthly Contribution Paid Upto", "")
        ).strip()

        firewood_paid_upto = resident.get("Fire Wood Contribution Paid Upto", "")

        if pd.isna(firewood_paid_upto):
            firewood_paid_upto = ""

        st.session_state.resident_firewood_paid_upto = (
            str(firewood_paid_upto).replace(".0", "").strip()
        )


def select_resident_by_house():
    selected_house = st.session_state.selected_resident_house

    if selected_house == "-- Select House No. --":
        st.session_state.selected_resident_name = "-- Select Resident --"
        st.session_state.resident_phone = ""
        st.session_state.resident_paid_upto = ""
        st.session_state.resident_firewood_paid_upto = ""
        return

    match = residents_df[
        residents_df["H No."].astype(str).str.strip() == selected_house
    ]

    if not match.empty:
        resident = match.iloc[0]

        st.session_state.selected_resident_name = str(resident["Name"]).strip()

        st.session_state.resident_phone = str(resident["Phone Number"]).strip()

        st.session_state.resident_paid_upto = str(
            resident.get("Monthly Contribution Paid Upto", "")
        ).strip()

        firewood_paid_upto = resident.get("Fire Wood Contribution Paid Upto", "")

        if pd.isna(firewood_paid_upto):
            firewood_paid_upto = ""

        st.session_state.resident_firewood_paid_upto = (
            str(firewood_paid_upto).replace(".0", "").strip()
        )


def update_resident_paid_upto(received_from, house_no, month_to):
    """
    Update only the Monthly Contribution Paid Upto cell
    for the matching resident.
    """

    try:
        residents = get_masjid_residents()

        if residents.empty:
            return False, "Masjid Residents sheet is empty."

        required_columns = [
            "Name",
            "H No.",
            "Monthly Contribution Paid Upto",
        ]

        missing_columns = [
            column for column in required_columns if column not in residents.columns
        ]

        if missing_columns:
            return (
                False,
                f"Missing Residents sheet columns: {', '.join(missing_columns)}",
            )

        target_name = str(received_from).strip()
        target_house = str(house_no).strip()

        names = residents["Name"].fillna("").astype(str).str.strip()

        houses = (
            residents["H No."]
            .fillna("")
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )

        match = names.eq(target_name) & houses.eq(target_house)

        if not match.any():
            return (
                False,
                f"Resident '{target_name}' (House No. {target_house}) was not found.",
            )

        # Google Sheets row = DataFrame row + header row
        row_number = int(match[match].index[0]) + 2

        # Google Sheets column number
        column_number = residents.columns.get_loc("Monthly Contribution Paid Upto") + 1

        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet("Masjid Residents")

        # Update ONLY the required cell
        worksheet.update_cell(
            row_number,
            column_number,
            month_to,
        )

        clear_resident_cache()

        return True, f"Paid Upto updated to {month_to}."

    except Exception as e:
        return False, str(e)


def update_resident_firewood_paid_upto(
    received_from,
    house_no,
    firewood_year,
):
    """
    Update only the Fire Wood Contribution Paid Upto cell
    for the matching resident.
    """

    try:
        residents = get_masjid_residents()

        if residents.empty:
            return False, "Masjid Residents sheet is empty."

        required_columns = [
            "Name",
            "H No.",
            "Fire Wood Contribution Paid Upto",
        ]

        missing_columns = [
            column for column in required_columns if column not in residents.columns
        ]

        if missing_columns:
            return (
                False,
                f"Missing Residents sheet columns: {', '.join(missing_columns)}",
            )

        target_name = str(received_from).strip()
        target_house = str(house_no).strip()

        names = residents["Name"].fillna("").astype(str).str.strip()

        houses = (
            residents["H No."]
            .fillna("")
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )

        match = names.eq(target_name) & houses.eq(target_house)

        if not match.any():
            return (
                False,
                f"Resident '{target_name}' (House No. {target_house}) was not found.",
            )

        row_number = int(match[match].index[0]) + 2

        column_number = (
            residents.columns.get_loc("Fire Wood Contribution Paid Upto") + 1
        )

        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet("Masjid Residents")

        # Update ONLY the required cell
        worksheet.update_cell(
            row_number,
            column_number,
            firewood_year,
        )

        clear_resident_cache()

        return (
            True,
            f"Fire Wood Contribution Paid Upto updated to {firewood_year}.",
        )

    except Exception as e:
        return False, str(e)


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
def generate_receipt_pdf(
    receipt_serial,
    received_from,
    house_no,
    phone,
    amount,
    purpose,
    month_from,
    month_to,
    payment_mode,
    date_value,
    firewood_year,
    address="",
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

    # Masjid Logo
    logo = RLImage(
        "masjid_logo.jpeg",
        width=30 * mm,
        height=18 * mm,
    )

    logo.hAlign = "CENTER"

    story.append(logo)
    story.append(Spacer(1, 2))

    # Masjid Name
    story.append(
        Paragraph(
            escape(MASJID_NAME),
            title_style,
        )
    )

    # Masjid Address
    story.append(
        Paragraph(
            escape(MASJID_ADDRESS),
            subtitle_style,
        )
    )

    # Bank Details
    story.append(
        Paragraph(
            escape(f"{MASJID_BANK} | A/C No. {MASJID_ACCOUNT} | IFSC: {MASJID_IFSC}"),
            small_center,
        )
    )

    # # --------------------------------------------------------
    # # HEADER
    # # --------------------------------------------------------

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
            Paragraph("<b>Received From</b>", normal),
            Paragraph(
                received_from
                if received_from.strip().lower() == "Jamaat"
                else f"Mr. {received_from}",
                normal,
            ),
            Paragraph(
                "<b>Address</b>" if address else "<b>House No.</b>",
                normal,
            ),
            Paragraph(
                address if address else (house_no or "—"),
                normal,
            ),
        ],
        [
            Paragraph("<b>Phone Number</b>", normal),
            Paragraph(phone or "—", normal),
            "",
            "",
        ],
        [
            Paragraph("<b>Amount</b>", normal),
            Paragraph(f"Rs. {amount:,.2f}", amount_style),
            "",
            "",
        ],
        [
            Paragraph("<b>On Account of</b>", normal),
            Paragraph(purpose, label),
            "",
            "",
        ],
    ]

    # ------------------------------------------------------------
    # MONTH FROM / TO
    # ONLY FOR MONTHLY CONTRIBUTION
    # ------------------------------------------------------------

    if purpose == "Monthly Contribution":
        content.append([
            Paragraph("<b>Month - From</b>", normal),
            Paragraph(month_from, normal),
            Paragraph("<b>To</b>", normal),
            Paragraph(month_to, normal),
        ])

    # ------------------------------------------------------------
    # FIRE WOOD FINANCIAL YEAR
    # ONLY FOR FIRE WOOD CONTRIBUTION
    # ------------------------------------------------------------

    if purpose == "Fire Wood Contribution":
        content.append([
            Paragraph("<b>Financial Year</b>", normal),
            Paragraph(firewood_year, normal),
            "",
            "",
        ])

    # ------------------------------------------------------------
    # PAYMENT MODE
    # ------------------------------------------------------------

    content.append([
        Paragraph("<b>Payment Mode</b>", normal),
        Paragraph(payment_mode, normal),
        "",
        "",
    ])

    # ------------------------------------------------------------
    # AMOUNT IN WORDS
    # ------------------------------------------------------------

    content.append([
        Paragraph("<b>Amount in Words</b>", normal),
        Paragraph(number_to_words(amount), normal),
        "",
        "",
    ])
    content_table = Table(
        content,
        colWidths=[35 * mm, 78 * mm, 25 * mm, 45 * mm],
    )

    table_style_commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # Phone
        ("SPAN", (1, 2), (3, 2)),
        # Amount
        ("SPAN", (1, 3), (3, 3)),
        # Purpose
        ("SPAN", (1, 4), (3, 4)),
    ]

    # ------------------------------------------------------------
    # PAYMENT MODE + AMOUNT IN WORDS
    # ------------------------------------------------------------

    if purpose == "Monthly Contribution":
        # Month row = 5
        # Payment Mode row = 6
        # Amount in Words row = 7

        table_style_commands.extend([
            ("SPAN", (1, 6), (3, 6)),
            ("SPAN", (1, 7), (3, 7)),
        ])

    elif purpose == "Fire Wood Contribution":
        # Financial Year row = 5
        # Payment Mode row = 6
        # Amount in Words row = 7

        table_style_commands.extend([
            ("SPAN", (1, 5), (3, 5)),
            ("SPAN", (1, 6), (3, 6)),
            ("SPAN", (1, 7), (3, 7)),
        ])

    else:
        # Payment Mode row = 5
        # Amount in Words row = 6

        table_style_commands.extend([
            ("SPAN", (1, 5), (3, 5)),
            ("SPAN", (1, 6), (3, 6)),
        ])

    content_table = Table(
        content,
        colWidths=[35 * mm, 78 * mm, 25 * mm, 45 * mm],
    )

    content_table.setStyle(TableStyle(table_style_commands))

    story.append(content_table)
    story.append(Spacer(1, 3))

    story.append(Spacer(1, 3))

    # --------------------------------------------------------
    # FOOTER + DIGITAL SIGNATURE
    # --------------------------------------------------------

    signature_image = RLImage(
        "dad_sign.jpeg",
        width=42 * mm,
        height=16 * mm,
    )

    # Left side footer text
    footer_content = [
        Paragraph(
            "This receipt is issued for Masjid contribution records.",
            small_center,
        ),
        Spacer(1, 2),
        Paragraph(
            "Powered by MAPOS",
            small_center,
        ),
    ]

    # Right side signature
    signature_content = [
        Spacer(1, 1),
        signature_image,
        Paragraph("________________________", small_center),
        Spacer(1, 2),
        Paragraph("Signature", small_center),
    ]
    # Two-column footer
    footer_table = Table(
        [
            [
                footer_content,
                signature_content,
            ]
        ],
        colWidths=[105 * mm, 78 * mm],
    )

    footer_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            # Left footer
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            # Right signature
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    story.append(Spacer(1, 3))
    story.append(footer_table)

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
    address,
    amount,
    purpose,
    month_from,
    month_to,
    payment_mode,
    phone,
    date_value,
    firewood_year,
):
    try:
        receipt_no = receipt_display_no(receipt_serial)

        # ============================================================
        # OPEN GOOGLE SHEETS DIRECTLY
        # IMPORTANT:
        # Do NOT use cached get_receipts() for duplicate protection.
        # ============================================================

        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet("Receipts")

        # Read the latest data directly from Google Sheets
        records = worksheet.get_all_records()

        existing = pd.DataFrame(records)

        # Prevent duplicate Transaction ID
        if not existing.empty:
            if "Transaction ID" in existing.columns:
                if existing["Transaction ID"].astype(str).eq(str(transaction_id)).any():
                    return False, "This receipt has already been saved."

            # Prevent duplicate Receipt No.
            if "Receipt No" in existing.columns:
                if existing["Receipt No"].astype(str).eq(receipt_no).any():
                    return False, f"Receipt No. {receipt_no} already exists."

        # Prepare the new row
        values = [
            receipt_no,
            transaction_id,
            date_value,
            received_from,
            house_no,
            address,
            float(amount),
            purpose,
            month_from,
            month_to,
            payment_mode,
            phone,
            month_to if purpose == "Monthly Contribution" else "",
            firewood_year if purpose == "Fire Wood Contribution" else "",
            "Saved",
        ]

        # Open the Receipts worksheet
        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet("Receipts")

        # Append ONLY the new receipt
        worksheet.append_row(
            values,
            value_input_option="USER_ENTERED",
        )

        # Clear only caches affected by this receipt
        clear_receipt_cache()

        return True, "Receipt saved successfully."

    except Exception as e:
        return False, str(e)


# ============================================================
# MASJID EXPENSES
# ============================================================

EXPENSES_SHEET = "Masjid Expenses"


@st.cache_data(ttl=120)
def get_expenses():
    """
    Read all expenses from the Masjid Expenses worksheet.
    """

    try:
        df = conn.read(
            worksheet=EXPENSES_SHEET,
            ttl=120,
        )
        mark_cache_synced("Masjid Expenses")

        if df.empty:
            return pd.DataFrame()

        df.columns = df.columns.astype(str).str.strip()

        # Clean text columns
        for col in [
            "Date",
            "Expense Type",
            "Particular",
            "Payment Mode",
            "Remarks",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Clean amount
        if "Amount" in df.columns:
            df["Amount"] = pd.to_numeric(
                df["Amount"],
                errors="coerce",
            ).fillna(0.0)

        if "Date" in df.columns:
            df["_Parsed Date"] = pd.to_datetime(
                df["Date"],
                dayfirst=True,
                errors="coerce",
            )

        return df

    except Exception:
        return pd.DataFrame()


def save_expense(
    date_value,
    expense_type,
    particular,
    amount,
    payment_mode,
    remarks,
):
    try:
        # Use cached data for validation / existing records
        existing = get_expenses()

        values = [
            date_value,
            expense_type,
            particular,
            float(amount),
            payment_mode,
            remarks,
        ]

        # Open worksheet
        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet(EXPENSES_SHEET)

        # Append only this expense
        worksheet.append_row(
            values,
            value_input_option="USER_ENTERED",
        )

        # Clear only caches affected by this expense
        clear_expense_cache()

        return True, "Expense saved successfully."

    except Exception as e:
        return False, str(e)


# ============================================================
# MONTHLY ACCOUNTS
# ============================================================

MONTHLY_ACCOUNTS_SHEET = "Monthly Accounts"


MONTHLY_ACCOUNT_COLUMNS = [
    "Month",
    "Last Month Cash",
    "Monthly Contribution",
    "Friday Collections",
    "Donation",
    "Recovery from Imam Sahib",
    "Fire Wood Contribution",
    "Total Income",
    "Salary Paid to Khadim",
    "Salary Paid to Imam Sahib",
    "Masjid Electricity Paid",
    "Darasgah Electricity Paid",
    "Other Expenses",
    "Total Expenses",
    "Amount Credited to Bank",
    "Amount Debited from Bank",
    "Bank Balance",
    "Cash in Hand",
    "Closing Balance",
]


@st.cache_data(ttl=120)
def get_monthly_accounts():

    try:
        df = conn.read(
            worksheet=MONTHLY_ACCOUNTS_SHEET,
            ttl=120,
        )
        mark_cache_synced("Monthly Accounts")

        if df.empty:
            return pd.DataFrame()

        df.columns = df.columns.astype(str).str.strip()

        return df

    except Exception:
        return pd.DataFrame()


def get_previous_month_balances(selected_period):
    """
    Get the previous month's closing Cash and Bank balance.
    """

    accounts_df = get_monthly_accounts()

    if accounts_df.empty:
        return 0.0, 0.0

    if "Month" not in accounts_df.columns:
        return 0.0, 0.0

    parsed_months = pd.to_datetime(
        accounts_df["Month"],
        format="%B %Y",
        errors="coerce",
    ).dt.to_period("M")

    previous_period = selected_period - 1

    previous = accounts_df.loc[parsed_months.eq(previous_period)]

    if previous.empty:
        return 0.0, 0.0

    previous_row = previous.iloc[-1]

    previous_cash = pd.to_numeric(
        previous_row.get("Cash in Hand", 0),
        errors="coerce",
    )

    previous_bank = pd.to_numeric(
        previous_row.get("Bank Balance", 0),
        errors="coerce",
    )

    if pd.isna(previous_cash):
        previous_cash = 0.0

    if pd.isna(previous_bank):
        previous_bank = 0.0

    return float(previous_cash), float(previous_bank)


def save_monthly_account(month_data):
    """
    Save or update one month's final accounts.

    Existing month:
        Update only that row.

    New month:
        Append only the new row.
    """

    try:
        spreadsheet = conn.client._open_spreadsheet()
        worksheet = spreadsheet.worksheet(MONTHLY_ACCOUNTS_SHEET)

        month_value = str(month_data.get("Month", "")).strip()

        if not month_value:
            return False, "Month is required."

        # Build row in the exact Monthly Accounts order
        values = [month_data.get(column, 0.0) for column in MONTHLY_ACCOUNT_COLUMNS]

        # Find existing month in Column A
        existing_cell = worksheet.find(
            month_value,
            in_column=1,
        )

        if existing_cell:
            row_number = existing_cell.row

            worksheet.update(
                values=[values],
                range_name=(f"A{row_number}:S{row_number}"),
            )

            message = f"{month_value} monthly account updated successfully."

        else:
            worksheet.append_row(
                values,
                value_input_option="USER_ENTERED",
            )

            message = f"{month_value} monthly account saved successfully."

        clear_monthly_account_cache()

        return True, message

    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=120)
def get_monthly_expenses(month_year):
    """
    Return expenses for the selected month.
    """

    expenses = get_expenses()

    if expenses.empty:
        return pd.DataFrame()

    if "_Parsed Date" not in expenses.columns:
        return pd.DataFrame()

    selected_period = pd.Period(
        month_year,
        freq="M",
    )

    mask = expenses["_Parsed Date"].dt.to_period("M").eq(selected_period)

    return expenses.loc[mask]


@st.cache_data(ttl=120)
def calculate_monthly_expenses(month_year):
    """
    Calculate expense totals for the selected month.
    Uses vectorized classification + groupby.
    """

    df = get_monthly_expenses(month_year)

    expense_categories = [
        "Salary Paid to Khadim",
        "Salary Paid to Imam Sahib",
        "Masjid Electricity Paid",
        "Darasgah Electricity Paid",
        "Other Expenses",
    ]

    expense_totals = {category: 0.0 for category in expense_categories}

    if df.empty:
        return expense_totals

    if "Amount" not in df.columns:
        return expense_totals

    amounts = pd.to_numeric(
        df["Amount"],
        errors="coerce",
    ).fillna(0.0)

    particular = (
        df
        .get(
            "Particular",
            pd.Series("", index=df.index),
        )
        .fillna("")
        .astype(str)
        .str.strip()
    )

    expense_type = (
        df
        .get(
            "Expense Type",
            pd.Series("", index=df.index),
        )
        .fillna("")
        .astype(str)
        .str.strip()
    )

    category = pd.Series(
        "Other Expenses",
        index=df.index,
    )

    category.loc[particular.eq("Salary Paid to Imam Sahib")] = (
        "Salary Paid to Imam Sahib"
    )

    category.loc[particular.eq("Salary Paid to Khadim")] = "Salary Paid to Khadim"

    category.loc[
        particular.eq("Masjid Electricity Paid")
        | (
            expense_type.eq("Electricity")
            & particular.str.contains(
                "Masjid",
                case=False,
                na=False,
            )
        )
    ] = "Masjid Electricity Paid"

    category.loc[
        particular.eq("Darasgah Electricity Paid")
        | (
            expense_type.eq("Electricity")
            & particular.str.contains(
                "Darasgah",
                case=False,
                na=False,
            )
        )
    ] = "Darasgah Electricity Paid"

    grouped = (
        pd
        .DataFrame({
            "Category": category,
            "Amount": amounts,
        })
        .groupby("Category")["Amount"]
        .sum()
    )

    for category_name in expense_categories:
        expense_totals[category_name] = float(grouped.get(category_name, 0.0))

    return expense_totals


# ============================================================
# MONTHLY ACCOUNTS
# ============================================================


@st.cache_data(ttl=120)
def get_monthly_receipts(month_year):
    """
    Get all receipts whose Receipt Date falls within
    the selected month and year.
    """

    receipts = get_receipts()

    if receipts.empty:
        return pd.DataFrame()

    if "_Parsed Date" not in receipts.columns:
        return pd.DataFrame()

    selected_period = pd.Period(
        month_year,
        freq="M",
    )

    mask = receipts["_Parsed Date"].dt.to_period("M").eq(selected_period)

    return receipts.loc[mask]


@st.cache_data(ttl=120)
def calculate_monthly_income(month_year):
    """
    Calculate item-wise income for a selected month
    using the Receipt Date column.
    """

    df = get_monthly_receipts(month_year)

    income_categories = [
        "Monthly Contribution",
        "Friday Collections",
        "Donation",
        "Recovery from Imam Sahib",
        "Fire Wood Contribution",
    ]

    income = {category: 0.0 for category in income_categories}

    if df.empty:
        return income

    if "Purpose" not in df.columns or "Amount" not in df.columns:
        return income

    amounts = pd.to_numeric(
        df["Amount"],
        errors="coerce",
    ).fillna(0.0)

    purposes = df["Purpose"].fillna("").astype(str).str.strip()

    grouped = (
        pd
        .DataFrame({
            "Purpose": purposes,
            "Amount": amounts,
        })
        .groupby("Purpose")["Amount"]
        .sum()
    )

    for category in income_categories:
        income[category] = float(grouped.get(category, 0.0))

    return income


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

st.title("🕌 Al Rehman Masjid Receipt System")
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

    st.header("🧾 Receipt")
    st.info(f"Next Receipt: **{receipt_display_no(st.session_state.receipt_serial)}**")

    st.caption(
        "The digital system starts from M-515 unless existing Google Sheet "
        "records require a higher number."
    )

    st.divider()
    st.header("🕌 Masjid Details")

    st.text_input("Masjid Name", value=MASJID_NAME, disabled=True)
    st.text_input("Address", value=MASJID_ADDRESS, disabled=True)
    st.text_input("Bank", value=MASJID_BANK, disabled=True)
    st.text_input("A/C No.", value=MASJID_ACCOUNT, disabled=True)
    st.text_input("IFSC", value=MASJID_IFSC, disabled=True)

    st.divider()

    st.caption(f"🟢 Last synced: {get_last_synced()}")

    st.caption(
        "Cached Google Sheets data refreshes automatically when the cache expires."
    )


def reset_new_receipt():
    # Refresh only receipt-related cached data
    clear_receipt_cache()

    # Get the latest receipt number from Google Sheets
    st.session_state.receipt_serial = get_next_receipt_serial()

    # Create a new transaction
    st.session_state.transaction_id = str(uuid.uuid4())

    # Allow a new receipt to be generated
    st.session_state.receipt_saved = False

    # Remove previous generated PDF
    st.session_state.pdf_bytes = None
    st.session_state.generated_receipt_no = None


# ============================================================
# RECEIPT FORM
# ============================================================

st.header("Create Masjid Receipt")

residents_df = get_masjid_residents()

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        '<div class="receipt-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="receipt-section-title">👤 Payer Information</div>',
        unsafe_allow_html=True,
    )
    if not residents_df.empty:
        # ----------------------------------------------------
        # PREPARE OPTIONS
        # ----------------------------------------------------

        resident_names = residents_df["Name"].dropna().astype(str).str.strip()

        resident_names = sorted([name for name in resident_names.unique() if name])

        house_numbers = residents_df["H No."].dropna().astype(str).str.strip()

        house_numbers = sorted(
            [house for house in house_numbers.unique() if house],
            key=lambda x: (int(x) if x.isdigit() else 999999, x),
        )

        # ----------------------------------------------------
        # SESSION STATE
        # ----------------------------------------------------

        if "selected_resident_name" not in st.session_state:
            st.session_state.selected_resident_name = "-- Select Resident --"

        if "selected_resident_house" not in st.session_state:
            st.session_state.selected_resident_house = "-- Select House No. --"

        if "resident_phone" not in st.session_state:
            st.session_state.resident_phone = ""

        if "resident_paid_upto" not in st.session_state:
            st.session_state.resident_paid_upto = ""

        if "resident_firewood_paid_upto" not in st.session_state:
            st.session_state.resident_firewood_paid_upto = ""

        # ----------------------------------------------------
        # RECEIVED WITH THANKS FROM
        # ----------------------------------------------------

        received_from = st.selectbox(
            "Received with Thanks From *",
            ["-- Select Resident --"] + resident_names + ["➕ Non Resident"],
            key="selected_resident_name",
            on_change=select_resident_by_name,
        )

        is_non_resident = received_from == "➕ Non Resident"

        # ----------------------------------------------------
        # RESIDENT / NON-RESIDENT DETAILS
        # ----------------------------------------------------

        if received_from == "➕ Non Resident":
            # ==================================================
            # NON RESIDENT
            # ==================================================

            non_resident_name = st.text_input(
                "Donor Name *",
                placeholder="Enter donor name",
                key="non_resident_name",
            )

            phone = st.text_input(
                "Phone Number",
                placeholder="Enter phone number",
                key="non_resident_phone",
            )

            address = st.text_input(
                "Address *",
                placeholder="Enter donor address",
                key="non_resident_address",
            )

            # No House No. for non-residents
            house_no = ""

        else:
            # ==================================================
            # NORMAL RESIDENT
            # ==================================================

            house_no = st.selectbox(
                "House No.",
                ["-- Select House No. --"] + house_numbers,
                key="selected_resident_house",
                on_change=select_resident_by_house,
            )

            phone = st.text_input(
                "Phone Number",
                key="resident_phone",
                disabled=True,
            )

            address = ""

        # ----------------------------------------------------
        # AMOUNT
        # ----------------------------------------------------

        amount = st.number_input(
            "Amount (₹) *",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

        # ============================================================
        # NEW RECEIPT
        # ============================================================

        st.button(
            "🔄 Start New Receipt",
            on_click=reset_new_receipt,
            width="stretch",
        )

        # ----------------------------------------------------
        # CONVERT PLACEHOLDERS
        # ----------------------------------------------------

        if received_from == "-- Select Resident --":
            received_from = ""

        if house_no == "-- Select House No. --":
            house_no = ""

        # For Non Residents use the manually entered donor name
        if st.session_state.selected_resident_name == "➕ Non Resident":
            received_from = non_resident_name.strip()

    else:
        st.error("Masjid Residents sheet could not be loaded.")

        received_from = ""
        house_no = ""
        phone = ""

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )
with col2:
    st.markdown(
        '<div class="receipt-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="receipt-section-title">🧾 Payment Information</div>',
        unsafe_allow_html=True,
    )
    # ==========================================================
    # PURPOSE OPTIONS
    # Residents -> All purposes
    # Non Residents -> Donation only
    # ==========================================================

    if is_non_resident:
        purpose = st.selectbox(
            "On Account of *",
            ["Donation"],
            key="purpose_non_resident",
        )

    else:
        purpose = st.selectbox(
            "On Account of *",
            [
                "Monthly Contribution",
                "Donation",
                "Friday Collections",
                "Recovery from Imam Sahib",
                "Fire Wood Contribution",
                "Other",
            ],
            key="purpose_resident",
        )

    if purpose == "Other":
        purpose_other = st.text_input("Specify Purpose")
        selected_purpose = purpose_other.strip()
    else:
        selected_purpose = purpose

    # ----------------------------------------------------
    # MONTHLY CONTRIBUTION PAID UPTO - AUTOMATIC
    # ----------------------------------------------------

    if not is_non_resident and purpose == "Monthly Contribution":
        paid_upto = st.text_input(
            "Monthly Contribution Paid Upto",
            key="resident_paid_upto",
            disabled=True,
        )
    else:
        paid_upto = ""

    # ----------------------------------------------------
    # FIRE WOOD CONTRIBUTION PAID UPTO - AUTOMATIC
    # ----------------------------------------------------

    if not is_non_resident and purpose == "Fire Wood Contribution":
        firewood_paid_upto = st.session_state.get("resident_firewood_paid_upto", "")

        st.text_input(
            "Fire Wood Contribution Paid Upto",
            value=firewood_paid_upto,
            disabled=True,
            key="firewood_paid_upto_display",
        )

    else:
        firewood_paid_upto = ""

    # ============================================================
    # MONTH-WISE CONTRIBUTION PERIOD
    # ONLY FOR MONTHLY CONTRIBUTION
    # ============================================================

    month_from = ""
    month_to = ""

    if purpose == "Monthly Contribution":
        month_names = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        current_year = datetime.now().year
        current_month = datetime.now().month

        # -------------------------
        # FROM MONTH
        # -------------------------

        st.markdown("**Month - From**")

        from_col1, from_col2 = st.columns([2, 1])

        with from_col1:
            from_month = st.selectbox(
                "Month",
                month_names,
                index=current_month - 1,
                key="from_month",
                label_visibility="collapsed",
            )

        with from_col2:
            from_year = st.number_input(
                "Year",
                min_value=1900,
                max_value=2100,
                value=current_year,
                step=1,
                key="from_year",
                label_visibility="collapsed",
            )

        # -------------------------
        # TO MONTH
        # -------------------------

        st.markdown("**To**")

        to_col1, to_col2 = st.columns([2, 1])

        with to_col1:
            # Default to next month
            if current_month == 12:
                default_to_month = 0
            else:
                default_to_month = current_month

            to_month = st.selectbox(
                "Month",
                month_names,
                index=default_to_month,
                key="to_month",
                label_visibility="collapsed",
            )

        with to_col2:
            default_to_year = current_year + 1 if current_month == 12 else current_year

            to_year = st.number_input(
                "Year",
                min_value=1900,
                max_value=2100,
                value=default_to_year,
                step=1,
                key="to_year",
                label_visibility="collapsed",
            )

        # Create final values
        month_from = f"{from_month} {int(from_year)}"
        month_to = f"{to_month} {int(to_year)}"

    # ============================================================
    # FIRE WOOD CONTRIBUTION YEAR
    # ONLY FOR FIRE WOOD CONTRIBUTION
    # ============================================================

    firewood_year = ""

    if purpose == "Fire Wood Contribution":
        current_year = datetime.now().year

        # Financial year format: 2026 - 2027
        current_financial_year = f"{current_year} - {current_year + 1}"

        financial_year_options = [
            f"{year} - {year + 1}" for year in range(current_year - 5, current_year + 6)
        ]

        firewood_year = st.selectbox(
            "Fire Wood Contribution Year",
            financial_year_options,
            index=financial_year_options.index(current_financial_year),
            key="firewood_year",
        )
    payment_mode = st.selectbox(
        "Payment Mode",
        ["Cash", "UPI", "Bank Transfer", "Cheque", "Other"],
    )
    st.markdown(
        "</div>",
        unsafe_allow_html=True,
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
# ============================================================
# MONTH RANGE VALIDATION
# ONLY FOR MONTHLY CONTRIBUTION
# ============================================================

if selected_purpose == "Monthly Contribution":
    from_date_for_comparison = datetime(
        int(from_year),
        month_names.index(from_month) + 1,
        1,
    )

    to_date_for_comparison = datetime(
        int(to_year),
        month_names.index(to_month) + 1,
        1,
    )

else:
    from_date_for_comparison = datetime.now()
    to_date_for_comparison = datetime.now()

# ============================================================
# GENERATE RECEIPT - RESPONSIVE ACTION AREA
# ============================================================

st.divider()
st.subheader("🧾 Generate Masjid Receipt")

st.caption(
    "Verify the payer, amount, purpose and payment details "
    "before generating the receipt."
)

generate_receipt = st.button(
    "🧾 Generate & Save Receipt",
    type="primary",
    width="stretch",
    disabled=st.session_state.receipt_saved,
    key="generate_masjid_receipt",
)

if st.session_state.receipt_saved:
    st.info(
        "This receipt has already been saved. "
        "Download it below or select Start New Receipt."
    )

if generate_receipt:
    name_ok, name_error = validate_name(received_from)
    phone_ok, phone_error = validate_phone(phone)

    is_non_resident = st.session_state.selected_resident_name == "Non Residents"

    if not received_from:
        if is_non_resident:
            st.error("❌ Please enter donor name.")
        else:
            st.error("❌ Please select a resident.")

    elif not name_ok:
        st.error(f"❌ {name_error}")

    elif is_non_resident and not address.strip():
        st.error("❌ Please enter donor address.")

    elif not phone_ok:
        st.error(f"❌ {phone_error}")

    elif amount <= 0:
        st.error("❌ Please enter an amount greater than ₹0.")

    elif is_non_resident and selected_purpose != "Donation":
        st.error("❌ Non Residents can only donate to the Masjid.")

    elif not selected_purpose:
        st.error("❌ Please select or enter purpose.")

    elif to_date_for_comparison < from_date_for_comparison:
        st.error("❌ 'To' month cannot be earlier than 'From' month.")

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
                address=address.strip(),
                phone=phone.strip(),
                amount=amount,
                purpose=selected_purpose,
                month_from=month_from,
                month_to=month_to,
                payment_mode=payment_mode,
                date_value=date_value.strftime("%d/%m/%Y"),
                firewood_year=firewood_year,
            )

            saved, message = save_receipt(
                receipt_serial=serial,
                transaction_id=st.session_state.transaction_id,
                received_from=received_from.strip(),
                house_no=house_no.strip(),
                address=address.strip(),
                amount=amount,
                purpose=selected_purpose,
                month_from=month_from,
                month_to=month_to,
                payment_mode=payment_mode,
                phone=phone.strip(),
                date_value=date_value.strftime("%d/%m/%Y"),
                firewood_year=firewood_year,
            )

            if saved:
                # --------------------------------------------------------
                # UPDATE RESIDENT'S Monthly Contribution Paid Upto
                # ONLY FOR MONTHLY CONTRIBUTION
                # --------------------------------------------------------

                updated = False
                update_message = ""

                if selected_purpose == "Monthly Contribution":
                    updated, update_message = update_resident_paid_upto(
                        received_from=received_from.strip(),
                        house_no=house_no.strip(),
                        month_to=month_to,
                    )
                firewood_updated = False
                firewood_update_message = ""

                if selected_purpose == "Fire Wood Contribution":
                    firewood_updated, firewood_update_message = (
                        update_resident_firewood_paid_upto(
                            received_from=received_from.strip(),
                            house_no=house_no.strip(),
                            firewood_year=firewood_year,
                        )
                    )

                st.session_state.pdf_bytes = pdf_bytes
                st.session_state.generated_receipt_no = receipt_no
                st.session_state.receipt_saved = True

                st.success(
                    f"✅ Receipt {receipt_no} generated and saved to Google Sheets."
                )

                if selected_purpose == "Monthly Contribution":
                    if updated:
                        st.success(
                            f"✅ {received_from.strip()} is now paid up to {month_to}."
                        )
                    else:
                        st.warning(
                            f"⚠️ Receipt was saved, but Monthly Contribution Paid Upto "
                            f"could not be updated: {update_message}"
                        )
                if selected_purpose == "Fire Wood Contribution":
                    if firewood_updated:
                        st.success(
                            f"✅ {received_from.strip()} is now paid up to {firewood_year} for Fire Wood Contribution."
                        )
                    else:
                        st.warning(
                            f"⚠️ Receipt was saved, but Fire Wood Contribution Paid Upto "
                            f"could not be updated: {firewood_update_message}"
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

    st.success(f"Receipt {st.session_state.generated_receipt_no} is ready.")

    st.subheader("📄 Download & Share")

    st.caption("Download the receipt PDF and optionally share it through WhatsApp.")

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
            f"Assalamualaikum {received_from},\n\n"
            f"Thank you for your contribution to {MASJID_NAME}.\n\n"
            f"Masjid Receipt: {st.session_state.generated_receipt_no}\n"
            f"Amount: ₹{amount:,.2f}\n"
            f"Purpose: {selected_purpose}\n"
            f"Date: {date_value.strftime('%d/%m/%Y')}\n\n"
            f"Please find your receipt attached.\n\n"
            f"Jazakallah Khair."
        )

        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={quote(whatsapp_message)}"

        st.markdown(
            f"""
            <a
                href="{whatsapp_url}"
                target="_blank"
                rel="noopener noreferrer"
                class="receipt-whatsapp-button"
            >
                📱 Open WhatsApp Message
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


# ------------------------------------------------------------
# REFRESH
# ------------------------------------------------------------

history_col1, history_col2 = st.columns([1, 1])

with history_col1:
    refresh_history = st.button(
        "🔄 Refresh Receipt History",
        width="stretch",
        key="refresh_receipt_history",
    )

if refresh_history:
    clear_receipt_cache()
    st.rerun()


# ------------------------------------------------------------
# LOAD RECEIPTS
# ------------------------------------------------------------

receipts_df = get_receipts()


if receipts_df.empty:
    st.info("No receipts found in the Google Sheets 'Receipts' worksheet yet.")

else:
    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

    display_df = receipts_df.copy()

    if "Amount" in display_df.columns:
        display_df["Amount"] = pd.to_numeric(
            display_df["Amount"],
            errors="coerce",
        ).fillna(0.0)

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search_text = st.text_input(
        "🔎 Search Receipt History",
        placeholder=("Search by Receipt No, Name, Phone, House No, Purpose..."),
        key="receipt_history_search",
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])

    # --------------------------------------------------------
    # PURPOSE FILTER
    # --------------------------------------------------------

    with filter_col1:
        purpose_options = ["All"]

        if "Purpose" in display_df.columns:
            purpose_values = display_df["Purpose"].dropna().astype(str).str.strip()

            purpose_options += sorted([
                value for value in purpose_values.unique() if value
            ])

        selected_purpose = st.selectbox(
            "Purpose",
            purpose_options,
            key="receipt_history_purpose",
        )

    # --------------------------------------------------------
    # PAYMENT MODE FILTER
    # --------------------------------------------------------

    with filter_col2:
        payment_options = ["All"]

        if "Payment Mode" in display_df.columns:
            payment_values = display_df["Payment Mode"].dropna().astype(str).str.strip()

            payment_options += sorted([
                value for value in payment_values.unique() if value
            ])

        selected_payment = st.selectbox(
            "Payment Mode",
            payment_options,
            key="receipt_history_payment",
        )

    # --------------------------------------------------------
    # NUMBER OF RECEIPTS TO DISPLAY
    # --------------------------------------------------------

    with filter_col3:
        rows_to_show = st.selectbox(
            "Receipts to Display",
            [15, 30, 50, 100],
            index=1,
            key="receipt_history_rows",
        )

    # --------------------------------------------------------
    # APPLY SEARCH
    # --------------------------------------------------------

    filtered_df = display_df.copy()

    if search_text.strip():
        search_columns = [
            "Receipt No",
            "Received From",
            "House No",
            "Phone",
            "Purpose",
            "Payment Mode",
        ]

        available_search_columns = [
            column for column in search_columns if column in filtered_df.columns
        ]

        search_mask = pd.Series(
            False,
            index=filtered_df.index,
        )

        search_value = search_text.strip().lower()

        for column in available_search_columns:
            search_mask = search_mask | (
                filtered_df[column]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    regex=False,
                    na=False,
                )
            )

        filtered_df = filtered_df[search_mask]

    # --------------------------------------------------------
    # APPLY PURPOSE FILTER
    # --------------------------------------------------------

    if selected_purpose != "All" and "Purpose" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["Purpose"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq(selected_purpose)
        ]

    # --------------------------------------------------------
    # APPLY PAYMENT MODE FILTER
    # --------------------------------------------------------

    if selected_payment != "All" and "Payment Mode" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["Payment Mode"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq(selected_payment)
        ]

    # --------------------------------------------------------
    # SORT — LATEST RECEIPTS FIRST
    # --------------------------------------------------------

    if "_Parsed Date" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            "_Parsed Date",
            ascending=False,
            na_position="last",
        )

    elif "Date" in filtered_df.columns:
        filtered_df["_SortDate"] = pd.to_datetime(
            filtered_df["Date"],
            dayfirst=True,
            errors="coerce",
        )

        filtered_df = filtered_df.sort_values(
            "_SortDate",
            ascending=False,
            na_position="last",
        ).drop(columns=["_SortDate"])

    # --------------------------------------------------------
    # RESULTS SUMMARY
    # --------------------------------------------------------

    total_matching = len(filtered_df)

    st.caption(
        f"Showing "
        f"{min(total_matching, rows_to_show)} "
        f"of {total_matching} matching receipts"
    )

    # --------------------------------------------------------
    # MOBILE-FRIENDLY DISPLAY COLUMNS
    # --------------------------------------------------------

    history_columns = [
        "Receipt No",
        "Date",
        "Received From",
        "Amount",
        "Purpose",
        "Payment Mode",
    ]

    available_history_columns = [
        column for column in history_columns if column in filtered_df.columns
    ]

    history_display = filtered_df[available_history_columns].head(rows_to_show).copy()

    # --------------------------------------------------------
    # FORMAT AMOUNT
    # --------------------------------------------------------

    if "Amount" in history_display.columns:
        history_display["Amount"] = history_display["Amount"].apply(
            lambda value: f"₹{value:,.0f}"
        )

    # --------------------------------------------------------
    # DISPLAY TABLE
    # --------------------------------------------------------

    if history_display.empty:
        st.warning("No receipts match your search/filter.")

    else:
        st.dataframe(
            history_display,
            width="stretch",
            hide_index=True,
        )

    # --------------------------------------------------------
    # DOWNLOAD FULL RECEIPT DATABOOK
    # --------------------------------------------------------

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl",
    ) as writer:
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
        mime=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        width="stretch",
    )

# ============================================================
# SUMMARY
# ============================================================

if not receipts_df.empty:
    st.divider()
    st.subheader("📈 Collection Summary")

    # --------------------------------------------------------
    # OVERALL TOTALS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ITEM-WISE COLLECTION BY RECEIPT DATE
    # --------------------------------------------------------

    st.markdown("---")
    st.markdown("### 📊 Item-wise Collection")

    # Convert Date column to actual dates
    summary_df = receipts_df.copy()

    summary_df["Date"] = pd.to_datetime(
        summary_df["Date"],
        dayfirst=True,
        errors="coerce",
    )

    # Create month options from Date column
    available_months = (
        summary_df["Date"]
        .dropna()
        .dt.to_period("M")
        .drop_duplicates()
        .sort_values(ascending=False)
    )

    month_options = [month.strftime("%B %Y") for month in available_months]

    if month_options:
        selected_month = st.selectbox(
            "Month",
            month_options,
            key="collection_summary_month",
        )

        selected_period = pd.Period(
            selected_month,
            freq="M",
        )

        # ----------------------------------------------------
        # FILTER USING RECEIPT DATE
        # ----------------------------------------------------

        month_filtered = summary_df[
            summary_df["Date"].dt.to_period("M") == selected_period
        ].copy()

        # ----------------------------------------------------
        # ITEM-WISE TOTAL
        # ----------------------------------------------------

        item_summary = (
            month_filtered
            .groupby("Purpose", as_index=False)["Amount"]
            .sum()
            .sort_values("Amount", ascending=False)
        )

        st.markdown(f"#### Item-wise Collection — {selected_month}")

        if not item_summary.empty:
            # Show item totals
            for _, row in item_summary.iterrows():
                st.metric(row["Purpose"], f"₹{row['Amount']:,.2f}")

            # Total for selected month
            month_total = item_summary["Amount"].sum()

            st.markdown("---")

            st.metric(f"Total Collection — {selected_month}", f"₹{month_total:,.2f}")

        else:
            st.info(f"No collections recorded during {selected_month}.")


# ============================================================
# NEW RECEIPT
# ============================================================

# ============================================================
# EXPENSE ENTRY
# ============================================================

st.markdown("---")
st.subheader("➕ Add Expense")

expense_col1, expense_col2 = st.columns(2)

with expense_col1:
    st.markdown(
        '<div class="expense-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="expense-section-title">📅 Expense Information</div>',
        unsafe_allow_html=True,
    )

    expense_date = st.date_input(
        "Expense Date",
        value=datetime.now().date(),
        format="DD/MM/YYYY",
        key="expense_date",
    )

    expense_type = st.selectbox(
        "Expense Type",
        [
            "Salary",
            "Electricity",
            "Maintenance",
            "Purchase",
            "Other",
        ],
        key="expense_type",
    )

    if expense_type == "Salary":
        salary_type = st.selectbox(
            "Salary",
            [
                "Salary Paid to Khadim",
                "Salary Paid to Imam Sahib",
            ],
            key="salary_type",
        )

        expense_particular = salary_type

    elif expense_type == "Electricity":
        electricity_type = st.selectbox(
            "Electricity",
            [
                "Masjid Electricity Paid",
                "Darasgah Electricity Paid",
            ],
            key="electricity_type",
        )

        expense_particular = electricity_type

    else:
        expense_particular = st.text_input(
            "Particular",
            placeholder="Enter expense particular",
            key="expense_particular",
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

with expense_col2:
    st.markdown(
        '<div class="expense-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="expense-section-title">💰 Payment Information</div>',
        unsafe_allow_html=True,
    )

    expense_amount = st.number_input(
        "Expense Amount (₹)",
        min_value=0.0,
        value=0.0,
        step=100.0,
        key="expense_amount",
    )

    expense_payment_mode = st.selectbox(
        "Payment Mode",
        [
            "Cash",
            "UPI",
            "Bank Transfer",
            "Cheque",
            "Other",
        ],
        key="expense_payment_mode",
    )

    expense_remarks = st.text_input(
        "Remarks",
        placeholder="Optional",
        key="expense_remarks",
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

save_expense_button = st.button(
    "💾 Save Expense",
    type="primary",
    width="stretch",
    key="save_expense_button",
)


if save_expense_button:
    if not expense_particular.strip():
        st.error("❌ Please enter the expense particular.")

    elif expense_amount <= 0:
        st.error("❌ Please enter an amount greater than ₹0.")

    else:
        expense_saved, expense_message = save_expense(
            date_value=expense_date.strftime("%d/%m/%Y"),
            expense_type=expense_type,
            particular=expense_particular.strip(),
            amount=expense_amount,
            payment_mode=expense_payment_mode,
            remarks=expense_remarks.strip(),
        )

        if expense_saved:
            st.success(
                f"✅ {expense_particular} of ₹{expense_amount:,.2f} saved successfully."
            )

        else:
            st.error(f"❌ Could not save expense: {expense_message}")

# ============================================================
# EXPENSE HISTORY
# ============================================================

st.markdown("---")
st.subheader("📋 Expense History")

expenses_df = get_expenses()

if expenses_df.empty:
    st.info("No expenses have been recorded yet.")

else:
    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    refresh_expense_history = st.button(
        "🔄 Refresh Expense History",
        width="stretch",
        key="refresh_expense_history",
    )

    if refresh_expense_history:
        clear_expense_cache()
        st.rerun()

    display_expenses = expenses_df.copy()

    # --------------------------------------------------------
    # NORMALIZE COLUMNS
    # --------------------------------------------------------

    if "Amount" in display_expenses.columns:
        display_expenses["Amount"] = pd.to_numeric(
            display_expenses["Amount"],
            errors="coerce",
        ).fillna(0.0)

    if "Date" in display_expenses.columns:
        display_expenses["_Parsed Date"] = pd.to_datetime(
            display_expenses["Date"],
            dayfirst=True,
            errors="coerce",
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    expense_search = (
        st
        .text_input(
            "🔎 Search Expenses",
            placeholder="Search type, particular, remarks, payment mode...",
            key="expense_history_search",
        )
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        if "Expense Type" in display_expenses.columns:
            expense_types = sorted(
                display_expenses["Expense Type"].dropna().astype(str).unique().tolist()
            )

            selected_expense_type = st.selectbox(
                "Expense Type",
                ["All"] + expense_types,
                key="expense_history_type_filter",
            )
        else:
            selected_expense_type = "All"

    with filter_col2:
        if "Payment Mode" in display_expenses.columns:
            payment_modes = sorted(
                display_expenses["Payment Mode"].dropna().astype(str).unique().tolist()
            )

            selected_payment_mode = st.selectbox(
                "Payment Mode",
                ["All"] + payment_modes,
                key="expense_history_payment_filter",
            )
        else:
            selected_payment_mode = "All"

    with filter_col3:
        if "_Parsed Date" in display_expenses.columns:
            valid_dates = display_expenses["_Parsed Date"].dropna()

            if not valid_dates.empty:
                month_options = sorted(
                    valid_dates.dt.strftime("%B %Y").unique().tolist(),
                    key=lambda x: pd.to_datetime(x, format="%B %Y"),
                    reverse=True,
                )

                selected_expense_month = st.selectbox(
                    "Month",
                    ["All"] + month_options,
                    key="expense_history_month_filter",
                )
            else:
                selected_expense_month = "All"
        else:
            selected_expense_month = "All"

    # --------------------------------------------------------
    # APPLY SEARCH
    # --------------------------------------------------------

    filtered_expenses = display_expenses.copy()

    if expense_search:
        searchable_columns = [
            column
            for column in [
                "Date",
                "Expense Type",
                "Particular",
                "Payment Mode",
                "Remarks",
                "Name of Person Who Died",
            ]
            if column in filtered_expenses.columns
        ]

        if searchable_columns:
            search_mask = (
                filtered_expenses[searchable_columns]
                .fillna("")
                .astype(str)
                .apply(
                    lambda column: column.str.lower().str.contains(
                        expense_search,
                        regex=False,
                    )
                )
                .any(axis=1)
            )

            filtered_expenses = filtered_expenses[search_mask]

    # --------------------------------------------------------
    # APPLY EXPENSE TYPE FILTER
    # --------------------------------------------------------

    if selected_expense_type != "All" and "Expense Type" in filtered_expenses.columns:
        filtered_expenses = filtered_expenses[
            filtered_expenses["Expense Type"].astype(str).eq(selected_expense_type)
        ]

    # --------------------------------------------------------
    # APPLY PAYMENT MODE FILTER
    # --------------------------------------------------------

    if selected_payment_mode != "All" and "Payment Mode" in filtered_expenses.columns:
        filtered_expenses = filtered_expenses[
            filtered_expenses["Payment Mode"].astype(str).eq(selected_payment_mode)
        ]

    # --------------------------------------------------------
    # APPLY MONTH FILTER
    # --------------------------------------------------------

    if selected_expense_month != "All" and "_Parsed Date" in filtered_expenses.columns:
        filtered_expenses = filtered_expenses[
            filtered_expenses["_Parsed Date"]
            .dt.strftime("%B %Y")
            .eq(selected_expense_month)
        ]

    # --------------------------------------------------------
    # LATEST FIRST
    # --------------------------------------------------------

    if "_Parsed Date" in filtered_expenses.columns:
        filtered_expenses = filtered_expenses.sort_values(
            "_Parsed Date",
            ascending=False,
            na_position="last",
        )

    # --------------------------------------------------------
    # RESULT COUNT + ROW LIMIT
    # --------------------------------------------------------

    result_col1, result_col2 = st.columns([2, 1])

    with result_col1:
        st.caption(f"Showing {len(filtered_expenses):,} matching expense(s)")

    with result_col2:
        rows_to_display = st.selectbox(
            "Rows",
            [15, 30, 50, 100],
            index=0,
            key="expense_history_rows",
        )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    visible_expenses = filtered_expenses.head(rows_to_display).copy()

    if "_Parsed Date" in visible_expenses.columns:
        visible_expenses = visible_expenses.drop(columns=["_Parsed Date"])

    st.dataframe(
        visible_expenses,
        width="stretch",
        hide_index=True,
    )

    # --------------------------------------------------------
    # EXCEL EXPORT
    # --------------------------------------------------------

    if not filtered_expenses.empty:
        export_expenses = filtered_expenses.copy()

        if "_Parsed Date" in export_expenses.columns:
            export_expenses = export_expenses.drop(columns=["_Parsed Date"])

        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl",
        ) as writer:
            export_expenses.to_excel(
                writer,
                index=False,
                sheet_name="Expense History",
            )

        excel_buffer.seek(0)

        st.download_button(
            "📥 Download Expense History",
            data=excel_buffer,
            file_name="Masjid_Expense_History.xlsx",
            mime=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            width="stretch",
            key="download_masjid_expense_history",
        )


# ============================================================
# MASJID MONTHLY STATEMENT
# ============================================================

st.divider()

st.header("📒 Masjid Monthly Statement")

st.caption(
    "Monthly income is calculated from Receipts and monthly "
    "expenses are calculated from Masjid Expenses."
)


# ============================================================
# MONTH SELECTION
# ============================================================

month_col1, month_col2 = st.columns([2, 1])

with month_col1:
    statement_month = st.selectbox(
        "Select Month",
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        index=datetime.now().month - 1,
        key="statement_month",
    )


with month_col2:
    statement_year = st.number_input(
        "Year",
        min_value=2020,
        max_value=2100,
        value=datetime.now().year,
        step=1,
        key="statement_year",
    )


selected_period = pd.Period(
    f"{int(statement_year)}-"
    f"{
        [
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December',
        ].index(statement_month)
        + 1:02d}",
    freq="M",
)

selected_month_text = f"{statement_month} {int(statement_year)}"


# ============================================================
# OPENING BALANCES
# ============================================================

opening_cash, opening_bank = get_previous_month_balances(selected_period)

st.markdown("---")
st.subheader(f"💰 Opening Balances — {selected_month_text}")

opening_col1, opening_col2 = st.columns(2)

with opening_col1:
    opening_cash_manual = st.number_input(
        "Last Month's Cash in Hand",
        min_value=0.0,
        value=float(opening_cash),
        step=100.0,
        key=f"opening_cash_{selected_month_text}",
    )

with opening_col2:
    opening_bank_manual = st.number_input(
        "Last Month's Balance with J&K Bank excluding Interest",
        min_value=0.0,
        value=float(opening_bank),
        step=100.0,
        key=f"opening_bank_{selected_month_text}",
    )

# Use the manually entered values for all calculations
opening_cash = opening_cash_manual
opening_bank = opening_bank_manual


# ============================================================
# INCOME
# ============================================================

income = calculate_monthly_income(selected_period)

monthly_contribution = income.get(
    "Monthly Contribution",
    0.0,
)


friday_idd = income.get(
    "Friday Collections",
    0.0,
)

donation = income.get(
    "Donation",
    0.0,
)


recovery = income.get(
    "Recovery from Imam Sahib",
    0.0,
)

fire_wood = income.get(
    "Fire Wood Contribution",
    0.0,
)


# Additions during the month
additions_during_month = (
    +monthly_contribution + friday_idd + donation + recovery + fire_wood
)

# ============================================================
# PAYMENT MODE WISE INCOME
# ============================================================

monthly_receipts = get_monthly_receipts(selected_period)

bank_income = 0.0

if not monthly_receipts.empty:
    monthly_receipts["Amount"] = pd.to_numeric(
        monthly_receipts["Amount"],
        errors="coerce",
    ).fillna(0.0)

    monthly_receipts["Payment Mode"] = (
        monthly_receipts["Payment Mode"].fillna("").astype(str).str.strip()
    )

    # --------------------------------------------------------
    # BANK INCOME
    # UPI + Bank Transfer + Cheque → Bank
    # --------------------------------------------------------

    bank_income = monthly_receipts.loc[
        monthly_receipts["Payment Mode"].isin([
            "UPI",
            "Bank Transfer",
            "Cheque",
        ]),
        "Amount",
    ].sum()


# ------------------------------------------------------------
# CASH INCOME
# Cash + Other → Cash
# ------------------------------------------------------------

cash_income = additions_during_month - bank_income


# ============================================================
# EXPENSES
# ============================================================

expenses = calculate_monthly_expenses(selected_period)

salary_khadim = expenses.get(
    "Salary Paid to Khadim",
    0.0,
)

salary_imam = expenses.get(
    "Salary Paid to Imam Sahib",
    0.0,
)

masjid_electricity = expenses.get(
    "Masjid Electricity Paid",
    0.0,
)

darasgah_electricity = expenses.get(
    "Darasgah Electricity Paid",
    0.0,
)

other_expenses = expenses.get(
    "Other Expenses",
    0.0,
)

total_expenses = (
    salary_khadim
    + salary_imam
    + masjid_electricity
    + darasgah_electricity
    + other_expenses
)

# ============================================================
# PAYMENT MODE WISE EXPENSES
# ============================================================

monthly_expenses_df = get_monthly_expenses(selected_period)

bank_expenses = 0.0

if not monthly_expenses_df.empty:
    if "Payment Mode" in monthly_expenses_df.columns:
        monthly_expenses_df["Payment Mode"] = (
            monthly_expenses_df["Payment Mode"].fillna("").astype(str).str.strip()
        )

        monthly_expenses_df["Amount"] = pd.to_numeric(
            monthly_expenses_df["Amount"],
            errors="coerce",
        ).fillna(0.0)

        # ----------------------------------------------------
        # BANK EXPENSES
        # UPI + Bank Transfer + Cheque → Bank
        # ----------------------------------------------------

        bank_expenses = monthly_expenses_df.loc[
            monthly_expenses_df["Payment Mode"].isin([
                "UPI",
                "Bank Transfer",
                "Cheque",
            ]),
            "Amount",
        ].sum()


# ------------------------------------------------------------
# CASH EXPENSES
# Cash + Other → Cash
# ------------------------------------------------------------

cash_expenses = total_expenses - bank_expenses


# ============================================================
# CLOSING BALANCES
# ============================================================

st.markdown("---")

st.subheader(f"💰 Closing Balances — {selected_month_text}")

# ============================================================
# BANK MOVEMENT
# ============================================================

st.markdown("---")
st.subheader(f"🏦 Bank Deposits / Withdrawals — {selected_month_text}")

st.markdown(
    '<div class="account-card">',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="account-section-title">🏦 Bank Movement</div>',
    unsafe_allow_html=True,
)

bank_transfer_col1, bank_transfer_col2 = st.columns(2)

with bank_transfer_col1:
    deposits_credits = st.number_input(
        "Amount Credited to Bank",
        min_value=0.0,
        value=0.0,
        step=100.0,
        key=f"deposits_credits_{selected_month_text}",
        help="Cash deposited into the bank account.",
    )

with bank_transfer_col2:
    withdrawals_debits = st.number_input(
        "Amount Debited from Bank",
        min_value=0.0,
        value=0.0,
        step=100.0,
        key=f"withdrawals_debits_{selected_month_text}",
        help="Cash withdrawn from the bank account.",
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Separate Cash and Bank movements
# ------------------------------------------------------------

# INCOME:
# Cash + Other              → Cash
# UPI + Bank Transfer + Cheque → Bank

cash_income = additions_during_month - bank_income


# EXPENSES:
# Cash + Other              → Cash
# UPI + Bank Transfer + Cheque → Bank

cash_expenses = total_expenses - bank_expenses


# ------------------------------------------------------------
# Automatically calculate closing balances
# ------------------------------------------------------------

closing_bank = (
    opening_bank + bank_income - bank_expenses + deposits_credits - withdrawals_debits
)

closing_cash = (
    opening_cash + cash_income - cash_expenses - deposits_credits + withdrawals_debits
)


# ============================================================
# CALCULATED CLOSING BALANCES
# ============================================================

st.markdown(
    '<div class="account-card">',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="account-section-title">📊 Closing Balances</div>',
    unsafe_allow_html=True,
)

balance_col1, balance_col2 = st.columns(2)

with balance_col1:
    st.number_input(
        "Balance with J&K Bank excluding Interest",
        min_value=0.0,
        value=float(closing_bank),
        step=100.0,
        disabled=True,
        key="calculated_closing_bank",
    )

with balance_col2:
    st.number_input(
        "Cash in Hand",
        min_value=0.0,
        value=float(closing_cash),
        step=100.0,
        disabled=True,
        key="calculated_closing_cash",
    )


st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# CALCULATE STATEMENT TOTALS
# ============================================================

total_resources = opening_cash + additions_during_month + opening_bank

closing_resources = total_expenses + closing_bank + closing_cash

difference = total_resources - closing_resources

# ============================================================
# DISPLAY STATEMENT
# ============================================================

st.markdown("---")

st.subheader(f"📊 Income Expenditure Details for Month of {selected_month_text}")


# ============================================================
# INCOME SIDE
# ============================================================

income_display_col, expense_display_col = st.columns(2)


with income_display_col:
    st.markdown("### 📥 Income Side")

    income_table = pd.DataFrame(
        [
            [
                "Last Month's Cash in Hand",
                opening_cash,
            ],
            [
                "Additions During the month",
                additions_during_month,
            ],
            [
                "a) Monthly Contribution",
                monthly_contribution,
            ],
            [
                "b) Friday Collections",
                friday_idd,
            ],
            [
                "c) Donation",
                donation,
            ],
            [
                "Recovery from Imam Sahib",
                recovery,
            ],
            [
                "Fire Wood Contribution",
                fire_wood,
            ],
            [
                "Last Months Balance in Bank excluding Interest",
                opening_bank,
            ],
        ],
        columns=[
            "Particulars",
            "Amount",
        ],
    )

    income_table["Amount"] = income_table["Amount"].map(lambda x: f"₹{x:,.2f}")

    st.dataframe(
        income_table,
        width="stretch",
        hide_index=True,
    )

    st.metric(
        "TOTAL",
        f"₹{total_resources:,.2f}",
    )


# ============================================================
# EXPENSE SIDE
# ============================================================

with expense_display_col:
    st.markdown("### 📤 Expenses Side")

    expense_table = pd.DataFrame(
        [
            [
                "Salary Paid to Khadim",
                salary_khadim,
            ],
            [
                "Salary Paid to Imam Sahib",
                salary_imam,
            ],
            [
                "Masjid Electricity Paid",
                masjid_electricity,
            ],
            [
                "Darasgah Electricity Paid",
                darasgah_electricity,
            ],
            [
                "Other Expenses",
                other_expenses,
            ],
            [
                "Amount Credited to Bank",
                deposits_credits,
            ],
            [
                "Amount Debited from Bank",
                withdrawals_debits,
            ],
            [
                "Balance with J&K Bank excluding Interest",
                closing_bank,
            ],
            [
                "Cash in Hand",
                closing_cash,
            ],
        ],
        columns=[
            "Particulars",
            "Amount",
        ],
    )

    expense_table["Amount"] = expense_table["Amount"].map(lambda x: f"₹{x:,.2f}")

    st.dataframe(
        expense_table,
        width="stretch",
        hide_index=True,
    )

    st.metric(
        "TOTAL",
        f"₹{closing_resources:,.2f}",
    )

# ============================================================
# BALANCE CHECK
# ============================================================

st.markdown("---")

if abs(difference) < 0.01:
    st.success("✅ Monthly statement is balanced.")

else:
    st.warning(f"⚠️ Statement difference: ₹{difference:,.2f}")


# ============================================================
# SAVE MONTH
# ============================================================

st.markdown("---")

st.subheader(f"💾 Save {selected_month_text}")

st.warning(
    "💡 One click saves this month to both "
    "'Monthly Accounts' and the formatted 'Masjid Monthly' statement."
    " Saving the same month again will update that month's record."
)


save_month_button = st.button(
    f"💾 Save {selected_month_text} Accounts",
    type="primary",
    width="stretch",
    key="save_month_accounts",
)

if save_month_button:
    # ========================================================
    # 1. SAVE TO MONTHLY ACCOUNTS
    # ========================================================

    month_data = {
        "Month": selected_month_text,
        "Last Month Cash": opening_cash,
        "Monthly Contribution": monthly_contribution,
        "Friday Collections": friday_idd,
        "Donation": donation,
        "Recovery from Imam Sahib": recovery,
        "Fire Wood Contribution": fire_wood,
        "Total Income": total_resources,
        "Salary Paid to Khadim": salary_khadim,
        "Salary Paid to Imam Sahib": salary_imam,
        "Masjid Electricity Paid": masjid_electricity,
        "Darasgah Electricity Paid": darasgah_electricity,
        "Other Expenses": other_expenses,
        "Total Expenses": total_expenses,
        "Amount Credited to Bank": deposits_credits,
        "Amount Debited from Bank": withdrawals_debits,
        "Bank Balance": closing_bank,
        "Cash in Hand": closing_cash,
        "Closing Balance": closing_resources,
    }

    # ========================================================
    # 2. SAVE TO MONTHLY ACCOUNTS SHEET
    # ========================================================

    saved_month, save_message = save_monthly_account(month_data)

    # ========================================================
    # 3. UPDATE MASJID MONTHLY STATEMENT
    # ========================================================

    saved_statement, statement_message = save_masjid_monthy_statement(
        month_name=statement_month,
        year=int(statement_year),
        opening_cash=opening_cash,
        opening_bank=opening_bank,
        additions_during_month=additions_during_month,
        monthly_contribution=monthly_contribution,
        friday_idd=friday_idd,
        donation=donation,
        recovery=recovery,
        fire_wood=fire_wood,
        salary_khadim=salary_khadim,
        salary_imam=salary_imam,
        masjid_electricity=masjid_electricity,
        darasgah_electricity=darasgah_electricity,
        other_expenses=other_expenses,
        deposits_credits=deposits_credits,
        withdrawals_debits=withdrawals_debits,
        closing_bank=closing_bank,
        closing_cash=closing_cash,
    )
    # ========================================================
    # 4. SHOW RESULT
    # ========================================================

    if saved_month and saved_statement:
        st.success(f"✅ {selected_month_text} saved successfully!")

        st.info("📒 Monthly Accounts updated and 📊 Masjid Monthly statement updated")

    elif saved_month and not saved_statement:
        st.warning(
            f"⚠️ {selected_month_text} was saved to "
            "Monthly Accounts, but Masjid Monthly "
            "could not be updated."
        )

        st.error(f"Masjid Monthly error: {statement_message}")

    elif not saved_month and saved_statement:
        st.warning(
            f"⚠️ Masjid Monthly was updated, but "
            f"{selected_month_text} could not be saved "
            "to Monthly Accounts."
        )

        st.error(f"Monthly Accounts error: {save_message}")

    else:
        st.error(f"❌ Could not save {selected_month_text}.")

        st.error(f"Monthly Accounts: {save_message}")

        st.error(f"Masjid Monthly: {statement_message}")

# ============================================================
# SAVED MONTHLY ACCOUNTS HISTORY
# ============================================================

st.markdown("---")

st.subheader("📚 Saved Monthly Accounts")

saved_accounts = get_monthly_accounts()

if saved_accounts.empty:
    st.info("No monthly accounts have been saved yet.")

else:
    display_accounts = saved_accounts.copy()

    # --------------------------------------------------------
    # SORT NEWEST MONTH FIRST
    # --------------------------------------------------------

    if "Month" in display_accounts.columns:
        display_accounts["_SortMonth"] = pd.to_datetime(
            display_accounts["Month"],
            format="%B %Y",
            errors="coerce",
        )

        display_accounts = display_accounts.sort_values(
            "_SortMonth",
            ascending=False,
        ).drop(columns=["_SortMonth"])

    # --------------------------------------------------------
    # CLEAN NUMERIC VALUES
    # --------------------------------------------------------

    for column in MONTHLY_ACCOUNT_COLUMNS:
        if column != "Month" and column in display_accounts.columns:
            display_accounts[column] = pd.to_numeric(
                display_accounts[column],
                errors="coerce",
            ).fillna(0.0)

    # --------------------------------------------------------
    # MONTH-BY-MONTH EXPANDABLE HISTORY
    # --------------------------------------------------------

    for index, row in display_accounts.iterrows():
        month_name = str(row.get("Month", "Unknown Month")).strip()

        # ----------------------------------------------------
        # SUMMARY VALUES
        # ----------------------------------------------------

        total_income_saved = float(row.get("Total Income", 0.0))

        total_expenses_saved = float(row.get("Total Expenses", 0.0))

        closing_balance = float(row.get("Closing Balance", 0.0))

        bank_balance = float(row.get("Bank Balance", 0.0))

        cash_in_hand = float(row.get("Cash in Hand", 0.0))

        # ----------------------------------------------------
        # MONTH HEADER
        # ----------------------------------------------------

        with st.expander(
            (
                f"📅 {month_name}"
                f"  •  📥 ₹{total_income_saved:,.2f}"
                f"  •  📤 ₹{total_expenses_saved:,.2f}"
                f"  •  📊 ₹{closing_balance:,.2f}"
            ),
            expanded=(index == display_accounts.index[0]),
        ):
            # =================================================
            # QUICK SUMMARY
            # =================================================

            summary_col1, summary_col2, summary_col3 = st.columns(3)

            with summary_col1:
                st.metric(
                    "🏦 Bank Balance",
                    f"₹{bank_balance:,.2f}",
                )

            with summary_col2:
                st.metric(
                    "💵 Cash in Hand",
                    f"₹{cash_in_hand:,.2f}",
                )

            with summary_col3:
                st.metric(
                    "📊 Closing Balance",
                    f"₹{closing_balance:,.2f}",
                )

            st.markdown("---")

            # =================================================
            # INCOME
            # =================================================

            st.markdown(
                '<div class="account-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="account-section-title">📥 Income</div>',
                unsafe_allow_html=True,
            )

            income_rows = [
                [
                    "Last Month Cash",
                    float(
                        row.get(
                            "Last Month Cash",
                            0.0,
                        )
                    ),
                ],
                [
                    "Monthly Contribution",
                    float(
                        row.get(
                            "Monthly Contribution",
                            0.0,
                        )
                    ),
                ],
                [
                    "Friday Collections",
                    float(
                        row.get(
                            "Friday Collections",
                            0.0,
                        )
                    ),
                ],
                [
                    "Donation",
                    float(
                        row.get(
                            "Donation",
                            0.0,
                        )
                    ),
                ],
                [
                    "Recovery from Imam Sahib",
                    float(
                        row.get(
                            "Recovery from Imam Sahib",
                            0.0,
                        )
                    ),
                ],
                [
                    "Fire Wood Contribution",
                    float(
                        row.get(
                            "Fire Wood Contribution",
                            0.0,
                        )
                    ),
                ],
                [
                    "Total Income",
                    float(
                        row.get(
                            "Total Income",
                            0.0,
                        )
                    ),
                ],
            ]

            income_table = pd.DataFrame(
                income_rows,
                columns=[
                    "Particulars",
                    "Amount",
                ],
            )

            income_table["Amount"] = income_table["Amount"].map(lambda x: f"₹{x:,.2f}")

            st.dataframe(
                income_table,
                width="stretch",
                hide_index=True,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            # =================================================
            # EXPENSES
            # =================================================

            st.markdown(
                '<div class="account-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="account-section-title">📤 Expenses</div>',
                unsafe_allow_html=True,
            )

            expense_rows = [
                [
                    "Salary Paid to Khadim",
                    float(
                        row.get(
                            "Salary Paid to Khadim",
                            0.0,
                        )
                    ),
                ],
                [
                    "Salary Paid to Imam Sahib",
                    float(
                        row.get(
                            "Salary Paid to Imam Sahib",
                            0.0,
                        )
                    ),
                ],
                [
                    "Masjid Electricity Paid",
                    float(
                        row.get(
                            "Masjid Electricity Paid",
                            0.0,
                        )
                    ),
                ],
                [
                    "Darasgah Electricity Paid",
                    float(
                        row.get(
                            "Darasgah Electricity Paid",
                            0.0,
                        )
                    ),
                ],
                [
                    "Other Expenses",
                    float(
                        row.get(
                            "Other Expenses",
                            0.0,
                        )
                    ),
                ],
                [
                    "Total Expenses",
                    float(
                        row.get(
                            "Total Expenses",
                            0.0,
                        )
                    ),
                ],
            ]

            expense_table = pd.DataFrame(
                expense_rows,
                columns=[
                    "Particulars",
                    "Amount",
                ],
            )

            expense_table["Amount"] = expense_table["Amount"].map(
                lambda x: f"₹{x:,.2f}"
            )

            st.dataframe(
                expense_table,
                width="stretch",
                hide_index=True,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            # =================================================
            # BANK MOVEMENT
            # =================================================

            st.markdown(
                '<div class="account-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="account-section-title">🏦 Bank Movement</div>',
                unsafe_allow_html=True,
            )

            bank_movement_rows = [
                [
                    "Amount Credited to Bank",
                    float(
                        row.get(
                            "Amount Credited to Bank",
                            0.0,
                        )
                    ),
                ],
                [
                    "Amount Debited from Bank",
                    float(
                        row.get(
                            "Amount Debited from Bank",
                            0.0,
                        )
                    ),
                ],
            ]

            bank_movement_table = pd.DataFrame(
                bank_movement_rows,
                columns=[
                    "Particulars",
                    "Amount",
                ],
            )

            bank_movement_table["Amount"] = bank_movement_table["Amount"].map(
                lambda x: f"₹{x:,.2f}"
            )

            st.dataframe(
                bank_movement_table,
                width="stretch",
                hide_index=True,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            # =================================================
            # CLOSING BALANCES
            # =================================================

            st.markdown(
                '<div class="account-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="account-section-title">📊 Closing Balances</div>',
                unsafe_allow_html=True,
            )

            balance_col1, balance_col2, balance_col3 = st.columns(3)

            with balance_col1:
                st.metric(
                    "🏦 Bank Balance",
                    f"₹{bank_balance:,.2f}",
                )

            with balance_col2:
                st.metric(
                    "💵 Cash in Hand",
                    f"₹{cash_in_hand:,.2f}",
                )

            with balance_col3:
                st.metric(
                    "📊 Closing Balance",
                    f"₹{closing_balance:,.2f}",
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )
