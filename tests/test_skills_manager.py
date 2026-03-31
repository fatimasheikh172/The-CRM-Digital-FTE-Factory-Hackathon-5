"""
Tests for the Skills Manager module.

Tests cover:
- Skills loading from manifest
- Pipeline execution order
- Performance tracking
- Escalation handling
- Cross-channel customer recognition
"""

import json
import pytest
from pathlib import Path

from skills.skills_manager import SkillsManager, SkillPerformance, PipelineResult


# Get paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
CONTEXT_DIR = PROJECT_ROOT / "context"


@pytest.fixture
def skills_manager():
    """Create a SkillsManager instance for testing."""
    return SkillsManager(
        manifest_path=str(SKILLS_DIR / "skills_manifest.json"),
        context_dir=str(CONTEXT_DIR)
    )


class TestSkillsLoading:
    """TEST 1 - Skills Loading Tests."""
    
    def test_load_manifest_success(self, skills_manager):
        """Verify manifest loads successfully."""
        manifest = skills_manager.get_manifest()
        
        assert manifest is not None
        assert "manifest_version" in manifest
        assert "skills" in manifest
        assert manifest["manifest_version"] == "1.0"
    
    def test_all_five_skills_present(self, skills_manager):
        """Verify all 5 skills are loaded from manifest."""
        manifest = skills_manager.get_manifest()
        skills = manifest.get("skills", [])
        
        assert len(skills) == 5
        
        skill_names = [s["name"] for s in skills]
        assert "knowledge_retrieval" in skill_names
        assert "sentiment_analysis" in skill_names
        assert "escalation_decision" in skill_names
        assert "channel_adaptation" in skill_names
        assert "customer_identification" in skill_names
    
    def test_all_required_fields_exist(self, skills_manager):
        """Verify all required fields exist in each skill definition."""
        manifest = skills_manager.get_manifest()
        required_fields = [
            "skill_id", "name", "display_name", "version",
            "description", "when_to_use", "inputs", "outputs",
            "constraints", "performance"
        ]
        
        for skill in manifest.get("skills", []):
            for field in required_fields:
                assert field in skill, f"Missing field '{field}' in skill '{skill.get('name')}'"
    
    def test_verify_all_skills_loaded(self, skills_manager):
        """Verify SkillsManager has loaded all skill instances."""
        assert skills_manager.verify_all_skills_loaded() is True
        
        expected_skills = {
            "knowledge_retrieval",
            "sentiment_analysis",
            "escalation_decision",
            "channel_adaptation",
            "customer_identification"
        }
        assert set(skills_manager._skills.keys()) == expected_skills
    
    def test_get_skill_info(self, skills_manager):
        """Verify get_skill_info returns correct data."""
        skill_info = skills_manager.get_skill_info("sentiment_analysis")
        
        assert skill_info is not None
        assert skill_info["skill_id"] == "SKL002"
        assert skill_info["name"] == "sentiment_analysis"
        assert "inputs" in skill_info
        assert "outputs" in skill_info


class TestPipelineExecution:
    """TEST 2 - Pipeline Execution Tests."""
    
    def test_pipeline_email_message(self, skills_manager):
        """Run full pipeline with email message."""
        result = skills_manager.run_pipeline(
            message="I cannot login to my account. Please help.",
            channel="email",
            customer_email="john@example.com"
        )
        
        assert isinstance(result, PipelineResult)
        assert result.channel_used == "email"
        assert result.customer_id is not None
        assert len(result.skills_executed) == 5
        assert result.skills_executed == skills_manager.get_pipeline_order()
    
    def test_pipeline_whatsapp_message(self, skills_manager):
        """Run full pipeline with WhatsApp message."""
        result = skills_manager.run_pipeline(
            message="hi my app is not working",
            channel="whatsapp",
            customer_phone="+1234567890"
        )
        
        assert isinstance(result, PipelineResult)
        assert result.channel_used == "whatsapp"
        assert result.customer_id is not None
        assert len(result.skills_executed) == 5
    
    def test_pipeline_web_form_message(self, skills_manager):
        """Run full pipeline with web form message."""
        result = skills_manager.run_pipeline(
            message="How do I reset my password?",
            channel="web_form",
            customer_email="sara@business.com"
        )
        
        assert isinstance(result, PipelineResult)
        assert result.channel_used == "web_form"
        assert result.customer_id is not None
        assert len(result.skills_executed) == 5
    
    def test_pipeline_correct_order(self, skills_manager):
        """Verify correct order of skill execution."""
        expected_order = [
            "customer_identification",
            "sentiment_analysis",
            "knowledge_retrieval",
            "escalation_decision",
            "channel_adaptation"
        ]
        
        result = skills_manager.run_pipeline(
            message="I need help with billing",
            channel="email",
            customer_email="test@example.com"
        )
        
        assert result.skills_executed == expected_order
    
    def test_pipeline_result_fields(self, skills_manager):
        """Verify pipeline result contains all required fields."""
        result = skills_manager.run_pipeline(
            message="How do I use the API?",
            channel="email",
            customer_email="dev@startup.com"
        )
        
        # Check all PipelineResult fields
        assert result.customer_id is not None
        assert isinstance(result.is_new_customer, bool)
        assert isinstance(result.is_returning_customer, bool)
        assert isinstance(result.sentiment_score, float)
        assert result.sentiment_label in ["positive", "neutral", "negative"]
        assert isinstance(result.should_escalate, bool)
        assert result.escalation_urgency in ["normal", "high", "critical"]
        assert result.channel_used == "email"
        assert isinstance(result.total_pipeline_time_ms, float)
        assert result.formatted_response is not None


class TestPerformanceTracking:
    """TEST 3 - Performance Tracking Tests."""
    
    def test_performance_stats_updated(self, skills_manager):
        """Verify performance stats are updated after running pipeline."""
        # Run pipeline multiple times
        for i in range(5):
            skills_manager.run_pipeline(
                message=f"Test message {i}",
                channel="email",
                customer_email=f"test{i}@example.com"
            )
        
        stats = skills_manager.get_skill_stats()
        
        # Verify all skills have been executed
        for skill_name, perf_data in stats.items():
            assert perf_data["total_executions"] >= 5
            assert "avg_response_time_ms" in perf_data
            assert "accuracy_rate" in perf_data
    
    def test_timing_data_recorded(self, skills_manager):
        """Verify timing data is recorded for each skill."""
        initial_stats = skills_manager.get_skill_stats()
        
        # Run single pipeline
        skills_manager.run_pipeline(
            message="Test timing",
            channel="email",
            customer_email="timing@example.com"
        )
        
        final_stats = skills_manager.get_skill_stats()
        
        # Verify executions increased
        for skill_name in ["customer_identification", "sentiment_analysis", 
                          "knowledge_retrieval", "escalation_decision", 
                          "channel_adaptation"]:
            assert final_stats[skill_name]["total_executions"] == \
                   initial_stats[skill_name]["total_executions"] + 1
    
    def test_update_performance_method(self, skills_manager):
        """Verify update_performance method works correctly."""
        # Create fresh manager to ensure clean state
        fresh_manager = SkillsManager(
            manifest_path=str(SKILLS_DIR / "skills_manifest.json"),
            context_dir=str(CONTEXT_DIR)
        )
        
        # Get initial state
        initial_perf = fresh_manager._performance.get("sentiment_analysis")
        initial_executions = initial_perf.total_executions
        initial_successful = initial_perf.successful_executions
        
        # Update performance
        fresh_manager.update_performance("sentiment_analysis", 10.5, True)
        
        # Verify update
        updated_perf = fresh_manager._performance.get("sentiment_analysis")
        assert updated_perf.total_executions == initial_executions + 1
        assert updated_perf.successful_executions == initial_successful + 1
    
    def test_performance_accuracy_calculation(self, skills_manager):
        """Verify accuracy rate is calculated correctly."""
        # Reset by creating fresh manager
        fresh_manager = SkillsManager(
            manifest_path=str(SKILLS_DIR / "skills_manifest.json"),
            context_dir=str(CONTEXT_DIR)
        )
        
        # Simulate some executions
        fresh_manager.update_performance("sentiment_analysis", 5.0, True)
        fresh_manager.update_performance("sentiment_analysis", 6.0, True)
        fresh_manager.update_performance("sentiment_analysis", 7.0, False)
        
        stats = fresh_manager.get_skill_stats()
        perf = stats["sentiment_analysis"]
        
        assert perf["total_executions"] == 3
        assert perf["accuracy_rate"] == pytest.approx(0.67, rel=0.01)


class TestEscalationPipeline:
    """TEST 4 - Escalation Pipeline Tests."""
    
    def test_pipeline_angry_message_escalates(self, skills_manager):
        """Run pipeline with angry message and verify escalation."""
        result = skills_manager.run_pipeline(
            message="This is TERRIBLE! I want my MONEY BACK immediately!",
            channel="email",
            customer_email="angry@customer.com"
        )
        
        assert result.should_escalate is True
        assert result.escalation_reason is not None
        assert result.escalation_urgency in ["high", "critical"]
    
    def test_escalation_decision_triggered(self, skills_manager):
        """Verify escalation_decision skill is triggered for angry messages."""
        # Run pipeline
        result = skills_manager.run_pipeline(
            message="I need to speak to a human agent NOW!",
            channel="whatsapp",
            customer_phone="+9876543210"
        )
        
        # Verify escalation was triggered
        assert result.should_escalate is True
        assert "escalation_decision" in result.skills_executed
        
        # Check escalation was tracked in performance
        stats = skills_manager.get_skill_stats()
        assert stats["escalation_decision"]["escalation_triggers"] >= 1
    
    def test_pipeline_stops_at_escalation(self, skills_manager):
        """Verify pipeline generates escalation response when needed."""
        result = skills_manager.run_pipeline(
            message="I'm going to call my lawyer about this!",
            channel="email",
            customer_email="legal@threat.com"
        )
        
        # Should escalate due to legal threat
        assert result.should_escalate is True
        assert "legal" in result.escalation_reason.lower()
        
        # Response should be escalation response, not knowledge base
        assert "escalated" in result.formatted_response.lower() or \
               "specialist" in result.formatted_response.lower()
    
    def test_refund_request_escalates(self, skills_manager):
        """Verify refund requests trigger escalation."""
        result = skills_manager.run_pipeline(
            message="I want a refund for my subscription",
            channel="web_form",
            customer_email="refund@example.com"
        )
        
        assert result.should_escalate is True
        assert "refund" in result.escalation_reason.lower()
    
    def test_neutral_message_no_escalation(self, skills_manager):
        """Verify neutral messages don't trigger escalation."""
        result = skills_manager.run_pipeline(
            message="How do I reset my password?",
            channel="email",
            customer_email="normal@example.com"
        )
        
        assert result.should_escalate is False
        assert result.escalation_reason is None


class TestCrossChannelPipeline:
    """TEST 5 - Cross Channel Pipeline Tests."""
    
    def test_returning_customer_identified(self, skills_manager):
        """Run pipeline for returning customer and verify identification."""
        # Known customer from simulated database
        result = skills_manager.run_pipeline(
            message="I need help again",
            channel="email",
            customer_email="john@example.com"
        )
        
        assert result.is_new_customer is False
        assert result.is_returning_customer is True
        assert result.customer_id == "CUST-001"
    
    def test_customer_history_found(self, skills_manager):
        """Verify customer_identification finds history for returning customers."""
        result = skills_manager.run_pipeline(
            message="Following up on my previous issue",
            channel="whatsapp",
            customer_email="sara@business.com"
        )
        
        assert result.is_returning_customer is True
        assert result.history_summary is not None
        assert "Enterprise" in result.history_summary or "previous" in result.history_summary.lower()
    
    def test_response_references_past_interaction(self, skills_manager):
        """Verify response can reference past interactions."""
        # Run for known returning customer
        result = skills_manager.run_pipeline(
            message="The issue from last time is back",
            channel="email",
            customer_email="dev@startup.com"
        )
        
        # Customer should be identified as returning
        assert result.is_returning_customer is True
        assert result.customer_id == "CUST-004"
    
    def test_new_customer_created(self, skills_manager):
        """Verify new customers are properly identified."""
        result = skills_manager.run_pipeline(
            message="Hello, I'm new here and need help",
            channel="web_form",
            customer_email="brandnew@customer.com"
        )
        
        assert result.is_new_customer is True
        assert result.is_returning_customer is False
        assert "New customer" in result.history_summary
    
    def test_cross_channel_same_customer(self, skills_manager):
        """Verify same customer recognized across different channels."""
        # First contact via email
        result1 = skills_manager.run_pipeline(
            message="I have a question",
            channel="email",
            customer_email="sara@business.com"
        )
        
        # Second contact via WhatsApp (same customer)
        result2 = skills_manager.run_pipeline(
            message="Quick question",
            channel="whatsapp",
            customer_email="sara@business.com"
        )
        
        # Should be same customer ID
        assert result1.customer_id == result2.customer_id
        assert result2.is_returning_customer is True


class TestSkillPerformanceDataclass:
    """Tests for SkillPerformance dataclass."""
    
    def test_avg_response_time_calculation(self):
        """Verify average response time is calculated correctly."""
        perf = SkillPerformance(skill_id="TEST001", skill_name="test_skill")
        
        # Simulate executions
        perf.total_executions = 3
        perf.total_time_ms = 30.0
        
        assert perf.avg_response_time_ms == 10.0
    
    def test_accuracy_rate_calculation(self):
        """Verify accuracy rate is calculated correctly."""
        perf = SkillPerformance(skill_id="TEST001", skill_name="test_skill")
        
        perf.total_executions = 10
        perf.successful_executions = 8
        perf.failed_executions = 2
        
        assert perf.accuracy_rate == 0.8
    
    def test_escalation_rate_calculation(self):
        """Verify escalation rate is calculated correctly."""
        perf = SkillPerformance(skill_id="TEST001", skill_name="test_skill")
        
        perf.total_executions = 20
        perf.escalation_triggers = 5
        
        assert perf.escalation_rate == 0.25
    
    def test_to_dict_method(self):
        """Verify to_dict method returns correct structure."""
        perf = SkillPerformance(skill_id="TEST001", skill_name="test_skill")
        perf.total_executions = 5
        perf.total_time_ms = 25.0
        perf.successful_executions = 5
        
        result = perf.to_dict()
        
        assert "skill_id" in result
        assert "skill_name" in result
        assert "total_executions" in result
        assert "avg_response_time_ms" in result
        assert "accuracy_rate" in result


class TestManifestWithPerformance:
    """Tests for manifest performance updates."""
    
    def test_get_manifest_with_performance(self, skills_manager):
        """Verify manifest includes performance data after execution."""
        # Run some pipelines to generate performance data
        for i in range(3):
            skills_manager.run_pipeline(
                message=f"Test {i}",
                channel="email",
                customer_email=f"perf{i}@test.com"
            )
        
        manifest = skills_manager.get_manifest_with_performance()
        
        # Check performance data is included
        for skill in manifest.get("skills", []):
            assert "performance" in skill
            assert "avg_response_time_ms" in skill["performance"]
            assert "accuracy_rate" in skill["performance"]
    
    def test_performance_numbers_updated(self, skills_manager):
        """Verify performance numbers reflect actual measurements."""
        # Run pipeline to generate data
        skills_manager.run_pipeline(
            message="Performance test",
            channel="email",
            customer_email="perf@test.com"
        )
        
        manifest = skills_manager.get_manifest_with_performance()
        
        # Find sentiment analysis skill
        sentiment_skill = None
        for skill in manifest.get("skills", []):
            if skill["name"] == "sentiment_analysis":
                sentiment_skill = skill
                break
        
        assert sentiment_skill is not None
        # Should have at least 1 execution recorded
        perf = sentiment_skill["performance"]
        assert perf["avg_response_time_ms"] >= 0
        assert perf["accuracy_rate"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
