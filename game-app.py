import io
import re
from PIL import Image, ImageDraw
import streamlit as st

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
                    {"text": "Hi! Could I get a medium iced latte, please?", "type": "best", "reason": "Polite, natural, and uses 'Could I get...' which native speakers use constantly in cafés."},
                    {"text": "I want coffee medium cold now.", "type": "awkward", "reason": "Grammatically broken and sounds overly demanding without 'please'."},
                    {"text": "Give me a latte immediately.", "type": "rude", "reason": "Too blunt and impolite for everyday service interactions."},
                    {"text": "Yes, I am going to the library later.", "type": "awkward", "reason": "Off-topic—doesn't answer the barista's question."},
                ],
                "keywords": ["latte", "coffee", "tea", "espresso", "cappuccino", "americano", "mocha", "please", "like", "get", "have", "can", "could"],
                "ideal_response": "Hi! Could I get a medium iced latte, please?",
                "tip": "Instead of saying 'I want...', native English speakers soften requests in cafés using **'Could I get...'**, **'Can I have...'**, or **'I'd like...'** followed by **'please'**.",
                "alternatives": [
                    "Morning! Can I have a medium iced latte, please?",
                    "Hi, I'd like to order a medium iced latte.",
                    "Could I please get an iced latte, medium size?",
                ],
            },
            {
                "speaker_a": "Sure thing! Would you like regular milk with that, or do you prefer oat or almond milk?",
                "hint": "State your milk preference clearly and politely.",
                "options": [
                    {"text": "Oat milk would be great, thanks!", "type": "best", "reason": "Friendly, concise, and uses 'would be great' to sound warm and appreciative."},
                    {"text": "I am preferring the milk of oats.", "type": "awkward", "reason": "Unnatural phrasing ('preferring' isn't normally used in continuous tense here)."},
                    {"text": "Why are you asking me about milk?", "type": "rude", "reason": "Defensive and rude when the barista is just customizing your drink."},
                    {"text": "Regular milk is a liquid from cows.", "type": "awkward", "reason": "Sounds robotic and doesn't clearly state your choice."},
                ],
                "keywords": ["regular", "oat", "almond", "soy", "milk", "please", "thanks", "great", "fine", "good"],
                "ideal_response": "Oat milk would be great, thanks!",
                "tip": "When answering a choice question casually, pairing your choice with **'...would be great, thanks'** or **'...please'** sounds much more natural than a one-word answer.",
                "alternatives": [
                    "Regular milk is fine, thank you.",
                    "Could you make it with almond milk, please?",
                    "Just regular milk for me, thanks!",
                ],
            },
            {
                "speaker_a": "Got it. Anything else for you today, or will that be all?",
                "hint": "Let the barista know you're finished ordering and ready to pay.",
                "options": [
                    {"text": "That'll be all, thank you. How much do I owe you?", "type": "best", "reason": "Uses the natural contraction 'That'll be all' and smoothly transitions to payment."},
                    {"text": "No more food or drink exists for me.", "type": "awkward", "reason": "Overly dramatic and unnatural phrasing."},
                    {"text": "Hurry up and tell me the money.", "type": "rude", "reason": "Rude and impatient."},
                    {"text": "I already ate breakfast yesterday.", "type": "awkward", "reason": "Irrelevant detail that doesn't answer whether you want anything else."},
                ],
                "keywords": ["all", "nothing", "no", "thank", "thanks", "pay", "much", "card", "total", "good"],
                "ideal_response": "That'll be all, thank you. How much do I owe you?",
                "tip": "**'That'll be all'** or **'I'm all set, thanks'** are classic, polite phrases to signal that you've finished ordering.",
                "alternatives": [
                    "I'm all set, thanks!",
                    "Nope, that's everything. Can I pay by card?",
                    "That's it for me, thank you.",
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
                    {"text": "Oh, thank you! Could you tell me how to get to the Central Train Station?", "type": "best", "reason": "Warm appreciation followed by an indirect polite question ('Could you tell me how to...')."},
                    {"text": "Tell me where is train station now.", "type": "awkward", "reason": "Missing articles ('the') and uses direct word order instead of indirect question order."},
                    {"text": "Mind your own business, I'm fine.", "type": "rude", "reason": "Hostile response to someone offering help."},
                    {"text": "Trains are very fast vehicles.", "type": "awkward", "reason": "Doesn't ask for directions at all."},
                ],
                "keywords": ["station", "train", "way", "get", "where", "how", "find", "looking", "help", "thanks", "thank"],
                "ideal_response": "Oh, thank you! Could you tell me how to get to the Central Train Station?",
                "tip": "Notice the word order in indirect questions: say **'Could you tell me where the station is?'** (subject before verb), NOT *'where is the station'*.",
                "alternatives": [
                    "Yes, please! Do you know the way to the Central Train Station?",
                    "Thanks so much! I'm looking for the Central Train Station—am I heading the right way?",
                    "Hi! Could you point me toward the train station?",
                ],
            },
            {
                "speaker_a": "Of course! Walk straight down this street for two blocks, then turn left at the traffic light. You'll see it right across from the park.",
                "hint": "Confirm you understood the steps (two blocks straight, left at the light) and check how long it takes.",
                "options": [
                    {"text": "Got it—two blocks straight and left at the light. About how long does it take to walk there?", "type": "best", "reason": "Paraphrasing directions confirms understanding, and 'About how long...' sounds very natural."},
                    {"text": "I understand street blocks light park.", "type": "awkward", "reason": "Broken telegraphic English without connecting words."},
                    {"text": "That sounds way too complicated, drive me there.", "type": "rude", "reason": "Unreasonable and impolite demand to a stranger."},
                    {"text": "Do you like walking in the park?", "type": "awkward", "reason": "Changes the subject instead of confirming the directions."},
                ],
                "keywords": ["blocks", "left", "straight", "long", "far", "minutes", "walk", "got", "understand", "thanks"],
                "ideal_response": "Got it—two blocks straight and left at the light. About how long does it take to walk there?",
                "tip": "Repeating key landmarks back with **'Got it, so...'** is a great communication habit that ensures you heard the directions accurately.",
                "alternatives": [
                    "So straight for two blocks and then a left? Is it far from here?",
                    "Makes sense! How many minutes' walk would you say that is?",
                    "Thank you! Just to double-check, I turn left at the light?",
                ],
            },
            {
                "speaker_a": "It's only about a five-minute walk! You really can't miss it.",
                "hint": "Express gratitude warmly and say goodbye.",
                "options": [
                    {"text": "That's super helpful. Thanks so much for your help, have a great day!", "type": "best", "reason": "Natural, appreciative, and closes the interaction warmly."},
                    {"text": "Five minutes is acceptable. Goodbye.", "type": "awkward", "reason": "Stiff and overly formal for a friendly street interaction."},
                    {"text": "Finally, I can stop talking to you.", "type": "rude", "reason": "Extremely rude to someone who just helped you."},
                    {"text": "My watch says it is 2:15 PM.", "type": "awkward", "reason": "Unrelated comment that ignores their helpfulness."},
                ],
                "keywords": ["thank", "thanks", "appreciate", "helpful", "great", "day", "bye", "wonderful"],
                "ideal_response": "That's super helpful. Thanks so much for your help, have a great day!",
                "tip": "Pairing **'Thanks so much for your help'** with a warm send-off like **'Have a great day!'** leaves a great impression in English-speaking cultures.",
                "alternatives": [
                    "Awesome, I really appreciate it! Have a wonderful afternoon.",
                    "Thanks a ton! Have a great rest of your day.",
                    "Thank you so much for taking the time to help me!",
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
                "hint": "Confirm you are checking in and mention you have a reservation under your name.",
                "options": [
                    {"text": "Good afternoon! Yes, I have a reservation under the name Alex Rivera.", "type": "best", "reason": "Uses the standard hospitality collocation 'a reservation under the name...'."},
                    {"text": "Yes, I booked room in this building for sleeping.", "type": "awkward", "reason": "Unnatural phrasing and missing articles."},
                    {"text": "Obviously, why else would I have suitcases?", "type": "rude", "reason": "Sarcastic and rude to a welcoming receptionist."},
                    {"text": "Is the swimming pool open right now?", "type": "awkward", "reason": "Skips answering the receptionist's check-in question."},
                ],
                "keywords": ["yes", "check", "checking", "reservation", "booked", "booking", "name", "under"],
                "ideal_response": "Good afternoon! Yes, I have a reservation under the name Alex Rivera.",
                "tip": "In hotels and restaurants, native speakers always say **'a reservation under [Name]'** or **'a reservation for [Name]'**.",
                "alternatives": [
                    "Hi! Yes, I'm checking in—the reservation is under Alex Rivera.",
                    "Good afternoon! I booked a room for two nights under Alex Rivera.",
                    "Yes, I have a booking under Rivera.",
                ],
            },
            {
                "speaker_a": "Let me pull that up for you... Ah yes, a deluxe queen room for two nights! May I see your ID and a credit card for incidentals?",
                "hint": "Hand over your ID and card politely, and ask if breakfast is included.",
                "options": [
                    {"text": "Here you go. By the way, is breakfast included with the room?", "type": "best", "reason": "'Here you go' is the natural phrase when handing items to someone, and 'By the way' introduces a polite follow-up question."},
                    {"text": "Take these plastic cards. Does food come free?", "type": "awkward", "reason": "Sounds blunt and unnatural ('Does food come free?')."},
                    {"text": "Why do you need my credit card? Are you going to steal from me?", "type": "rude", "reason": "Accusatory and inappropriate for a standard hotel policy."},
                    {"text": "I like queen beds because they are big.", "type": "awkward", "reason": "Ignores the receptionist's request for ID and card."},
                ],
                "keywords": ["here", "sure", "course", "id", "passport", "card", "breakfast", "included", "go"],
                "ideal_response": "Here you go. By the way, is breakfast included with the room?",
                "tip": "When handing something to someone, say **'Here you go'** or **'Here you are'**—never *'Take this'*, which sounds aggressive.",
                "alternatives": [
                    "Sure, here's my passport and card. Also, could you tell me if breakfast is included?",
                    "Of course, here you are. Does my rate include breakfast?",
                    "Here you go! Quick question—is breakfast included in my stay?",
                ],
            },
            {
                "speaker_a": "Yes, complimentary breakfast is served in the lobby lounge from 7:00 to 10:00 AM. Here is your key card—you're in Room 412 on the fourth floor. Enjoy your stay!",
                "hint": "Thank the receptionist and confirm where the elevators are.",
                "options": [
                    {"text": "Wonderful, thank you! Could you point me toward the elevators?", "type": "best", "reason": "Polite, appreciative, and naturally asks for directions inside the building."},
                    {"text": "Room 412 is four hundred and twelve. Where elevator?", "type": "awkward", "reason": "Unnecessary repetition and broken grammar ('Where elevator?')."},
                    {"text": "Only until 10 AM? That's terrible service.", "type": "rude", "reason": "Hostile complaint about standard hotel hours."},
                    {"text": "I usually wake up at 6:30 in the morning.", "type": "awkward", "reason": "Doesn't thank them or wrap up the check-in smoothly."},
                ],
                "keywords": ["thank", "thanks", "elevator", "elevators", "lift", "where", "great", "wonderful", "appreciate"],
                "ideal_response": "Wonderful, thank you! Could you point me toward the elevators?",
                "tip": "**'Could you point me toward...'** is a super polished and natural way to ask for directions indoors (elevators, restrooms, exits).",
                "alternatives": [
                    "Thanks so much! Which way are the elevators?",
                    "Great, I appreciate it! Are the elevators just around the corner?",
                    "Thank you! Where can I catch the elevator?",
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
                "hint": "Introduce yourself, share something positive about the event, and ask a question back.",
                "options": [
                    {"text": "Nice to meet you, Jordan! I'm Sam. I'm really enjoying it—the keynote speaker was great. What brought you here tonight?", "type": "best", "reason": "Follows the golden rule of small talk: answer positively + ask an open-ended question back."},
                    {"text": "I am Sam. The event is fine.", "type": "awkward", "reason": "Too short and abrupt—kills the momentum of the conversation."},
                    {"text": "Honestly, I'm bored and the snacks are terrible.", "type": "rude", "reason": "Overly negative for a first impression at a social/professional event."},
                    {"text": "I took the bus to get here.", "type": "awkward", "reason": "Answers 'how did you get here' instead of 'how are you enjoying the event'."},
                ],
                "keywords": ["nice", "meet", "enjoying", "great", "good", "speaker", "you", "what", "how", "name"],
                "ideal_response": "Nice to meet you, Jordan! I'm Sam. I'm really enjoying it—the keynote speaker was great. What brought you here tonight?",
                "tip": "Great small talk works like a tennis rally: **greet + answer + bounce a question back** (e.g., *'What brought you here tonight?'* or *'How about you?'*).",
                "alternatives": [
                    "Hey Jordan, nice to meet you! I'm Sam. It's been great so far—have you been to one of these meetups before?",
                    "Hi Jordan! I'm Sam. I'm having a great time—there's such a good crowd tonight. Are you in tech as well?",
                    "Nice meeting you, Jordan! I'm Sam. Really liking the vibe here—how about you?",
                ],
            },
            {
                "speaker_a": "I'm a UX designer at a small startup, so I always try to connect with other creatives. What line of work are you in?",
                "hint": "Describe your job or studies briefly and express interest in their UX design work.",
                "options": [
                    {"text": "Oh, that's awesome! I work in data analytics, so I actually collaborate with UX designers quite a bit.", "type": "best", "reason": "Finds common ground ('collaborate with UX designers') which deepens rapport naturally."},
                    {"text": "My job is working with computers in an office.", "type": "awkward", "reason": "Vague and misses the chance to connect over shared interests."},
                    {"text": "UX design sounds really easy compared to my job.", "type": "rude", "reason": "Condescending and dismissive of the other person's career."},
                    {"text": "Do you make a lot of money at your startup?", "type": "rude", "reason": "Asking about salary during small talk is considered a major faux pas in English-speaking cultures."},
                ],
                "keywords": ["work", "study", "student", "designer", "developer", "engineer", "marketing", "data", "project", "cool", "awesome", "interesting"],
                "ideal_response": "Oh, that's awesome! I work in data analytics, so I actually collaborate with UX designers quite a bit.",
                "tip": "When someone asks **'What line of work are you in?'**, look for a bridge between their field and yours—phrases like **'I actually work closely with...'** build instant connection.",
                "alternatives": [
                    "Oh nice! I'm a software developer, so I work with UX folks all the time.",
                    "That sounds really cool! I'm currently studying marketing and hoping to break into tech.",
                    "How interesting! I'm a project manager—I love working with creative teams.",
                ],
            },
            {
                "speaker_a": "No way, small world! Hey, I'm going to grab another drink before the next panel starts, but let's stay in touch—are you on LinkedIn?",
                "hint": "Respond enthusiastically and agree to connect before they head off.",
                "options": [
                    {"text": "Definitely! Let me pull up my QR code so we can connect right now. It was great chatting with you!", "type": "best", "reason": "Enthusiastic, practical, and includes a warm closing ('great chatting with you')."},
                    {"text": "Yes, I have an internet account on LinkedIn.", "type": "awkward", "reason": "Stiff and robotic phrasing."},
                    {"text": "No, I don't want to connect with you.", "type": "rude", "reason": "Blunt rejection when a polite decline ('I don't use LinkedIn much, but here's my email') would be expected."},
                    {"text": "What kind of drink are you going to get?", "type": "awkward", "reason": "Ignores their invitation to connect on LinkedIn."},
                ],
                "keywords": ["yes", "sure", "definitely", "linkedin", "connect", "touch", "great", "chatting", "talking", "qr", "email"],
                "ideal_response": "Definitely! Let me pull up my QR code so we can connect right now. It was great chatting with you!",
                "tip": "**'It was great chatting with you!'** is the most natural, friendly way to wrap up a conversation at an event without sounding overly formal.",
                "alternatives": [
                    "For sure! Here's my LinkedIn—it was really nice talking to you, Jordan!",
                    "Absolutely, let's connect! Enjoy the next panel!",
                    "Yes, definitely! Let me search your name right now—great meeting you!",
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
        "setting": "A formal video or in-person interview for a Project Coordinator role.",
        "turns": [
            {
                "speaker_a": "Thanks for coming in today. To kick things off, could you tell me a little bit about yourself and what drew you to this role?",
                "hint": "Give a concise, confident summary of your background and explain why you're excited about this company.",
                "options": [
                    {"text": "Thank you for having me! I have three years of experience coordinating cross-functional projects, and I was drawn to this role because of your company's focus on sustainable innovation.", "type": "best", "reason": "Structured (Present/Past experience + Why this company), confident, and professional."},
                    {"text": "I was born in 1998 and I need a job because rent is expensive.", "type": "awkward", "reason": "Focuses on personal life and financial need rather than professional value."},
                    {"text": "Everything is already on my resume, didn't you read it?", "type": "rude", "reason": "Confrontational and unprofessional."},
                    {"text": "I like working with people and doing good work every day.", "type": "awkward", "reason": "Too generic—lacks concrete experience or tailored interest in the role."},
                ],
                "keywords": ["thank", "experience", "background", "skills", "role", "company", "excited", "drawn", "passionate", "team", "projects"],
                "ideal_response": "Thank you for having me! I have three years of experience coordinating cross-functional projects, and I was drawn to this role because of your company's focus on sustainable innovation.",
                "tip": "Start interview answers with **'Thank you for having me'** and use the **Past–Present–Future** formula: highlight relevant experience, then connect it directly to why this specific role excites you.",
                "alternatives": [
                    "Thanks so much for the opportunity! Over the past few years, I've focused on streamlining team workflows, so this Project Coordinator position felt like a natural next step.",
                    "I appreciate you taking the time to meet with me. With my background in client operations, I'm excited to bring strong organizational skills to your growing team.",
                    "Thank you for having me! I've admired your product launches for a while, and my experience managing tight timelines aligns closely with what you're looking for.",
                ],
            },
            {
                "speaker_a": "That's great to hear. Can you share an example of a time you had to handle a tight deadline or an unexpected setback?",
                "hint": "Use the STAR method briefly: describe a challenge, the action you took, and the positive outcome.",
                "options": [
                    {"text": "Certainly. Last quarter, a key vendor delayed delivery two days before launch. I reprioritized our schedule, coordinated backup suppliers, and we still launched on time.", "type": "best", "reason": "Concise STAR structure (Situation, Action, Result) demonstrating calm problem-solving."},
                    {"text": "When deadlines are tight, I usually get very stressed and work until midnight.", "type": "awkward", "reason": "Focuses on stress rather than structured problem-solving or results."},
                    {"text": "Setbacks only happen when my coworkers are lazy.", "type": "rude", "reason": "Blaming colleagues is a major red flag in interviews."},
                    {"text": "Yes, I have had many deadlines in my previous job.", "type": "awkward", "reason": "Fails to give a specific example as requested."},
                ],
                "keywords": ["deadline", "project", "problem", "challenge", "team", "solution", "resolved", "schedule", "result", "time", "launch", "delivered"],
                "ideal_response": "Certainly. Last quarter, a key vendor delayed delivery two days before launch. I reprioritized our schedule, coordinated backup suppliers, and we still launched on time.",
                "tip": "In behavioral interviews, keep stories crisp using **STAR** (Situation → Task → Action → Result) and emphasize **'I'** for your actions while keeping the tone calm and solution-oriented.",
                "alternatives": [
                    "Sure! On a recent campaign, our scope changed mid-week. I broke the tasks into daily milestones, aligned the team, and we hit our Friday deadline without cutting quality.",
                    "Of course. When a teammate unexpectedly fell ill before a client presentation, I stepped in to consolidate our slides and ensured the pitch went smoothly.",
                    "Definitely—last month we faced a sudden budget cut, so I renegotiated deliverables with stakeholders and still met our core objectives on schedule.",
                ],
            },
            {
                "speaker_a": "Impressive adaptability. Before we wrap up, do you have any questions for me about the team or the role?",
                "hint": "Ask a thoughtful, forward-looking question about team goals or success in the role.",
                "options": [
                    {"text": "Yes, thank you! What would success look like for someone in this role during their first 90 days?", "type": "best", "reason": "Shows strategic thinking, proactivity, and genuine interest in performing well."},
                    {"text": "No, I have zero questions.", "type": "awkward", "reason": "Saying 'no questions' can signal a lack of preparation or enthusiasm."},
                    {"text": "How soon can I take paid vacation after starting?", "type": "rude", "reason": "Asking about time off before receiving an offer sends the wrong priority signal."},
                    {"text": "What does your company actually sell?", "type": "awkward", "reason": "Shows you didn't do basic research before the interview."},
                ],
                "keywords": ["success", "team", "goals", "days", "culture", "challenge", "expect", "growth", "project", "collaborate", "question"],
                "ideal_response": "Yes, thank you! What would success look like for someone in this role during their first 90 days?",
                "tip": "Always prepare 1–2 thoughtful questions! Asking **'What does success look like in the first 90 days?'** shows ambition and helps you picture yourself in the job.",
                "alternatives": [
                    "I do! How does this team typically collaborate across departments on new initiatives?",
                    "Yes—what are the biggest priorities the team is tackling over the next six months?",
                    "Thank you, yes! What do you enjoy most about working with this team?",
                ],
            },
        ],
    },
    {
        "id": "doctor",
        "title": "Doctor's Appointment",
        "difficulty": "Advanced",
        "theme_color": "#dc2626",
        "bg_color": "#fee2e2",
        "person_a_role": "Dr. Patel",
        "person_a_avatar": "🩺",
        "person_b_role": "Patient (You)",
        "person_b_avatar": "🤒",
        "setting": "An examination room at a primary care clinic.",
        "turns": [
            {
                "speaker_a": "Hello! I'm Dr. Patel. What brings you into the clinic today?",
                "hint": "Describe your symptoms clearly and mention how long you've had them.",
                "options": [
                    {"text": "Hi Dr. Patel. I've had a sore throat and a mild fever for the past three days, and it's getting harder to swallow.", "type": "best", "reason": "Uses present perfect ('I've had... for three days') accurately to describe ongoing symptoms."},
                    {"text": "My throat is hurting since three days ago and body is hot.", "type": "awkward", "reason": "Grammar error ('since three days ago' should be 'for three days') and imprecise vocabulary."},
                    {"text": "You're the doctor, shouldn't you already know?", "type": "rude", "reason": "Sarcastic and unhelpful during a medical consultation."},
                    {"text": "I came here by taxi because traffic was bad.", "type": "awkward", "reason": "'What brings you in today?' is a medical idiom asking about your health issue, not transportation."},
                ],
                "keywords": ["throat", "fever", "cough", "headache", "pain", "sick", "days", "week", "feeling", "symptoms", "ache", "stomach"],
                "ideal_response": "Hi Dr. Patel. I've had a sore throat and a mild fever for the past three days, and it's getting harder to swallow.",
                "tip": "When doctors ask **'What brings you in today?'**, they are asking about your symptoms. Use **'I've had [symptom] for [duration]'** (present perfect) for symptoms that started in the past and are still happening.",
                "alternatives": [
                    "Good morning, Doctor. I've been dealing with a persistent cough and fatigue since Monday.",
                    "Hi Dr. Patel. I came in because I've had a sharp pain in my lower back for about a week.",
                    "Hello! I've been feeling dizzy and congested over the last couple of days.",
                ],
            },
            {
                "speaker_a": "I see. Have you taken any over-the-counter medication for it yet, and do you have any known drug allergies?",
                "hint": "Answer both parts of the doctor's question clearly (medication taken + allergies).",
                "options": [
                    {"text": "I took some ibuprofen last night to bring the fever down, and I don't have any known allergies.", "type": "best", "reason": "Directly answers both questions with natural medical phrasing ('bring the fever down')."},
                    {"text": "I ate one pill yesterday. No allergy.", "type": "awkward", "reason": "In English, we 'take' medicine (not 'eat' pills), and 'No allergy' is incomplete."},
                    {"text": "I don't remember what I took, stop asking so many questions.", "type": "rude", "reason": "Hostile and unsafe during medical care."},
                    {"text": "I'm allergic to waking up early on Mondays.", "type": "awkward", "reason": "Joking around when the doctor needs serious allergy safety info."},
                ],
                "keywords": ["took", "taken", "medicine", "medication", "ibuprofen", "tylenol", "painkiller", "allergy", "allergies", "none", "no", "penicillin"],
                "ideal_response": "I took some ibuprofen last night to bring the fever down, and I don't have any known allergies.",
                "tip": "Remember the verb collocation: we **'take medication / pills / syrup'**, never *'eat'* or *'drink'* medicine.",
                "alternatives": [
                    "I haven't taken anything yet, and as far as I know, I'm not allergic to any medications.",
                    "Just some throat lozenges and tea so far. I am allergic to penicillin, though.",
                    "I took acetaminophen this morning, and I have no drug allergies.",
                ],
            },
            {
                "speaker_a": "Thank you—that's very helpful. After checking your throat, it looks like a mild viral infection, so rest and fluids are key. I'll prescribe a soothing throat spray just in case. Any questions before you head out?",
                "hint": "Ask a practical question about recovery time or when to follow up if symptoms don't improve.",
                "options": [
                    {"text": "That makes sense, thank you. How many days should it take to clear up, and when should I come back if I don't feel better?", "type": "best", "reason": "Uses natural phrasal verb 'clear up' and asks a smart follow-up care question."},
                    {"text": "Okay, give me antibiotics right now anyway.", "type": "rude", "reason": "Demanding antibiotics for a viral infection ignores medical advice."},
                    {"text": "Virus is small organism. I will drink water.", "type": "awkward", "reason": "Robotic phrasing that doesn't ask a helpful recovery question."},
                    {"text": "Do you think it's going to rain tomorrow?", "type": "awkward", "reason": "Off-topic small talk at the end of a medical exam."},
                ],
                "keywords": ["days", "long", "recover", "better", "clear", "spray", "times", "follow", "back", "thank", "thanks"],
                "ideal_response": "That makes sense, thank you. How many days should it take to clear up, and when should I come back if I don't feel better?",
                "tip": "Native speakers use the phrasal verb **'clear up'** when talking about an illness, rash, or infection going away (e.g., *'How soon should this clear up?'*).",
                "alternatives": [
                    "Thanks, Dr. Patel! How often should I use the throat spray each day?",
                    "Got it, thank you! Should I schedule a follow-up if the fever doesn't go down by Friday?",
                    "I appreciate your help! Is there anything specific I should avoid eating or drinking?",
                ],
            },
        ],
    },
]


# -----------------------------------------------------------------------------
# Helpers: Context Illustration (PIL) & Audio Pronunciation (gTTS)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_scenario_banner(title: str, setting: str, difficulty: str, theme_color: str, bg_color: str) -> bytes:
    """Generates a crisp, zero-dependency PIL header card for the active scenario."""
    w, h = 760, 150
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Accent bar on the left & decorative circles on the right
    draw.rectangle([0, 0, 14, h], fill=theme_color)
    draw.ellipse([w - 130, -35, w + 30, 125], fill=theme_color)
    draw.ellipse([w - 75, 55, w + 45, 175], fill="#ffffff")

    # Border
    draw.rectangle([0, 0, w - 1, h - 1], outline=theme_color, width=3)

    # Chat bubble icon graphics
    draw.rounded_rectangle([36, 36, 114, 92], radius=16, fill=theme_color)
    draw.polygon([(52, 92), (68, 92), (48, 110)], fill=theme_color)
    draw.ellipse([54, 59, 62, 67], fill="#ffffff")
    draw.ellipse([71, 59, 79, 67], fill="#ffffff")
    draw.ellipse([88, 59, 96, 67], fill="#ffffff")

    # Text rendering using Pillow default scalable font (Pillow 10+) with fallback
    try:
        title_font = ImageFont.load_default(size=28)
        sub_font = ImageFont.load_default(size=17)
        badge_font = ImageFont.load_default(size=15)
    except TypeError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    draw.text((138, 30), title, fill="#111827", font=title_font)
    draw.text((138, 70), setting[:72] + ("..." if len(setting) > 72 else ""), fill="#374151", font=sub_font)
    draw.text((138, 104), f"Level: {difficulty.upper()}   |   Multi-Turn Speaking Practice", fill=theme_color, font=badge_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def text_to_speech_bytes(text: str) -> bytes | None:
    """Generates MP3 audio bytes using gTTS with graceful offline/error fallback."""
    if not GTTS_AVAILABLE or not text.strip():
        return None
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def evaluate_free_response(user_text: str, turn_data: dict) -> tuple[str, int, str]:
    """
    Evaluates typed user dialogue using length, politeness/intent keyword matching,
    and question/structure heuristics.
    Returns: (rating_level, points_earned, feedback_message)
    """
    cleaned = user_text.strip()
    lower_text = cleaned.lower()
    words = re.findall(r"\b\w+\b", lower_text)

    if len(words) < 2:
        return (
            "needs_work",
            25,
            "Your response is a bit too brief for natural conversation. Try speaking in a full sentence!",
        )

    keywords = [kw.lower() for kw in turn_data["keywords"]]
    matched_keywords = [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lower_text)]
    polite_markers = {"please", "thank", "thanks", "could", "would", "hi", "hello", "good", "great", "appreciate", "sorry", "excuse"}
    has_politeness = any(w in polite_markers for w in words)

    score_hits = len(matched_keywords) + (1 if has_politeness else 0) + (1 if len(words) >= 5 else 0)

    if score_hits >= 3:
        return (
            "excellent",
            100,
            f"🌟 **Natural & Context-Aware!** Great phrasing (matched key context cues: *{', '.join(matched_keywords[:4])}*).",
        )
    elif score_hits >= 1:
        return (
            "good",
            70,
            "👍 **Good Effort!** Your meaning comes across, though adding a polite phrase or specific detail will make it sound even more natural.",
        )
    else:
        return (
            "needs_work",
            35,
            "🤔 **Off-Context or Unclear:** Your reply didn't directly address what Person A just asked. Compare your answer with the model response below!",
        )


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
def reset_scenario(scenario_id: str, mode: str):
    st.session_state.scenario_id = scenario_id
    st.session_state.mode = mode
    st.session_state.turn_idx = 0
    st.session_state.chat_history = []  # List of dicts: {"role": "A"|"B", "text": str}
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.best_streak = 0
    st.session_state.show_hint = False
    st.session_state.turn_answered = False
    st.session_state.last_feedback = None  # {"status": str, "msg": str, "points": int, "user_choice": str}
    st.session_state.selected_mc_option = None


if "scenario_id" not in st.session_state:
    reset_scenario(SCENARIOS[0]["id"], "Choose the Best Response")


# -----------------------------------------------------------------------------
# Sidebar Navigation & Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎙️ Conversation Settings")

    difficulty_filter = st.selectbox(
        "Filter by Difficulty",
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
        "Select Scenario",
        options=list(scenario_titles.keys()),
        index=list(scenario_titles.values()).index(current_scenario_obj["id"]),
    )
    chosen_id = scenario_titles[chosen_title]

    chosen_mode = st.radio(
        "Practice Mode",
        options=["Choose the Best Response", "Type Your Own Response"],
        index=0 if st.session_state.mode == "Choose the Best Response" else 1,
    )

    # Reset automatically if scenario or mode changes
    if chosen_id != st.session_state.scenario_id or chosen_mode != st.session_state.mode:
        reset_scenario(chosen_id, chosen_mode)
        st.rerun()

    if st.button("🔄 Restart Scenario", use_container_width=True):
        reset_scenario(chosen_id, chosen_mode)
        st.rerun()

    st.divider()
    st.subheader("🎧 Audio Status")
    if GTTS_AVAILABLE:
        st.caption("Text-to-Speech (`gTTS`) is enabled. Click **Listen** buttons in the chat to hear pronunciation.")
    else:
        st.caption("`gTTS` not installed. Run `pip install gTTS` to enable voice playback.")


# -----------------------------------------------------------------------------
# Active Scenario & Header
# -----------------------------------------------------------------------------
scenario = next(s for s in SCENARIOS if s["id"] == st.session_state.scenario_id)
total_turns = len(scenario["turns"])
turn_idx = st.session_state.turn_idx

st.title("💬 English Speaking & Dialogue Game")

# Context Banner (PIL-generated)
banner_bytes = generate_scenario_banner(
    scenario["title"],
    scenario["setting"],
    scenario["difficulty"],
    scenario["theme_color"],
    scenario["bg_color"],
)
st.image(banner_bytes, use_container_width=True)

# Scoreboard Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Turn", f"{min(turn_idx + 1, total_turns)} / {total_turns}")
m2.metric("Score", f"{st.session_state.score} pts")
m3.metric("Fluency Streak 🔥", st.session_state.streak)
m4.metric("Best Streak 🏆", st.session_state.best_streak)

st.progress(min(turn_idx / total_turns, 1.0))
st.divider()

# -----------------------------------------------------------------------------
# Render Completed Conversation History
# -----------------------------------------------------------------------------
for entry in st.session_state.chat_history:
    if entry["role"] == "A":
        with st.chat_message("assistant", avatar=scenario["person_a_avatar"]):
            st.markdown(f"**{scenario['person_a_role']}:** {entry['text']}")
    else:
        with st.chat_message("user", avatar=scenario["person_b_avatar"]):
            st.markdown(f"**{scenario['person_b_role']}:** {entry['text']}")

# -----------------------------------------------------------------------------
# Scenario Completion Summary
# -----------------------------------------------------------------------------
if turn_idx >= total_turns:
    st.balloons()
    st.success(f"🎉 **Conversation Complete!** You finished **{scenario['title']}**.")
    st.markdown(
        f"""
        - **Total Score:** `{st.session_state.score}` points
        - **Best Fluency Streak:** `{st.session_state.best_streak}`
        - **Practice Mode:** `{st.session_state.mode}`
        """
    )

    col_replay, col_next = st.columns(2)
    with col_replay:
        if st.button("🔁 Practice This Scenario Again", use_container_width=True):
            reset_scenario(scenario["id"], st.session_state.mode)
            st.rerun()
    with col_next:
        next_idx = (SCENARIOS.index(scenario) + 1) % len(SCENARIOS)
        next_scen = SCENARIOS[next_idx]
        if st.button(f"➡️ Next: {next_scen['title']}", type="primary", use_container_width=True):
            reset_scenario(next_scen["id"], st.session_state.mode)
            st.rerun()
    st.stop()

# -----------------------------------------------------------------------------
# Current Active Turn
# -----------------------------------------------------------------------------
current_turn = scenario["turns"][turn_idx]

# Display Person A's current line (if not yet added to history)
if not st.session_state.turn_answered:
    with st.chat_message("assistant", avatar=scenario["person_a_avatar"]):
        st.markdown(f"**{scenario['person_a_role']}:** {current_turn['speaker_a']}")

        # Listen to Person A Button
        if st.button("🔊 Listen to Person A", key=f"tts_a_{scenario['id']}_{turn_idx}"):
            audio_a = text_to_speech_bytes(current_turn["speaker_a"])
            if audio_a:
                st.audio(audio_a, format="audio/mp3", autoplay=True)
            else:
                st.info("🔇 Audio unavailable offline. Read aloud to practice intonation!")

# Hint Controls (Before Answering)
if not st.session_state.turn_answered:
    h_col1, h_col2 = st.columns([1, 2])
    with h_col1:
        if st.button("💡 Hint / Situation Context", use_container_width=True):
            st.session_state.show_hint = not st.session_state.show_hint
    with h_col2:
        st.caption("Need a nudge? View the communication goal for this turn.")

    if st.session_state.show_hint:
        st.markdown(
            f"<div class='hint-banner'><strong>🧭 Situation Goal:</strong> {current_turn['hint']}</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    # -------------------------------------------------------------------------
    # MODE 1: Choose the Best Response
    # -------------------------------------------------------------------------
    if st.session_state.mode == "Choose the Best Response":
        option_texts = [opt["text"] for opt in current_turn["options"]]
        selected_text = st.radio(
            f"How should **{scenario['person_b_role']}** respond?",
            options=option_texts,
            key=f"mc_radio_{scenario['id']}_{turn_idx}",
        )

        if st.button("✅ Submit Response", type="primary", use_container_width=True):
            chosen_opt = next(o for o in current_turn["options"] if o["text"] == selected_text)
            opt_type = chosen_opt["type"]

            if opt_type == "best":
                earned = 100 + (st.session_state.streak * 15)
                st.session_state.score += earned
                st.session_state.streak += 1
                st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
                status = "best"
                fb_msg = f"🎉 **Spot on! (+{earned} pts)** {chosen_opt['reason']}"
            elif opt_type == "awkward":
                earned = 40
                st.session_state.score += earned
                st.session_state.streak = 0
                status = "awkward"
                fb_msg = f"⚠️ **Understandable, but awkward (+{earned} pts):** {chosen_opt['reason']}"
            else:
                earned = 0
                st.session_state.streak = 0
                status = "rude"
                fb_msg = f"❌ **Too blunt / off-tone (+0 pts):** {chosen_opt['reason']}"

            # Append both turns to chat history so the dialogue flows naturally
            st.session_state.chat_history.append({"role": "A", "text": current_turn["speaker_a"]})
            st.session_state.chat_history.append({"role": "B", "text": selected_text})
            st.session_state.turn_answered = True
            st.session_state.last_feedback = {
                "status": status,
                "msg": fb_msg,
                "points": earned,
                "user_choice": selected_text,
            }
            st.rerun()

    # -------------------------------------------------------------------------
    # MODE 2: Type Your Own Response
    # -------------------------------------------------------------------------
    else:
        with st.form(key=f"free_form_{scenario['id']}_{turn_idx}"):
            typed_reply = st.text_input(
                f"Type what **{scenario['person_b_role']}** would say:",
                placeholder="Write a natural, polite response...",
            )
            submitted_free = st.form_submit_button("✅ Say / Submit Response", type="primary", use_container_width=True)

        if submitted_free:
            if not typed_reply.strip():
                st.warning("Please type a response before submitting!")
            else:
                rating, earned, fb_msg = evaluate_free_response(typed_reply, current_turn)
                if rating == "excellent":
                    earned += st.session_state.streak * 15
                    st.session_state.streak += 1
                    st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
                elif rating == "good":
                    st.session_state.streak += 1
                    st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
                else:
                    st.session_state.streak = 0

                st.session_state.score += earned
                st.session_state.chat_history.append({"role": "A", "text": current_turn["speaker_a"]})
                st.session_state.chat_history.append({"role": "B", "text": typed_reply.strip()})
                st.session_state.turn_answered = True
                st.session_state.last_feedback = {
                    "status": rating,
                    "msg": f"{fb_msg} **(+{earned} pts)**",
                    "points": earned,
                    "user_choice": typed_reply.strip(),
                }
                st.rerun()

# -----------------------------------------------------------------------------
# Post-Turn Coaching: Feedback, Pronunciation & Natural Speaking Tip
# -----------------------------------------------------------------------------
if st.session_state.turn_answered and st.session_state.last_feedback:
    fb = st.session_state.last_feedback
    if fb["status"] in ("best", "excellent"):
        st.success(fb["msg"])
    elif fb["status"] in ("awkward", "good"):
        st.warning(fb["msg"])
    else:
        st.error(fb["msg"])

    # Ideal Response & Audio Pronunciation
    ideal_line = current_turn["ideal_response"]
    st.markdown(f"**✨ Ideal Natural Response:** *\"{ideal_line}\"*")

    if st.button("🔊 Listen to Ideal Pronunciation", key=f"tts_ideal_{scenario['id']}_{turn_idx}"):
        audio_ideal = text_to_speech_bytes(ideal_line)
        if audio_ideal:
            st.audio(audio_ideal, format="audio/mp3", autoplay=True)
        else:
            st.info("🔇 Audio unavailable offline. Practice saying the ideal response aloud three times!")

    # Natural Speaking Tip & Native Alternatives
    alts_html = "".join(f"<span class='alt-pill'>“{alt}”</span>" for alt in current_turn["alternatives"])
    st.markdown(
        f"""
        <div class="tip-card">
            <h4 style="margin-top:0;">🗣️ Natural Speaking Tip</h4>
            <p>{current_turn['tip']}</p>
            <p style="margin-bottom:0.35rem;"><strong>Other ways native speakers say this:</strong></p>
            <div>{alts_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    next_btn_label = "➡️ Continue Conversation" if turn_idx + 1 < total_turns else "🏁 Finish & View Score"
    if st.button(next_btn_label, type="primary", use_container_width=True):
        st.session_state.turn_idx += 1
        st.session_state.turn_answered = False
        st.session_state.show_hint = False
        st.session_state.last_feedback = None
        st.rerun()
