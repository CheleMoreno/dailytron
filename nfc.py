import streamlit as st
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from supabase import create_client, Client


# ---------------------------------------------
# 1. PAGE CONFIGURATION AND SUPABASE CONNECTION
# ---------------------------------------------

st.set_page_config(
    page_title="Dailytron 3000",
    page_icon="🌿",
    layout="wide"
)


@st.cache_resource
def init_connection():

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SECRET_KEY"]

    return create_client(url, key)


supabase = init_connection()


# Local timezone
TIMEZONE = ZoneInfo("Atlantic/Canary")


# ---------------------------------------------
# 2. DATABASE FUNCTIONS
# ---------------------------------------------

# Retrieve profiles from Supabase
def get_profiles():

    response = (
        supabase.table("profiles")
        .select("id, name")
        .execute()
    )

    return response.data


# Retrieve habits from Supabase
def get_habits():

    response = (
        supabase.table("habits")
        .select("id, profile_id, name, frequency, target, tag_token")
        .execute()
    )

    return response.data


# Get the date range for the current habit period
def get_period_range(habit):

    today = datetime.now(TIMEZONE).date()

    if habit["frequency"] == "daily":

        start_date = today
        end_date = today + timedelta(days=1)

    elif habit["frequency"] == "weekly":

        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)

    else:

        raise ValueError("Unknown habit frequency")

    start = datetime.combine(
        start_date,
        time.min,
        tzinfo=TIMEZONE
    )

    end = datetime.combine(
        end_date,
        time.min,
        tzinfo=TIMEZONE
    )

    return start, end


# Calculate the current total from Supabase
def get_habit_total(habit):

    start, end = get_period_range(habit)

    response = (
        supabase.table("habit_logs")
        .select("delta")
        .eq("habit_id", habit["id"])
        .gte("created_at", start.isoformat())
        .lt("created_at", end.isoformat())
        .execute()
    )

    total = sum(
        int(row["delta"])
        for row in response.data
    )

    return total


# Register a change in Supabase
def save_habit_change(habit, delta, source):

    if delta not in (-1, 1):
        raise ValueError("Delta must be either -1 or 1")

    if source not in ("nfc", "manual", "undo"):
        raise ValueError("Invalid registration source")

    if delta == -1 and source != "undo":
        raise ValueError("Negative registrations must use undo")

    if delta == 1 and source == "undo":
        raise ValueError("Undo must be a negative registration")

    current_total = get_habit_total(habit)

    # Never allow the total to go below zero
    if current_total + delta < 0:
        return current_total

    supabase.table("habit_logs").insert({
        "habit_id": habit["id"],
        "delta": delta,
        "source": source
    }).execute()

    return get_habit_total(habit)

def register_nfc_token(token):
    # Find the habit associated with this token
    response = (
        supabase.table("habits")
        .select("id, profile_id, name, frequency, target, tag_token")
        .eq("tag_token", token)
        .execute()
    )

    # If no habit matches the token
    if not response.data:
        return None

    habit = response.data[0]

    # Register one completion
    save_habit_change(
        habit,
        delta=1,
        source="nfc"
    )

    return habit


# ---------------------------------------------
# 3. RETRIEVE DATABASE INFORMATION
# ---------------------------------------------

profiles = get_profiles()
habits = get_habits()

# Check whether the app was opened through an NFC tag
nfc_token = st.query_params.get("tag")

if nfc_token:
    # Remove the token from the URL so it can't register again
    st.query_params.clear()

    # Register the habit
    registered_habit = register_nfc_token(nfc_token)

    if registered_habit:
        st.success(
            f"✅ {registered_habit['name']} registered successfully!"
        )
    else:
        st.error("Invalid NFC tag.")


# Associate habits with their profiles
profiles_with_habits = []

for profile in profiles:

    profile_habits = [
        habit for habit in habits
        if habit["profile_id"] == profile["id"]
    ]

    profiles_with_habits.append({
        "profile": profile,
        "habits": profile_habits
    })


# ---------------------------------------------
# 4. CUSTOM CSS
# ---------------------------------------------

st.markdown("""
<style>


/* Main background */
.stApp {
    background-color: #F3F0E9;
}

/* Streamlit header */
header[data-testid="stHeader"] {
    background-color: #F3F0E9 !important;
    border-bottom: none !important;
}

/* Move success messages down */
div[data-testid="stAlert"] {
    margin-top: 1rem !important;
}

/* Reduce wasted space at the top */
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 1rem;
}

/* Main title */
h1 {
    color: #454B32 !important;
    font-family: sans-serif;
    font-size: 38px !important;
    font-weight: 800;
    margin-bottom: 0px !important;
}

/* Profile names and section titles */
h2, h3 {
    color: #596344 !important;
    font-weight: 750 !important;
}

/* Remove borders from nested containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: transparent;
    border: none !important;
    border-radius: 0;
    box-shadow: none !important;
}
/* Profile cards - single subtle outline */
.st-key-profile_chele,
.st-key-profile_isa {
    background-color: #FFFCF6;
    border: 1px solid #E5DDCE !important;
    border-radius: 18px;
    padding: 15px;
}

/* General text */
p {
    color: #55564F;
}

/* Captions */
.stCaption {
    color: #88877C !important;
}

/* Dividers */
hr {
    border-color: #E2DED4;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

/* Progress bars */
.stProgress > div > div > div > div {
    background-color: #84916B;
}

/* -------------------------------- */
/* ADD BUTTON */
/* -------------------------------- */

.stButton > button[kind="primary"] {
    background-color: #84916B;
    color: white;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    border-radius: 10px;
    font-weight: 650;
    padding: 5px;
}

.stButton > button[kind="primary"]:hover {
    background-color: #6F7D57;
    color: white;
    border: none !important;
    box-shadow: none !important;
}

/* -------------------------------- */
/* UNDO BUTTON */
/* -------------------------------- */

.stButton > button[kind="secondary"] {
    background-color: #E8E5DE;
    color: #596344;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    border-radius: 10px;
    font-weight: 600;
    padding: 5px;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #D9E0CC;
    color: #35412E;
    border: none !important;
    box-shadow: none !important;
}

/* Disabled buttons */
.stButton > button:disabled {
    background-color: #E8E5DE;
    color: #929184;
    border: none !important;
    box-shadow: none !important;
}


</style>
""", unsafe_allow_html=True)


# ---------------------------------------------
# 5. PROFILE DISPLAY FUNCTION
# ---------------------------------------------

def show_profile(profile, profile_habits, profile_key):

    with st.container(border=True, key=f"profile_{profile_key}"):

        st.subheader(profile["name"])

        st.caption(
            f"{len(profile_habits)} habits in your routine"
        )

        for habit in profile_habits:

            habit_id = habit["id"]

            # Determine period label
            if habit["frequency"] == "daily":
                period_label = "Daily"

            else:
                period_label = "Weekly"

            # Get current progress from Supabase
            count = get_habit_total(habit)

            target = habit["target"]

            # Habit information
            st.markdown(f"**{habit['name']}**")

            st.caption(
                f"{period_label} · Target: {target}"
            )

            # Progress indicator
            progress = min(count / target, 1.0)

            st.progress(progress)

            st.caption(
                f"{count} / {target} completed"
            )

            # --------------------------------
            # ADD AND UNDO BUTTONS
            # --------------------------------

            col_add, col_undo = st.columns(
                [3, 1],
                gap="small"
            )

            with col_add:

                if st.button(
                    "＋ Add",
                    key=f"add_{habit_id}",
                    type="primary",
                    use_container_width=True
                ):

                    save_habit_change(
                        habit,
                        delta=1,
                        source="manual"
                    )

                    st.rerun()


            with col_undo:

                if st.button(
                    "－",
                    key=f"undo_{habit_id}",
                    type="secondary",
                    disabled=count <= 0,
                    use_container_width=True
                ):

                    save_habit_change(
                        habit,
                        delta=-1,
                        source="undo"
                    )

                    st.rerun()

            # Space between habits
            st.write("")


# ---------------------------------------------
# 6. DASHBOARD HEADER
# ---------------------------------------------

now = datetime.now(TIMEZONE)

st.title("dailytron.")

st.caption(
    now.strftime("%A, %B %d, %Y")
)

st.divider()


# ---------------------------------------------
# 7. TWO-COLUMN LAYOUT
# ---------------------------------------------

col1, col2 = st.columns(2, gap="large")


# Display first profile
with col1:

    if len(profiles_with_habits) >= 1:

        show_profile(
            profiles_with_habits[0]["profile"],
            profiles_with_habits[0]["habits"],
            "chele"
        )


# Display second profile
with col2:

    if len(profiles_with_habits) >= 2:

        show_profile(
            profiles_with_habits[1]["profile"],
            profiles_with_habits[1]["habits"],
            "isa"
        )


# ---------------------------------------------
# 8. FOOTER
# ---------------------------------------------

st.write("")
st.divider()

st.markdown(
    """
    <div style="
        text-align: center;
        color: #99978C;
        font-size: 12px;
        padding: 10px;
    ">
        EL MERO TRACKER 🌿
    </div>
    """,
    unsafe_allow_html=True
)
