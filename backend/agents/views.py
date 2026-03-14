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


def build_llm(temperature=0.7):
    return LLM(
        model=f"groq/{GROQ_MODEL}",
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=2048,
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

            llm_research = build_llm(temperature=0.3)
            llm_analysis = build_llm(temperature=0.5)
            llm_creative = build_llm(temperature=0.8)
            llm_critic   = build_llm(temperature=0.4)

            researcher = Agent(
                role="Senior Market Researcher",
                goal=(
                    f"Conduct deep research on '{topic}' in the '{industry}' industry. "
                    "Find current trends, key statistics, market size, major players, and recent news."
                ),
                backstory=(
                    "You are a world-class market researcher with 15 years of experience. "
                    "You find accurate, relevant, up-to-date information and back claims with evidence."
                ),
                llm=llm_research,
                verbose=True,
                allow_delegation=False,
                max_iter=3,
            )

            analyst = Agent(
                role="Strategic Business Analyst",
                goal=(
                    f"Perform a deep SWOT and competitive analysis on '{topic}'. "
                    f"Identify top 3 opportunities, top 3 risks, and key success factors "
                    f"for targeting '{audience}'."
                ),
                backstory=(
                    "You are a Harvard-trained business analyst who worked at McKinsey. "
                    "You specialize in turning raw research into actionable strategic insights."
                ),
                llm=llm_analysis,
                verbose=True,
                allow_delegation=False,
                max_iter=3,
            )

            strategist = Agent(
                role="Marketing Strategist",
                goal=(
                    f"Design a comprehensive marketing strategy for '{topic}' "
                    f"targeting '{audience}' in the '{industry}' industry. "
                    "Include channels, messaging, content plan, budget allocation, and KPIs."
                ),
                backstory=(
                    "You are a creative marketing strategist who has built campaigns for "
                    "Fortune 500 companies. You blend data with creativity to build strategies "
                    "that work in the real world."
                ),
                llm=llm_creative,
                verbose=True,
                allow_delegation=False,
                max_iter=3,
            )

            writer = Agent(
                role="Professional Report Writer",
                goal=(
                    f"Write a polished, executive-level marketing strategy report for '{topic}'. "
                    "Make it clear, compelling, and professional."
                ),
                backstory=(
                    "You are an award-winning business writer who has authored reports for "
                    "top consulting firms. You turn complex strategies into clear, beautifully "
                    "structured documents."
                ),
                llm=llm_creative,
                verbose=True,
                allow_delegation=False,
                max_iter=3,
            )

            critic = Agent(
                role="Quality Assurance Critic",
                goal=(
                    "Review the full marketing strategy report. Score it out of 10. "
                    "Identify exactly what is weak, what is missing, and provide "
                    "3 specific actionable improvement recommendations."
                ),
                backstory=(
                    "You are a ruthlessly honest senior consultant who has reviewed thousands "
                    "of strategy documents. Your feedback always makes the final product better."
                ),
                llm=llm_critic,
                verbose=True,
                allow_delegation=False,
                max_iter=3,
            )

            task1 = Task(
                description=(
                    f"Research '{topic}' thoroughly for the '{industry}' industry.\n"
                    "Cover: market size, growth trends, key players, recent news, "
                    "consumer behavior, and emerging technologies. Be specific with numbers."
                ),
                expected_output=(
                    "A structured research report with:\n"
                    "- Market Overview (size, growth rate)\n"
                    "- Key Players & Competitors\n"
                    "- Latest Trends (at least 5)\n"
                    "- Consumer Behavior Insights\n"
                    "- Key Statistics & Data Points"
                ),
                agent=researcher,
            )

            task2 = Task(
                description=(
                    f"Using the research on '{topic}', conduct a full strategic analysis.\n"
                    f"Target audience: '{audience}'. Industry: '{industry}'.\n"
                    "Perform SWOT analysis, competitive landscape, and identify "
                    "the top 3 market opportunities to pursue."
                ),
                expected_output=(
                    "A strategic analysis containing:\n"
                    "- SWOT Analysis\n"
                    "- Competitive Landscape Summary\n"
                    "- Top 3 Market Opportunities\n"
                    "- Key Success Factors\n"
                    "- Risk Mitigation Strategies"
                ),
                agent=analyst,
                context=[task1],
            )

            task3 = Task(
                description=(
                    f"Design a full marketing strategy for '{topic}' targeting '{audience}'.\n"
                    "Use the research and analysis to build a strategy that is realistic, "
                    "creative, and measurable. Include specific tactics for each channel."
                ),
                expected_output=(
                    "A detailed marketing strategy with:\n"
                    "- Executive Summary\n"
                    "- Target Audience Profile & Personas\n"
                    "- Unique Value Proposition\n"
                    "- Marketing Channels (Social, SEO, Email, Paid, PR)\n"
                    "- Content Strategy\n"
                    "- 90-Day Action Plan\n"
                    "- Budget Allocation\n"
                    "- KPIs & Success Metrics"
                ),
                agent=strategist,
                context=[task1, task2],
            )

            task4 = Task(
                description=(
                    f"Write the final executive marketing strategy report for '{topic}'.\n"
                    "Combine all research, analysis, and strategy into one cohesive, "
                    "professional document ready to present to a board of directors."
                ),
                expected_output=(
                    "A complete polished executive report with:\n"
                    "- Executive Summary\n"
                    "- Market Research Findings\n"
                    "- Strategic Analysis\n"
                    "- Marketing Strategy\n"
                    "- Implementation Roadmap\n"
                    "- Conclusion & Next Steps"
                ),
                agent=writer,
                context=[task1, task2, task3],
            )

            task5 = Task(
                description=(
                    "Review the complete marketing strategy report critically.\n"
                    "Give an honest quality score out of 10 with clear justification. "
                    "List exactly what is missing or weak, and provide 3 specific "
                    "actionable recommendations to improve it."
                ),
                expected_output=(
                    "A quality review with:\n"
                    "- Overall Score: X/10\n"
                    "- What Works Well (3 points)\n"
                    "- What Needs Improvement (3 points)\n"
                    "- 3 Specific Actionable Recommendations\n"
                    "- Final Verdict"
                ),
                agent=critic,
                context=[task4],
            )

            crew = Crew(
                agents=[researcher, analyst, strategist, writer, critic],
                tasks=[task1, task2, task3, task4, task5],
                process=Process.sequential,
                verbose=True,
                memory=False,
            )

            result = crew.kickoff()
            elapsed = round(time.time() - start_time, 1)

            return Response({
                "status": "success",
                "topic": topic,
                "industry": industry,
                "audience": audience,
                "time_taken": f"{elapsed} seconds",
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
            traceback.print_exc()
            return Response({
                "status": "error",
                "error": str(e),
                "hint": "Check your GROQ_API_KEY in the .env file"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status": "online",
            "agents": 5,
            "model": f"groq/{GROQ_MODEL}",
            "groq_key_set": bool(GROQ_API_KEY),
        })
