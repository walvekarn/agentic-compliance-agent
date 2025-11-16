"""Jurisdiction analysis module for compliance risk assessment"""

from typing import List, Tuple
from .risk_models import (
    Jurisdiction,
    EntityContext,
    TaskContext,
    IndustryCategory
)


class JurisdictionAnalyzer:
    """Analyzes jurisdiction-specific compliance risks"""
    
    # Jurisdiction complexity scores (0-1, higher = more complex)
    JURISDICTION_COMPLEXITY = {
        Jurisdiction.EU: 0.9,  # GDPR, complex multi-country
        Jurisdiction.MULTI_JURISDICTIONAL: 0.95,  # Highest complexity
        Jurisdiction.US_FEDERAL: 0.7,  # Complex federal regulations
        Jurisdiction.US_STATE: 0.6,  # State-specific variations
        Jurisdiction.UK: 0.75,  # Post-Brexit complexity
        Jurisdiction.CANADA: 0.65,  # Provincial variations
        Jurisdiction.APAC: 0.7,  # Diverse regulatory landscape
        Jurisdiction.UNKNOWN: 0.5,  # Default moderate risk
    }
    
    # Industry-specific jurisdiction risks
    INDUSTRY_JURISDICTION_RISKS = {
        IndustryCategory.FINANCIAL_SERVICES: {
            Jurisdiction.EU: 0.95,  # MiFID II, PSD2, etc.
            Jurisdiction.US_FEDERAL: 0.9,  # SEC, FINRA, etc.
            Jurisdiction.UK: 0.85,  # FCA regulations
        },
        IndustryCategory.HEALTHCARE: {
            Jurisdiction.US_FEDERAL: 0.95,  # HIPAA
            Jurisdiction.EU: 0.9,  # GDPR + health data
            Jurisdiction.CANADA: 0.85,  # PIPEDA + provincial health laws
        },
        IndustryCategory.TECHNOLOGY: {
            Jurisdiction.EU: 0.85,  # GDPR, DSA, DMA
            Jurisdiction.MULTI_JURISDICTIONAL: 0.9,
        },
    }
    
    def analyze_jurisdiction_risk(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Tuple[float, List[str]]:
        """
        Analyze jurisdiction-specific risks
        
        Args:
            entity: Entity context information
            task: Task context information
            
        Returns:
            Tuple of (risk_score, reasoning_list)
        """
        reasoning = []
        risk_scores = []
        
        # Base jurisdiction complexity
        if not entity.jurisdictions:
            reasoning.append("⚠️ No jurisdiction specified - assuming moderate risk")
            return 0.5, reasoning
        
        # Multiple jurisdictions increase complexity
        if len(entity.jurisdictions) > 1:
            reasoning.append(
                f"🌍 Multi-jurisdictional scope ({len(entity.jurisdictions)} jurisdictions) "
                "increases regulatory complexity"
            )
            risk_scores.append(0.8)
        
        # Analyze each jurisdiction
        for jurisdiction in entity.jurisdictions:
            base_risk = self.JURISDICTION_COMPLEXITY.get(jurisdiction, 0.5)
            risk_scores.append(base_risk)
            
            # Add specific reasoning
            if jurisdiction == Jurisdiction.EU:
                reasoning.append("🇪🇺 EU jurisdiction: GDPR compliance mandatory (strict penalties)")
            elif jurisdiction == Jurisdiction.US_FEDERAL:
                reasoning.append("🇺🇸 US Federal: Multiple agency oversight (SEC, FTC, etc.)")
            elif jurisdiction == Jurisdiction.MULTI_JURISDICTIONAL:
                reasoning.append("🌐 Multi-jurisdictional: Complex regulatory harmonization required")
            
            # Industry-specific jurisdiction risks
            industry_risks = self.INDUSTRY_JURISDICTION_RISKS.get(entity.industry, {})
            if jurisdiction in industry_risks:
                industry_risk = industry_risks[jurisdiction]
                risk_scores.append(industry_risk)
                reasoning.append(
                    f"⚡ {entity.industry.value} in {jurisdiction.value}: "
                    f"Heightened regulatory scrutiny"
                )
        
        # Cross-border data transfer risks
        if task.involves_cross_border:
            risk_scores.append(0.85)
            if Jurisdiction.EU in entity.jurisdictions:
                reasoning.append(
                    "📦 Cross-border data transfer with EU: "
                    "Schrems II compliance and adequacy decisions required"
                )
            else:
                reasoning.append("📦 Cross-border data transfer: Additional compliance requirements")
        
        # Calculate final score
        final_risk = max(risk_scores) if risk_scores else 0.5
        
        return final_risk, reasoning
    
    def identify_applicable_regulations(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> List[str]:
        """
        Identify applicable regulations based on jurisdiction and context
        
        Args:
            entity: Entity context
            task: Task context
            
        Returns:
            List of applicable regulations
        """
        regulations = []
        
        for jurisdiction in entity.jurisdictions:
            if jurisdiction == Jurisdiction.EU:
                regulations.append("GDPR (General Data Protection Regulation)")
                if entity.industry == IndustryCategory.FINANCIAL_SERVICES:
                    regulations.extend(["MiFID II", "PSD2"])
                if task.category.value == "DATA_PRIVACY":
                    regulations.append("ePrivacy Directive")
                    
            elif jurisdiction == Jurisdiction.US_FEDERAL:
                if entity.industry == IndustryCategory.HEALTHCARE:
                    regulations.append("HIPAA (Health Insurance Portability and Accountability Act)")
                if entity.industry == IndustryCategory.FINANCIAL_SERVICES:
                    regulations.extend(["SOX (Sarbanes-Oxley)", "GLBA", "Dodd-Frank"])
                if task.affects_personal_data:
                    regulations.append("FTC Act (Consumer Privacy)")
                    
            elif jurisdiction == Jurisdiction.UK:
                regulations.append("UK GDPR")
                if entity.industry == IndustryCategory.FINANCIAL_SERVICES:
                    regulations.append("FCA Handbook")
                    
            elif jurisdiction == Jurisdiction.CANADA:
                regulations.append("PIPEDA (Personal Information Protection)")
                if entity.industry == IndustryCategory.HEALTHCARE:
                    regulations.append("Provincial Health Privacy Laws")
        
        return regulations

