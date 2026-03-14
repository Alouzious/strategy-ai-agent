from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
import os
import time
import traceback
import logging

logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Your exact available models from Groq API ──
MODELS = [
    "llama-3.1-8b-instant",                      # fastest, high limit
    "meta-llama/llama-4-scout-17b-16e-instruct",  # latest Meta model
    "qwen/qwen3-32b",                             # Alibaba - powerful
    "moonshotai/kimi-k2-instruct",                # Moonshot AI
    "llama-3.3-70b-versatile",                    # smartest Meta
]


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

    return [researcher, analyst, strategist, writer, critic], [task1, task2, task3, task4, task5]


class RunAgentView(APIView):
    def post(self, request):
        topic    = request.data.get("topic", "").strip()
        industry = request.data.get("industry", "General").strip()
        audience = request.data.get("audience", "General public").strip()

        if not topic:
            return Response(
                {"error": "Topic is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not GROQ_API_KEY:
            return Response(
                {"error": "API key not configured. Contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        start_time = time.time()

        for model in MODELS:
            try:
                logger.info(f"[StrategyAI] Trying: {model}")
                print(f"[StrategyAI] Trying: {model}")

                llm = build_llm(model)
                agents, tasks = make_agents_and_tasks(topic, industry, audience, llm)

                crew = Crew(
                    agents=agents,
                    tasks=tasks,
                    process=Process.sequential,
                    verbose=False,
                    memory=False,
                )

                result  = crew.kickoff()
                elapsed = round(time.time() - start_time, 1)

                print(f"[StrategyAI] Success with: {model} in {elapsed}s")

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
                print(f"[StrategyAI] Error on {model}: {error_msg[:200]}")

                # Rate limit — try next model
                if "rate_limit" in error_msg.lower() or "ratelimit" in error_msg.lower():
                    print(f"[StrategyAI] Rate limited on {model} — switching...")
                    time.sleep(2)
                    continue

                # Model not found — try next
                if "model_not_found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"[StrategyAI] Model not found: {model} — switching...")
                    continue

                # Auth error — stop immediately
                if "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    return Response({
                        "status": "error",
                        "error": "API key is invalid. Please contact support.",
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Any other error — log and try next model
                traceback.print_exc()
                print(f"[StrategyAI] Unknown error on {model} — trying next...")
                continue

        # All models failed
        print("[StrategyAI] All models exhausted.")
        return Response({
            "status": "error",
            "error":  "Our AI pipeline is at capacity right now. Please try again in 15 minutes.",
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status":   "online",
            "stages":   5,
            "models":   MODELS,
            "total":    len(MODELS),
            "key_set":  bool(GROQ_API_KEY),
        })
