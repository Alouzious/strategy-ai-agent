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
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def build_llm(temperature=0.5):
    return LLM(
        model=f"groq/{GROQ_MODEL}",
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=500,
    )


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

        try:
            start_time = time.time()

            llm = build_llm()

            # ── Agents ──
            researcher = Agent(
                role="Market Researcher",
                goal=f"Research '{topic}' in '{industry}'. Find market size, top 3 trends, key competitors.",
                backstory="Expert researcher who finds accurate market data quickly and concisely.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                max_iter=1,
            )

            analyst = Agent(
                role="Business Analyst",
                goal=f"Analyze '{topic}' for '{audience}'. SWOT analysis and top 3 opportunities.",
                backstory="Senior analyst who turns research into clear, actionable strategic insights.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                max_iter=1,
            )

            strategist = Agent(
                role="Marketing Strategist",
                goal=f"Design a marketing strategy for '{topic}' targeting '{audience}' in '{industry}'.",
                backstory="Creative strategist who builds focused, data-driven marketing campaigns.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                max_iter=1,
            )

            writer = Agent(
                role="Report Writer",
                goal=f"Write a clear, structured executive report for '{topic}'.",
                backstory="Professional writer who produces polished, board-ready strategy documents.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                max_iter=1,
            )

            critic = Agent(
                role="Quality Reviewer",
                goal="Score the report out of 10 and give 3 specific improvement recommendations.",
                backstory="Honest senior consultant who ensures every report meets high standards.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                max_iter=1,
            )

            # ── Tasks ──
            task1 = Task(
                description=(
                    f"Research '{topic}' in the '{industry}' industry.\n"
                    f"Be brief and factual. Cover:\n"
                    f"- Market size and growth rate\n"
                    f"- Top 3 competitors\n"
                    f"- Top 3 current trends\n"
                    f"- Key consumer insight\n"
                    f"Keep response under 150 words."
                ),
                expected_output="Concise bullet-point research summary under 150 words.",
                agent=researcher,
            )

            task2 = Task(
                description=(
                    f"Analyze '{topic}' targeting '{audience}' in '{industry}'.\n"
                    f"Cover:\n"
                    f"- SWOT (2 points each)\n"
                    f"- Top 3 market opportunities\n"
                    f"Keep response under 150 words."
                ),
                expected_output="SWOT analysis and top 3 opportunities under 150 words.",
                agent=analyst,
                context=[task1],
            )

            task3 = Task(
                description=(
                    f"Create a marketing strategy for '{topic}' targeting '{audience}'.\n"
                    f"Cover:\n"
                    f"- Top 3 marketing channels\n"
                    f"- Key message\n"
                    f"- 30-day action plan (3 steps)\n"
                    f"- 3 KPIs\n"
                    f"Keep response under 200 words."
                ),
                expected_output="Focused marketing strategy under 200 words.",
                agent=strategist,
                context=[task1, task2],
            )

            task4 = Task(
                description=(
                    f"Write an executive strategy report for '{topic}'.\n"
                    f"Sections:\n"
                    f"- Executive Summary\n"
                    f"- Market Findings\n"
                    f"- Strategic Analysis\n"
                    f"- Marketing Strategy\n"
                    f"- Next Steps\n"
                    f"Keep response under 250 words."
                ),
                expected_output="Structured executive report under 250 words.",
                agent=writer,
                context=[task1, task2, task3],
            )

            task5 = Task(
                description=(
                    f"Review the marketing strategy report.\n"
                    f"Provide:\n"
                    f"- Score out of 10\n"
                    f"- 2 things that work well\n"
                    f"- 3 specific improvements\n"
                    f"Keep response under 120 words."
                ),
                expected_output="Quality review with score and recommendations under 120 words.",
                agent=critic,
                context=[task4],
            )

            # ── Run tasks one by one with delay to avoid rate limit ──
            all_tasks  = [task1, task2, task3, task4, task5]
            all_agents = [researcher, analyst, strategist, writer, critic]

            crew = Crew(
                agents=all_agents,
                tasks=all_tasks,
                process=Process.sequential,
                verbose=False,
                memory=False,
            )

            result = crew.kickoff()
            elapsed = round(time.time() - start_time, 1)

            return Response({
                "status":    "success",
                "topic":     topic,
                "industry":  industry,
                "audience":  audience,
                "time_taken": f"{elapsed}s",
                "agents": {
                    "researcher": str(task1.output),
                    "analyst":    str(task2.output),
                    "strategist": str(task3.output),
                    "writer":     str(task4.output),
                    "critic":     str(task5.output),
                },
                "final_report": str(result),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = str(e)
            traceback.print_exc()

            if "rate_limit" in error_msg.lower() or "ratelimit" in error_msg.lower():
                return Response({
                    "status": "error",
                    "error": "Too many requests at once. Please wait 60 seconds and try again.",
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            return Response({
                "status": "error",
                "error": "Something went wrong. Please try again.",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status":  "online",
            "stages":  5,
            "key_set": bool(GROQ_API_KEY),
        })
