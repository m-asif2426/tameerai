"""
TameerAI - Construction Intelligence Workflow & Synthetic Chat Prototype (Phase 03F)
Orchestrates 5-layer domain classification, language adaptation, context extraction,
scoped RAG retrieval, provider execution (Gemini or Mock), citation validation,
and response quality assurance auditing into an integrated, production-grade chat pipeline.
"""

import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.ai.contracts.provider import (
    AIProvider,
    ChatMessageInput,
    ModelRequest,
)
from app.ai.contracts.retrieval import RetrievalQuery, ScopeType
from app.ai.contracts.validation import CitationValidationReport
from app.ai.guardrails.context_engine import (
    ConstructionContext,
    ConstructionContextEngine,
    ResponseStrategy,
    RiskLevel,
)
from app.ai.guardrails.intent import ConstructionIntent
from app.ai.guardrails.structural_safety import HazardCategory
from app.ai.guardrails.domain_guard import (
    ConfidenceCategory,
    ConstructionDomainGuard,
    DomainCategory,
    DomainClassificationResult,
)
from app.ai.guardrails.response_policy import (
    ConstructionResponsePolicy,
    detect_language,
)
from app.ai.prompts.construction import get_construction_system_prompt
from app.ai.providers.factory import get_ai_provider
from app.ai.retrieval.service import ScopedRetrievalService
from app.ai.validation.citation import CitationValidator
from app.ai.validation.grounded_policy import (
    EvidenceTier,
    GroundedResponseEvaluation,
    GroundedResponsePolicy,
)
from app.ai.validation.quality import QualityValidationReport, ResponseQualityValidator
from app.services.material_rates.ai_bridge import (
    MaterialRateIntelligenceBridge,
    material_rate_bridge,
)


class ConstructionChatResponse(BaseModel):
    """Normalized response from the construction chat intelligence engine."""
    session_id: Optional[UUID] = None
    query: str
    detected_language: str
    domain_category: DomainCategory
    answer: str
    answer_urdu: Optional[str] = None
    is_off_topic: bool = False
    is_ambiguous: bool = False
    is_mixed_topic: bool = False
    is_grounded: bool = True
    retrieved_chunks_count: int = 0
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    validation_report: Optional[CitationValidationReport] = None
    disclaimer: str
    latency_ms: float = 0.0
    telemetry: Dict[str, Any] = Field(default_factory=dict)

    # Phase 03F Additions
    context: Optional[ConstructionContext] = None
    quality_report: Optional[QualityValidationReport] = None

    # Phase 03G Stage B3 & B3.1 Additions
    evidence_tier: Optional[str] = None
    grounded_evaluation: Optional[GroundedResponseEvaluation] = None
    evidence_status: Optional[str] = None
    calculation_status: Optional[str] = None
    regulatory_status: Optional[str] = None
    citation_status: Optional[str] = None


class ConstructionChatWorkflow:
    """
    Core conversational intelligence pipeline for TameerAI.
    Enforces construction domain restrictions, context awareness, and quality validation.
    """

    def __init__(
        self,
        ai_provider: Optional[AIProvider] = None,
        retrieval_service: Optional[ScopedRetrievalService] = None,
        domain_guard: Optional[ConstructionDomainGuard] = None,
        citation_validator: Optional[CitationValidator] = None,
        quality_validator: Optional[ResponseQualityValidator] = None,
        material_rate_bridge: Optional[MaterialRateIntelligenceBridge] = None,
    ):
        self.ai_provider = ai_provider or get_ai_provider("mock")
        self.retrieval_service = retrieval_service
        self.domain_guard = domain_guard or ConstructionDomainGuard()
        self.citation_validator = citation_validator or CitationValidator()
        self.quality_validator = quality_validator or ResponseQualityValidator()
        self.material_rate_bridge = material_rate_bridge or MaterialRateIntelligenceBridge()

    async def process_user_query(
        self,
        query: str,
        project_id: Optional[UUID] = None,
        requesting_user_id: Optional[UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        scope: ScopeType = ScopeType.HYBRID,
        top_k: int = 4,
        db: Optional[Any] = None,
    ) -> ConstructionChatResponse:
        """
        Executes end-to-end processing of a user dialogue turn.
        """
        start_time = time.monotonic()
        clean_query = query.strip()
        lang = detect_language(clean_query)

        # 1. 5-Layer Domain Guardrail & Context Extraction Check
        guard_result: DomainClassificationResult = self.domain_guard.classify(
            query=clean_query,
            conversation_history=conversation_history,
        )

        context = guard_result.context_analysis

        # Handle purely OFF_TOPIC queries without calling AI or retrieval
        if guard_result.category == DomainCategory.OFF_TOPIC:
            redirect_msg = ConstructionResponsePolicy.get_off_topic_redirect(lang)
            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            return ConstructionChatResponse(
                query=clean_query,
                detected_language=lang,
                domain_category=guard_result.category,
                answer=redirect_msg,
                is_off_topic=True,
                is_grounded=True,
                disclaimer="Domain Restriction: Off-topic inquiries are safely redirected.",
                latency_ms=elapsed_ms,
                telemetry={"guard_reasoning": guard_result.reasoning},
                context=context,
            )

        # Handle LEVEL 4 — CRITICAL Structural Emergency & Life-Safety Hazards
        if context is not None and context.risk_level == RiskLevel.CRITICAL:
            advisory_msg = (
                context.safety_assessment.safety_advisory
                if context.safety_assessment and context.safety_assessment.safety_advisory
                else ConstructionResponsePolicy.get_critical_safety_advisory(lang)
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            return ConstructionChatResponse(
                query=clean_query,
                detected_language=lang,
                domain_category=guard_result.category,
                answer=advisory_msg,
                is_grounded=True,
                disclaimer="CRITICAL STRUCTURAL SAFETY ALERT: Immediate life-safety and professional structural inspection required.",
                latency_ms=elapsed_ms,
                telemetry={
                    "risk_level": "critical",
                    "hazard_category": context.safety_assessment.hazard_category.value if context.safety_assessment else "unknown",
                    "guard_reasoning": guard_result.reasoning,
                },
                context=context,
            )

        # Handle LEVEL 3 — HIGH Structural Design, Modification & Sizing Hazards
        if context is not None and context.risk_level in (RiskLevel.HIGH, RiskLevel.HIGH_STRUCTURAL_SAFETY):
            advisory_msg = (
                context.safety_assessment.safety_advisory
                if context.safety_assessment and context.safety_assessment.safety_advisory
                else ConstructionResponsePolicy.get_high_risk_structural_advisory(
                    category=context.safety_assessment.hazard_category if context.safety_assessment else HazardCategory.STRUCTURAL_MODIFICATION,
                    missing_vars=context.safety_assessment.missing_engineering_variables if context.safety_assessment else [],
                    lang=lang,
                )
            )
            if guard_result.category == DomainCategory.MIXED_TOPIC:
                prefix_note = ConstructionResponsePolicy.get_mixed_topic_prefix(lang)
                advisory_msg = prefix_note + advisory_msg

            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            return ConstructionChatResponse(
                query=clean_query,
                detected_language=lang,
                domain_category=guard_result.category,
                answer=advisory_msg,
                is_mixed_topic=(guard_result.category == DomainCategory.MIXED_TOPIC),
                is_grounded=True,
                disclaimer="STRUCTURAL ENGINEERING ADVISORY: Site-specific professional structural engineering review mandatory.",
                latency_ms=elapsed_ms,
                telemetry={
                    "risk_level": "high",
                    "hazard_category": context.safety_assessment.hazard_category.value if context.safety_assessment else "unknown",
                    "missing_variables": context.safety_assessment.missing_engineering_variables if context.safety_assessment else [],
                    "guard_reasoning": guard_result.reasoning,
                },
                context=context,
            )

        # Handle low confidence (< 0.60), AMBIGUOUS, unreliably separated mixed queries, or missing critical variables
        is_low_confidence = (
            guard_result.confidence < 0.60
            or guard_result.confidence_category == ConfidenceCategory.LOW
        )
        is_ambiguous = guard_result.category == DomainCategory.AMBIGUOUS
        is_unreliable_mixed = (
            guard_result.category == DomainCategory.MIXED_TOPIC
            and not guard_result.separation_reliable
        )
        needs_context_clarification = (
            context is not None
            and context.recommended_strategy == ResponseStrategy.CLARIFICATION_REQUIRED
        )

        # Check if query is a follow-up or primary material rate inquiry
        is_material_rate_inquiry = False
        parsed_bridge_query = self.material_rate_bridge.parse_material_query(
            clean_query,
            conversation_history=conversation_history,
        )
        is_followup_rate_inquiry = False
        if conversation_history and len(conversation_history) > 0:
            last_turn = conversation_history[-1].get("content", "").lower()
            if any(k in last_turn for k in ["rate", "قیمت", "ریٹ", "price", "cost", "qeemat"]):
                is_followup_rate_inquiry = True

        if (context is not None and context.intent == ConstructionIntent.MATERIAL_RATE_INQUIRY) or (
            is_followup_rate_inquiry and (parsed_bridge_query.city or parsed_bridge_query.material_category)
        ):
            is_material_rate_inquiry = True

        if not is_material_rate_inquiry and (is_low_confidence or is_ambiguous or is_unreliable_mixed or needs_context_clarification):
            clarify_msg = ConstructionResponsePolicy.get_intelligent_clarification(
                context=context,
                lang=lang,
                query=clean_query,
                is_mixed_inseparable=is_unreliable_mixed,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            return ConstructionChatResponse(
                query=clean_query,
                detected_language=lang,
                domain_category=guard_result.category,
                answer=clarify_msg,
                is_ambiguous=True,
                is_grounded=True,
                disclaimer="Advisory Clarification: Please provide more details on the construction context.",
                latency_ms=elapsed_ms,
                telemetry={
                    "guard_reasoning": guard_result.reasoning,
                    "confidence": guard_result.confidence,
                    "confidence_category": guard_result.confidence_category.value,
                    "separation_reliable": guard_result.separation_reliable,
                },
                context=context,
            )

        # Handle clean MIXED_TOPIC or CONSTRUCTION_RELATED
        effective_query = clean_query
        prefix_note = ""
        is_mixed = False

        if guard_result.category == DomainCategory.MIXED_TOPIC:
            is_mixed = True
            prefix_note = ConstructionResponsePolicy.get_mixed_topic_prefix(lang)
            effective_query = guard_result.sanitized_construction_query or clean_query

        # Material Rate Intelligence Bridge Routing (Phase 03.1)
        if is_material_rate_inquiry and parsed_bridge_query.material_category:
            # If city is missing and not multi-turn resolved, request location clarification
            if not parsed_bridge_query.city:
                mat_name = parsed_bridge_query.product_name or parsed_bridge_query.material_category
                if lang == "ur":
                    clarify_q = f"آپ کس شہر کے لیے {mat_name} کا ریٹ معلوم کرنا چاہتے ہیں؟ (مثلاً لاہور، کراچی، اسلام آباد)"
                elif lang == "roman_ur":
                    clarify_q = f"Aap kis shehar ke liye {mat_name} ka rate malum karna chahte hain? (jaise Lahore, Karachi, Islamabad)"
                else:
                    clarify_q = f"Which city would you like to check {mat_name} rates for? (e.g. Lahore, Karachi, Islamabad)"

                elapsed_ms = (time.monotonic() - start_time) * 1000.0
                return ConstructionChatResponse(
                    query=clean_query,
                    detected_language=lang,
                    domain_category=guard_result.category,
                    answer=clarify_q,
                    is_ambiguous=False,
                    is_grounded=True,
                    disclaimer="Location required for regional market rate quotation.",
                    latency_ms=elapsed_ms,
                    context=context,
                    telemetry={"intent": "material_rate_inquiry", "clarification": "city_missing"},
                )

            # Query the database via the bridge
            if db is not None:
                bridge_result = await self.material_rate_bridge.resolve_material_rate_query(
                    query=effective_query,
                    db=db,
                    conversation_history=conversation_history,
                    language=lang,
                    project_id=project_id,
                )
            else:
                try:
                    from app.core.database import get_session_factory
                    factory = get_session_factory()
                    async with factory() as session:
                        bridge_result = await self.material_rate_bridge.resolve_material_rate_query(
                            query=effective_query,
                            db=session,
                            conversation_history=conversation_history,
                            language=lang,
                            project_id=project_id,
                        )
                except Exception:
                    bridge_result = await self.material_rate_bridge.resolve_material_rate_query(
                        query=effective_query,
                        db=None,
                        conversation_history=conversation_history,
                        language=lang,
                        project_id=project_id,
                    )

            final_answer = prefix_note + bridge_result.formatted_answer if prefix_note else bridge_result.formatted_answer
            elapsed_ms = (time.monotonic() - start_time) * 1000.0

            # Grounded evidence validation (Phase 03G Stage B3.1)
            grounded_eval = GroundedResponsePolicy.evaluate_grounding(
                query=effective_query,
                response_text=final_answer,
                context=context,
                retrieved_chunks=[],
                citations=bridge_result.citations,
                project_id=project_id,
                available_rates=bridge_result.evidence_items,
                language=lang,
            )

            tier_val = (
                EvidenceTier.VERIFIED_ANSWER.value
                if bridge_result.status == "verified_evidence"
                else (
                    EvidenceTier.PARTIALLY_SUPPORTED.value
                    if bridge_result.status == "indicative_evidence"
                    else EvidenceTier.INSUFFICIENT_EVIDENCE.value
                )
            )

            return ConstructionChatResponse(
                query=clean_query,
                detected_language=lang,
                domain_category=guard_result.category,
                answer=final_answer,
                is_off_topic=False,
                is_ambiguous=False,
                is_mixed_topic=is_mixed,
                is_grounded=True,
                retrieved_chunks_count=len(bridge_result.evidence_items),
                citations=bridge_result.citations,
                disclaimer=bridge_result.disclaimer,
                latency_ms=elapsed_ms,
                telemetry={
                    "bridge_status": bridge_result.status,
                    "bridge_telemetry": bridge_result.telemetry,
                    "evidence_tier": tier_val,
                },
                context=context,
                evidence_tier=tier_val,
                grounded_evaluation=grounded_eval,
                evidence_status="verified" if bridge_result.status == "verified_evidence" else "indicative",
                calculation_status="not_applicable",
                regulatory_status="not_applicable",
                citation_status="valid",
            )

        # 2. Scoped Retrieval (if retrieval service is provided)
        retrieved_chunks = []
        if self.retrieval_service is not None:
            retrieval_query = RetrievalQuery(
                query_text=effective_query,
                project_id=project_id,
                scope=scope,
                top_k=top_k,
                minimum_score=0.1,
            )
            ret_result = await self.retrieval_service.retrieve(
                query=retrieval_query,
                requesting_user_id=requesting_user_id,
                allow_synthetic=True,
            )
            retrieved_chunks = ret_result.chunks

        # 3. Assemble Prompt & Execute AI Provider
        system_prompt = get_construction_system_prompt()
        evidence_prompt_part = ""
        if retrieved_chunks:
            evidence_lines = ["\n[AUTHORIZED RETRIEVED EVIDENCE CHUNKS]:"]
            for idx, c in enumerate(retrieved_chunks, start=1):
                evidence_lines.append(
                    f"<evidence id='{c.chunk_id}' source='{c.source_code}' page='{c.page_number}'>\n"
                    f"{c.content}\n"
                    f"</evidence>"
                )
            evidence_prompt_part = "\n".join(evidence_lines)

        messages: List[ChatMessageInput] = []
        # Include recent history if provided
        if conversation_history:
            for turn in conversation_history[-4:]:  # Bounded to last 4 turns
                role = turn.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append(ChatMessageInput(role=role, content=turn.get("content", "")))

        user_content = effective_query
        if evidence_prompt_part:
            user_content = f"{effective_query}\n\n{evidence_prompt_part}"

        messages.append(ChatMessageInput(role="user", content=user_content))

        model_req = ModelRequest(
            messages=messages,
            system_instruction=system_prompt,
            temperature=0.2,
            max_tokens=1500,
            timeout_seconds=30.0,
        )

        model_resp = await self.ai_provider.generate_text(model_req)
        raw_answer = model_resp.content

        # 4. Formulate citations & run validation
        citations: List[Dict[str, Any]] = []
        for c in retrieved_chunks:
            citations.append({
                "title": c.source_title,
                "source_code": c.source_code,
                "page_number": c.page_number,
                "section_or_clause": c.clause_or_section,
                "chunk_id": str(c.chunk_id),
                "document_id": str(c.document_id) if c.document_id else None,
                "project_id": str(c.project_id) if c.project_id else None,
            })

        val_report = None
        if citations:
            val_report = self.citation_validator.validate_citations(
                citations=citations,
                evidence_chunks=retrieved_chunks,
                project_id=project_id,
            )

        final_answer = prefix_note + raw_answer if prefix_note else raw_answer

        # 5. Response Quality & Engineering Validation
        quality_rep = None
        if context:
            quality_rep = self.quality_validator.validate_response(
                query=effective_query,
                response_text=final_answer,
                context=context,
                has_verified_evidence=bool(retrieved_chunks),
            )
            if quality_rep.corrected_answer:
                final_answer = quality_rep.corrected_answer

        # 6. Technical Accuracy & Grounded Evidence Policy (Phase 03G Stage B3)
        grounded_eval = GroundedResponsePolicy.evaluate_grounding(
            query=effective_query,
            response_text=final_answer,
            context=context,
            retrieved_chunks=retrieved_chunks,
            citations=citations,
            project_id=project_id,
            language=lang,
        )
        final_answer = grounded_eval.annotated_answer
        is_grounded_flag = grounded_eval.is_grounded
        if val_report:
            is_grounded_flag = is_grounded_flag and val_report.is_fully_grounded

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        telemetry_payload = {
            "provider": model_resp.provider_name,
            "model": model_resp.model_identifier,
            "tokens": model_resp.usage.model_dump(),
            "guard_reasoning": guard_result.reasoning,
            "evidence_tier": grounded_eval.tier.value,
            "evidence_status": grounded_eval.evidence_status.value,
            "calculation_status": grounded_eval.calculation_status.value,
            "regulatory_status": grounded_eval.regulatory_status.value,
            "citation_status": grounded_eval.citation_status.value,
        }
        if quality_rep:
            telemetry_payload["quality_score"] = quality_rep.overall_quality_score
            telemetry_payload["dimensions_passed"] = quality_rep.dimensions_passed
        if context:
            telemetry_payload["intent"] = context.intent.value
            telemetry_payload["strategy"] = context.recommended_strategy.value

        return ConstructionChatResponse(
            query=clean_query,
            detected_language=lang,
            domain_category=guard_result.category,
            answer=final_answer,
            is_off_topic=False,
            is_ambiguous=False,
            is_mixed_topic=is_mixed,
            is_grounded=is_grounded_flag,
            retrieved_chunks_count=len(retrieved_chunks),
            citations=citations,
            validation_report=val_report,
            disclaimer=(
                "TameerAI Advisory Output: For formal approvals and structural execution, "
                "final verification by a licensed Professional Engineer (PEC) is mandatory."
            ),
            latency_ms=elapsed_ms,
            telemetry=telemetry_payload,
            context=context,
            quality_report=quality_rep,
            evidence_tier=grounded_eval.tier.value,
            grounded_evaluation=grounded_eval,
            evidence_status=grounded_eval.evidence_status.value,
            calculation_status=grounded_eval.calculation_status.value,
            regulatory_status=grounded_eval.regulatory_status.value,
            citation_status=grounded_eval.citation_status.value,
        )
