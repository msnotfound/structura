"""
LLM-powered explainer for generating natural language explanations.
Uses Cerebras (Qwen 3 235B) with Groq fallback.
"""

import os
from typing import Optional, List
from datetime import datetime

from ..models.parsing import ParseResult
from ..models.geometry import GeometryResult
from ..models.structural import StructuralAnalysisResult
from ..models.materials import MaterialsResult
from ..models.cost import ProjectCost
from ..models.report import ElementExplanation, OptimizationSuggestion, FullReport

# Mock mode flag
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


class Explainer:
    """Generates natural language explanations using LLMs."""

    def __init__(self):
        self.cerebras_api_key = os.getenv("CEREBRAS_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.client = None
        self.provider = None

        if not MOCK_MODE:
            self._init_client()

    def _init_client(self):
        """Initialize the LLM client."""
        try:
            from openai import OpenAI

            # Try Cerebras first
            if self.cerebras_api_key:
                self.client = OpenAI(
                    api_key=self.cerebras_api_key, base_url="https://api.cerebras.ai/v1"
                )
                self.provider = "cerebras"
                self.model = "qwen-3-32b"
                print("Explainer initialized with Cerebras (Qwen 3)")
            # Fallback to Groq
            elif self.groq_api_key:
                self.client = OpenAI(
                    api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1"
                )
                self.provider = "groq"
                self.model = "llama-3.3-70b-versatile"
                print("Explainer initialized with Groq (Llama 3.3 70B)")
            else:
                print("Warning: No LLM API keys configured, using mock mode")

        except Exception as e:
            print(f"Warning: Failed to initialize LLM client: {e}")
            self.client = None

    def generate_report(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
        materials_result: MaterialsResult,
        cost_result: ProjectCost,
        optimization_suggestions: List[OptimizationSuggestion],
        debug_dir: Optional[str] = None,
    ) -> FullReport:
        """
        Generate a full report with LLM explanations.

        Args:
            parse_result: Parsing result
            geometry_result: Geometry analysis
            structural_result: Structural analysis
            materials_result: Material recommendations
            cost_result: Cost estimation
            optimization_suggestions: Layout suggestions
            debug_dir: Directory for debug output

        Returns:
            FullReport with explanations
        """
        if MOCK_MODE or self.client is None:
            return self._generate_mock_report(
                parse_result,
                geometry_result,
                structural_result,
                materials_result,
                cost_result,
                optimization_suggestions,
            )

        try:
            return self._generate_real_report(
                parse_result,
                geometry_result,
                structural_result,
                materials_result,
                cost_result,
                optimization_suggestions,
                debug_dir,
            )
        except Exception as e:
            print(f"LLM report generation failed: {e}, falling back to mock")
            return self._generate_mock_report(
                parse_result,
                geometry_result,
                structural_result,
                materials_result,
                cost_result,
                optimization_suggestions,
            )

    def _generate_real_report(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
        materials_result: MaterialsResult,
        cost_result: ProjectCost,
        optimization_suggestions: List[OptimizationSuggestion],
        debug_dir: Optional[str] = None,
    ) -> FullReport:
        """Generate report using actual LLM."""

        # Generate project summary
        summary = self._generate_summary(
            parse_result,
            geometry_result,
            structural_result,
            materials_result,
            cost_result,
        )

        # Generate element explanations
        explanations = self._generate_explanations(geometry_result, materials_result)

        # Generate overall assessment
        assessment = self._generate_assessment(
            structural_result, cost_result, optimization_suggestions
        )

        report = FullReport(
            project_summary=summary,
            element_explanations=explanations,
            structural_warnings=structural_result.warnings,
            cost_summary=cost_result,
            optimization_suggestions=optimization_suggestions,
            overall_assessment=assessment,
            methodology_notes="Analysis performed using VLM+CV fusion for parsing, graph-based structural analysis, and multi-criteria material optimization.",
            limitations=[
                "Scale detection may have limited accuracy without explicit scale bar",
                "Wall thickness estimation is approximate",
                "Material costs are estimates and may vary by region",
                "Structural analysis is preliminary - professional review recommended for construction",
            ],
            generated_at=datetime.now().isoformat(),
            version="1.0",
        )

        if debug_dir:
            self._save_debug(report, debug_dir)

        return report

    def _generate_summary(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
        materials_result: MaterialsResult,
        cost_result: ProjectCost,
    ) -> str:
        """Generate project summary using LLM."""

        prompt = f"""Generate a concise project summary (2-3 paragraphs) for a structural analysis report.

Floor Plan Details:
- Building shape: {parse_result.building_shape}
- Number of rooms: {len(parse_result.rooms)}
- Room types: {", ".join(set(r.room_type for r in parse_result.rooms))}
- Total floor area: {cost_result.total_area_sqm:.1f} sqm

Structural Analysis:
- Total walls: {len(geometry_result.classified_walls)}
- Load-bearing walls: {geometry_result.load_bearing_wall_count}
- Partition walls: {geometry_result.partition_wall_count}
- Maximum span: {structural_result.max_span_in_plan:.1f}m
- Structural score: {structural_result.overall_structural_score:.0%}
- Critical warnings: {structural_result.critical_count}

Cost Summary:
- Estimated total cost: ₹{cost_result.grand_total:,.0f}
- Cost per sqm: ₹{cost_result.cost_per_sqm:,.0f}
- Potential savings vs premium: ₹{cost_result.savings_vs_premium:,.0f}

Write professionally, focusing on key findings and recommendations."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a structural engineering report writer. Be concise and professional.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    def _generate_explanations(
        self, geometry_result: GeometryResult, materials_result: MaterialsResult
    ) -> List[ElementExplanation]:
        """Generate explanations for key elements."""

        explanations = []

        # Generate explanations for a sample of walls (not all to save API calls)
        sample_recs = materials_result.recommendations[:5]

        for rec in sample_recs:
            prompt = f"""Explain this material recommendation in 2-3 sentences:

Element: {rec.element_description}
Element Type: {rec.element_type}
Selected Material: {rec.selected.material.name}
Score: {rec.selected.score:.2f}
Context: {", ".join(rec.context_factors)}

Alternative considered: {rec.options[1].material.name if len(rec.options) > 1 else "N/A"} (score: {rec.options[1].score:.2f if len(rec.options) > 1 else 0})

Explain why this material was chosen and what tradeoffs were considered."""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a construction materials expert. Be concise.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.7,
                )

                explanation_text = response.choices[0].message.content.strip()
            except Exception:
                explanation_text = f"{rec.selected.material.name} selected for {rec.element_type} based on optimal balance of cost and structural requirements."

            explanations.append(
                ElementExplanation(
                    element_id=rec.element_id,
                    element_description=rec.element_description,
                    recommendation_text=explanation_text,
                    tradeoff_summary=f"Selected {rec.selected.material.name} (score: {rec.selected.score:.2f}) over alternatives based on {rec.element_type} requirements.",
                    structural_notes=rec.selected.disqualification_reason,
                    measurements_cited=[f"Length: {rec.element_description}"],
                    confidence=rec.selected.score,
                )
            )

        return explanations

    def _generate_assessment(
        self,
        structural_result: StructuralAnalysisResult,
        cost_result: ProjectCost,
        suggestions: List[OptimizationSuggestion],
    ) -> str:
        """Generate overall assessment using LLM."""

        prompt = f"""Write a brief overall assessment (1 paragraph) for this structural analysis:

Structural Score: {structural_result.overall_structural_score:.0%}
Critical Issues: {structural_result.critical_count}
Warnings: {structural_result.warning_count}
Max Span: {structural_result.max_span_in_plan:.1f}m
Requires Engineer Review: {structural_result.requires_engineer_review}

Cost: ₹{cost_result.grand_total:,.0f} (₹{cost_result.cost_per_sqm:,.0f}/sqm)
Potential Savings: ₹{cost_result.savings_vs_premium:,.0f}

Optimization Opportunities: {len(suggestions)}

Provide a professional conclusion with key recommendations."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a structural engineering consultant. Be professional and actionable.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    def _generate_mock_report(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
        materials_result: MaterialsResult,
        cost_result: ProjectCost,
        optimization_suggestions: List[OptimizationSuggestion],
    ) -> FullReport:
        """Generate mock report without LLM."""

        # Generate mock summary
        summary = f"""This {parse_result.building_shape} floor plan contains {len(parse_result.rooms)} rooms with a total area of {cost_result.total_area_sqm:.1f} square meters. The structural analysis identified {geometry_result.load_bearing_wall_count} load-bearing walls and {geometry_result.partition_wall_count} partition walls.

The overall structural integrity score is {structural_result.overall_structural_score:.0%} with {structural_result.critical_count} critical issues and {structural_result.warning_count} warnings requiring attention. The maximum span of {structural_result.max_span_in_plan:.1f}m {"requires intermediate support" if structural_result.max_span_in_plan > 4.5 else "is within acceptable limits"}.

The estimated construction cost is ₹{cost_result.grand_total:,.0f} (₹{cost_result.cost_per_sqm:,.0f}/sqm), representing a potential savings of ₹{cost_result.savings_vs_premium:,.0f} compared to premium material options."""

        # Generate mock explanations
        explanations = []
        for rec in materials_result.recommendations[:3]:
            explanations.append(
                ElementExplanation(
                    element_id=rec.element_id,
                    element_description=rec.element_description,
                    recommendation_text=f"{rec.selected.material.name} is recommended for this {rec.element_type} due to its optimal balance of cost (₹{rec.selected.material.cost_per_sqm}/sqm) and structural properties ({rec.selected.material.compressive_strength_mpa} MPa strength).",
                    tradeoff_summary=f"Score: {rec.selected.score:.2f}. Key factors: {', '.join(rec.context_factors[:2])}",
                    structural_notes=None,
                    measurements_cited=[],
                    confidence=rec.selected.score,
                )
            )

        # Generate mock assessment
        assessment = f"""Based on the comprehensive analysis, this floor plan demonstrates {"good" if structural_result.overall_structural_score > 0.7 else "acceptable"} structural integrity. {"Professional structural engineering review is recommended before construction." if structural_result.requires_engineer_review else "The design appears suitable for residential construction with the recommended materials."}

Key recommendations: Address the {structural_result.warning_count} identified warnings, consider the {len(optimization_suggestions)} optimization suggestions for potential cost savings, and ensure proper material specifications during construction."""

        return FullReport(
            project_summary=summary,
            element_explanations=explanations,
            structural_warnings=structural_result.warnings,
            cost_summary=cost_result,
            optimization_suggestions=optimization_suggestions,
            overall_assessment=assessment,
            methodology_notes="Analysis performed using VLM+CV fusion parsing, graph-based geometry analysis, and multi-criteria material optimization. (Mock mode - LLM explanations disabled)",
            limitations=[
                "Scale detection accuracy depends on image quality",
                "Wall thickness estimation is approximate",
                "Regional material cost variations not accounted for",
                "Professional structural review recommended for construction",
            ],
            generated_at=datetime.now().isoformat(),
            version="1.0-mock",
        )

    def _save_debug(self, report: FullReport, debug_dir: str):
        """Save report debug info."""
        import json

        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "generated_at": report.generated_at,
            "version": report.version,
            "summary_length": len(report.project_summary),
            "explanation_count": len(report.element_explanations),
            "warning_count": len(report.structural_warnings),
            "suggestion_count": len(report.optimization_suggestions),
            "llm_provider": self.provider or "mock",
        }

        with open(os.path.join(debug_dir, "explainer_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
