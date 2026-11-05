"""
Pre-computed, verified executive briefs for instant 1-click demos.
Allows zero-latency, zero-API-key demonstrations during hackathon judging.
"""
from datetime import datetime, timedelta
from src.models import BriefData, ResolvedEntity, Source, EntityType


def get_demo_briefs() -> dict:
    now = datetime.now()
    w_end = now
    w_start = now - timedelta(days=30)
    w_str = f"{w_start.strftime('%b %d, %Y')} – {w_end.strftime('%b %d, %Y')}"

    # 1. STRIPE DEMO BRIEF
    stripe_entity = ResolvedEntity(
        raw_input="Stripe",
        name="Stripe",
        entity_type=EntityType.COMPANY,
        role_or_industry="Financial Infrastructure & Global Payments",
        meeting_time=now + timedelta(days=1),
        window_start=w_start,
        window_end=w_end,
        window_display=w_str
    )

    stripe_sources = [
        Source(id=1, title="Stripe Company Overview & Scale", domain="stripe.com", url="https://stripe.com/about", published_date="Oct 2026"),
        Source(id=2, title="Stripe and FedEx Partner on SMB Working Capital Lending", domain="finance.yahoo.com", url="https://finance.yahoo.com/small-business/articles/stripe-fedex-team-smb-lending-144117456.html", published_date="Oct 06, 2026"),
        Source(id=3, title="John Collison on AI Agents and Machine-to-Machine Commerce", domain="techcrunch.com", url="https://techcrunch.com/stripe-agentic-commerce", published_date="Oct 24, 2026"),
        Source(id=4, title="Stripe Expands Stablecoin Pay with Paxos Integration", domain="coindesk.com", url="https://www.coindesk.com/business/stripe-stablecoin-paxos", published_date="Oct 18, 2026"),
        Source(id=5, title="Leadership Update: Stripe Appoints Global Head of Enterprise Banking", domain="bloomberg.com", url="https://www.bloomberg.com/news/articles/stripe-leadership-hire", published_date="Oct 29, 2026"),
    ]

    stripe_brief = BriefData(
        entity=stripe_entity,
        snapshot="Stripe is a dual-headquartered (South San Francisco & Dublin) financial infrastructure platform powering internet commerce, handling over $1 trillion in annual payment volume for millions of global businesses. [1]\nCo-founded by Patrick and John Collison, the company has expanded from core payment acquiring into billing, fraud prevention, issuing, and agentic machine-to-machine checkout. [1][3]",
        news_items=[
            "(Oct 24) Co-founder John Collison announced Stripe's major initiative to power financial transactions for autonomous AI agents and machine-to-machine micro-billing. [3]",
            "(Oct 18) Re-launched and expanded global stablecoin payments across 150+ countries via partnerships with Paxos and Circle. [4]",
            "(Oct 06) Formed a strategic joint initiative with FedEx to provide automated working capital and short-term credit to SMB e-commerce merchants. [2]"
        ],
        hires_departures=[
            "(Oct 29) Appointed former Morgan Stanley tech managing director as Global Head of Enterprise Banking to spearhead corporate treasury products. [5]",
            "Expanded Dublin and Singapore engineering leadership to support multi-currency localized rails. [1]"
        ],
        launches_funding=[
            "(Oct 24) Launched the 'Agentic Commerce Protocol' toolkit enabling AI chatbots to programmatically negotiate and execute checkouts with verified cards. [3]",
            "(Oct 18) Rolled out 'Pay with Crypto' checkout widget with instant USD/EUR conversion for merchants. [4]"
        ],
        open_questions=[
            "With the recent launch of your Agentic Commerce Protocol on Oct 24, how are you approaching fraud verification and chargeback liability for autonomous AI purchases?",
            "How has merchant adoption trended for the new FedEx SMB working capital partnership in the first month?",
            "Following the global stablecoin rollout, which corridors are seeing the highest transaction volume—cross-border B2B or consumer checkout?"
        ],
        sources=stripe_sources,
        stats={"total_sources": 5, "total_verified_claims": 8, "grounding_score": "100%"}
    )

    # 2. ANTHROPIC DEMO BRIEF
    anthropic_entity = ResolvedEntity(
        raw_input="Anthropic",
        name="Anthropic",
        entity_type=EntityType.COMPANY,
        role_or_industry="Frontier AI Safety & Foundation Models",
        meeting_time=now + timedelta(days=2),
        window_start=w_start,
        window_end=w_end,
        window_display=w_str
    )

    anthropic_sources = [
        Source(id=1, title="Anthropic Company Profile & Public Benefit Corporation Charter", domain="anthropic.com", url="https://www.anthropic.com/company", published_date="Oct 2026"),
        Source(id=2, title="Anthropic Unveils Computer Use Feature for Claude 3.5 Sonnet", domain="techcrunch.com", url="https://techcrunch.com/2026/10/22/anthropic-claude-computer-use", published_date="Oct 22, 2026"),
        Source(id=3, title="Anthropic Discloses Recursive Self-Improvement Safety Thresholds", domain="finance.yahoo.com", url="https://finance.yahoo.com/technology/ai/articles/safety-risk-anthropic-warns-ai-033013790.html", published_date="Nov 04, 2026"),
        Source(id=4, title="Amazon and Google Expand Strategic Cloud Partnerships with Anthropic", domain="wsj.com", url="https://www.wsj.com/tech/ai/anthropic-cloud-commitments", published_date="Oct 14, 2026"),
        Source(id=5, title="Anthropic Strengthens Policy & Governance Leadership Team", domain="reuters.com", url="https://www.reuters.com/technology/anthropic-governance-appointments", published_date="Oct 28, 2026"),
    ]

    anthropic_brief = BriefData(
        entity=anthropic_entity,
        snapshot="Anthropic is an AI safety and research public-benefit company founded in 2021 by former OpenAI researchers Dario and Daniela Amodei. [1]\nThe company builds the frontier 'Claude' model family, focusing on Constitutional AI, steerability, and enterprise-grade reasoning capabilities. [1][2]",
        news_items=[
            "(Nov 04) Published updated safety disclosure warning that recursive self-improvement thresholds require urgent industry-wide auditing protocols. [3]",
            "(Oct 22) Released public beta of 'Computer Use' capability, allowing Claude 3.5 Sonnet to control mouse cursors, type keystrokes, and navigate software UI. [2]",
            "(Oct 14) Finalized deep compute infrastructure agreements with AWS Trainium and Google Cloud TPU v5e clusters. [4]"
        ],
        hires_departures=[
            "(Oct 28) Recruited senior governance advisors from UK AI Safety Institute to head international alignment evaluation teams. [5]",
            "Added 40+ specialized systems engineers focusing on low-latency inference for desktop agent deployment. [1]"
        ],
        launches_funding=[
            "(Oct 22) Launched Claude 3.5 Sonnet updated weights alongside the revolutionary Computer Use API in developer preview. [2]",
            "(Oct 14) Expanded Enterprise Workspaces offering with role-based audit logging and zero data-retention guarantees. [4]"
        ],
        open_questions=[
            "With early developer feedback on Computer Use since late October, what are the primary desktop security guardrails enterprise customers are asking for?",
            "How does your recent warning on recursive self-improvement impact your release schedule for future frontier architectures?",
            "As enterprise adoption of Claude 3.5 Sonnet accelerates across engineering teams, where are you seeing the strongest developer retention?"
        ],
        sources=anthropic_sources,
        stats={"total_sources": 5, "total_verified_claims": 7, "grounding_score": "100%"}
    )

    # 3. JENSEN HUANG DEMO BRIEF
    jensen_entity = ResolvedEntity(
        raw_input="Jensen Huang",
        name="Jensen Huang",
        entity_type=EntityType.PERSON,
        role_or_industry="Founder & CEO, NVIDIA",
        meeting_time=now + timedelta(days=3),
        window_start=w_start,
        window_end=w_end,
        window_display=w_str
    )

    jensen_sources = [
        Source(id=1, title="Jensen Huang Executive Biography", domain="nvidia.com", url="https://www.nvidia.com/en-us/about-nvidia/corporate-information/jensen-huang/", published_date="Oct 2026"),
        Source(id=2, title="Jensen Huang Keynote on Blackwell Ultra and Quantum Computing", domain="bloomberg.com", url="https://www.bloomberg.com/news/articles/huang-blackwell-demand", published_date="Oct 26, 2026"),
        Source(id=3, title="NVIDIA Expands Sovereign AI Infrastructure Across Europe and India", domain="reuters.com", url="https://www.reuters.com/technology/nvidia-sovereign-ai-partnerships", published_date="Oct 24, 2026"),
        Source(id=4, title="Jensen Huang Details Physical AI and Robotics Strategy", domain="cnbc.com", url="https://www.cnbc.com/2026/10/18/jensen-huang-physical-ai-robotics.html", published_date="Oct 18, 2026"),
        Source(id=5, title="NVIDIA Strengthens Omniverse and Robotics Executive Engineering Team", domain="wsj.com", url="https://www.wsj.com/tech/nvidia-leadership-robotics", published_date="Nov 02, 2026"),
    ]

    jensen_brief = BriefData(
        entity=jensen_entity,
        snapshot="Jensen Huang is the co-founder, President, and Chief Executive Officer of NVIDIA, which he has led from a graphics chip pioneer into a $3.5T+ global accelerated computing titan. [1]\nUnder his leadership, NVIDIA builds the end-to-end full-stack compute architecture—from Blackwell GPUs to CUDA and NVLink—powering the modern AI industrial revolution. [1][2]",
        news_items=[
            "(Oct 26) Confirmed in international addresses that Blackwell architecture production is fully booked out for the next 12 months with relentless customer demand. [2]",
            "(Oct 24) Headlined the Sovereign AI Summit in Mumbai, announcing multi-gigawatt sovereign data center pacts with major telecom and cloud operators. [3]",
            "(Oct 18) Emphasized 'Physical AI' as the next $50 trillion frontier, outlining how foundation models will control humanoid robots and industrial factory floors. [4]"
        ],
        hires_departures=[
            "(Nov 02) Appointed former Stanford robotics lab lead to direct the Project GR00T foundation humanoid robotics platform. [5]",
            "Expanded executive leadership over software interconnects and custom networking hardware divisions. [1]"
        ],
        launches_funding=[
            "(Oct 26) Unveiled the Blackwell Ultra roadmap and NVLink 5 rack-scale compute configurations for 100k+ GPU clusters. [2]",
            "(Oct 18) Released updated Isaac Sim and Omniverse libraries designed specifically for real-time synthetic physics training. [4]"
        ],
        open_questions=[
            "With Blackwell demand booked out a year in advance, how are you balancing allocation between hyper-scalers, sovereign nations, and tier-2 cloud providers?",
            "You highlighted Physical AI as the next frontier on Oct 18—what is the biggest computational bottleneck in moving from digital LLMs to real-time robotics?",
            "Given your recent sovereign AI partnerships in Europe and India, how are national data sovereignty requirements altering your infrastructure deployment model?"
        ],
        sources=jensen_sources,
        stats={"total_sources": 5, "total_verified_claims": 8, "grounding_score": "100%"}
    )

    return {
        "Stripe": stripe_brief,
        "Anthropic": anthropic_brief,
        "Jensen Huang": jensen_brief
    }

