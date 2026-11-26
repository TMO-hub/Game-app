from io import BytesIO
import re
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import streamlit.components.v1 as components

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SpeakFlow — English Dialogue & Speaking Game",
    page_icon="💬",
    layout="centered",
)

st.markdown(
    """
    <style>
    .tip-card {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 1rem 1.25rem;
        border-radius: 0.5rem;
        margin: 0.75rem 0;
        color: #14532d;
    }
    .hint-banner {
        background-color: #fffbeb;
        border: 1px solid #fcd34d;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #78350f;
    }
    .alt-pill {
        display: inline-block;
        background-color: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        font-size: 0.9rem;
        margin: 0.2rem 0.3rem 0.2rem 0;
        border: 1px solid #86efac;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Scenarios & Multi-Turn Dialogue Dataset
# -----------------------------------------------------------------------------
SCENARIOS = [
    {
        "id": "cafe",
        "title": "Ordering at a Café",
        "difficulty": "Beginner",
        "theme_color": "#d97706",
        "bg_color": "#fef3c7",
        "person_a_role": "Barista",
        "person_a_avatar": "☕",
        "person_b_role": "Customer (You)",
        "person_b_avatar": "🧑",
        "setting": "A busy neighborhood coffee shop on a Saturday morning.",
        "turns": [
            {
                "speaker_a": "Hi there! Welcome to Sunrise Café. What can I get started for you today?",
                "hint": "Greet the barista politely and order a drink (e.g., 'Could I get...' or 'I'd like...').",
                "options": [
                    {"text": "Hi! Could I get a medium iced latte, please?", "type": "best", "reason": "Polite, natural, and uses 'Could I get...' which native speakers use every day in cafés."},
                    {"text": "I want coffee medium cold now.", "type": "awkward", "reason": "Awkward word order and lacks polite phrasing."},
                    {"text": "Give me a latte immediately.", "type": "rude", "reason": "Too blunt and impolite for everyday service interactions."},
                    {"text": "Yes, I am going to the library later.", "type": "awkward", "reason": "Off-topic—doesn't answer the barista's question."},
                ],
                "keywords": ["latte", "coffee", "tea", "espresso", "cappuccino", "americano", "mocha", "please", "like", "get", "have", "can", "could"],
                "ideal_response": "Hi! Could I get a medium iced latte, please?",
                "tip": "Instead of saying 'I want...', native English speakers soften requests in cafés using **'Could I get...'**, **'Can I have...'**, or **'I'd like...'** plus **'please'**.",
                "alternatives": [
                    "Morning! Can I have a medium iced latte, please?",
                    "Hi, I'd like to order a medium iced latte.",
                ],
            },
            {
                "speaker_a": "Sure thing! Would you like regular milk with that, or do you prefer oat or almond milk?",
                "hint": "State your milk preference clearly and politely.",
                "options": [
                    {"text": "Oat milk would be great, thanks!", "type": "best", "reason": "Friendly, concise, and uses 'would be great' to sound warm and appreciative."},
                    {"text": "I am preferring the milk of oats.", "type": "awkward", "reason": "Unnatural phrasing ('preferring' is rarely used in continuous tense here)."},
                    {"text": "Why are you asking me about milk?", "type": "rude", "reason": "Defensive and rude when the barista is customizing your drink."},
                    {"text": "Regular milk is a liquid from cows.", "type": "awkward", "reason": "Robotic phrasing that doesn't clearly state your choice."},
                ],
                "keywords": ["regular", "oat", "almond", "soy", "milk", "please", "thanks", "great", "fine", "good"],
                "ideal_response": "Oat milk would be great, thanks!",
                "tip": "When answering a choice question casually, pairing your selection with **'...would be great, thanks'** or **'...please'** sounds natural and warm.",
                "alternatives": [
                    "Regular milk is fine, thank you.",
                    "Could you make it with almond milk, please?",
                ],
            },
            {
                "speaker_a": "Got it. Anything else for you today, or will that be all?",
                "hint": "Let the barista know you're finished ordering.",
                "options": [
                    {"text": "That'll be all, thank you. How much do I owe you?", "type": "best", "reason": "Uses the natural contraction 'That'll be all' and smoothly moves to payment."},
                    {"text": "No more food or drink exists for me.", "type": "awkward", "reason": "Overly dramatic and unnatural phrasing."},
                    {"text": "Hurry up and tell me the money.", "type": "rude", "reason": "Rude and impatient."},
                    {"text": "I already ate breakfast yesterday.", "type": "awkward", "reason": "Irrelevant detail that doesn't answer whether you want anything else."},
                ],
                "keywords": ["all", "nothing", "no", "thank", "thanks", "pay", "much", "card", "total", "good"],
                "ideal_response": "That'll be all, thank you. How much do I owe you?",
                "tip": "**'That'll be all'** or **'I'm all set, thanks'** are classic, polite ways to signal that you have finished ordering.",
                "alternatives": [
                    "I'm all set, thanks!",
                    "Nope, that's everything. Can I pay by card?",
                ],
            },
        ],
    },
    {
        "id": "directions",
        "title": "Asking for Directions",
        "difficulty": "Beginner",
        "theme_color": "#0284c7",
        "bg_color": "#e0f2fe",
        "person_a_role": "Local Resident",
        "person_a_avatar": "🚶",
        "person_b_role": "Traveler (You)",
        "person_b_avatar": "🎒",
        "setting": "A sunny downtown street corner near the city center.",
        "turns": [
            {
                "speaker_a": "Good afternoon! You look a little lost—can I help you find something?",
                "hint": "Thank them and ask how to get to the Central Train Station.",
                "options": [
                    {"text": "Oh, thank you! Could you tell me how to get to the Central Train Station?", "type": "best", "reason": "Warm appreciation followed by a polite indirect question."},
                    {"text": "Tell me where is train station now.", "type": "awkward", "reason": "Missing articles and uses inverted question order inside a statement."},
                    {"text": "Mind your own business, I'm fine.", "type": "rude", "reason": "Hostile response to someone offering help."},
                    {"text": "Trains are very fast vehicles.", "type": "awkward", "reason": "Doesn't ask for directions at all."},
                ],
                "keywords": ["station", "train", "way", "get", "where", "how", "find", "looking", "help", "thanks", "thank"],
                "ideal_response": "Oh, thank you! Could you tell me how to get to the Central Train Station?",
                "tip": "In indirect questions, keep subject-before-verb order: say **'Could you tell me where the station is?'** rather than *'where is the station'*.",
                "alternatives": [
                    "Yes, please! Do you know the way to the Central Train Station?",
                    "Thanks so much! I'm looking for the Central Train Station.",
                ],
            },
            {
                "speaker_a": "Of course! Walk straight down this street for two blocks, then turn left at the traffic light. You'll see it right across from the park.",
                "hint": "Confirm you understood the route and ask how long the walk takes.",
                "options": [
                    {"text": "Got it—two blocks straight and left at the light. About how long does it take to walk there?", "type": "best", "reason": "Recapping landmarks confirms understanding, and 'About how long...' sounds natural."},
                    {"text": "I understand street blocks light park.", "type": "awkward", "reason": "Broken telegraphic phrasing without connecting words."},
                    {"text": "That sounds way too complicated, drive me there.", "type": "rude", "reason": "Unreasonable demand to a stranger."},
                    {"text": "Do you like walking in the park?", "type": "awkward", "reason": "Changes the subject instead of confirming the directions."},
                ],
                "keywords": ["blocks", "left", "straight", "long", "far", "minutes", "walk", "got", "understand", "thanks"],
                "ideal_response": "Got it—two blocks straight and left at the light. About how long does it take to walk there?",
                "tip": "Repeating key steps back with **'Got it—two blocks straight...'** is a practical habit that prevents wrong turns.",
                "alternatives": [
                    "So straight for two blocks and then a left? Is it far from here?",
                    "Makes sense! How many minutes' walk would you say that is?",
                ],
            },
            {
                "speaker_a": "It's only about a five-minute walk! You really can't miss it.",
                "hint": "Thank them warmly and wish them a good day.",
                "options": [
                    {"text": "That's super helpful. Thanks so much for your help, have a great day!", "type": "best", "reason": "Natural, appreciative, and closes the interaction warmly."},
                    {"text": "Five minutes is acceptable. Goodbye.", "type": "awkward", "reason": "Stiff and overly formal for a friendly street interaction."},
                    {"text": "Finally, I can stop talking to you.", "type": "rude", "reason": "Rude to someone who just helped you."},
                    {"text": "My watch says it is 2:15 PM.", "type": "awkward", "reason": "Unrelated comment that ignores their help."},
                ],
                "keywords": ["thank", "thanks", "appreciate", "helpful", "great", "day", "bye", "wonderful"],
                "ideal_response": "That's super helpful. Thanks so much for your help, have a great day!",
                "tip": "Pairing **'Thanks so much for your help'** with **'Have a great day!'** makes for a polite, natural closing.",
                "alternatives": [
                    "Awesome, I really appreciate it! Have a wonderful afternoon.",
                    "Thanks a ton! Have a great rest of your day.",
                ],
            },
        ],
    },
    {
        "id": "airport",
        "title": "Airport Check-in",
        "difficulty": "Intermediate",
        "theme_color": "#0d9488",
        "bg_color": "#ccfbf1",
        "person_a_role": "Airline Agent",
        "person_a_avatar": "🛫",
        "person_b_role": "Passenger (You)",
        "person_b_avatar": "🛂",
        "setting": "The check-in counter at an international airport.",
        "turns": [
            {
                "speaker_a": "Good morning! Where are you flying to today, and may I see your passport?",
                "hint": "State your destination (e.g., Tokyo or London) and hand over your passport politely.",
                "options": [
                    {"text": "Good morning! I'm flying to Tokyo. Here's my passport.", "type": "best", "reason": "Clear, polite, and answers both parts of the agent's question."},
                    {"text": "Fly Tokyo. Passport take.", "type": "awkward", "reason": "Fragmented grammar and unnatural word order."},
                    {"text": "Why do you always ask for passports? It's annoying.", "type": "rude", "reason": "Combative over a standard travel requirement."},
                    {"text": "I bought a sandwich at the terminal earlier.", "type": "awkward", "reason": "Off-topic—doesn't answer the check-in question."},
                ],
                "keywords": ["flying", "fly", "going", "to", "passport", "here", "morning", "good", "please"],
                "ideal_response": "Good morning! I'm flying to Tokyo. Here's my passport.",
                "tip": "Keep airport counter replies clear and calm: state your destination and say **'Here's my passport'** or **'Here you go'**.",
                "alternatives": [
                    "Morning! I'm heading to Tokyo today—here you go.",
                    "Hi there! I'm on the flight to Tokyo. Here is my passport.",
                ],
            },
            {
                "speaker_a": "Thank you. Are you checking any bags today, or do you only have carry-on luggage?",
                "hint": "Let the agent know if you have a checked bag or only carry-on.",
                "options": [
                    {"text": "Just this carry-on bag, thank you. Could I get a window seat if one's available?", "type": "best", "reason": "Clear luggage answer plus a polite seat request ('Could I get... if one's available?')."},
                    {"text": "I have bag for carrying with my hand only.", "type": "awkward", "reason": "Wordy and unnatural compared to 'carry-on bag'."},
                    {"text": "Put me in first class for free right now.", "type": "rude", "reason": "Demanding and unrealistic at standard check-in."},
                    {"text": "Blue is my favorite color for suitcases.", "type": "awkward", "reason": "Irrelevant to luggage check-in."},
                ],
                "keywords": ["bag", "bags", "carry-on", "carry", "checked", "check", "seat", "window", "aisle", "thank", "thanks"],
                "ideal_response": "Just this carry-on bag, thank you. Could I get a window seat if one's available?",
                "tip": "When asking for a seat preference, adding **'if one's available'** or **'if possible'** sounds polite and flexible.",
                "alternatives": [
                    "I'm just traveling with a carry-on today. Any chance I could get an aisle seat?",
                    "I have one suitcase to check, please. Could I sit near the front?",
                ],
            },
            {
                "speaker_a": "I've put you in 14A by the window. Boarding starts at 9:15 AM at Gate B7. Have a safe flight!",
                "hint": "Thank the agent and confirm boarding time or gate if helpful.",
                "options": [
                    {"text": "Thanks so much! Gate B7 at 9:15—got it. Have a great day!", "type": "best", "reason": "Confirms key details naturally and returns a friendly closing."},
                    {"text": "14A is number fourteen and letter A. Bye.", "type": "awkward", "reason": "States the obvious and ends abruptly."},
                    {"text": "Gate B7 is too far, move it closer.", "type": "rude", "reason": "Impossible demand about airport gates."},
                    {"text": "I like eating pretzels on airplanes.", "type": "awkward", "reason": "Off-topic at the end of check-in."},
                ],
                "keywords": ["thank", "thanks", "gate", "b7", "9:15", "great", "day", "flight", "got"],
                "ideal_response": "Thanks so much! Gate B7 at 9:15—got it. Have a great day!",
                "tip": "Echoing back the **gate and boarding time** helps you remember details easily while keeping the tone upbeat.",
                "alternatives": [
                    "Thank you so much! I'll head over toward Gate B7 later. Have a good one!",
                    "Great, thanks for your help! Have a nice day.",
                ],
            },
        ],
    },
    {
        "id": "hotel",
        "title": "Hotel Reception Check-in",
        "difficulty": "Intermediate",
        "theme_color": "#7c3aed",
        "bg_color": "#ede9fe",
        "person_a_role": "Front Desk Receptionist",
        "person_a_avatar": "🛎️",
        "person_b_role": "Hotel Guest (You)",
        "person_b_avatar": "🧳",
        "setting": "The lobby of the Grand Harbor Hotel at 3:30 PM.",
        "turns": [
            {
                "speaker_a": "Good afternoon and welcome to the Grand Harbor Hotel! Are you checking in today?",
                "hint": "Confirm you're checking in and share the name on your reservation.",
                "options": [
                    {"text": "Good afternoon! Yes, I have a reservation under the name Alex Rivera.", "type": "best", "reason": "Uses the natural hospitality phrase 'a reservation under the name...'."},
                    {"text": "Yes, I booked room in this building for sleeping.", "type": "awkward", "reason": "Unnatural phrasing and missing articles."},
                    {"text": "Obviously, why else would I have suitcases?", "type": "rude", "reason": "Sarcastic and rude to a welcoming host."},
                    {"text": "Is the swimming pool open right now?", "type": "awkward", "reason": "Skips answering the check-in question."},
                ],
                "keywords": ["yes", "check", "checking", "reservation", "booked", "booking", "name", "under"],
                "ideal_response": "Good afternoon! Yes, I have a reservation under the name Alex Rivera.",
                "tip": "In English, hotel and restaurant bookings are naturally phrased as **'a reservation under [Name]'**.",
                "alternatives": [
                    "Hi! Yes, I'm checking in—the reservation is under Alex Rivera.",
                    "Good afternoon! I booked a room under Alex Rivera.",
                ],
            },
            {
                "speaker_a": "Let me pull that up for you... Ah yes, a deluxe queen room for two nights! May I see your ID and a credit card for incidentals?",
                "hint": "Hand over your ID/card politely and ask if breakfast is included.",
                "options": [
                    {"text": "Here you go. By the way, is breakfast included with the room?", "type": "best", "reason": "'Here you go' is natural when handing items over, and 'By the way' introduces a polite question."},
                    {"text": "Take these plastic cards. Does food come free?", "type": "awkward", "reason": "Blunt phrasing ('Take these...') and unnatural question ('Does food come free?')."},
                    {"text": "Why do you need my credit card? Are you going to steal from me?", "type": "rude", "reason": "Accusatory over a standard hotel incidentals deposit."},
                    {"text": "I like queen beds because they are big.", "type": "awkward", "reason": "Ignores the receptionist's request for ID and card."},
                ],
                "keywords": ["here", "sure", "course", "id", "passport", "card", "breakfast", "included", "go"],
                "ideal_response": "Here you go. By the way, is breakfast included with the room?",
                "tip": "Say **'Here you go'** or **'Here you are'** when handing someone an ID or card.",
                "alternatives": [
                    "Sure, here's my ID and card. Also, is breakfast included?",
                    "Of course, here you are. Does my stay include breakfast?",
                ],
            },
            {
                "speaker_a": "Yes, complimentary breakfast is served in the lobby lounge from 7:00 to 10:00 AM. Here is your key card—you're in Room 412 on the fourth floor. Enjoy your stay!",
                "hint": "Thank the receptionist and ask where the elevators are.",
                "options": [
                    {"text": "Wonderful, thank you! Could you point me toward the elevators?", "type": "best", "reason": "Polite, appreciative, and uses a natural phrase to ask for indoor directions."},
                    {"text": "Room 412 is four hundred and twelve. Where elevator?", "type": "awkward", "reason": "Repeats the room number unnecessarily and uses broken grammar."},
                    {"text": "Only until 10 AM? That's terrible service.", "type": "rude", "reason": "Hostile complaint about standard breakfast hours."},
                    {"text": "I usually wake up at 6:30 in the morning.", "type": "awkward", "reason": "Doesn't thank them or wrap up check-in smoothly."},
                ],
                "keywords": ["thank", "thanks", "elevator", "elevators", "lift", "where", "great", "wonderful", "appreciate"],
                "ideal_response": "Wonderful, thank you! Could you point me toward the elevators?",
                "tip": "**'Could you point me toward...'** is a smooth, polite way to ask where elevators, lounges, or exits are located.",
                "alternatives": [
                    "Thanks so much! Which way are the elevators?",
                    "Great, I appreciate it! Where can I find the elevator?",
                ],
            },
        ],
    },
    {
        "id": "small_talk",
        "title": "Making Small Talk at a Networking Event",
        "difficulty": "Intermediate",
        "theme_color": "#059669",
        "bg_color": "#d1fae5",
        "person_a_role": "Event Attendee (Jordan)",
        "person_a_avatar": "🤝",
        "person_b_role": "Attendee (You)",
        "person_b_avatar": "🙂",
        "setting": "An evening tech & design meetup with light refreshments.",
        "turns": [
            {
                "speaker_a": "Hi! I don't think we've met yet—I'm Jordan. How are you enjoying the event so far?",
                "hint": "Introduce yourself, give a positive reaction, and ask a question back.",
                "options": [
                    {"text": "Nice to meet you, Jordan! I'm Sam. I'm really enjoying it—the talks have been great. What brought you here tonight?", "type": "best", "reason": "Greets, answers positively, and asks an open-ended question back."},
                    {"text": "I am Sam. The event is fine.", "type": "awkward", "reason": "Too brief—stalls the conversation."},
                    {"text": "Honestly, I'm bored and the snacks are terrible.", "type": "rude", "reason": "Overly negative for a first greeting at a social event."},
                    {"text": "I took the bus to get here.", "type": "awkward", "reason": "Answers how you arrived instead of how you're enjoying the event."},
                ],
                "keywords": ["nice", "meet", "enjoying", "great", "good", "talks", "speaker", "you", "what", "how", "name"],
                "ideal_response": "Nice to meet you, Jordan! I'm Sam. I'm really enjoying it—the talks have been great. What brought you here tonight?",
                "tip": "Keep small talk moving by pairing your answer with a follow-up question like **'What brought you here tonight?'** or **'How about you?'**.",
                "alternatives": [
                    "Hey Jordan, nice to meet you! I'm Sam. It's been great so far—have you been to this meetup before?",
                    "Hi Jordan! I'm Sam. Really liking it tonight—how about you?",
                ],
            },
            {
                "speaker_a": "I'm a UX designer at a small startup, so I always try to connect with other creatives. What line of work are you in?",
                "hint": "Share what you do or study and show interest in their work.",
                "options": [
                    {"text": "Oh, that's awesome! I work in data analytics, so I actually collaborate with UX designers quite a bit.", "type": "best", "reason": "Finds a natural connection between your work and theirs."},
                    {"text": "My job is working with computers in an office.", "type": "awkward", "reason": "Too vague and misses a chance to connect."},
                    {"text": "UX design sounds really easy compared to my job.", "type": "rude", "reason": "Dismissive and condescending."},
                    {"text": "Do you make a lot of money at your startup?", "type": "rude", "reason": "Asking about salary is considered intrusive in casual networking."},
                ],
                "keywords": ["work", "study", "student", "designer", "developer", "engineer", "marketing", "data", "project", "cool", "awesome", "interesting"],
                "ideal_response": "Oh, that's awesome! I work in data analytics, so I actually collaborate with UX designers quite a bit.",
                "tip": "When asked **'What line of work are you in?'**, mention your role briefly and highlight any overlap with what they do.",
                "alternatives": [
                    "Oh nice! I'm a software developer, so I work with UX designers all the time.",
                    "That sounds cool! I'm studying marketing—how long have you been at your startup?",
                ],
            },
            {
                "speaker_a": "No way, small world! Hey, I'm going to grab another drink before the next panel starts, but let's stay in touch—are you on LinkedIn?",
                "hint": "Agree enthusiastically and close the chat warmly.",
                "options": [
                    {"text": "Definitely! Let's connect right now. It was great chatting with you!", "type": "best", "reason": "Enthusiastic, practical, and uses a warm closing phrase."},
                    {"text": "Yes, I have an internet account on LinkedIn.", "type": "awkward", "reason": "Stiff and unnatural phrasing."},
                    {"text": "No, I don't want to connect with you.", "type": "rude", "reason": "Blunt brush-off instead of a polite response."},
                    {"text": "What kind of drink are you going to get?", "type": "awkward", "reason": "Ignores their offer to connect."},
                ],
                "keywords": ["yes", "sure", "definitely", "linkedin", "connect", "touch", "great", "chatting", "talking", "qr", "email"],
                "ideal_response": "Definitely! Let's connect right now. It was great chatting with you!",
                "tip": "**'It was great chatting with you!'** is a friendly, natural wrap-up for casual conversations.",
                "alternatives": [
                    "For sure! Here's my LinkedIn—it was really nice talking to you, Jordan!",
                    "Absolutely, let's connect! Enjoy the rest of the evening.",
                ],
            },
        ],
    },
    {
        "id": "job_interview",
        "title": "Job Interview",
        "difficulty": "Advanced",
        "theme_color": "#1e3a8a",
        "bg_color": "#dbeafe",
        "person_a_role": "Hiring Manager (Ms. Chen)",
        "person_a_avatar": "💼",
        "person_b_role": "Candidate (You)",
        "person_b_avatar": "👔",
        "setting": "An interview for a Project Coordinator position.",
        "turns": [
            {
                "speaker_a": "Thanks for coming in today. To kick things off, could you tell me a little bit about yourself and what drew you to this role?",
                "hint": "Summarize your relevant experience briefly and say why this role appeals to you.",
                "options": [
                    {"text": "Thank you for having me! I have three years of experience coordinating projects, and I was drawn to this role because of your focus on clean, sustainable products.", "type": "best", "reason": "Clear, confident, and connects past experience to genuine interest in the role."},
                    {"text": "I was born in 1998 and I need a job because rent is high.", "type": "awkward", "reason": "Focuses on personal circumstances rather than qualifications."},
                    {"text": "Everything is already on my resume, didn't you read it?", "type": "rude", "reason": "Defensive and unprofessional."},
                    {"text": "I like working with people and doing good work every day.", "type": "awkward", "reason": "Too generic—lacks specific skills or tailored interest."},
                ],
                "keywords": ["thank", "experience", "background", "skills", "role", "company", "excited", "drawn", "passionate", "team", "projects"],
                "ideal_response": "Thank you for having me! I have three years of experience coordinating projects, and I was drawn to this role because of your focus on clean, sustainable products.",
                "tip": "Open with **'Thank you for having me'** and tie your relevant experience directly to why the role interests you.",
                "alternatives": [
                    "Thanks so much for the opportunity! I've spent the past few years streamlining team schedules, so this role felt like a great fit.",
                    "I appreciate you meeting with me. With my background in operations, I'm excited to support your team's upcoming projects.",
                ],
            },
            {
                "speaker_a": "That's great to hear. Can you share an example of a time you had to handle a tight deadline or an unexpected setback?",
                "hint": "Briefly explain the situation, what you did, and the result.",
                "options": [
                    {"text": "Certainly. Last quarter, a supplier delayed materials two days before launch. I adjusted our timeline, lined up a backup vendor, and we still launched on schedule.", "type": "best", "reason": "Shows calm problem-solving and a concrete positive outcome."},
                    {"text": "When deadlines are tight, I usually get very stressed and panic.", "type": "awkward", "reason": "Highlights stress instead of constructive problem-solving."},
                    {"text": "Setbacks only happen when my coworkers are careless.", "type": "rude", "reason": "Blaming colleagues sounds unprofessional in an interview."},
                    {"text": "Yes, I have had many deadlines in my previous job.", "type": "awkward", "reason": "Doesn't provide a specific example."},
                ],
                "keywords": ["deadline", "project", "problem", "challenge", "team", "solution", "resolved", "schedule", "result", "time", "launch", "delivered"],
                "ideal_response": "Certainly. Last quarter, a supplier delayed materials two days before launch. I adjusted our timeline, lined up a backup vendor, and we still launched on schedule.",
                "tip": "Keep behavioral answers focused on **what you did** and **how it worked out**, using calm, action-oriented verbs.",
                "alternatives": [
                    "Sure! When a project scope shifted mid-week, I broke tasks into daily check-ins and helped the team hit our deadline.",
                    "Of course. When a teammate was out sick before a client update, I stepped in to organize the notes and keep things moving.",
                ],
            },
            {
                "speaker_a": "Impressive adaptability. Before we wrap up, do you have any questions for me about the team or the role?",
                "hint": "Ask a thoughtful question about expectations, team workflow, or early priorities.",
                "options": [
                    {"text": "Yes, thank you! What would success look like in this role during the first three months?", "type": "best", "reason": "Shows initiative and focus on delivering strong early results."},
                    {"text": "No, I have zero questions.", "type": "awkward", "reason": "Can come across as uncurious or unprepared."},
                    {"text": "How soon can I take three weeks of vacation?", "type": "rude", "reason": "Focuses on time off before receiving an offer."},
                    {"text": "What does your company actually do?", "type": "awkward", "reason": "Suggests little preparation before the interview."},
                ],
                "keywords": ["success", "team", "goals", "months", "days", "culture", "challenge", "expect", "growth", "project", "collaborate", "question"],
                "ideal_response": "Yes, thank you! What would success look like in this role during the first three months?",
                "tip": "Asking **'What would success look like in the first three months?'** shows forward thinking and helps clarify expectations.",
                "alternatives": [
                    "I do! How does this team usually coordinate on cross-functional projects?",
                    "Yes—what are the main priorities the team is focusing on right now?",
                ],
            },
        ],
    },
]


# -----------------------------------------------------------------------------
# PIL Font & Scenario Banner Helpers
# -----------------------------------------------------------------------------
def get_font(size: int) -> ImageFont.ImageFont:
    """Safely loads a default PIL font of the given size across Pillow versions."""
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


@st.cache_data(show_spinner=False)
def generate_scenario_banner(
    title: str, setting: str, difficulty: str, theme_color: str, bg_color: str
) -> bytes:
    """Generates a crisp PIL banner card for the active dialogue scenario."""
    w, h = 760, 150
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Accent bar & decorative circles
    draw.rectangle([0, 0, 14, h], fill=theme_color)
    draw.ellipse([w - 130, -35, w + 30, 125], fill=theme_color)
    draw.ellipse([w - 75, 55, w + 45, 175], fill="#ffffff")
    draw.rectangle([0, 0, w - 1, h - 1], outline=theme_color, width=3)

    # Chat bubble emblem
    draw.rounded_rectangle([36, 36, 114, 92], radius=16, fill=theme_color)
    draw.polygon([(52, 92), (68, 92), (48, 110)], fill=theme_color)
    draw.ellipse([54, 59, 62, 67], fill="#ffffff")
    draw.ellipse([71, 59, 79, 67], fill="#ffffff")
    draw.ellipse([88, 59, 96, 67], fill="#ffffff")

    title_font = get_font(28)
    sub_font = get_font(17)
    badge_font = get_font(15)

    trimmed_setting = setting[:72] + ("..." if len(setting) > 72 else "")
    draw.text((138, 30), title, fill="#111827", font=title_font)
    draw.text((138, 70), trimmed_setting, fill="#374151", font=sub_font)
    draw.text(
        (138, 104),
        f"Level: {difficulty.upper()}   |   Conversation Practice",
        fill=theme_color,
        font=badge_font,
    )

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# -----------------------------------------------------------------------------
# Reliable Audio Helper (gTTS + Explicit Diagnostics + Browser Speech Fallback)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def text_to_mp3_bytes(text: str, lang: str = "en") -> tuple[bytes | None, str | None]:
    """
    Converts stripped text to MP3 bytes via gTTS.
    Returns (mp3_bytes, error_reason). Never silently swallows errors.
    """
    cleaned = text.strip() if isinstance(text, str) else ""
    if not cleaned:
        return None, "Empty text provided to text-to-speech."
    if not GTTS_AVAILABLE:
        return None, "`gTTS` is not installed in this Python environment (`pip install gTTS`)."

    try:
        tts = gTTS(text=cleaned, lang=lang, slow=False)
        buf = BytesIO()
        tts.write_to_fp(buf)
        mp3_data = buf.getvalue()
        if not mp3_data:
            return None, "`gTTS` returned empty audio data."
        return mp3_data, None
    except Exception as exc:
        return None, f"`gTTS` error ({type(exc).__name__}): {exc}"


def render_browser_speech_fallback(text: str, button_label: str, widget_key: str) -> None:
    """Renders a browser Web Speech API (`window.speechSynthesis`) fallback button."""
    safe_text = text.strip().replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    safe_label = button_label.replace("<", "&lt;").replace(">", "&gt;")
    html = f"""
    <div style="margin: 0.25rem 0 0.5rem 0;">
        <button id="btn_{widget_key}" type="button"
            style="background:#f1f5f9;color:#0f172a;border:1px solid #cbd5e1;
                   border-radius:0.5rem;padding:0.35rem 0.75rem;font-size:0.875rem;
                   cursor:pointer;">
            🌐 {safe_label}
        </button>
    </div>
    <script>
    (function() {{
        const btn = document.getElementById("btn_{widget_key}");
        if (!btn) return;
        btn.onclick = function() {{
            if (!("speechSynthesis" in window)) {{
                btn.textContent = "Browser speechSynthesis unsupported";
                return;
            }}
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance("{safe_text}");
            utter.lang = "en-US";
            window.speechSynthesis.speak(utter);
        }};
    }})();
    </script>
    """
    components.html(html, height=44)


def render_pronunciation_controls(text: str, mp3_label: str, key_prefix: str) -> None:
    """Plays gTTS audio if available; otherwise shows exact error diagnostic + browser fallback."""
    mp3_bytes, err_reason = text_to_mp3_bytes(text, lang="en")
    if mp3_bytes:
        st.audio(mp3_bytes, format="audio/mp3", autoplay=True)
    else:
        st.warning(f"Audio fallback active — {err_reason}")
        render_browser_speech_fallback(
            text=text,
            button_label=f"Speak in Browser ({mp3_label})",
            widget_key=key_prefix,
        )


# -----------------------------------------------------------------------------
# Response Evaluation Helper
# -----------------------------------------------------------------------------
def evaluate_free_response(user_text: str, turn_data: dict) -> tuple[str, int, str]:
    """Evaluates typed user dialogue using keyword and intent cues."""
    cleaned = user_text.strip()
    lower_text = cleaned.lower()
    words = re.findall(r"\b\w+\b", lower_text)

    if len(words) < 2:
        return (
            "needs_work",
            25,
            "Your reply is very short. Try writing a full, natural sentence.",
        )

    keywords = [kw.lower() for kw in turn_data["keywords"]]
    matched_keywords = [
        kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lower_text)
    ]
    polite_markers = {
        "please", "thank", "thanks", "could", "would", "hi",
        "hello", "good", "great", "appreciate", "sorry", "excuse",
    }
    has_politeness = any(w in polite_markers for w in words)

    score_hits = (
        len(matched_keywords)
        + (1 if has_politeness else 0)
        + (1 if len(words) >= 5 else 0)
    )

    if score_hits >= 3:
        return (
            "excellent",
            100,
            f"🌟 **Natural & Context-Aware!** Matched helpful cues: *{', '.join(matched_keywords[:4])}*.",
        )
    if score_hits >= 1:
        return (
            "good",
            70,
            "👍 **Good Start!** Your meaning is understandable—check the model answer below for extra polish.",
        )
    return (
        "needs_work",
        35,
        "🤔 **Off-Context or Unclear:** Your response didn't clearly address the prompt. Compare it with the model response below.",
    )


# -----------------------------------------------------------------------------
# Session State Management
# -----------------------------------------------------------------------------
def reset_scenario(scenario_id: str, mode: str):
    st.session_state.scenario_id = scenario_id
    st.session_state.mode = mode
    st.session_state.turn_idx = 0
    st.session_state.chat_history = []
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.best_streak = 0
    st.session_state.show_hint = False
    st.session_state.turn_answered = False
    st.session_state.last_feedback = None
    st.session_state.play_a_audio = False
    st.session_state.play_ideal_audio = False


if "scenario_id" not in st.session_state:
    reset_scenario(SCENARIOS[0]["id"], "Choose the Best Response")


# -----------------------------------------------------------------------------
# Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎙️ Conversation Settings")

    difficulty_filter = st.selectbox(
        "Difficulty Level",
        options=["All", "Beginner", "Intermediate", "Advanced"],
        index=0,
    )

    filtered_scenarios = [
        s for s in SCENARIOS if difficulty_filter == "All" or s["difficulty"] == difficulty_filter
    ]
    if not filtered_scenarios:
        filtered_scenarios = SCENARIOS

    scenario_titles = {s["title"]: s["id"] for s in filtered_scenarios}
    current_scenario_obj = next(
        (s for s in filtered_scenarios if s["id"] == st.session_state.scenario_id),
        filtered_scenarios[0],
    )

    chosen_title = st.selectbox(
        "Scenario",
        options=list(scenario_titles.keys()),
        index=list(scenario_titles.values()).index(current_scenario_obj["id"]),
    )
    chosen_id = scenario_titles[chosen_title]

    chosen_mode = st.radio(
        "Gameplay Mode",
        options=["Choose the Best Response", "Type Your Own Response"],
        index=0 if st.session_state.mode == "Choose the Best Response" else 1,
    )

    if chosen_id != st.session_state.scenario_id or chosen_mode != st.session_state.mode:
        reset_scenario(chosen_id, chosen_mode)
        st.rerun()

    if st.button("🔄 Restart Scenario", use_container_width=True):
        reset_scenario(chosen_id, chosen_mode)
        st.rerun()

    st.divider()
    st.caption(
        "🎧 **Audio:** `gTTS` MP3 synthesis with diagnostic & browser speech fallback."
        if GTTS_AVAILABLE
        else "🎧 **Audio:** `gTTS` not installed; browser `speechSynthesis` fallback active."
    )


# -----------------------------------------------------------------------------
# Main Header, Banner & Metrics
# -----------------------------------------------------------------------------
scenario = next(s for s in SCENARIOS if s["id"] == st.session_state.scenario_id)
total_turns = len(scenario["turns"])
turn_idx = st.session_state.turn_idx

st.title("💬 English Speaking & Dialogue Game")

banner_bytes = generate_scenario_banner(
    scenario["title"],
    scenario["setting"],
    scenario["difficulty"],
    scenario["theme_color"],
    scenario["bg_color"],
)
st.image(banner_bytes, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Turn", f"{min(turn_idx + 1, total_turns)} / {total_turns}")
m2.metric("Score", f"{st.session_state.score} pts")
m3.metric("Streak 🔥", st.session_state.streak)
m4.metric("Best Streak 🏆", st.session_state.best_streak)

st.progress(min(turn_idx / total_turns, 1.0))
st.divider()

# -----------------------------------------------------------------------------
# Dialogue History
# -----------------------------------------------------------------------------
for entry in st.session_state.chat_history:
    if entry["role"] == "A":
        with st.chat_message("assistant", avatar=scenario["person_a_avatar"]):
            st.markdown(f"**{scenario['person_a_role']}:** {entry['text']}")
    else:
        with st.chat_message("user", avatar=scenario["person_b_avatar"]):
            st.markdown(f"**{scenario['person_b_role']}:** {entry['text']}")

# -----------------------------------------------------------------------------
# End-of-Scenario Summary
# -----------------------------------------------------------------------------
if turn_idx >= total_turns:
    st.balloons()
    st.success(f"🎉 **Scenario Complete!** You finished **{scenario['title']}**.")
    st.markdown(
        f"""
        - **Final Score:** `{st.session_state.score}` points
        - **Best Streak:** `{st.session_state.best_streak}`
        - **Mode:** `{st.session_state.mode}`
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 Restart Scenario", use_container_width=True):
            reset_scenario(scenario["id"], st.session_state.mode)
            st.rerun()
    with c2:
        next_scen = SCENARIOS[(SCENARIOS.index(scenario) + 1) % len(SCENARIOS)]
        if st.button(f"➡️ Next: {next_scen['title']}", type="primary", use_container_width=True):
            reset_scenario(next_scen["id"], st.session_state.mode)
            st.rerun()
    st.stop()

# -----------------------------------------------------------------------------
# Active Turn Gameplay
# -----------------------------------------------------------------------------
current_turn = scenario["turns"][turn_idx]

if not st.session_state.turn_answered:
    with st.chat_message("assistant", avatar=scenario["person_a_avatar"]):
        st.markdown(f"**{scenario['person_a_role']}:** {current_turn['speaker_a']}")
        if st.button("🔊 Listen", key=f"listen_a_{scenario['id']}_{turn_idx}"):
            st.session_state.play_a_audio = True

        if st.session_state.play_a_audio:
            render_pronunciation_controls(
                text=current_turn["speaker_a"],
                mp3_label="Person A",
                key_prefix=f"sp_a_{scenario['id']}_{turn_idx}",
            )

    h_col1, h_col2 = st.columns([1, 2])
    with h_col1:
        if st.button("💡 Hint / Situation Context", use_container_width=True):
            st.session_state.show_hint = not st.session_state.show_hint
    with h_col2:
        st.caption("Need guidance on tone or goal for this turn?")

    if st.session_state.show_hint:
        st.markdown(
            f"<div class='hint-banner'><strong>🧭 Situation Context:</strong> {current_turn['hint']}</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    if st.session_state.mode == "Choose the Best Response":
        option_texts = [opt["text"] for opt in current_turn["options"]]
        selected_text = st.radio(
            f"What should **{scenario['person_b_role']}** say next?",
            options=option_texts,
            key=f"mc_{scenario['id']}_{turn_idx}",
        )

        if st.button("✅ Submit Response", type="primary", use_container_width=True):
            chosen_opt = next(o for o in current_turn["options"] if o["text"] == selected_text)
            opt_type = chosen_opt["type"]

            if opt_type == "best":
                earned = 100 + (st.session_state.streak * 15)
                st.session_state.score += earned
                st.session_state.streak += 1
                st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
                msg = f"🎉 **Great choice! (+{earned} pts)** {chosen_opt['reason']}"
            elif opt_type == "awkward":
                earned = 40
                st.session_state.score += earned
                st.session_state.streak = 0
                msg = f"⚠️ **A bit awkward (+{earned} pts):** {chosen_opt['reason']}"
            else:
                earned = 0
                st.session_state.streak = 0
                msg = f"❌ **Off-tone or rude (+0 pts):** {chosen_opt['reason']}"

            st.session_state.chat_history.append({"role": "A", "text": current_turn["speaker_a"]})
            st.session_state.chat_history.append({"role": "B", "text": selected_text})
            st.session_state.turn_answered = True
            st.session_state.play_a_audio = False
            st.session_state.last_feedback = {"status": opt_type, "msg": msg}
            st.rerun()

    else:
        with st.form(key=f"free_{scenario['id']}_{turn_idx}"):
            typed_reply = st.text_input(
                f"Type what **{scenario['person_b_role']}** would say:",
                placeholder="Write your response here...",
            )
            submitted_free = st.form_submit_button("✅ Submit Response", type="primary", use_container_width=True)

        if submitted_free:
            if not typed_reply.strip():
                st.warning("Please type a response first.")
            else:
                rating, earned, eval_msg = evaluate_free_response(typed_reply, current_turn)
                if rating in ("excellent", "good"):
                    if rating == "excellent":
                        earned += st.session_state.streak * 15
                    st.session_state.streak += 1
                    st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
                else:
                    st.session_state.streak = 0

                st.session_state.score += earned
                st.session_state.chat_history.append({"role": "A", "text": current_turn["speaker_a"]})
                st.session_state.chat_history.append({"role": "B", "text": typed_reply.strip()})
                st.session_state.turn_answered = True
                st.session_state.play_a_audio = False
                st.session_state.last_feedback = {
                    "status": rating,
                    "msg": f"{eval_msg} **(+{earned} pts)**",
                }
                st.rerun()

# -----------------------------------------------------------------------------
# Post-Turn Feedback, Pronunciation & Natural Speaking Tip
# -----------------------------------------------------------------------------
if st.session_state.turn_answered and st.session_state.last_feedback:
    fb = st.session_state.last_feedback
    if fb["status"] in ("best", "excellent"):
        st.success(fb["msg"])
    elif fb["status"] in ("awkward", "good"):
        st.warning(fb["msg"])
    else:
        st.error(fb["msg"])

    ideal_line = current_turn["ideal_response"]
    st.markdown(f"**✨ Model Natural Response:** *\"{ideal_line}\"*")

    if st.button("🔊 Listen", key=f"listen_ideal_{scenario['id']}_{turn_idx}"):
        st.session_state.play_ideal_audio = True

    if st.session_state.play_ideal_audio:
        render_pronunciation_controls(
            text=ideal_line,
            mp3_label="Model Response",
            key_prefix=f"sp_ideal_{scenario['id']}_{turn_idx}",
        )

    alts_html = "".join(
        f"<span class='alt-pill'>“{alt}”</span>" for alt in current_turn["alternatives"][:2]
    )
    st.markdown(
        f"""
        <div class="tip-card">
            <h4 style="margin-top:0;">🗣️ Natural Speaking Tip</h4>
            <p>{current_turn['tip']}</p>
            <p style="margin-bottom:0.35rem;"><strong>2 Alternative Native Expressions:</strong></p>
            <div>{alts_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    next_label = "➡️ Next Turn" if turn_idx + 1 < total_turns else "🏁 View Summary"
    if st.button(next_label, type="primary", use_container_width=True):
        st.session_state.turn_idx += 1
        st.session_state.turn_answered = False
        st.session_state.show_hint = False
        st.session_state.last_feedback = None
        st.session_state.play_a_audio = False
        st.session_state.play_ideal_audio = False
        st.rerun()
