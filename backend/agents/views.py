from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
import os, time, traceback, logging

logger = logging.getLogger(__name__)
load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

MODELS = [
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
    "llama-3.3-70b-versatile",
]

def build_llm(model, temperature=0.6):
    return LLM(
        model=f"groq/{model}",
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=1024,
    )

def get_search_tools():
    """Return search tools if Serper key is available."""
    if not SERPER_API_KEY:
        return []
    try:
        from crewai_tools import SerperDevTool
        os.environ["SERPER_API_KEY"] = SERPER_API_KEY
        return [SerperDevTool()]
    except Exception as e:
        logger.warning(f"Search tool unavailable: {e}")
        return []

def make_agents_and_tasks(topic, industry, audience, location, llm, search_tools):

    has_search = len(search_tools) > 0
    search_note = (
        "You have access to a real-time web search tool. "
        "Use it to find current, accurate, local data. "
        "Search specifically for local companies, local market sizes, "
        "local consumer behavior, and location-specific statistics."
        if has_search else
        "Use your training knowledge to produce the best possible research. "
        "Be specific with estimates and name real companies you know about."
    )

    # ── Location context ──
    loc_context = f" in {location}" if location and location.strip().lower() not in ["global","worldwide",""] else ""
    loc_instruction = (
        f"\n\nLOCATION CONTEXT: This research is specifically for '{location}'. "
        f"You MUST prioritize local data, local companies, local regulations, "
        f"local consumer behavior, local payment methods, local infrastructure, "
        f"and local market conditions. Do NOT default to US/European data. "
        f"Search for '{topic} {location}', '{industry} market {location}', "
        f"'competitors {industry} {location}' specifically."
        if location and location.strip().lower() not in ["global","worldwide",""]
        else "\n\nThis is a global market research — include major worldwide players and global trends."
    )

    researcher = Agent(
        role="Senior Market Research Analyst",
        goal=(
            f"Research '{topic}' in '{industry}'{loc_context} with specific local data, "
            f"named local and international competitors, and accurate market figures."
        ),
        backstory=(
            f"World-class McKinsey market research analyst specializing in emerging and local markets. {search_note} "
            f"You ALWAYS include: exact market size in USD, CAGR, named competitors with market share % summing to ~100%, "
            f"local competitor analysis, local pricing, local consumer behavior, local payment methods, "
            f"local regulations, local infrastructure challenges, and market gaps. "
            f"For African/Asian/Latin American markets you know: local startups, mobile money, "
            f"internet penetration rates, smartphone adoption, local regulatory bodies. "
            f"Use TABLE FORMAT: | Competitor | Share% | Pricing | Strength | Weakness |"
            f"{loc_instruction}"
        ),
        llm=llm,
        tools=search_tools,
        verbose=False,
        allow_delegation=False,
        max_iter=3,
    )

    analyst = Agent(
        role="Strategic Business Intelligence Analyst",
        goal=(
            f"Analyze '{topic}' for '{audience}'{loc_context} with SWOT, local personas, "
            f"risk matrix specific to the local market, and opportunities."
        ),
        backstory=(
            f"Harvard MBA strategic analyst with deep expertise in emerging markets. {search_note} "
            f"You produce: evidenced SWOT with local-specific data points, "
            f"2 detailed LOCAL personas (realistic names, incomes in local currency, "
            f"local lifestyle, local apps they use, local payment methods), "
            f"risk matrix covering LOCAL risks (political, infrastructure, currency, competition): "
            f"| Risk | Probability | Impact | Mitigation | Budget |, "
            f"competitor deep dive with local exploitation strategies, "
            f"top 3 opportunities specific to the local market. "
            f"For African markets: consider mobile money (MTN, Airtel), low data costs, "
            f"informal economy, boda bodas, market days, WhatsApp commerce etc."
            f"{loc_instruction}"
        ),
        llm=llm,
        tools=search_tools,
        verbose=False,
        allow_delegation=False,
        max_iter=3,
    )

    strategist = Agent(
        role="Chief Marketing Strategist",
        goal=(
            f"Design complete LOCAL marketing strategy for '{topic}' targeting '{audience}'{loc_context}."
        ),
        backstory=(
            f"CMO with 20 years experience in both global and emerging markets. {search_note} "
            f"Your strategies are LOCALLY ADAPTED — you know that: "
            f"in Africa, WhatsApp marketing outperforms email; "
            f"mobile money is more used than credit cards; "
            f"radio and community marketing still matter; "
            f"local influencers have more trust than global ones. "
            f"You ALWAYS produce: UVP adapted to local values, "
            f"channel budget TABLE with LOCAL channels (WhatsApp, local radio, community events, "
            f"mobile money promotions, local influencers, SMS marketing where relevant): "
            f"| Channel | Budget% | Monthly$ | Tactics | KPI |, "
            f"90-day roadmap TABLE: | Week | Task | KPI | Notes |, "
            f"KPI dashboard TABLE with realistic LOCAL targets, "
            f"financial projections in LOCAL context with local CAC and LTV estimates. "
            f"Budget percentages must total 100%."
            f"{loc_instruction}"
        ),
        llm=llm,
        tools=search_tools,
        verbose=False,
        allow_delegation=False,
        max_iter=3,
    )

    writer = Agent(
        role="Executive Strategy Report Writer",
        goal=f"Write comprehensive board-ready executive report for '{topic}'{loc_context}.",
        backstory=(
            f"Award-winning McKinsey consultant who has written strategies for companies in 40+ countries. "
            f"You produce reports that are locally relevant — not copy-pasted global templates. "
            f"You include local context, local examples, local market dynamics, "
            f"and locally actionable recommendations. "
            f"Your reports reproduce all key tables and are detailed enough for a local CEO "
            f"or investor to act on immediately."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=2,
    )

    critic = Agent(
        role="Senior Strategy Quality Auditor",
        goal="Score and audit the strategy report with focus on local relevance and completeness.",
        backstory=(
            f"Big 4 partner who audits strategies for global and emerging market companies. "
            f"You specifically check: is the research LOCAL or generic global? "
            f"Are competitors LOCAL ones? Are personas realistic for the local market? "
            f"Are KPIs achievable in the local context? Is the financial model realistic for local economics? "
            f"Score TABLE: | Area | Score/10 | Status | Gap | Fix |"
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=2,
    )

    # ── Location-aware task descriptions ──
    loc_tag = f" in {location}" if location and location.strip().lower() not in ["global","worldwide",""] else ""
    search_tag = "\nUSE YOUR SEARCH TOOL to find current local data before writing." if has_search else ""

    task1 = Task(
        description=(
            f"Research '{topic}' in '{industry}'{loc_tag}.{search_tag}\n\n"
            f"SECTION 1 — MARKET OVERVIEW\n"
            f"- Local market size in USD (and local currency if known)\n"
            f"- CAGR and 5-year forecast for this specific location\n"
            f"- Top 3 geographic sub-markets (cities/regions) by revenue\n"
            f"- Primary local market driver\n"
            f"- Internet/mobile penetration rate{loc_tag}\n\n"
            f"SECTION 2 — COMPETITOR BENCHMARKING (table format)\n"
            f"| Competitor | Local/Global | Market Share% | Pricing | Strength | Weakness |\n"
            f"Include both LOCAL startups AND international players. Shares sum to ~100%.\n"
            f"Identify the #1 gap none of them address locally.\n\n"
            f"SECTION 3 — LOCAL INDUSTRY TRENDS\n"
            f"5 trends specific to{loc_tag}, each with statistic.\n"
            f"2 disrupting technologies relevant locally.\n"
            f"1 local regulatory/government factor.\n\n"
            f"SECTION 4 — LOCAL CONSUMER INSIGHTS\n"
            f"- Local buyer demographics (age, income in local context, location)\n"
            f"- Local payment methods used (mobile money, cash, card)\n"
            f"- Top 3 purchase triggers (locally relevant)\n"
            f"- Top 3 barriers (local: affordability, trust, awareness, connectivity)\n"
            f"- Preferred channels (WhatsApp, Facebook, radio, word of mouth, etc.)\n\n"
            f"SECTION 5 — KEY LOCAL STATISTICS\n"
            f"8+ specific data points about{loc_tag} market."
        ),
        expected_output=f"Local market research{loc_tag} with competitor table, local trends, local consumer insights, 8+ local stats. Min 400 words.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Analyze '{topic}' for '{audience}'{loc_tag}.{search_tag}\n\n"
            f"SECTION 1 — SWOT ANALYSIS (locally specific)\n"
            f"Strengths (4): local advantages with evidence\n"
            f"Weaknesses (4): local challenges with business impact\n"
            f"Opportunities (4): local market opportunities with size estimate\n"
            f"Threats (4): local threats (competition, regulation, infrastructure, currency) "
            f"— each with mitigation strategy and budget allocation\n\n"
            f"SECTION 2 — COMPETITOR DEEP DIVE (local focus)\n"
            f"Profile top 3 competitors operating{loc_tag}: name, position, pricing, UVP, weakness.\n"
            f"What gap do ALL of them miss locally?\n\n"
            f"SECTION 3 — LOCAL USER PERSONAS\n"
            f"Persona 1 — Realistic local name, Age, Job, Monthly income (local currency), "
            f"3 Goals, 3 Pain Points, Phone used, Apps used, Payment method, Buying trigger\n"
            f"Persona 2 — same format, different local segment\n\n"
            f"SECTION 4 — RISK MATRIX (table)\n"
            f"| Risk | Probability | Impact | Mitigation Strategy | Budget Allocation |\n"
            f"Include local-specific risks: power outages, connectivity, political, currency fluctuation.\n\n"
            f"SECTION 5 — LOCAL STRATEGIC OPPORTUNITIES\n"
            f"Top 3 opportunities specific to{loc_tag}: market size, why now, first move, ROI"
        ),
        expected_output=f"Local SWOT, competitor profiles{loc_tag}, 2 local personas, risk matrix, 3 local opportunities. Min 500 words.",
        agent=analyst,
        context=[task1],
    )

    task3 = Task(
        description=(
            f"Design complete LOCAL marketing strategy for '{topic}' targeting '{audience}'{loc_tag}.\n\n"
            f"SECTION 1 — BRAND POSITIONING (locally adapted)\n"
            f"- UVP in language/values relevant to local audience\n"
            f"- Positioning statement for local market\n"
            f"- Local brand tone (what resonates locally)\n\n"
            f"SECTION 2 — LOCAL CHANNEL STRATEGY (table, total 100%)\n"
            f"| Channel | Budget% | Monthly$ | Local Tactics | Expected Result | Tools |\n"
            f"Prioritize locally effective channels:\n"
            f"- WhatsApp marketing / groups\n"
            f"- Facebook (dominant in many African markets)\n"
            f"- Local influencers / community leaders\n"
            f"- SMS / mobile money promotions\n"
            f"- Local radio / community events\n"
            f"- Google Search (if internet penetration allows)\n\n"
            f"SECTION 3 — LOCAL CONTENT PLAN\n"
            f"4 content pillars relevant to local culture/values.\n"
            f"Posting frequency per platform.\n"
            f"6 specific content ideas with local context.\n\n"
            f"SECTION 4 — 90-DAY ROADMAP (table)\n"
            f"| Week | Key Tasks | KPI Target | Notes |\n"
            f"All 12 weeks. Week 1 should start with local market validation.\n\n"
            f"SECTION 5 — KPI DASHBOARD (table)\n"
            f"| KPI | 30-Day | 60-Day | 90-Day | Tool |\n"
            f"Realistic targets for local market: CTR%, CAC$, MAU, Conversion%, Engagement%, Revenue$\n\n"
            f"SECTION 6 — FINANCIAL PROJECTIONS (local context)\n"
            f"Assumptions: Local CAC estimate, LTV, Conversion Rate, ARPU in USD and local currency\n"
            f"Budget table: | Channel | Monthly$ | % |\n"
            f"Revenue forecast: | Month | Users | Revenue$ | CAC$ | ROI% |\n"
            f"Break-even month. Total 12-month investment. Expected ROI."
        ),
        expected_output=f"Local marketing strategy{loc_tag} with channel table, content plan, 12-week roadmap, KPI dashboard, financial projections. Min 600 words.",
        agent=strategist,
        context=[task1, task2],
    )

    task4 = Task(
        description=(
            f"Write the final executive strategy report for '{topic}'{loc_tag}.\n"
            f"Industry: {industry} | Audience: {audience} | Location: {location}\n\n"
            f"This report must reflect the LOCAL market — not generic global content.\n\n"
            f"EXECUTIVE SUMMARY\n"
            f"4 sentences: local opportunity, strategy, expected outcome, investment needed.\n\n"
            f"1. LOCAL MARKET OPPORTUNITY\n"
            f"- Market size + CAGR{loc_tag}\n"
            f"- Competitor table (local + global, top 3 with share%)\n"
            f"- Primary local gap being exploited\n\n"
            f"2. STRATEGIC ANALYSIS\n"
            f"- SWOT highlights (local focus)\n"
            f"- Persona 1 and Persona 2 (local, realistic)\n"
            f"- Our competitive advantage in local market\n\n"
            f"3. RISK MITIGATION PLAN\n"
            f"| Risk | Impact | Mitigation | Budget |\n"
            f"Include local risks.\n\n"
            f"4. LOCAL MARKETING STRATEGY\n"
            f"- UVP + positioning for local audience\n"
            f"- Channel table with local channels\n"
            f"- Content strategy summary\n\n"
            f"5. 90-DAY ROADMAP\n"
            f"| Week | Task | Target | (all 12 weeks) |\n\n"
            f"6. KPIs & FINANCIAL OUTLOOK\n"
            f"- KPI table\n"
            f"- Financial table: Month 3 / 6 / 12 Revenue$ and ROI%\n"
            f"- Assumptions (local CAC, LTV, conversion)\n"
            f"- Break-even month\n\n"
            f"7. NEXT STEPS\n"
            f"- Top 3 actions THIS WEEK (locally actionable)\n"
            f"- 12-month vision for local market"
        ),
        expected_output=f"Complete 7-section executive report for{loc_tag}, local tables, local competitors, local personas, KPIs, financials. Min 700 words.",
        agent=writer,
        context=[task1, task2, task3],
    )

    task5 = Task(
        description=(
            f"Audit the strategy report for '{topic}'{loc_tag}.\n\n"
            f"SCORE TABLE\n"
            f"| Area | Score/10 | Status | Gap | Exact Fix |\n"
            f"Areas: Research Quality, Local Relevance, Strategic Depth, Risk Coverage, Financial Detail, Actionability\n\n"
            f"SPECIAL CHECK — LOCAL RELEVANCE AUDIT:\n"
            f"- Are competitors LOCAL ones named? ✓/✗\n"
            f"- Are personas realistic for local income/lifestyle? ✓/✗\n"
            f"- Are channels locally appropriate (WhatsApp, mobile money, etc.)? ✓/✗\n"
            f"- Are KPI targets realistic for local market size? ✓/✗\n"
            f"- Are financial projections based on local economics? ✓/✗\n\n"
            f"OVERALL SCORE: X/10\n"
            f"WHAT WORKS WELL: 3 specific strengths\n"
            f"GAPS & EXACT FIXES: write exact missing local data\n"
            f"SELF-ASSESSMENT CHECKLIST\n"
            f"| Check | Pass/Fail |\n"
            f"FINAL VERDICT: Ready for local investors? Yes/No + reason."
        ),
        expected_output="Score table, local relevance audit, overall score, strengths, exact fixes, checklist, verdict. Min 300 words.",
        agent=critic,
        context=[task4],
    )

    return [researcher, analyst, strategist, writer, critic], [task1, task2, task3, task4, task5]


class RunAgentView(APIView):
    def post(self, request):
        topic    = request.data.get("topic",    "").strip()
        industry = request.data.get("industry", "General").strip()
        audience = request.data.get("audience", "General public").strip()
        location = request.data.get("location", "Global").strip()

        if not topic:
            return Response({"error": "Topic is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not GROQ_API_KEY:
            return Response({"error": "API key not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        search_tools = get_search_tools()
        has_search   = len(search_tools) > 0
        print(f"[StrategyAI] Search tools: {'enabled' if has_search else 'disabled'}")
        print(f"[StrategyAI] Location: {location}")

        start_time = time.time()

        for model in MODELS:
            try:
                print(f"[StrategyAI] Trying: {model}")
                llm = build_llm(model)
                agents, tasks = make_agents_and_tasks(topic, industry, audience, location, llm, search_tools)
                crew = Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=False, memory=False)
                result  = crew.kickoff()
                elapsed = round(time.time() - start_time, 1)
                print(f"[StrategyAI] Success: {model} in {elapsed}s")

                return Response({
                    "status":     "success",
                    "topic":      topic,
                    "industry":   industry,
                    "audience":   audience,
                    "location":   location,
                    "time_taken": f"{elapsed}s",
                    "web_search": has_search,
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

        return Response({
            "status": "error",
            "error":  "Pipeline at capacity. Please try again in 15 minutes.",
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status":     "online",
            "stages":     5,
            "models":     MODELS,
            "web_search": bool(SERPER_API_KEY),
            "key_set":    bool(GROQ_API_KEY),
        })
