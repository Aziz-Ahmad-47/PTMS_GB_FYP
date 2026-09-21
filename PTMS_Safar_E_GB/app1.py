import streamlit as st
from groq import Groq
from dotenv import load_dotenv

import os
import json
from datetime import datetime

from services.location_service import (
    get_coordinates,
    get_elevation
)

from services.weather_service import (
    get_weather
)

from services.route_service import (
    get_route
)

from database.chat_db import (
    init_database,
    create_chat,
    update_chat,
    add_message,
    get_all_chats,
    get_chat,
    get_chat_messages,
    delete_chat
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        GROQ_API_KEY = None

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

client = Groq(
    api_key=GROQ_API_KEY
)

MODEL = "openai/gpt-oss-20b"

st.set_page_config(
    page_title="AI TravelMate",
    page_icon="✈️",
    layout="wide"
)


# =========================================================
# DATABASE
# =========================================================

init_database()


# =========================================================
# SESSION STATE
# =========================================================

def initialize_session():

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "trip_info" not in st.session_state:
        st.session_state.trip_info = {}

    if "location" not in st.session_state:
        st.session_state.location = None

    if "elevation" not in st.session_state:
        st.session_state.elevation = None

    if "weather" not in st.session_state:
        st.session_state.weather = ""

    if "route" not in st.session_state:
        st.session_state.route = None


initialize_session()


# =========================================================
# CREATE NEW DATABASE CHAT
# =========================================================

def start_new_chat():

    chat_id = create_chat(
        title="New Chat",
        trip_info={}
    )

    st.session_state.chat_id = chat_id

    st.session_state.messages = []

    st.session_state.trip_info = {}

    st.session_state.location = None

    st.session_state.elevation = None

    st.session_state.weather = ""

    st.session_state.route = None


# =========================================================
# ENSURE ACTIVE CHAT
# =========================================================

if st.session_state.chat_id is None:

    start_new_chat()


# =========================================================
# LOAD CHAT FROM DATABASE
# =========================================================

def load_chat(chat_id):

    chat = get_chat(
        chat_id
    )

    if not chat:
        return

    messages = get_chat_messages(
        chat_id
    )

    st.session_state.chat_id = chat_id

    st.session_state.messages = [
        {
            "role": message["role"],
            "content": message["content"]
        }

        for message in messages
    ]


    # -----------------------------------------
    # Restore trip information
    # -----------------------------------------

    try:

        trip_info = json.loads(
            chat["trip_info"]
        )

    except Exception:

        trip_info = {}


    st.session_state.trip_info = (
        trip_info
    )


    # -----------------------------------------
    # Restore destination data
    # -----------------------------------------

    destination = trip_info.get(
        "destination"
    )

    if destination:

        try:

            location = get_coordinates(
                destination
            )

            if location:

                st.session_state.location = (
                    location
                )

                elevation = get_elevation(
                    location["latitude"],
                    location["longitude"]
                )

                st.session_state.elevation = (
                    elevation
                )

        except Exception:

            st.session_state.location = None

            st.session_state.elevation = None


# =========================================================
# TITLE GENERATOR
# =========================================================

def generate_chat_title(
    user_input
):

    text = user_input.strip()

    if len(text) <= 45:

        return text

    return (
        text[:45].rstrip()
        + "..."
    )


# =========================================================
# SAFE GROQ CALL
# =========================================================

def groq_call(
    messages,
    temperature=0.3,
    max_tokens=6000
):

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:

            return ""

        return content.strip()

    except Exception as error:

        return (
            f"ERROR:{str(error)}"
        )


# =========================================================
# EXTRACT TRIP INFORMATION
# =========================================================

def extract_trip_info(
    user_input
):

    prompt = f"""
You are a travel information extraction assistant.

Extract ONLY information explicitly stated
by the user.

Return ONLY valid JSON.

Use exactly:

{{
    "starting_location": null,
    "destination": null,
    "days": null,
    "travelers": null,
    "budget_pkr": null,
    "interests": []
}}

Rules:

- Do not guess.
- Do not invent information.
- "location", "destination", "place",
  "there", and "it" are not destinations.
- Only extract actual place names.
- days must be a number.
- travelers must be a number.
- budget_pkr must be a number.
- interests must be a list.
- Missing information must be null.
- If user updates an existing value,
  return the new value.

User message:

{user_input}
"""

    result = groq_call(
        [
            {
                "role": "system",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=500
    )

    if result.startswith("ERROR:"):

        return {}


    result = result.replace(
        "```json",
        ""
    )

    result = result.replace(
        "```",
        ""
    )

    result = result.strip()


    try:

        data = json.loads(
            result
        )

        if isinstance(
            data,
            dict
        ):

            return data

    except json.JSONDecodeError:

        pass


    return {}


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(
    user_input
):

    prompt = f"""
Classify this travel-related user message.

Return ONLY ONE category.

Categories:

plan_trip
route
destination_info
elevation
weather
update_trip
general_question

Definitions:

plan_trip:
User asks for itinerary, travel plan,
day-by-day plan, or complete trip planning.

route:
User asks for road map, route,
driving route, road journey,
distance, driving time, or directions.

destination_info:
User asks about destination information,
places, attractions, overview, highlights,
or things to know.

elevation:
User asks height, altitude,
elevation, or height above sea level.

weather:
User asks weather, temperature,
rain, or forecast.

update_trip:
User wants to change existing trip
information such as days, budget,
travelers, destination, starting location,
or interests.

general_question:
Everything else.

IMPORTANT:

"road map" means route.

Do NOT classify road map as plan_trip.

"location", "destination", "it",
and "there" are not actual destinations.

User message:

{user_input}

Return ONLY the category name.
"""

    result = groq_call(
        [
            {
                "role": "system",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=50
    )

    result = result.strip().lower()


    valid = [
        "plan_trip",
        "route",
        "destination_info",
        "elevation",
        "weather",
        "update_trip",
        "general_question"
    ]


    if result in valid:

        return result


    return "general_question"


# =========================================================
# WEATHER FORMAT
# =========================================================

def format_weather(
    weather_data
):

    daily = weather_data.get(
        "daily",
        {}
    )

    dates = daily.get(
        "time",
        []
    )

    max_temps = daily.get(
        "temperature_2m_max",
        []
    )

    min_temps = daily.get(
        "temperature_2m_min",
        []
    )

    rain_probs = daily.get(
        "precipitation_probability_max",
        []
    )


    if not dates:

        return (
            "Weather information "
            "is unavailable."
        )


    result = []


    for index in range(
        len(dates)
    ):

        minimum = (
            min_temps[index]
            if index < len(min_temps)
            else "N/A"
        )

        maximum = (
            max_temps[index]
            if index < len(max_temps)
            else "N/A"
        )

        rain = (
            rain_probs[index]
            if index < len(rain_probs)
            else "N/A"
        )


        result.append(
            f"""
### 📅 {dates[index]}

🌡️ **Temperature:** {minimum}°C - {maximum}°C

🌧️ **Rain Probability:** {rain}%
"""
        )


    return "\n".join(
        result
    )


# =========================================================
# GENERATE ITINERARY
# =========================================================

def generate_itinerary(
    trip_info,
    weather_text=""
):

    prompt = f"""
You are AI TravelMate,
a professional travel planner.

Create a COMPLETE and practical
day-by-day travel itinerary.

TRIP INFORMATION:

Starting Location:
{trip_info.get("starting_location")}

Destination:
{trip_info.get("destination")}

Days:
{trip_info.get("days")}

Travelers:
{trip_info.get("travelers")}

Budget:
PKR {trip_info.get("budget_pkr")}

Interests:
{trip_info.get("interests")}

WEATHER:

{weather_text}


IMPORTANT:

The user explicitly requested
a travel itinerary.

Return the ACTUAL complete itinerary.

Do NOT return only:

"Your itinerary has been created."

For every day include:

## Day X

### 🌅 Morning

Activities and places.

### ☀️ Afternoon

Activities and places.

### 🌆 Evening

Activities and places.

### 💰 Estimated Daily Cost

Approximate cost.

Continue until the exact
requested number of days is completed.

Then include:

# 💰 Estimated Budget

| Category | Estimated Cost |
|---|---:|
| Transportation | PKR ... |
| Accommodation | PKR ... |
| Food | PKR ... |
| Activities | PKR ... |
| Other Expenses | PKR ... |
| **Total Estimated Cost** | **PKR ...** |

Then:

# 🎒 Packing Suggestions

- item
- item
- item
- item
- item

Rules:

- Respect exact number of days.
- Consider travelers.
- Consider budget.
- Consider interests.
- Use available weather.
- Costs are estimates.
- Do not claim live prices.
- Do not claim live hotel availability.
- Do not invent real-time transport information.
"""

    result = groq_call(
        [
            {
                "role": "system",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=8000
    )


    if result.startswith(
        "ERROR:"
    ):

        return ""


    if len(
        result.strip()
    ) < 300:

        return ""


    return result


# =========================================================
# DESTINATION INFORMATION
# =========================================================

def generate_destination_info(
    destination,
    location,
    elevation
):

    prompt = f"""
You are AI TravelMate.

Give useful information about:

Destination:
{destination}

Latitude:
{location["latitude"]}

Longitude:
{location["longitude"]}

Elevation:
{elevation} meters above sea level.

Include:

## 📍 Overview

## 🌍 Location

## ⛰️ Elevation

## 🏔️ Highlights

## 🎒 Travel Tips

Keep it useful and concise.

Do not invent exact facts.
"""

    result = groq_call(
        [
            {
                "role": "system",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=1800
    )


    if result.startswith(
        "ERROR:"
    ):

        return (
            "I couldn't generate "
            "destination information "
            "right now."
        )


    return result


# =========================================================
# GENERAL QUESTION
# =========================================================

def answer_general_question(
    user_input,
    trip_info,
    messages
):

    conversation = messages[-12:]


    prompt = f"""
You are AI TravelMate.

Current trip information:

{json.dumps(
    trip_info,
    indent=2
)}

Answer the user's actual question.

Rules:

- Remember current destination.
- Do not accidentally change destination.
- "it", "there", "location",
  and "destination" refer to
  the existing destination.
- Do not generate an itinerary
  unless explicitly requested.
- Answer the actual question.
- Do not invent live information.
- Be helpful and concise.

Latest question:

{user_input}
"""


    result = groq_call(
        [
            {
                "role": "system",
                "content": prompt
            }
        ]
        + conversation,
        temperature=0.4,
        max_tokens=2500
    )


    if result.startswith(
        "ERROR:"
    ):

        return (
            "Sorry, I couldn't process "
            "that question right now."
        )


    return result


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        "✈️🚌SAFAR-E-GB🚗🚐"
    )


    # -----------------------------------------------------
    # NEW CHAT
    # -----------------------------------------------------

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        start_new_chat()

        st.rerun()


    # -----------------------------------------------------
    # CHAT HISTORY
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "💬 Recent Chats"
    )


    chats = get_all_chats()


    if not chats:

        st.caption(
            "No previous chats."
        )


    for chat in chats:

        chat_id = chat["id"]

        title = chat["title"]


        col1, col2 = st.columns(
            [5, 1]
        )


        with col1:

            if st.button(
                title,
                key=f"open_{chat_id}",
                use_container_width=True
            ):

                load_chat(
                    chat_id
                )

                st.rerun()


        with col2:

            if st.button(
                "🗑️",
                key=f"delete_{chat_id}"
            ):

                delete_chat(
                    chat_id
                )


                # If active chat deleted,
                # create a new one.

                if (
                    st.session_state.chat_id
                    == chat_id
                ):

                    st.session_state.chat_id = None

                    st.session_state.messages = []

                    st.session_state.trip_info = {}

                    st.session_state.location = None

                    st.session_state.elevation = None

                    st.session_state.weather = ""

                    st.session_state.route = None


                    start_new_chat()


                st.rerun()


    # -----------------------------------------------------
    # TRIP INFORMATION
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "🧳 Trip Information"
    )


    trip = (
        st.session_state.trip_info
    )


    if trip:

        if trip.get(
            "starting_location"
        ):

            st.write(
                f"**From:** "
                f"{trip['starting_location']}"
            )


        if trip.get(
            "destination"
        ):

            st.write(
                f"**Destination:** "
                f"{trip['destination']}"
            )


        if trip.get(
            "days"
        ):

            st.write(
                f"**Days:** "
                f"{trip['days']}"
            )


        if trip.get(
            "travelers"
        ):

            st.write(
                f"**Travelers:** "
                f"{trip['travelers']}"
            )


        if trip.get(
            "budget_pkr"
        ):

            st.write(
                f"**Budget:** "
                f"PKR {trip['budget_pkr']:,}"
            )


        if trip.get(
            "interests"
        ):

            st.write(
                f"**Interests:** "
                f"{', '.join(trip['interests'])}"
            )


    else:

        st.info(
            "Your trip information "
            "will appear here."
        )


    # -----------------------------------------------------
    # DESTINATION DATA
    # -----------------------------------------------------

    if st.session_state.location:

        st.divider()

        st.subheader(
            "📍 Destination Data"
        )


        location = (
            st.session_state.location
        )


        st.write(
            f"**Latitude:** "
            f"{location['latitude']:.4f}"
        )


        st.write(
            f"**Longitude:** "
            f"{location['longitude']:.4f}"
        )


        if (
            st.session_state.elevation
            is not None
        ):

            st.write(
                f"**Elevation:** "
                f"{st.session_state.elevation} m"
            )

            st.caption(
                "Above sea level"
            )


    st.divider()

    st.caption(
        "AI-powered personal "
        "travel assistant"
    )


# =========================================================
# MAIN TITLE
# =========================================================

st.title(
    "🏔️ SAFAR-E-GB"
)

st.caption(
    "Your AI-powered personal "
    "travel assistant"
)


# =========================================================
# DISPLAY COMPLETE CHAT HISTORY
# =========================================================

for message in (
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# CHAT INPUT
# =========================================================

user_input = st.chat_input(
    "Ask me anything about your trip..."
)


# =========================================================
# PROCESS MESSAGE
# =========================================================

if user_input:

    # -----------------------------------------------------
    # SAVE USER MESSAGE IN SESSION
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # -----------------------------------------------------
    # SAVE USER MESSAGE IN DATABASE
    # -----------------------------------------------------

    add_message(
        st.session_state.chat_id,
        "user",
        user_input
    )


    # -----------------------------------------------------
    # CREATE CHAT TITLE
    # -----------------------------------------------------

    current_messages = (
        st.session_state.messages
    )


    if len(
        current_messages
    ) == 1:

        title = generate_chat_title(
            user_input
        )


        update_chat(
            st.session_state.chat_id,
            title=title
        )


    # -----------------------------------------------------
    # SHOW USER
    # -----------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            user_input
        )


    # -----------------------------------------------------
    # DETECT INTENT
    # -----------------------------------------------------

    with st.spinner(
        "🔎 Understanding..."
    ):

        intent = detect_intent(
            user_input
        )


    # -----------------------------------------------------
    # EXTRACT INFORMATION
    # -----------------------------------------------------

    extracted = extract_trip_info(
        user_input
    )


    for key, value in (
        extracted.items()
    ):

        if (
            value is not None
            and value != []
        ):

            st.session_state.trip_info[
                key
            ] = value


    trip = (
        st.session_state.trip_info
    )


    # -----------------------------------------------------
    # SAVE UPDATED TRIP INFO
    # -----------------------------------------------------

    update_chat(
        st.session_state.chat_id,
        trip_info=trip
    )


    destination = trip.get(
        "destination"
    )

    starting_location = trip.get(
        "starting_location"
    )

    days = trip.get(
        "days"
    )


    # =====================================================
    # PLAN TRIP
    # =====================================================

    if intent == "plan_trip":

        if not destination:

            ai_reply = (
                "Sure! ✈️ "
                "Please tell me your destination."
            )


        elif not days:

            ai_reply = (
                "Great! 👍 "
                "How many days would you "
                "like to travel?"
            )


        else:

            with st.spinner(
                "📍 Finding destination..."
            ):

                location = (
                    get_coordinates(
                        destination
                    )
                )


            if not location:

                ai_reply = (
                    f"I couldn't find "
                    f"**{destination}**. "
                    "Please check the "
                    "destination name."
                )


            else:

                st.session_state.location = (
                    location
                )


                # -----------------------------------------
                # WEATHER
                # -----------------------------------------

                weather_text = ""


                try:

                    with st.spinner(
                        "🌤️ Getting weather..."
                    ):

                        weather_data = get_weather(
                            location["latitude"],
                            location["longitude"],
                            forecast_days=min(
                                int(days),
                                16
                            )
                        )


                        weather_text = (
                            format_weather(
                                weather_data
                            )
                        )


                        st.session_state.weather = (
                            weather_text
                        )


                except Exception:

                    weather_text = (
                        "Weather information "
                        "is currently unavailable."
                    )


                # -----------------------------------------
                # ELEVATION
                # -----------------------------------------

                try:

                    elevation = (
                        get_elevation(
                            location["latitude"],
                            location["longitude"]
                        )
                    )


                    st.session_state.elevation = (
                        elevation
                    )


                except Exception:

                    elevation = None


                # -----------------------------------------
                # ITINERARY
                # -----------------------------------------

                with st.spinner(
                    "✈️ Creating itinerary..."
                ):

                    itinerary = (
                        generate_itinerary(
                            trip,
                            weather_text
                        )
                    )


                if not itinerary:

                    ai_reply = (
                        "I couldn't generate "
                        "the complete itinerary "
                        "right now. Please try "
                        "again."
                    )


                else:

                    ai_reply = (
                        f"## ✈️ {days}-Day "
                        f"Trip to {destination}\n\n"
                    )


                    if elevation is not None:

                        ai_reply += (
                            f"⛰️ **Destination "
                            f"Elevation:** "
                            f"{elevation} meters "
                            f"above sea level\n\n"
                        )


                    ai_reply += itinerary


    # =====================================================
    # ROUTE
    # =====================================================

    elif intent == "route":

        if not starting_location:

            ai_reply = (
                "🛣️ To create your road route, "
                "I need your **starting location**."
            )


        elif not destination:

            ai_reply = (
                "🛣️ To create your road route, "
                "I need your **destination**."
            )


        else:

            with st.spinner(
                "🛣️ Calculating road route..."
            ):

                start = get_coordinates(
                    starting_location
                )

                end = get_coordinates(
                    destination
                )


            if not start:

                ai_reply = (
                    f"I couldn't find "
                    f"**{starting_location}**."
                )


            elif not end:

                ai_reply = (
                    f"I couldn't find "
                    f"**{destination}**."
                )


            else:

                try:

                    route = get_route(
                        start["latitude"],
                        start["longitude"],
                        end["latitude"],
                        end["longitude"]
                    )

                except Exception:

                    route = None


                if not route:

                    ai_reply = (
                        "I couldn't retrieve "
                        "the road route right now."
                    )


                else:

                    st.session_state.route = (
                        route
                    )


                    distance = (
                        route["distance_km"]
                    )

                    duration = (
                        route["duration_hours"]
                    )


                    hours = int(
                        duration
                    )

                    minutes = int(
                        (duration - hours) * 60
                    )


                    ai_reply = (
                        "## 🛣️ Road Route\n\n"

                        f"**From:** "
                        f"{starting_location}\n\n"

                        f"**To:** "
                        f"{destination}\n\n"

                        f"📏 **Driving Distance:** "
                        f"{distance:.1f} km\n\n"

                        f"⏱️ **Estimated Driving Time:** "
                        f"{hours}h {minutes}m\n\n"

                        "### 🗺️ Route Information\n\n"

                        "The route has been "
                        "calculated using a "
                        "road-routing service.\n\n"

                        "⚠️ Actual travel time may "
                        "vary because of traffic, "
                        "weather, road conditions, "
                        "construction and stops."
                    )


    # =====================================================
    # DESTINATION INFO
    # =====================================================

    elif intent == "destination_info":

        if not destination:

            ai_reply = (
                "📍 Which destination "
                "would you like to "
                "know about?"
            )


        else:

            with st.spinner(
                "📍 Getting destination information..."
            ):

                location = (
                    get_coordinates(
                        destination
                    )
                )


            if not location:

                ai_reply = (
                    f"I couldn't find "
                    f"**{destination}**."
                )


            else:

                st.session_state.location = (
                    location
                )


                try:

                    elevation = (
                        get_elevation(
                            location["latitude"],
                            location["longitude"]
                        )
                    )


                    st.session_state.elevation = (
                        elevation
                    )


                except Exception:

                    elevation = None


                ai_reply = (
                    generate_destination_info(
                        destination,
                        location,
                        elevation
                    )
                )


    # =====================================================
    # ELEVATION
    # =====================================================

    elif intent == "elevation":

        if not destination:

            ai_reply = (
                "⛰️ Please tell me "
                "the destination first."
            )


        else:

            location = (
                get_coordinates(
                    destination
                )
            )


            if not location:

                ai_reply = (
                    f"I couldn't find "
                    f"**{destination}**."
                )


            else:

                try:

                    elevation = (
                        get_elevation(
                            location["latitude"],
                            location["longitude"]
                        )
                    )


                    st.session_state.location = (
                        location
                    )

                    st.session_state.elevation = (
                        elevation
                    )


                    ai_reply = (
                        f"## ⛰️ {destination}\n\n"

                        f"**Elevation:** "
                        f"{elevation} meters "
                        f"above sea level.\n\n"

                        f"📍 **Latitude:** "
                        f"{location['latitude']:.4f}\n\n"

                        f"📍 **Longitude:** "
                        f"{location['longitude']:.4f}"
                    )


                except Exception:

                    ai_reply = (
                        "I couldn't retrieve "
                        "the elevation right now."
                    )


    # =====================================================
    # WEATHER
    # =====================================================

    elif intent == "weather":

        if not destination:

            ai_reply = (
                "🌤️ Which destination "
                "do you want weather "
                "information for?"
            )


        else:

            location = (
                get_coordinates(
                    destination
                )
            )


            if not location:

                ai_reply = (
                    f"I couldn't find "
                    f"**{destination}**."
                )


            else:

                try:

                    weather_data = (
                        get_weather(
                            location["latitude"],
                            location["longitude"],
                            forecast_days=5
                        )
                    )


                    weather_text = (
                        format_weather(
                            weather_data
                        )
                    )


                    st.session_state.location = (
                        location
                    )

                    st.session_state.weather = (
                        weather_text
                    )


                    ai_reply = (
                        f"## 🌤️ Weather in "
                        f"{destination}\n\n"
                        f"{weather_text}"
                    )


                except Exception:

                    ai_reply = (
                        "Weather information "
                        "is currently unavailable."
                    )


    # =====================================================
    # UPDATE TRIP
    # =====================================================

    elif intent == "update_trip":

        if not extracted:

            ai_reply = (
                "What would you like "
                "to change in your trip?"
            )


        else:

            updates = []


            for key, value in (
                extracted.items()
            ):

                if (
                    value is not None
                    and value != []
                ):

                    label = (
                        key
                        .replace(
                            "_",
                            " "
                        )
                        .title()
                    )


                    updates.append(
                        f"**{label}:** {value}"
                    )


            ai_reply = (
                "## ✅ Trip Updated\n\n"

                + "\n".join(
                    updates
                )

                + "\n\n"

                "Your previous itinerary "
                "is still available above.\n\n"

                "Say **generate the updated "
                "itinerary** when you want "
                "a new plan."
            )


    # =====================================================
    # GENERAL QUESTION
    # =====================================================

    else:

        ai_reply = (
            answer_general_question(
                user_input,
                trip,
                st.session_state.messages
            )
        )


    # =====================================================
    # SAVE AI MESSAGE
    # =====================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_reply
        }
    )


    add_message(
        st.session_state.chat_id,
        "assistant",
        ai_reply
    )


    # -----------------------------------------------------
    # SAVE LATEST TRIP INFO
    # -----------------------------------------------------

    update_chat(
        st.session_state.chat_id,
        trip_info=(
            st.session_state.trip_info
        )
    )


    # =====================================================
    # SHOW AI RESPONSE
    # =====================================================

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            ai_reply
        )
