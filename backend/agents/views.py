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


def make_agents_and_tasks(topic, industry, audience, llm):

    researcher = Agent(
        role="Senior Market Research Analyst",
        goal=(
            f"Conduct comprehensive, data-rich market research on '{topic}' "
            f"within the '{industry}' industry. Your research must be specific, "
            f"factual, and actionable — not generic. Include real market figures, "
            f"named competitors, and concrete trend data."
        ),
        backstory=(
            "You are a world-class market research analyst with 15 years of experience "
            "at top consulting firms like McKinsey and Deloitte. You are known for producing "
            "research reports packed with specific data points, named companies, market sizes, "
            "growth rates, and consumer behavior insights. You never write vague generalities — "
            "every statement you make is backed by a specific number, example, or named entity. "
            "You write in a structured, professional format using clear sections and bullet points."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    analyst = Agent(
        role="Strategic Business Intelligence Analyst",
        goal=(
            f"Perform a deep strategic analysis of '{topic}' targeting '{audience}' "
            f"in the '{industry}' industry. Produce a thorough SWOT analysis with "
            f"specific evidence for each point, detailed competitor profiles, user "
            f"personas with demographics and psychographics, and clearly ranked "
            f"market opportunities with business case reasoning."
        ),
        backstory=(
            "You are a Harvard MBA-trained strategic analyst who has advised Fortune 500 "
            "companies and high-growth startups. You are known for producing razor-sharp "
            "SWOT analyses with concrete evidence, not generic observations. You build "
            "detailed user personas with names, demographics, goals, pain points, and "
            "buying behaviors. You identify opportunities with specific market sizing "
            "and competitive differentiation strategies. Your analysis always connects "
            "directly to business outcomes and revenue potential."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    strategist = Agent(
        role="Chief Marketing Strategist",
        goal=(
            f"Design a comprehensive, detailed, and immediately actionable marketing "
            f"strategy for '{topic}' targeting '{audience}' in '{industry}'. "
            f"Include specific channel tactics with budget percentages, a content "
            f"calendar framework, messaging frameworks for each audience segment, "
            f"a 90-day phased action plan with weekly milestones, KPIs with specific "
            f"numeric targets, and realistic financial projections."
        ),
        backstory=(
            "You are a Chief Marketing Officer with 20 years of experience building "
            "marketing strategies for both startups and Fortune 500 companies. You have "
            "launched over 50 products across diverse markets. Your strategies are famous "
            "for being specific, measurable, and executable from day one. You always include "
            "exact budget breakdowns (e.g., 40% social, 25% SEO, 20% paid ads, 15% PR), "
            "realistic timelines, specific platform recommendations, content types, posting "
            "frequencies, and KPIs with numeric targets like 'achieve 10,000 monthly "
            "active users by month 3' or 'reduce CAC to under $15 by Q2'. "
            "You never write vague plans — everything is specific and implementable."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    writer = Agent(
        role="Executive Strategy Report Writer",
        goal=(
            f"Write a comprehensive, professional, board-ready executive strategy "
            f"report for '{topic}'. This report must synthesize ALL research, "
            f"analysis, and strategy into a single polished document that a CEO "
            f"or investor could read and immediately act upon. The report must be "
            f"detailed, well-structured, and reflect the specific context of the topic."
        ),
        backstory=(
            "You are an award-winning business writer and former McKinsey consultant "
            "who specializes in writing executive strategy documents. Your reports are "
            "known for being comprehensive yet readable, with crystal-clear structure, "
            "compelling executive summaries, and actionable recommendations. You write "
            "with authority and specificity — every section contains concrete data, "
            "named strategies, specific timelines, and clear next steps. You format "
            "reports with proper headings, subsections, bullet points, and numbered "
            "lists to maximize readability. Your reports are typically 600-900 words "
            "and cover every aspect a decision-maker needs."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    critic = Agent(
        role="Senior Strategy Quality Auditor",
        goal=(
            "Rigorously review the complete marketing strategy report. Provide a "
            "detailed quality audit with a score out of 10, specific praise for "
            "what works well, identification of gaps or weaknesses, and 3-5 "
            "highly specific, actionable recommendations to strengthen the strategy. "
            "Your review should add real value and help improve the final output."
        ),
        backstory=(
            "You are a ruthlessly honest senior strategy consultant and former partner "
            "at a Big 4 consulting firm. You have reviewed thousands of strategy "
            "documents and your feedback is legendary for being specific, constructive, "
            "and transformative. You score reports fairly but demand excellence — you "
            "never give high scores without strong justification. Your recommendations "
            "are always specific and implementable, not vague suggestions. You identify "
            "missing elements like financial projections, risk mitigation plans, or "
            "specific KPI targets, and tell the team exactly how to fix them."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=2,
    )

    task1 = Task(
        description=(
            f"Conduct comprehensive market research on: '{topic}'\n"
            f"Industry: {industry}\n\n"
            f"Your research report MUST include ALL of the following sections:\n\n"
            f"1. MARKET OVERVIEW\n"
            f"   - Current market size (in USD) and projected growth rate\n"
            f"   - Key market drivers and inhibitors\n"
            f"   - Geographic market breakdown\n\n"
            f"2. COMPETITOR LANDSCAPE\n"
            f"   - Name and profile at least 4 specific competitors\n"
            f"   - Their market share, pricing, strengths and weaknesses\n"
            f"   - Gaps in the market they are not addressing\n\n"
            f"3. INDUSTRY TRENDS\n"
            f"   - At least 5 specific current trends with data or examples\n"
            f"   - Emerging technologies disrupting this space\n"
            f"   - Regulatory or macroeconomic factors to consider\n\n"
            f"4. CONSUMER INSIGHTS\n"
            f"   - Who is buying, why they buy, how they buy\n"
            f"   - Key pain points and unmet needs\n"
            f"   - Purchase triggers and barriers\n\n"
            f"5. KEY STATISTICS\n"
            f"   - Include at least 6 specific data points with numbers\n\n"
            f"Be specific. Use real company names, real numbers, and concrete examples."
        ),
        expected_output=(
            "A detailed, structured market research report with 5 clear sections: "
            "Market Overview, Competitor Landscape, Industry Trends, Consumer Insights, "
            "and Key Statistics. Must include specific numbers, named competitors, "
            "and concrete data points. Minimum 350 words."
        ),
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Based on the research provided, conduct a deep strategic analysis of '{topic}'.\n"
            f"Target Audience: {audience}\n"
            f"Industry: {industry}\n\n"
            f"Your analysis MUST include ALL of the following:\n\n"
            f"1. SWOT ANALYSIS\n"
            f"   - Strengths: 3-4 specific internal advantages\n"
            f"   - Weaknesses: 3-4 specific internal challenges\n"
            f"   - Opportunities: 3-4 specific external opportunities with market sizing\n"
            f"   - Threats: 3-4 specific external threats with impact assessment\n\n"
            f"2. USER PERSONAS (create 2 detailed personas)\n"
            f"   For each persona include: Name, Age, Job, Income, Goals, "
            f"   Pain Points, Online Behavior, Preferred Channels, Buying Triggers\n\n"
            f"3. COMPETITIVE POSITIONING\n"
            f"   - Where does this product/service fit vs competitors?\n"
            f"   - Unique differentiation strategy\n"
            f"   - Positioning statement\n\n"
            f"4. TOP 3 STRATEGIC OPPORTUNITIES\n"
            f"   - Each with market size estimate, why now, and first move recommendation\n\n"
            f"5. KEY RISKS & MITIGATION\n"
            f"   - Top 3 risks with specific mitigation strategies"
        ),
        expected_output=(
            "A comprehensive strategic analysis with SWOT, 2 detailed user personas, "
            "competitive positioning, top 3 opportunities, and risk mitigation. "
            "Must be specific to the topic. Minimum 400 words."
        ),
        agent=analyst,
        context=[task1],
    )

    task3 = Task(
        description=(
            f"Design a complete, detailed, immediately actionable marketing strategy for '{topic}'.\n"
            f"Target Audience: {audience}\n"
            f"Industry: {industry}\n\n"
            f"Your strategy MUST include ALL of the following:\n\n"
            f"1. BRAND POSITIONING & MESSAGING\n"
            f"   - Unique Value Proposition (one clear sentence)\n"
            f"   - Core brand message\n"
            f"   - Messaging for each user persona\n"
            f"   - Brand voice and tone guidelines\n\n"
            f"2. MARKETING CHANNELS & BUDGET ALLOCATION\n"
            f"   - List 5 specific channels with budget % for each\n"
            f"   - Specific tactics for each channel (not generic)\n"
            f"   - Expected reach and conversion rates per channel\n\n"
            f"3. CONTENT STRATEGY\n"
            f"   - Content pillars (3-4 themes)\n"
            f"   - Content types and formats\n"
            f"   - Posting frequency per platform\n"
            f"   - Sample content ideas (at least 5 specific ideas)\n\n"
            f"4. 90-DAY PHASED ACTION PLAN\n"
            f"   - Month 1 (Days 1-30): Foundation — specific tasks and milestones\n"
            f"   - Month 2 (Days 31-60): Launch — specific campaigns and activities\n"
            f"   - Month 3 (Days 61-90): Growth — specific optimization and scaling steps\n\n"
            f"5. KPIs & SUCCESS METRICS\n"
            f"   - At least 8 KPIs with specific numeric targets\n"
            f"   - Measurement tools and frequency\n"
            f"   - Success benchmarks at 30, 60, and 90 days\n\n"
            f"6. BUDGET & FINANCIAL PROJECTIONS\n"
            f"   - Estimated monthly marketing budget breakdown\n"
            f"   - Expected CAC (Customer Acquisition Cost)\n"
            f"   - Revenue projection at 3, 6, and 12 months\n"
            f"   - Expected ROI timeline"
        ),
        expected_output=(
            "A comprehensive marketing strategy with brand positioning, channel tactics "
            "with budget percentages, content strategy, 90-day action plan with monthly "
            "milestones, 8+ KPIs with numeric targets, and financial projections. "
            "Must be specific and immediately actionable. Minimum 500 words."
        ),
        agent=strategist,
        context=[task1, task2],
    )

    task4 = Task(
        description=(
            f"Write a comprehensive, board-ready executive strategy report for '{topic}'.\n"
            f"Industry: {industry} | Target Audience: {audience}\n\n"
            f"Synthesize ALL the research, analysis, and strategy into one polished document.\n\n"
            f"The report MUST follow this exact structure:\n\n"
            f"EXECUTIVE SUMMARY\n"
            f"- 3-4 sentences capturing the opportunity, strategy, and expected outcome\n"
            f"- Key recommendation in one clear sentence\n\n"
            f"1. MARKET OPPORTUNITY\n"
            f"- Market size and growth trajectory\n"
            f"- Why this is the right time to enter/expand\n"
            f"- The core customer problem being solved\n\n"
            f"2. STRATEGIC ANALYSIS\n"
            f"- SWOT summary with most critical points\n"
            f"- Primary target audience profile\n"
            f"- Competitive advantage and positioning\n\n"
            f"3. MARKETING STRATEGY\n"
            f"- Brand positioning and core message\n"
            f"- Top 3 marketing channels with tactics\n"
            f"- Content strategy overview\n\n"
            f"4. 90-DAY IMPLEMENTATION ROADMAP\n"
            f"- Month 1: Foundation activities\n"
            f"- Month 2: Launch activities\n"
            f"- Month 3: Growth activities\n\n"
            f"5. KPIs & FINANCIAL OUTLOOK\n"
            f"- Top 5 KPIs with numeric targets\n"
            f"- Revenue projections at 3, 6, 12 months\n"
            f"- Expected ROI\n\n"
            f"6. CONCLUSION & NEXT STEPS\n"
            f"- Top 3 immediate actions to take this week\n"
            f"- Long-term strategic vision\n\n"
            f"Write with authority and confidence. Be specific. "
            f"This document should be impressive enough to present to investors or a board."
        ),
        expected_output=(
            "A polished, comprehensive executive strategy report with 6 major sections: "
            "Executive Summary, Market Opportunity, Strategic Analysis, Marketing Strategy, "
            "90-Day Roadmap, and KPIs/Financial Outlook. Must be specific, data-rich, "
            "and immediately actionable. Minimum 600 words."
        ),
        agent=writer,
        context=[task1, task2, task3],
    )

    task5 = Task(
        description=(
            f"Conduct a rigorous quality audit of the executive strategy report for '{topic}'.\n\n"
            f"Your audit MUST include:\n\n"
            f"1. OVERALL QUALITY SCORE\n"
            f"   - Score out of 10 with specific justification\n"
            f"   - Breakdown score by: Research Quality, Strategic Depth, "
            f"     Actionability, Financial Realism, Presentation\n\n"
            f"2. STRENGTHS (what the report does well)\n"
            f"   - At least 3 specific strengths with examples from the report\n\n"
            f"3. GAPS & WEAKNESSES\n"
            f"   - At least 3 specific areas that are weak or missing\n"
            f"   - Explain the business impact of each gap\n\n"
            f"4. IMPROVEMENT RECOMMENDATIONS\n"
            f"   - At least 4 specific, actionable recommendations\n"
            f"   - Each must include WHAT to add/change and HOW to do it\n\n"
            f"5. FINAL VERDICT\n"
            f"   - Is this report ready to present to investors/board? Why or why not?\n"
            f"   - One key thing that would make this a 10/10 report"
        ),
        expected_output=(
            "A detailed quality audit with overall score breakdown, 3+ strengths, "
            "3+ gaps, 4+ specific improvement recommendations, and final verdict. "
            "Must reference specific parts of the report. Minimum 250 words."
        ),
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

                crew = Crew(
                    agents=agents, tasks=tasks,
                    process=Process.sequential,
                    verbose=False, memory=False,
                )

                result  = crew.kickoff()
                elapsed = round(time.time() - start_time, 1)
                print(f"[StrategyAI] Success: {model} in {elapsed}s")

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
                print(f"[StrategyAI] Error on {model}: {error_msg[:300]}")

                if "rate_limit" in error_msg.lower() or "ratelimit" in error_msg.lower():
                    print(f"[StrategyAI] Rate limited — switching model...")
                    time.sleep(2)
                    continue
                if "model_not_found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    continue
                if "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    return Response({"status":"error","error":"API key invalid."}, status=status.HTTP_401_UNAUTHORIZED)

                traceback.print_exc()
                continue

        return Response({
            "status": "error",
            "error":  "Our pipeline is at capacity. Please try again in 15 minutes.",
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status":  "online",
            "stages":  5,
            "models":  MODELS,
            "total":   len(MODELS),
            "key_set": bool(GROQ_API_KEY),
        })
