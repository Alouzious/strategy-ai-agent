from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
import os, time, traceback, logging

logger = logging.getLogger(__name__)
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODELS = [
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
    "llama-3.3-70b-versatile",
]

def build_llm(model, temperature=0.6):
    return LLM(model=f"groq/{model}", api_key=GROQ_API_KEY, temperature=temperature, max_tokens=1024)

def make_agents_and_tasks(topic, industry, audience, llm):

    researcher = Agent(
        role="Senior Market Research Analyst",
        goal=f"Research '{topic}' in '{industry}' with specific data, named competitors, and market figures.",
        backstory=(
            "World-class McKinsey market research analyst. You ALWAYS produce: "
            "exact market size in USD, CAGR, named competitors with market share % that adds to ~100%, "
            "competitor strengths/weaknesses/pricing, market gaps, 5 trends with statistics, "
            "consumer demographics, purchase triggers/barriers. Every statement has a number or named company. "
            "Use TABLE FORMAT for competitor benchmarking: | Competitor | Share% | Pricing | Strength | Weakness |"
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    analyst = Agent(
        role="Strategic Business Intelligence Analyst",
        goal=f"Analyze '{topic}' for '{audience}' with SWOT, personas, risk matrix, and opportunities.",
        backstory=(
            "Harvard MBA strategic analyst. You produce: "
            "evidenced SWOT with specific data points, "
            "2 detailed personas (Name/Age/Job/Income/Goals/Pain Points/Channels/Trigger), "
            "risk matrix in TABLE FORMAT: | Risk | Probability | Impact | Mitigation Strategy |, "
            "competitor deep dive with exploitation strategies, "
            "top 3 opportunities with market size and ROI estimate. "
            "Every threat has a concrete mitigation with budget allocation."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    strategist = Agent(
        role="Chief Marketing Strategist",
        goal=f"Design complete marketing strategy for '{topic}' targeting '{audience}' in '{industry}'.",
        backstory=(
            "CMO with 20 years experience. You ALWAYS produce: "
            "UVP and positioning statement, "
            "channel budget TABLE: | Channel | Budget% | Budget$ | Tactics | KPI Target |, "
            "content plan with posting frequency per platform, "
            "6 specific content ideas, "
            "90-day weekly roadmap TABLE: | Week | Tasks | KPI Target | Owner |, "
            "KPI dashboard TABLE: | KPI | Target | Measurement Tool | Frequency |, "
            "financial projections TABLE: | Month | Revenue | CAC | Users | ROI% |, "
            "assumptions clearly stated: CAC $X, LTV $X, conversion rate X%, ARPU $X. "
            "Budget percentages must total 100%."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    writer = Agent(
        role="Executive Strategy Report Writer",
        goal=f"Write comprehensive board-ready executive report for '{topic}'.",
        backstory=(
            "Award-winning McKinsey consultant. Your reports include EVERYTHING — "
            "no section is skipped or summarized too briefly. "
            "You reproduce key tables from research/analysis/strategy in the report. "
            "Named competitors with market share, risk mitigation table, "
            "KPI dashboard, financial projections table, weekly roadmap. "
            "A CEO must be able to act on this immediately without reading anything else."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    critic = Agent(
        role="Senior Strategy Quality Auditor",
        goal="Score and audit the strategy report across 6 dimensions with exact improvement content.",
        backstory=(
            "Big 4 partner quality auditor. You score 6 areas out of 10: "
            "Research Quality, Strategic Depth, Risk Coverage, Financial Detail, KPI Measurability, Actionability. "
            "For EVERY area below 8/10 you write the EXACT missing content — not suggestions but actual data. "
            "You verify: competitors named with %, KPIs numeric, budget broken down, "
            "risk mitigations specific with budget, projections with assumptions. "
            "Output a score TABLE: | Area | Score | Status | Gap/Action |"
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    task1 = Task(
        description=(
            f"Research '{topic}' in '{industry}'.\n\n"
            f"SECTION 1 — MARKET OVERVIEW\n"
            f"- Market size USD (current year)\n"
            f"- CAGR and 5-year forecast\n"
            f"- Top 3 geographic markets by revenue\n"
            f"- Primary market driver\n\n"
            f"SECTION 2 — COMPETITOR BENCHMARKING (use table format)\n"
            f"| Competitor | Market Share% | Pricing Model | Key Strength | Key Weakness |\n"
            f"List 5 competitors. Shares should sum to ~100%. Identify #1 market gap.\n\n"
            f"SECTION 3 — INDUSTRY TRENDS\n"
            f"List 5 trends, each with a specific statistic or data point.\n"
            f"Add 2 disrupting technologies and 1 regulatory factor.\n\n"
            f"SECTION 4 — CONSUMER INSIGHTS\n"
            f"- Primary buyer demographics\n"
            f"- Top 3 purchase triggers\n"
            f"- Top 3 barriers to purchase\n"
            f"- Preferred channels ranked\n\n"
            f"SECTION 5 — KEY STATISTICS\n"
            f"List 8+ specific data points with numbers."
        ),
        expected_output="Market research with competitor table (5 companies, share%), 5 trends, consumer insights, 8+ stats. Min 400 words.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Analyze '{topic}' for '{audience}' in '{industry}'.\n\n"
            f"SECTION 1 — SWOT ANALYSIS\n"
            f"Strengths (4): each with supporting evidence or metric\n"
            f"Weaknesses (4): each with business impact stated\n"
            f"Opportunities (4): each with market size estimate\n"
            f"Threats (4): each with specific mitigation strategy and budget allocation\n\n"
            f"SECTION 2 — COMPETITOR DEEP DIVE\n"
            f"Profile top 3 competitors: name, position, pricing, UVP, weakness to exploit.\n"
            f"State the competitive gap all of them miss.\n\n"
            f"SECTION 3 — USER PERSONAS\n"
            f"Persona 1 — Name, Age, Job Title, Annual Income, 3 Goals, 3 Pain Points, "
            f"Preferred Channels, Buying Trigger, Max Budget\n"
            f"Persona 2 — same format, different segment\n\n"
            f"SECTION 4 — RISK MATRIX (use table format)\n"
            f"| Risk | Probability | Impact | Mitigation Strategy | Budget Allocation |\n"
            f"List top 5 risks.\n\n"
            f"SECTION 5 — STRATEGIC OPPORTUNITIES\n"
            f"Top 3 opportunities: market size, why now, first move, expected ROI"
        ),
        expected_output="SWOT with evidence, competitor profiles, 2 personas, risk matrix table, 3 opportunities. Min 500 words.",
        agent=analyst,
        context=[task1],
    )

    task3 = Task(
        description=(
            f"Design complete marketing strategy for '{topic}' targeting '{audience}' in '{industry}'.\n\n"
            f"SECTION 1 — BRAND POSITIONING\n"
            f"- UVP (one sentence)\n"
            f"- Positioning: For [audience] who [need], [brand] is [category] that [benefit] "
            f"unlike [competitor] who [alternative]\n"
            f"- Core message and tone (3 adjectives)\n\n"
            f"SECTION 2 — CHANNEL STRATEGY (use table, must total 100%)\n"
            f"| Channel | Budget% | Monthly$  | Specific Tactics | Expected CTR/Engagement | Tools |\n"
            f"List 5 channels.\n\n"
            f"SECTION 3 — CONTENT PLAN\n"
            f"4 content pillars with 2 example topics each.\n"
            f"Posting frequency: Instagram X/week, TikTok X/week, LinkedIn X/week, Blog X/month\n"
            f"6 specific content ideas: title, format, platform, goal\n\n"
            f"SECTION 4 — 90-DAY ROADMAP (use table)\n"
            f"| Week | Key Tasks | KPI Target | Notes |\n"
            f"Cover all 12 weeks.\n\n"
            f"SECTION 5 — KPI DASHBOARD (use table)\n"
            f"| KPI | 30-Day Target | 60-Day Target | 90-Day Target | Tool |\n"
            f"Include: CTR%, CAC$, MAU, Conversion%, Engagement%, Email Open%, Revenue$, ROI%\n\n"
            f"SECTION 6 — FINANCIAL PROJECTIONS\n"
            f"Assumptions: CAC $X, LTV $X, Conversion Rate X%, ARPU $X, Monthly Growth X%\n"
            f"Budget breakdown table: | Channel | Monthly$ | % of Total |\n"
            f"Revenue forecast table: | Month | Users | Revenue$ | CAC$ | ROI% |\n"
            f"Break-even month: X\n"
            f"Total 12-month marketing investment: $X\n"
            f"Expected 12-month ROI: X%"
        ),
        expected_output="Strategy with 5-channel table, content plan, 12-week roadmap table, KPI dashboard table, financial projection table. Min 600 words.",
        agent=strategist,
        context=[task1, task2],
    )

    task4 = Task(
        description=(
            f"Write the final executive strategy report for '{topic}'.\n"
            f"Industry: {industry} | Audience: {audience}\n\n"
            f"Include ALL sections. Reproduce key tables. Do not summarize too briefly.\n\n"
            f"EXECUTIVE SUMMARY (4 sentences: opportunity, strategy, outcome, investment)\n\n"
            f"1. MARKET OPPORTUNITY\n"
            f"- Market size + CAGR\n"
            f"- Competitor table (top 3 with share%)\n"
            f"- Primary gap being exploited\n\n"
            f"2. STRATEGIC ANALYSIS\n"
            f"- SWOT highlights (2 per quadrant)\n"
            f"- Persona 1 and Persona 2 summary\n"
            f"- Our competitive advantage in one sentence\n\n"
            f"3. RISK MITIGATION PLAN\n"
            f"- Risk table: | Risk | Impact | Mitigation | Budget |\n\n"
            f"4. MARKETING STRATEGY\n"
            f"- UVP + positioning statement\n"
            f"- Channel table: | Channel | Budget% | Key Tactic |\n"
            f"- Content strategy summary\n\n"
            f"5. 90-DAY ROADMAP\n"
            f"- Month 1 table: | Week | Task | Target |\n"
            f"- Month 2 table: | Week | Task | Target |\n"
            f"- Month 3 table: | Week | Task | Target |\n\n"
            f"6. KPIs & FINANCIAL OUTLOOK\n"
            f"- KPI table: | KPI | Target | Tool |\n"
            f"- Financial table: | Month 3 | Month 6 | Month 12 | with Revenue$ and ROI% |\n"
            f"- Assumptions stated\n"
            f"- Break-even: Month X\n\n"
            f"7. NEXT STEPS\n"
            f"- Top 3 actions THIS WEEK with owner and deadline\n"
            f"- 12-month vision"
        ),
        expected_output="Complete 7-section executive report with all tables reproduced, named competitors, risk mitigations, KPIs, financials. Min 700 words.",
        agent=writer,
        context=[task1, task2, task3],
    )

    task5 = Task(
        description=(
            f"Audit the executive strategy report for '{topic}'.\n\n"
            f"SCORE TABLE (use table format)\n"
            f"| Area | Score /10 | Status | Gap | Exact Fix |\n"
            f"Areas: Research Quality, Strategic Depth, Risk Coverage, Financial Detail, KPI Measurability, Actionability\n\n"
            f"OVERALL SCORE: X/10\n\n"
            f"WHAT WORKS WELL\n"
            f"3 specific strengths with examples from the report.\n\n"
            f"GAPS & EXACT FIXES\n"
            f"For each area below 8/10 — write the exact missing data that should be added.\n"
            f"Example: 'Research Quality gap: Add competitor Revolut with 20.5% share, "
            f"N26 with 15.2% share, Monzo 12.1%, others 52.2%'\n\n"
            f"SELF-ASSESSMENT CHECKLIST\n"
            f"| Check | Pass/Fail |\n"
            f"- Competitors named with market share%\n"
            f"- KPIs all have numeric targets\n"
            f"- Budget broken down by channel with %\n"
            f"- Each risk has a mitigation with budget\n"
            f"- Financial projections have stated assumptions\n"
            f"- 90-day roadmap has weekly tasks\n\n"
            f"FINAL VERDICT: Ready for investors? Yes/No + one-sentence reason."
        ),
        expected_output="Score table for 6 areas, overall score, strengths, exact gap fixes, self-assessment checklist, final verdict. Min 300 words.",
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
            return Response({"error": "Topic is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not GROQ_API_KEY:
            return Response({"error": "API key not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        start_time = time.time()

        for model in MODELS:
            try:
                print(f"[StrategyAI] Trying: {model}")
                llm = build_llm(model)
                agents, tasks = make_agents_and_tasks(topic, industry, audience, llm)
                crew = Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=False, memory=False)
                result  = crew.kickoff()
                elapsed = round(time.time() - start_time, 1)
                print(f"[StrategyAI] Success: {model} in {elapsed}s")
                return Response({
                    "status": "success", "topic": topic, "industry": industry,
                    "audience": audience, "time_taken": f"{elapsed}s",
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
                print(f"[StrategyAI] Error on {model}: {error_msg[:300]}")
                if "rate_limit" in error_msg.lower() or "ratelimit" in error_msg.lower():
                    time.sleep(2); continue
                if "model_not_found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    continue
                if "invalid_api_key" in error_msg.lower():
                    return Response({"status":"error","error":"API key invalid."}, status=status.HTTP_401_UNAUTHORIZED)
                traceback.print_exc(); continue

        return Response({"status":"error","error":"Pipeline at capacity. Please try again in 15 minutes."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status":"online","stages":5,"models":MODELS,"key_set":bool(GROQ_API_KEY)})
