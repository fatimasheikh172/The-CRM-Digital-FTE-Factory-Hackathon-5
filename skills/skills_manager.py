"""
Skills Manager for TechCorp Customer Success AI Agent.

This module provides a unified interface for managing and executing
all agent skills in the correct pipeline order, with performance tracking.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# Import all skills
from skills.knowledge_retrieval import KnowledgeRetrievalSkill
from skills.sentiment_analysis import SentimentAnalysisSkill
from skills.escalation_decision import EscalationDecisionSkill
from skills.channel_adaptation import ChannelAdaptationSkill
from skills.customer_identification import CustomerIdentificationSkill


@dataclass
class SkillPerformance:
    """Tracks performance metrics for a single skill."""
    skill_id: str
    skill_name: str
    total_executions: int = 0
    total_time_ms: float = 0.0
    successful_executions: int = 0
    failed_executions: int = 0
    escalation_triggers: int = 0
    
    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average response time in milliseconds."""
        if self.total_executions == 0:
            return 0.0
        return round(self.total_time_ms / self.total_executions, 2)
    
    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate (successful / total)."""
        if self.total_executions == 0:
            return 0.0
        return round(self.successful_executions / self.total_executions, 2)
    
    @property
    def escalation_rate(self) -> float:
        """Calculate escalation trigger rate."""
        if self.total_executions == 0:
            return 0.0
        return round(self.escalation_triggers / self.total_executions, 2)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "total_executions": self.total_executions,
            "avg_response_time_ms": self.avg_response_time_ms,
            "accuracy_rate": self.accuracy_rate,
            "escalation_rate": self.escalation_rate,
            "escalation_triggers": self.escalation_triggers
        }


@dataclass
class PipelineResult:
    """Result of running the full skills pipeline."""
    customer_id: str
    is_new_customer: bool
    is_returning_customer: bool
    sentiment_score: float
    sentiment_label: str
    should_escalate: bool
    escalation_reason: Optional[str]
    escalation_urgency: str
    knowledge_results: Optional[str]
    formatted_response: str
    channel_used: str
    total_pipeline_time_ms: float
    skills_executed: List[str] = field(default_factory=list)
    history_summary: Optional[str] = None


class SkillsManager:
    """
    Manages all agent skills and executes them in the correct pipeline order.
    
    Pipeline Order:
    1. customer_identification (always first)
    2. sentiment_analysis (always second)
    3. knowledge_retrieval (if product question)
    4. escalation_decision (always before response)
    5. channel_adaptation (always last)
    """
    
    # Pipeline execution order
    PIPELINE_ORDER = [
        "customer_identification",
        "sentiment_analysis",
        "knowledge_retrieval",
        "escalation_decision",
        "channel_adaptation"
    ]
    
    def __init__(self, manifest_path: str = None, context_dir: str = None):
        """
        Initialize the Skills Manager.
        
        Args:
            manifest_path: Path to skills_manifest.json.
            context_dir: Path to context directory with docs and rules.
        """
        # Set paths
        if manifest_path is None:
            self.manifest_path = Path(__file__).parent / "skills_manifest.json"
        else:
            self.manifest_path = Path(manifest_path)
        
        if context_dir is None:
            self.context_dir = Path(__file__).parent.parent / "context"
        else:
            self.context_dir = Path(context_dir)
        
        # Load manifest
        self._manifest = self._load_manifest()
        
        # Initialize all skills
        self._skills = self._initialize_skills()
        
        # Initialize performance tracking
        self._performance: Dict[str, SkillPerformance] = {}
        self._init_performance_tracking()
    
    def _load_manifest(self) -> Dict:
        """Load the skills manifest from JSON file."""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skills manifest not found at {self.manifest_path}")
            return {"manifest_version": "1.0", "skills": []}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in skills manifest: {e}")
            return {"manifest_version": "1.0", "skills": []}
    
    def _initialize_skills(self) -> Dict[str, Any]:
        """Initialize all skill instances."""
        return {
            "knowledge_retrieval": KnowledgeRetrievalSkill(
                self.context_dir / "product-docs.md"
            ),
            "sentiment_analysis": SentimentAnalysisSkill(),
            "escalation_decision": EscalationDecisionSkill(
                self.context_dir / "escalation-rules.md"
            ),
            "channel_adaptation": ChannelAdaptationSkill(
                self.context_dir / "brand-voice.md"
            ),
            "customer_identification": CustomerIdentificationSkill()
        }
    
    def _init_performance_tracking(self) -> None:
        """Initialize performance tracking for all skills."""
        for skill_data in self._manifest.get("skills", []):
            skill_id = skill_data.get("skill_id")
            skill_name = skill_data.get("name")
            self._performance[skill_name] = SkillPerformance(
                skill_id=skill_id,
                skill_name=skill_name
            )
    
    def get_manifest(self) -> Dict:
        """
        Get the full skills manifest.
        
        Returns:
            Complete manifest dictionary.
        """
        return self._manifest
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """
        Get information about a specific skill.
        
        Args:
            skill_name: Name of the skill.
            
        Returns:
            Skill information dictionary or None if not found.
        """
        for skill_data in self._manifest.get("skills", []):
            if skill_data.get("name") == skill_name:
                return skill_data
        return None
    
    def run_skill(self, skill_name: str, inputs: Dict) -> Dict:
        """
        Run a single skill with the given inputs.
        
        Args:
            skill_name: Name of the skill to run.
            inputs: Dictionary of inputs for the skill.
            
        Returns:
            Dictionary of outputs from the skill.
            
        Raises:
            ValueError: If skill name is not found.
        """
        if skill_name not in self._skills:
            raise ValueError(f"Unknown skill: {skill_name}")
        
        start_time = time.time()
        success = False
        result = {}
        
        try:
            skill = self._skills[skill_name]
            
            if skill_name == "knowledge_retrieval":
                query = inputs.get("query", "")
                top_k = inputs.get("max_results", 3)
                sections = skill.get_relevant_sections(query, top_k=top_k)
                found = "No relevant documentation found" not in sections
                result = {
                    "results": sections,
                    "confidence": 0.8 if found else 0.0,
                    "found": found
                }
                success = True
                
            elif skill_name == "sentiment_analysis":
                message = inputs.get("message", "")
                analysis = skill.analyze(message)
                score = analysis.get("score", 0.5)
                label = analysis.get("label", "neutral")
                
                # Generate recommendation
                if score < 0.3:
                    recommendation = "Recommend immediate escalation - customer is highly negative"
                elif score < 0.5:
                    recommendation = "Handle with extra empathy - customer is frustrated"
                else:
                    recommendation = "Proceed normally - customer sentiment is acceptable"
                
                result = {
                    "score": score,
                    "label": label,
                    "recommendation": recommendation
                }
                success = True
                
            elif skill_name == "escalation_decision":
                message = inputs.get("message", "")
                sentiment_score = inputs.get("sentiment_score", 0.5)
                decision = skill.should_escalate(message, sentiment_score)
                result = {
                    "should_escalate": decision.get("escalate", False),
                    "reason": decision.get("reason"),
                    "urgency": decision.get("urgency", "normal")
                }
                success = True
                if result["should_escalate"]:
                    self._performance[skill_name].escalation_triggers += 1
                    
            elif skill_name == "channel_adaptation":
                response = inputs.get("response", "")
                channel = inputs.get("channel", "email")
                customer_name = inputs.get("customer_name")
                formatted = skill.format_response(response, channel, customer_name)
                result = {
                    "formatted_response": formatted,
                    "channel_used": channel,
                    "length": len(formatted)
                }
                success = True
                
            elif skill_name == "customer_identification":
                email = inputs.get("email")
                phone = inputs.get("phone")
                identification = skill.identify(email=email, phone=phone)
                customer_info = identification.get("customer_info", {}) or {}
                result = {
                    "customer_id": identification.get("customer_id"),
                    "is_new_customer": identification.get("is_new_customer", True),
                    "is_returning": not identification.get("is_new_customer", True),
                    "previous_channels": [],  # Would need DB integration
                    "history_summary": identification.get("history_summary", ""),
                    "customer_info": customer_info
                }
                success = True
                
        except Exception as e:
            result = {"error": str(e)}
            success = False
        
        # Track performance
        elapsed_ms = (time.time() - start_time) * 1000
        self.update_performance(skill_name, elapsed_ms, success)
        
        return result
    
    def run_pipeline(
        self,
        message: str,
        channel: str,
        customer_email: str = None,
        customer_phone: str = None,
        customer_name: str = None
    ) -> PipelineResult:
        """
        Run the full skills pipeline for a customer message.
        
        Args:
            message: Customer message text.
            channel: Channel type (email, whatsapp, web_form).
            customer_email: Customer email address.
            customer_phone: Customer phone number.
            customer_name: Optional customer name.
            
        Returns:
            PipelineResult with all outputs.
        """
        start_time = time.time()
        skills_executed = []
        
        # STEP 1: Customer Identification (always first)
        customer_result = self.run_skill("customer_identification", {
            "email": customer_email,
            "phone": customer_phone,
            "channel": channel
        })
        skills_executed.append("customer_identification")
        
        customer_id = customer_result.get("customer_id", "unknown")
        is_new_customer = customer_result.get("is_new_customer", True)
        is_returning = customer_result.get("is_returning", False)
        history_summary = customer_result.get("history_summary", "")
        customer_info = customer_result.get("customer_info", {})
        
        # Use customer name from info if not provided
        if not customer_name and customer_info:
            customer_name = customer_info.get("name")
        
        # STEP 2: Sentiment Analysis (always second)
        sentiment_result = self.run_skill("sentiment_analysis", {
            "message": message
        })
        skills_executed.append("sentiment_analysis")
        
        sentiment_score = sentiment_result.get("score", 0.5)
        sentiment_label = sentiment_result.get("label", "neutral")
        
        # STEP 3: Knowledge Retrieval (if product question)
        knowledge_result = self.run_skill("knowledge_retrieval", {
            "query": message,
            "max_results": 3
        })
        skills_executed.append("knowledge_retrieval")
        
        knowledge_results = knowledge_result.get("results", "")
        
        # STEP 4: Escalation Decision (always before response)
        escalation_result = self.run_skill("escalation_decision", {
            "message": message,
            "sentiment_score": sentiment_score,
            "conversation_history": []
        })
        skills_executed.append("escalation_decision")
        
        should_escalate = escalation_result.get("should_escalate", False)
        escalation_reason = escalation_result.get("reason")
        escalation_urgency = escalation_result.get("urgency", "normal")
        
        # Generate response based on escalation
        if should_escalate:
            response_text = self._generate_escalation_response(channel, escalation_reason)
        else:
            response_text = knowledge_results
        
        # STEP 5: Channel Adaptation (always last)
        channel_result = self.run_skill("channel_adaptation", {
            "response": response_text,
            "channel": channel,
            "customer_name": customer_name
        })
        skills_executed.append("channel_adaptation")
        
        formatted_response = channel_result.get("formatted_response", "")
        
        # Calculate total pipeline time
        total_time_ms = (time.time() - start_time) * 1000
        
        return PipelineResult(
            customer_id=customer_id,
            is_new_customer=is_new_customer,
            is_returning_customer=is_returning,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            should_escalate=should_escalate,
            escalation_reason=escalation_reason,
            escalation_urgency=escalation_urgency,
            knowledge_results=knowledge_results,
            formatted_response=formatted_response,
            channel_used=channel,
            total_pipeline_time_ms=round(total_time_ms, 2),
            skills_executed=skills_executed,
            history_summary=history_summary
        )
    
    def _generate_escalation_response(self, channel: str, reason: str) -> str:
        """Generate a response for escalated tickets."""
        if channel == "whatsapp":
            return "I understand your concern. Let me connect you with a human agent who can better assist you."
        elif channel == "email":
            return """Thank you for bringing this to our attention. Your message has been
escalated to our specialist team. A team member will contact you within 24 hours."""
        else:
            return """Your request has been escalated to our specialist team.
We will contact you via email within 24 hours with a resolution."""
    
    def update_performance(self, skill_name: str, time_ms: float, success: bool) -> None:
        """
        Update performance tracking for a skill.
        
        Args:
            skill_name: Name of the skill.
            time_ms: Execution time in milliseconds.
            success: Whether the execution was successful.
        """
        if skill_name not in self._performance:
            return
        
        perf = self._performance[skill_name]
        perf.total_executions += 1
        perf.total_time_ms += time_ms
        
        if success:
            perf.successful_executions += 1
        else:
            perf.failed_executions += 1
    
    def get_skill_stats(self) -> Dict[str, Dict]:
        """
        Get performance statistics for all skills.
        
        Returns:
            Dictionary mapping skill names to their performance data.
        """
        return {
            name: perf.to_dict()
            for name, perf in self._performance.items()
        }
    
    def get_manifest_with_performance(self) -> Dict:
        """
        Get the manifest with updated performance numbers.
        
        Returns:
            Manifest dictionary with performance fields updated.
        """
        manifest_copy = json.loads(json.dumps(self._manifest))
        
        for skill_data in manifest_copy.get("skills", []):
            skill_name = skill_data.get("name")
            if skill_name in self._performance:
                perf = self._performance[skill_name]
                skill_data["performance"] = {
                    "avg_response_time_ms": perf.avg_response_time_ms,
                    "accuracy_rate": perf.accuracy_rate
                }
        
        return manifest_copy
    
    def save_manifest_with_performance(self, output_path: str = None) -> None:
        """
        Save the manifest with updated performance numbers to file.
        
        Args:
            output_path: Optional output path. Defaults to original manifest path.
        """
        if output_path is None:
            output_path = self.manifest_path
        
        manifest_with_perf = self.get_manifest_with_performance()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_with_perf, f, indent=2)
    
    def verify_all_skills_loaded(self) -> bool:
        """
        Verify that all skills from manifest are loaded.
        
        Returns:
            True if all skills are loaded, False otherwise.
        """
        manifest_skills = set()
        for skill_data in self._manifest.get("skills", []):
            manifest_skills.add(skill_data.get("name"))
        
        loaded_skills = set(self._skills.keys())
        
        return manifest_skills == loaded_skills
    
    def get_pipeline_order(self) -> List[str]:
        """
        Get the ordered list of skills in the pipeline.
        
        Returns:
            List of skill names in execution order.
        """
        return self.PIPELINE_ORDER.copy()
