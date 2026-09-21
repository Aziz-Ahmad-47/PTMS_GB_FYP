import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import json

from services.location_service import (
    get_coordinates,
    get_elevation
)

from services.weather_service import get_weather


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI TravelMate",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ AI TravelMate")
st.caption("Your AI-powered personal travel assistant")


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "trip_info" not in st.session_state:
    st.session_state.trip_info = {}

if "itinerary" not in st.session_state:
    st.session_state.itinerary = ""

if "weather" not in st.session_state:
    st.session_state.weather = ""

if "location" not in st.session_state:
    st.session_state.location = None

if "elevation" not in st.session_state:
    st.session_state.elevation = None


# =========================================================
# SHOW PREVIOUS CHAT
# =========================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =========================================================
# FUNCTION 1
# EXTRACT TRIP INFORMATION
# =========================================================

def extract_trip_info(user_input):

    extraction_prompt = f"""
You are a travel information extraction assistant.

Extract ONLY explicit travel information from the user's message.

Return ONLY valid JSON.

Use exactly these fields:

{{
    "starting_location": null,
    "destination": null,
    "days": null,
    "travelers": null,
    "budget_pkr": null,
    "interests": []
}}

IMPORTANT RULES:

1. Do NOT guess information.

2. Only extract information explicitly mentioned
   in the user's message.

3. Do NOT interpret words like:
   "location"
   "destination"
   "place"
   "it"
   "there"
   as a destination.

4. If the user says:
   "tell me about the destination"

   return:

   {{
       "starting_location": null,
       "destination": null,
       "days": null,
       "travelers": null,
       "budget_pkr": null,
       "interests": []
   }}

5. If the user updates an existing value,
   extract ONLY the new value.

6. days must be a number.

7. travelers must be a number.

8. budget_pkr must be a number.

9. interests must be a list of strings.

User message:

{user_input}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": extraction_prompt
            }
        ],
        temperature=0
    )

    text = response.choices[0].message.content.strip()

    if text.startswith("```"):

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        return {}


# =========================================================
# FUNCTION 2
# DETECT USER INTENT
# =========================================================

def detect_intent(user_input):

    intent_prompt = f"""
You are an intent classifier for an AI travel assistant.

Classify the user's message into exactly ONE of these intents:

plan_trip
destination_info
elevation
weather
update_trip
general_question

Definitions:

plan_trip:
User wants to create, generate, make, or plan a trip itinerary.

Examples:
- plan a trip
- make a trip plan
- create itinerary
- plan 5 days in Hunza

destination_info:
User wants information/details about a destination.

Examples:
- tell me about Hunza
- tell me more about the destination
- destination details
- what is Hunza like

elevation:
User asks about height above sea level, elevation, altitude,
mountain height, or destination elevation.

Examples:
- what is the height of Hunza?
- how high is Hunza above sea level?
- destination elevation
- altitude of Hunza

weather:
User asks about weather or forecast.

Examples:
- what is the weather?
- weather in Hunza
- will it rain?

update_trip:
User wants to change existing trip information.

Examples:
- make it 6 days
- increase budget to 60000
- change destination to Skardu

general_question:
Any other travel-related question.

IMPORTANT:

Do not classify "destination" or "location"
as an actual destination unless the user gives a place name.

User message:

{user_input}

Return ONLY one intent name.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": intent_prompt
            }
        ],
        temperature=0
    )

    intent = response.choices[0].message.content.strip()

    valid_intents = [
        "plan_trip",
        "destination_info",
        "elevation",
        "weather",
        "update_trip",
        "general_question"
    ]

    if intent not in valid_intents:
        return "general_question"

    return intent


# =========================================================
# FUNCTION 3
# WEATHER FORMATTER
# =========================================================

def format_weather(weather_data):

    daily = weather_data.get("daily", {})

    dates = daily.get("time", [])
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

    weather_text = []

    for i in range(len(dates)):

        weather_text.append(
            f"""
### 📅 {dates[i]}

🌡️ **Temperature:**  
{min_temps[i]}°C - {max_temps[i]}°C

🌧️ **Rain Probability:**  
{rain_probs[i]}%
"""
        )

    return "\n".join(weather_text)


# =========================================================
# FUNCTION 4
# GENERATE ITINERARY
# =========================================================

def generate_itinerary(
    trip_info,
    weather_text=""
):

    itinerary_prompt = f"""
You are AI TravelMate, a professional travel planning assistant.

Create a practical and realistic day-by-day travel itinerary.

TRIP INFORMATION

Starting Location:
{trip_info.get("starting_location")}

Destination:
{trip_info.get("destination")}

Number of Days:
{trip_info.get("days")}

Number of Travelers:
{trip_info.get("travelers")}

Budget:
{trip_info.get("budget_pkr")} PKR

Interests:
{trip_info.get("interests")}

Weather Forecast:
{weather_text}


Create an itinerary for the COMPLETE number of requested days.

For every day include:

## Day X

### 🌅 Morning

- Activities
- Places to visit

### ☀️ Afternoon

- Activities
- Places to visit

### 🌆 Evening

- Activities
- Places to visit

### 💰 Estimated Daily Cost

- Approximate cost


After all days provide:

# 💰 Estimated Budget

| Category | Estimated Cost |
|---|---:|
| Transportation | PKR ... |
| Accommodation | PKR ... |
| Food | PKR ... |
| Activities | PKR ... |
| Other Expenses | PKR ... |
| **Total Estimated Cost** | **PKR ...** |

Then provide:

# 🎒 Packing Suggestions

- Item 1
- Item 2
- Item 3
- Item 4

IMPORTANT:

- Respect the requested number of days.
- Consider number of travelers.
- Consider the budget.
- Consider interests.
- Use the supplied weather forecast.
- Prices are approximate.
- Do not claim live hotel availability.
- Do not claim real-time transport availability.
- Do not invent weather.
- Keep the plan practical.
- Return Markdown.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": itinerary_prompt
            }
        ],
        temperature=0.4
    )

    return response.choices[0].message.content


# =========================================================
# FUNCTION 5
# DESTINATION INFORMATION
# =========================================================

def generate_destination_info(
    destination,
    location,
    elevation
):

    prompt = f"""
You are AI TravelMate.

Provide useful destination information about:

Destination:
{destination}

Coordinates:
Latitude: {location.get("latitude")}
Longitude: {location.get("longitude")}

Elevation:
{elevation} meters above sea level

Provide:

## 📍 Destination Overview

Give a short introduction.

## ⛰️ Elevation

Explain the destination's approximate elevation
above sea level.

## 🌍 Location

Explain where the destination is located.

## 🏔️ Highlights

Mention important natural or tourist attractions.

## 🎒 Travel Tips

Give practical travel advice.

Do not invent exact facts that are not provided.
Keep the response concise and useful.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# =========================================================
# USER INPUT
# =========================================================

user_input = st.chat_input(
    "Ask about your trip..."
)


if user_input:

    # -----------------------------------------------------
    # SAVE USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)


    # -----------------------------------------------------
    # DETECT INTENT
    # -----------------------------------------------------

    with st.spinner("🔎 Understanding your request..."):

        intent = detect_intent(user_input)


    # -----------------------------------------------------
    # EXTRACT TRIP INFORMATION
    # -----------------------------------------------------

    extracted_info = extract_trip_info(
        user_input
    )


    for key, value in extracted_info.items():

        if value is not None and value != []:

            st.session_state.trip_info[key] = value


    trip_info = st.session_state.trip_info

    destination = trip_info.get(
        "destination"
    )

    days = trip_info.get(
        "days"
    )


    # =====================================================
    # INTENT: PLAN TRIP
    # =====================================================

    if intent == "plan_trip":

        if not destination:

            ai_reply = (
                "Sure! ✈️ Please tell me your "
                "**destination** first."
            )

        elif not days:

            ai_reply = (
                "Sure! ✈️ How many **days** would "
                "you like to travel?"
            )

        else:

            # -------------------------------------------------
            # FIND DESTINATION
            # -------------------------------------------------

            with st.spinner(
                "📍 Finding destination..."
            ):

                location = get_coordinates(
                    destination
                )


            if location:

                st.session_state.location = location

                # ---------------------------------------------
                # WEATHER
                # ---------------------------------------------

                weather_text = ""

                with st.spinner(
                    "🌤️ Getting weather forecast..."
                ):

                    try:

                        weather_data = get_weather(
                            location["latitude"],
                            location["longitude"],
                            forecast_days=min(
                                int(days),
                                16
                            )
                        )

                        weather_text = format_weather(
                            weather_data
                        )

                        st.session_state.weather = (
                            weather_text
                        )

                    except Exception:

                        weather_text = (
                            "Weather information "
                            "is currently unavailable."
                        )

                # ---------------------------------------------
                # ELEVATION
                # ---------------------------------------------

                try:

                    elevation = get_elevation(
                        location["latitude"],
                        location["longitude"]
                    )

                    st.session_state.elevation = (
                        elevation
                    )

                except Exception:

                    elevation = None


                # ---------------------------------------------
                # ITINERARY
                # ---------------------------------------------

                with st.spinner(
                    "✈️ Creating your itinerary..."
                ):

                    itinerary = generate_itinerary(
                        trip_info,
                        weather_text
                    )

                st.session_state.itinerary = (
                    itinerary
                )


                ai_reply = (
                    f"## ✈️ Your {days}-Day Trip to "
                    f"{destination}\n\n"
                    f"I've created your complete itinerary "
                    f"using the available weather forecast.\n\n"
                    f"📍 **Coordinates:** "
                    f"{location['latitude']:.4f}, "
                    f"{location['longitude']:.4f}\n\n"
                )

                if elevation is not None:

                    ai_reply += (
                        f"⛰️ **Elevation:** "
                        f"{elevation} meters above sea level\n\n"
                    )

                ai_reply += (
                    "Your complete itinerary is shown "
                    "below."
                )

            else:

                ai_reply = (
                    f"I couldn't find the location "
                    f"**{destination}**. "
                    f"Please check the destination name."
                )


    # =====================================================
    # INTENT: DESTINATION INFO
    # =====================================================

    elif intent == "destination_info":

        if not destination:

            ai_reply = (
                "Sure! 📍 Which destination would "
                "you like to know about?"
            )

        else:

            with st.spinner(
                "📍 Getting destination information..."
            ):

                location = get_coordinates(
                    destination
                )


            if location:

                st.session_state.location = location

                try:

                    elevation = get_elevation(
                        location["latitude"],
                        location["longitude"]
                    )

                    st.session_state.elevation = (
                        elevation
                    )

                except Exception:

                    elevation = None


                with st.spinner(
                    "🤖 Preparing destination details..."
                ):

                    ai_reply = generate_destination_info(
                        destination,
                        location,
                        elevation
                    )

            else:

                ai_reply = (
                    f"I couldn't find **{destination}**."
                )


    # =====================================================
    # INTENT: ELEVATION
    # =====================================================

    elif intent == "elevation":

        if not destination:

            ai_reply = (
                "⛰️ Please tell me the destination "
                "first so I can check its elevation."
            )

        else:

            with st.spinner(
                "⛰️ Checking elevation..."
            ):

                location = get_coordinates(
                    destination
                )


            if location:

                try:

                    elevation = get_elevation(
                        location["latitude"],
                        location["longitude"]
                    )

                    st.session_state.location = (
                        location
                    )

                    st.session_state.elevation = (
                        elevation
                    )

                    ai_reply = (
                        f"## ⛰️ {destination} Elevation\n\n"
                        f"**Elevation:** approximately "
                        f"**{elevation} meters above sea level**.\n\n"
                        f"📍 **Latitude:** "
                        f"{location['latitude']:.4f}\n\n"
                        f"📍 **Longitude:** "
                        f"{location['longitude']:.4f}"
                    )

                except Exception:

                    ai_reply = (
                        "Sorry, I couldn't retrieve "
                        "the elevation right now."
                    )

            else:

                ai_reply = (
                    f"I couldn't find the location "
                    f"**{destination}**."
                )


    # =====================================================
    # INTENT: WEATHER
    # =====================================================

    elif intent == "weather":

        if not destination:

            ai_reply = (
                "🌤️ Please tell me which destination "
                "you want the weather for."
            )

        else:

            with st.spinner(
                "🌤️ Getting weather..."
            ):

                location = get_coordinates(
                    destination
                )


            if location:

                try:

                    weather_data = get_weather(
                        location["latitude"],
                        location["longitude"],
                        forecast_days=5
                    )

                    weather_text = format_weather(
                        weather_data
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
                        "Weather information is "
                        "currently unavailable."
                    )

            else:

                ai_reply = (
                    f"I couldn't find **{destination}**."
                )


    # =====================================================
    # INTENT: UPDATE TRIP
    # =====================================================

    elif intent == "update_trip":

        if not extracted_info:

            ai_reply = (
                "What would you like to change "
                "in your trip?"
            )

        else:

            updated_items = []

            for key, value in extracted_info.items():

                if value is not None and value != []:

                    label = key.replace(
                        "_",
                        " "
                    ).title()

                    updated_items.append(
                        f"**{label}:** {value}"
                    )

            ai_reply = (
                "✅ I've updated your trip details.\n\n"
                + "\n".join(updated_items)
                + "\n\n"
                "If you want, you can now ask me "
                "to generate the updated itinerary."
            )


    # =====================================================
    # INTENT: GENERAL QUESTION
    # =====================================================

    else:

        system_prompt = f"""
You are AI TravelMate.

You are helping the user with travel planning.

CURRENT TRIP INFORMATION:

{json.dumps(
    st.session_state.trip_info,
    indent=2
)}

Answer the user's question naturally.

Important:

- Remember the current destination.
- Do not replace the destination with words like
  "location", "destination", "it", or "there".
- Do not generate a new itinerary unless the user
  explicitly asks for a trip plan.
- Do not invent live information.
- Give concise but useful answers.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + st.session_state.messages,
            temperature=0.4
        )

        ai_reply = response.choices[0].message.content


    # =====================================================
    # SAVE AI RESPONSE
    # =====================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_reply
        }
    )


    # =====================================================
    # SHOW AI RESPONSE
    # =====================================================

    with st.chat_message("assistant"):

        st.markdown(ai_reply)


# =========================================================
# TRIP ITINERARY
# =========================================================

if st.session_state.get("itinerary"):

    st.divider()

    st.header("🗓️ Trip Itinerary")

    st.markdown(
        st.session_state.itinerary
    )


# =========================================================
# WEATHER SECTION
# =========================================================

if st.session_state.get("weather"):

    st.divider()

    st.header("🌤️ Weather Forecast")

    st.markdown(
        st.session_state.weather
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🧳 Trip Information")

    if st.session_state.trip_info:

        for key, value in (
            st.session_state.trip_info.items()
        ):

            label = key.replace(
                "_",
                " "
            ).title()

            st.write(
                f"**{label}:** {value}"
            )

    else:

        st.info(
            "Tell me about your trip and I'll "
            "extract the details here."
        )


    # -----------------------------------------------------
    # DESTINATION DATA
    # -----------------------------------------------------

    if st.session_state.location:

        st.divider()

        st.subheader("📍 Destination Data")

        location = st.session_state.location

        st.write(
            f"**Latitude:** "
            f"{location['latitude']:.4f}"
        )

        st.write(
            f"**Longitude:** "
            f"{location['longitude']:.4f}"
        )


        if st.session_state.elevation is not None:

            st.write(
                f"**Elevation:** "
                f"{st.session_state.elevation} m"
            )

            st.caption(
                "Above sea level"
            )


    st.divider()

    st.subheader("✈️ TravelMate")

    st.write(
        "AI-powered travel planning assistant."
    )