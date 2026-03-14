from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
import os
import time
import traceback

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── All free Groq models in priority order ──
# If one hits rate limit, automatically tries the next one
FALLBACK_MODELS = [
    os.getenv("GROQ_MODEL", "gemma2-9b-it"),  # primary from .env
    "gemma2-9b-it",                            # 500k/day
    "mixtral-8x7b-32768",                      # 500k/day
    "llama-3.1-8b-instant",                    # 500k/day - fastest
    "llama3-8b-8192",                          # 500k/day
    "llama3-70b-8192",                         # 500k/day
    "llama-3.3-70b-versatile",                 # 100k/day - smartest
]

# Remove duplicates while keeping order
seen = set()
MODELS = []
for m in FALLBACK_MODELS:
    if m not in seen:
        seen.add(m)
        MODELS.append(m)


def build_llm(model, temperature=0.5):
    return LLM(
        model=f"groq/{model}",
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=500,
    )


def make_agents_and_tasks(topic, industry, audience, llm):
    researcher = Agent(
        role="Market Researcher",
        goal=f"Research '{topic}' in '{industry}'. Find market size, top 3 trends, key competitors.",
        backstory="Expert researcher who finds accurate market data quickly and concisely.",
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )
    analyst = Agent(
        role="Business Analyst",
        goal=f"Analyze '{topic}' for '{audience}'. SWOT and top 3 opportunities.",
        backstory="Senior analyst who turns research into clear strategic insights.",
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )
    strategist = Agent(
        role="Marketing Strategist",
        goal=f"Design a marketing strategy for '{topic}' targeting '{audience}' in '{industry}'.",
        backstory="Creative strategist who builds focused data-driven marketing campaigns.",
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )
    writer = Agent(
        role="Report Writer",
        goal=f"Write a clear executive report for '{topic}'.",
        backstory="Professional writer who produces polished strategy documents.",
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )
    critic = Agent(
        role="Quality Reviewer",
        goal="Score the report out of 10 and give 3 improvement recommendations.",
        backstory="Honest senior consultant who ensures every report meets high standards.",
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )

    task1 = Task(
        description=f"Research '{topic}' in '{industry}'. Cover: market size, top 3 competitors, top 3 trends, one consumer insight. Max 150 words.",
        expected_output="Bullet-point research summary. Max 150 words.",
        agent=researcher,
    )
    task2 = Task(
        description=f"Analyze '{topic}' for '{audience}'. SWOT (2 points each) and top 3 opportunities. Max 150 words.",
        expected_output="SWOT analysis and opportunities. Max 150 words.",
        agent=analyst,
        context=[task1],
    )
    task3 = Task(
        description=f"Marketing strategy for '{topic}' targeting '{audience}'. Top 3 channels, key message, 30-day plan, 3 KPIs. Max 200 words.",
        expected_output="Focused marketing strategy. Max 200 words.",
        agent=strategist,
        context=[task1, task2],
    )
    task4 = Task(
        description=f"Executive report for '{topic}'. Sections: Summary, Market, Analysis, Strategy, Next Steps. Max 250 words.",
        expected_output="Structured executive report. Max 250 words.",
        agent=writer,
        context=[task1, task2, task3],
    )
    task5 = Task(
        description="Score the report out of 10. List 2 strengths and 3 specific improvements. Max 120 words.",
        expected_output="Score, strengths and improvements. Max 120 words.",
        agent=critic,
        context=[task4],
    )

    agents = [researcher, analyst, strategist, writer, critic]
    tasks  = [task1, task2, task3, task4, task5]
    return agents, tasks


class RunAgentView(APIView):
    def post(self, request):
        topic    = request.data.get("topic", "AI trends").strip()
        industry = request.data.get("industry", "General").strip()
        audience = request.data.get("audience", "General public").strip()

        if not topic:
            return Response(
                {"error": "Topic is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time  = time.time()
        last_error  = None
        used_model  = None

        # ── Try each model until one works ──
        for model in MODELS:
            try:
                print(f"[StrategyAI] Trying model: {model}")
                llm = build_llm(model)
                agents, tasks = make_agents_and_tasks(topic, industry, audience, llm)

                crew = Crew(
                    agents=agents,
                    tasks=tasks,
                    process=Process.sequential,
                    verbose=False,
                    memory=False,
                )

                result   = crew.kickoff()
                used_model = model
                elapsed  = round(time.time() - start_time, 1)

                print(f"[StrategyAI] Success with model: {model}")

                return Response({
                    "status":     "success",
                    "topic":      topic,
                    "industry":   industry,
                    "audience":   audience,
                    "time_taken": f"{elapsed}s",
                    "agents": {
                        "researcher": str(tasks[0].output),
                        "analyst":    str(tasks[1].output),
                        "strategist": str(tasks[2].output),
                        "writer":     str(tasks[3].output),
                        "critic":     str(tasks[4].output),
                    },
                    "final_report": str(result),
                }, status=status.HTTP_200_OK)

            except Exception as e:
                error_msg = str(e)
                last_error = error_msg

                if "rate_limit" in error_msg.lower() or "ratelimit" in error_msg.lower():
                    print(f"[StrategyAI] Rate limit on {model} — trying next model...")
                    time.sleep(1)
                    continue
                else:
                    # Not a rate limit error — stop trying
                    traceback.print_exc()
                    return Response({
                        "status": "error",
                        "error":  "Something went wrong. Please try again.",
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # All models exhausted
        print(f"[StrategyAI] All models rate limited.")
        return Response({
            "status": "error",
            "error":  "All AI models are currently at capacity. Please try again in 15 minutes.",
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status":         "online",
            "stages":         5,
            "primary_model":  MODELS[0],
            "fallback_models": MODELS[1:],
            "total_models":   len(MODELS),
            "key_set":        bool(GROQ_API_KEY),
        })
